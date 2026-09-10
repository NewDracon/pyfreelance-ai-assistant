import asyncio
import asyncpg
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.core.config import settings
from freelance_assistant.core.database import engine
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis
from freelance_assistant.services.rag_analyzer import RAGAnalyzer
from freelance_assistant.infrastructure.vector_store.chroma_client import ChromaClient

# ─── Настройки ────────────────────────────────────────────────────────────
MAX_PARALLEL_ANALYSES = 3      # сколько заказов анализируется одновременно
QUEUE_MAX_SIZE = 1000          # защита от неограниченного роста очереди

# ─── Инфраструктура ───────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Очередь: сюда слушатель кладёт order_id, оттуда воркеры их достают
_analysis_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)

# Сильные ссылки на воркеры, чтобы их не собрал GC
_worker_tasks: set[asyncio.Task] = set()


# ─── Анализ одного заказа ─────────────────────────────────────────────────
async def _analyze_one(order_id: str) -> None:
    try:
        uid = UUID(order_id)
    except ValueError:
        print(f"[worker] Invalid UUID: {order_id}")
        return

    chroma = ChromaClient()
    async with AsyncSessionLocal() as session:
        order = (await session.execute(
            select(Order).where(Order.id == uid)
        )).scalar_one_or_none()
        if order is None:
            print(f"[worker] Order {order_id} not found")
            return

        already = (await session.execute(
            select(OrderAnalysis.id).where(OrderAnalysis.order_id == uid)
        )).scalar_one_or_none()
        if already is not None:
            print(f"[worker] Order {order_id} already analyzed, skipping")
            return

        analyzer = RAGAnalyzer(session, chroma)
        try:
            await analyzer.analyze_order(order)
            print(f"[worker] ✅ Order {order_id} analyzed")
        except Exception as e:
            print(f"[worker] ❌ Failed order {order_id}: {e}")


# ─── Воркер: читает очередь и анализирует по одному ───────────────────────
async def _worker(worker_id: int) -> None:
    print(f"[worker-{worker_id}] started")
    try:
        while True:
            order_id = await _analysis_queue.get()
            try:
                await _analyze_one(order_id)
            finally:
                _analysis_queue.task_done()   # важно для join()
    except asyncio.CancelledError:
        print(f"[worker-{worker_id}] stopped")
        raise


# ─── Слушатель NOTIFY ─────────────────────────────────────────────────────
def _handle_notification(connection, pid, channel, payload):
    print(f"[listener] NOTIFY '{channel}': order_id={payload}")
    try:
        _analysis_queue.put_nowait(payload)
    except asyncio.QueueFull:
        # Очередь переполнена — это значит, парсер опережает анализатор
        # на >1000 заказов. Логируем и пропускаем (не блокируем NOTIFY-цикл).
        print(f"[listener] ⚠️ Queue full, dropping order {payload}")


async def listen_for_new_orders() -> None:
    # asyncpg не понимает '+asyncpg' в DSN — убираем его
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    # Запускаем N воркеров
    for i in range(MAX_PARALLEL_ANALYSES):
        t = asyncio.create_task(_worker(i + 1), name=f"analyzer-worker-{i+1}")
        _worker_tasks.add(t)
        t.add_done_callback(_worker_tasks.discard)

    await conn.add_listener("new_orders", _handle_notification)
    print(f"[listener] Listening on 'new_orders' with {MAX_PARALLEL_ANALYSES} workers")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await conn.close()
        for t in list(_worker_tasks):
            t.cancel()
        print("[listener] Connection closed, workers stopped")