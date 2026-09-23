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
    dp["session_factory"] = async_sessionmaker(engine, expire_on_commit=False)

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

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())