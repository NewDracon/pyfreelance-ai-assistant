import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.core.config import settings
from freelance_assistant.core.database import engine
from freelance_assistant.bot.handlers import start, jobs, settings as settings_h, subscribe, help as help_h
from freelance_assistant.bot.middlewares.throttling import ThrottlingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # session_factory доступен во всех хендлерах как аргумент
    dp["session_factory"] = async_sessionmaker(engine, expire_on_commit=False)

    dp.include_router(start.router)
    dp.include_router(jobs.router)
    dp.include_router(settings_h.router)
    dp.include_router(subscribe.router)
    dp.include_router(help_h.router)
    throttler = ThrottlingMiddleware(default_rate=1.0)
    dp.message.middleware(throttler)  # 1 секунда между запросами
    dp.callback_query.middleware(throttler)  # 0.5 секунды для кнопок
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())