from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.bot.services.user_service import get_or_create_user, update_user
from freelance_assistant.bot.services.job_service import get_all_sites
from freelance_assistant.bot.keyboards.settings import (
    settings_menu_keyboard,
    categories_keyboard,
    budget_keyboard,
    sites_keyboard,
    CATEGORIES,
    BUDGET_PRESETS,
)
from freelance_assistant.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


def _settings_summary(user) -> str:
    cats = user.categories or []
    cat_names = [title for code, title in CATEGORIES if code in cats] or ["все"]
    budget = (
        "без ограничений"
        if not user.min_budget
        else f"от {user.min_budget:,} ₽".replace(",", " ")
    )
    sites = user.sites or ["все"]
    return (
        "⚙️ <b>Ваши настройки:</b>\n\n"
        f"📂 Категории: {', '.join(cat_names)}\n"
        f"💰 Мин. бюджет: {budget}\n"
        f"🌐 Сайты: {', '.join(sites)}"
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(
            session, telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
    await message.answer(_settings_summary(user), reply_markup=settings_menu_keyboard())


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
    await callback.message.edit_text(
        _settings_summary(user), reply_markup=settings_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings:back")
async def cb_settings_back(callback: CallbackQuery, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
    await callback.message.edit_text(
        _settings_summary(user), reply_markup=settings_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings:categories")
async def cb_categories(callback: CallbackQuery, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
    await callback.message.edit_text(
        "Выберите интересные категории (нажмите, чтобы переключить):",
        reply_markup=categories_keyboard(user),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:toggle:"))
async def cb_cat_toggle(callback: CallbackQuery, session_factory: async_sessionmaker):
    code = callback.data.split(":", 2)[2]
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
        cats = set(user.categories or [])
        if code in cats:
            cats.discard(code)
        else:
            cats.add(code)
        user = await update_user(session, callback.from_user.id, categories=list(cats))

    await callback.message.edit_reply_markup(reply_markup=categories_keyboard(user))
    await callback.answer()


@router.callback_query(F.data == "settings:budget")
async def cb_budget(callback: CallbackQuery, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
    await callback.message.edit_text(
        "Выберите минимальный бюджет:",
        reply_markup=budget_keyboard(user),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("budget:set:"))
async def cb_budget_set(callback: CallbackQuery, session_factory: async_sessionmaker):
    amount = int(callback.data.split(":", 2)[2])
    async with session_factory() as session:
        user = await update_user(session, callback.from_user.id, min_budget=amount)
    await callback.message.edit_reply_markup(reply_markup=budget_keyboard(user))
    await callback.answer(f"Установлено: {amount} ₽")


@router.callback_query(F.data == "settings:sites")
async def cb_sites(callback: CallbackQuery, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
        sites = await get_all_sites(session)
    if not sites:
        await callback.answer("Пока нет ни одного сайта в базе", show_alert=True)
        return
    await callback.message.edit_text(
        "Выберите сайты:",
        reply_markup=sites_keyboard(user, sites),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("site:toggle:"))
async def cb_site_toggle(callback: CallbackQuery, session_factory: async_sessionmaker):
    site = callback.data.split(":", 2)[2]
    async with session_factory() as session:
        user = await get_or_create_user(session, telegram_id=callback.from_user.id)
        sites = set(user.sites or [])
        if site in sites:
            sites.discard(site)
        else:
            sites.add(site)
        user = await update_user(session, callback.from_user.id, sites=list(sites))
        all_sites = await get_all_sites(session)
    await callback.message.edit_reply_markup(reply_markup=sites_keyboard(user, all_sites))
    await callback.answer()