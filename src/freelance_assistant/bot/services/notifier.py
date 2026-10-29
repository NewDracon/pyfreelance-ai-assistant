import asyncio
import asyncpg
from uuid import UUID

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from freelance_assistant.core.config import settings
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis
from freelance_assistant.models.bot_user import BotUser
from freelance_assistant.bot.services.job_service import parse_budget

_background: set[asyncio.Task] = set()
# Telegram: ~1 сообщение в секунду на чат, ~30/сек глобально.
# Простой семафор ограничит глобальную скорость.
_send_semaphore = asyncio.Semaphore(20)


def _matches(order: Order, analysis: OrderAnalysis, user: BotUser) -> bool:
    if user.categories and analysis.category not in user.categories:
        return False
    if user.sites and order.site_name not in user.sites:
        return False
    if user.min_budget and parse_budget(order.budget) < user.min_budget:
        return False
    return True


async def _notify_for_order(
    bot: Bot,
    session_factory: async_sessionmaker,
    order_id: UUID,
) -> None:
    async with session_factory() as session:
        row = (await session.execute(
            select(Order, OrderAnalysis)
            .join(OrderAnalysis, OrderAnalysis.order_id == Order.id)
            .where(Order.id == order_id)
            .where(OrderAnalysis.is_relevant.is_(True))
        )).first()
        if row is None:
            return
        order, analysis = row

        users = (await session.execute(
            select(BotUser).where(BotUser.is_subscribed.is_(True))
        )).scalars().all()

    if not users:
        return

    text = (
        f"🔥 <b>Новый заказ по вашим фильтрам</b>\n\n"
        f"<b>{order.title}</b>\n"
        f"🌐 {order.site_name} · 💰 {order.budget or 'не указан'}\n"
        f"📂 {analysis.category}\n\n"
        f"<a href='{order.url}'>Открыть на бирже</a>"
    )

    for user in users:
        if not _matches(order, analysis, user):
            continue
        async with _send_semaphore:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    disable_web_page_preview=True,
                )
                # 50 мс паузы — подстраховка от флуда на много подписчиков
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"[notifier] failed to send to {user.telegram_id}: {e}")


def _on_notify(connection, pid, channel, payload):
    task = asyncio.create_task(
        _notify_for_order(_bot_ref[0], _session_factory_ref[0], UUID(payload))
    )
    _background.add(task)
    task.add_done_callback(_background.discard)


# Заполняются при старте
_bot_ref: list[Bot | None] = [None]
_session_factory_ref: list = [None]


async def listen_order_analyzed(
    bot: Bot,
    session_factory: async_sessionmaker,
) -> None:
    _bot_ref[0] = bot
    _session_factory_ref[0] = session_factory

    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    await conn.add_listener("order_analyzed", _on_notify)
    print("[notifier] Listening on 'order_analyzed'")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await conn.close()