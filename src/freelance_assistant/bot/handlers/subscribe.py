from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.bot.services.user_service import get_or_create_user, update_user
from freelance_assistant.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=message.from_user.id)
        if not user.is_subscribed:
            await update_user(
                session,
                message.from_user.id,
                is_subscribed=True,
                subscribed_at=datetime.utcnow(),
            )
    await message.answer(
        "🔔 Вы подписаны на уведомления о новых заказах по вашим фильтрам.\n"
        "Отписаться: /unsubscribe",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, session_factory: async_sessionmaker):
    async with session_factory() as session:
        await get_or_create_user(session, telegram_id=message.from_user.id)
        await update_user(session, message.from_user.id, is_subscribed=False)
    await message.answer(
        "🔕 Подписка отключена.",
        reply_markup=main_menu_keyboard(),
    )