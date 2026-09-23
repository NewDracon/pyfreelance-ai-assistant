from aiogram import flags
from freelance_assistant.bot.middlewares.throttling import ThrottlingMiddleware
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from freelance_assistant.bot.keyboards.main_menu import main_menu_keyboard

router = Router()

HELP_TEXT = (
    "🤖 <b>Доступные команды:</b>\n\n"
    "/start — начать работу\n"
    "/get_jobs — топ-10 заказов по вашим фильтрам\n"
    "/job &lt;id&gt; — детальная карточка заказа\n"
    "/settings — настроить категории, бюджет, сайты\n"
    "/subscribe — подписаться на уведомления\n"
    "/unsubscribe — отписаться\n"
    "/help — эта справка\n\n"
    "💡 <b>Совет:</b> начните с /settings — выберите категории и минимальный бюджет, "
    "чтобы получать только релевантные заказы."
)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(HELP_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 Главное меню. Что будем делать?",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:jobs")
@flags.rate_limit(rate=2.0)
async def cb_menu_jobs(callback: CallbackQuery, session_factory):
    """Программный вызов /get_jobs из inline-меню."""
    from freelance_assistant.bot.services.user_service import get_or_create_user
    from freelance_assistant.bot.services.job_service import get_top_jobs_for_user
    from freelance_assistant.bot.keyboards.job_card import jobs_list_keyboard

    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
        jobs = await get_top_jobs_for_user(session, user, limit=10)

    if not jobs:
        await callback.message.edit_text(
            "😕 По вашим фильтрам пока нет заказов. Попробуйте /settings.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.message.edit_text(
            f"🔥 Найдено <b>{len(jobs)}</b> заказов:",
            reply_markup=jobs_list_keyboard(jobs),
        )
    await callback.answer()


@router.callback_query(F.data == "menu:subscription")
async def cb_menu_subscription(callback: CallbackQuery, session_factory):
    from freelance_assistant.bot.services.user_service import get_or_create_user

    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)

    status = "🔔 активна" if user.is_subscribed else "🔕 отключена"
    await callback.message.edit_text(
        f"Текущий статус подписки: {status}\n\n"
        "Команды: /subscribe, /unsubscribe",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()