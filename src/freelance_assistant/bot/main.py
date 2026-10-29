import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.core.config import settings
from freelance_assistant.core.database import engine
from freelance_assistant.bot.handlers import (
    start,
    jobs,
    settings as settings_h,
    subscribe,
    help as help_h,
)
from freelance_assistant.bot.services.notifier import listen_order_analyzed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_session() -> AiohttpSession | None:
    """
    Возвращает AiohttpSession с прокси, если BOT_PROXY_URL задан,
    иначе None (aiogram создаст сессию по умолчанию без прокси).
    """
    proxy_url = (settings.BOT_PROXY_URL or "").strip()
    if not proxy_url:
        logger.info("Bot: proxy disabled, using direct connection")
        return None

    # В aiogram 3.x прокси передаётся через параметр proxy
    session = AiohttpSession(proxy=proxy_url)
    logger.info(f"Bot: using proxy {proxy_url}")
    return session


async def main():
    session = build_session()

    bot = Bot(
        token=settings.BOT_TOKEN,
        session=session,                       # None → дефолтная сессия
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    dp["session_factory"] = session_factory

    # Регистрируем throttling middleware (если добавляли)
    from freelance_assistant.bot.middlewares.throttling import ThrottlingMiddleware
    throttler = ThrottlingMiddleware(default_rate=1.0)
    dp.message.middleware(throttler)
    dp.callback_query.middleware(throttler)

    dp.include_router(start.router)
    dp.include_router(jobs.router)
    dp.include_router(settings_h.router)
    dp.include_router(subscribe.router)
    dp.include_router(help_h.router)

    # Запускаем фоновый слушатель для рассылки уведомлений
    logger.info("Starting background notifier...")
    notifier_task = asyncio.create_task(
        listen_order_analyzed(bot, session_factory)
    )

    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        # При остановке бота аккуратно гасим фоновую задачу
        logger.info("Stopping background notifier...")
        notifier_task.cancel()
        try:
            await notifier_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())