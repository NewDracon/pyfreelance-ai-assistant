import asyncio
import sys
from pathlib import Path

# Добавляем путь к src для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, asc
from freelance_assistant.core.config import settings
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis
from freelance_assistant.services.order_fetcher import OrderFetcher
from freelance_assistant.services.rag_analyzer import RAGAnalyzer
from freelance_assistant.infrastructure.vector_store.chroma_client import ChromaClient

SLEEP_BETWEEN = 0.5      # Задержка между запросами (сек), чтобы не перегрузить API

async def analyze_all_orders_sorted():
    # Создаём сессию БД
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    chroma = ChromaClient()

    async with async_session() as session:
        # Получаем все заказы, у которых нет анализа, сортируем по created_at (самые старые первыми)
        stmt = (
            select(Order)
            .where(Order.id.not_in(select(OrderAnalysis.order_id)))
            .order_by(asc(Order.created_at))   # сортировка по возрастанию (старые → новые)
        )
        result = await session.execute(stmt)
        orders = result.scalars().all()
        total = len(orders)
        print(f"Найдено {total} заказов для анализа (обработка от старых к новым)")

        analyzer = RAGAnalyzer(session, chroma)
        processed = 0
        errors = 0

        for i, order in enumerate(orders, 1):
            try:
                print(f"Обработка заказа {i}/{total}: {order.title[:50]}... (created_at: {order.created_at})")
                analysis = await analyzer.analyze_order(order)
                processed += 1
                await asyncio.sleep(SLEEP_BETWEEN)
            except Exception as e:
                print(f"Ошибка при анализе заказа {order.id}: {e}")
                errors += 1
                # Можно добавить логику повторной попытки (например, 3 раза с экспоненциальной задержкой)

        print(f"\n✅ Готово! Обработано: {processed}, Ошибок: {errors}")

if __name__ == "__main__":
    asyncio.run(analyze_all_orders_sorted())