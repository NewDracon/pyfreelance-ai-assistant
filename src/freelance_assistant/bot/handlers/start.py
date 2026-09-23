from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.bot.services.user_service import get_or_create_user
from freelance_assistant.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session_factory: async_sessionmaker):
    async with session_factory() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

    text = (
        f"👋 Привет, {message.from_user.first_name or 'друг'}!\n\n"
        "Я — бот для поиска актуальных заказов по <b>Python</b> и <b>AI</b>.\n\n"
        "🔧 Что я умею:\n"
        "• /get_jobs — топовые заказы по вашим фильтрам\n"
        "• /settings — настроить категории, бюджет, сайты\n"
        "• /subscribe — подписаться на новые заказы\n"
        "• /help — все команды\n\n"
        "Совет: сначала настройте фильтры через /settings."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())