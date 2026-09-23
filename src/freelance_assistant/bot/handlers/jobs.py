from uuid import UUID
from aiogram import flags
from freelance_assistant.bot.middlewares.throttling import ThrottlingMiddleware
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from freelance_assistant.bot.services.user_service import get_or_create_user
from freelance_assistant.bot.services.job_service import (
    get_top_jobs_for_user,
    get_job_by_id,
)
from freelance_assistant.bot.keyboards.job_card import (
    job_card_keyboard,
    jobs_list_keyboard,
)
from freelance_assistant.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


def _format_job_card(order, analysis, full: bool = False) -> str:
    """Форматирует карточку заказа в HTML."""
    lines = [
        f"<b>{order.title}</b>",
        "",
        f"🌐 <b>Биржа:</b> {order.site_name}",
        f"💰 <b>Бюджет:</b> {order.budget or 'не указан'}",
    ]

    if order.published_at:
        lines.append(f"📅 <b>Опубликован:</b> {order.published_at:%d.%m.%Y %H:%M}")
    if order.answers is not None:
        lines.append(f"💬 <b>Откликов:</b> {order.answers}")

    if analysis:
        lines.append("")
        lines.append("🤖 <b>AI-анализ:</b>")
        cat = analysis.category or "—"
        conf = analysis.category_confidence or 0
        lines.append(f"• Категория: <code>{cat}</code> (уверенность {conf:.0%})")
        if analysis.estimated_demand:
            demand_emoji = {"high": "🔥", "medium": "⚡", "low": "❄️"}.get(
                analysis.estimated_demand, ""
            )
            lines.append(f"• Спрос: {demand_emoji} {analysis.estimated_demand}")
        if analysis.popularity_score is not None:
            lines.append(f"• Популярность: {analysis.popularity_score:.0%}")

        if full and analysis.questions:
            lines.append("")
            lines.append("❓ <b>Вопросы заказчику:</b>")
            for q in analysis.questions[:5]:
                lines.append(f"  • {q}")

    if full and order.description:
        lines.append("")
        lines.append("📝 <b>Описание:</b>")
        desc = order.description[:800] + ("..." if len(order.description) > 800 else "")
        lines.append(f"<i>{desc}</i>")

    return "\n".join(lines)


@router.message(Command("get_jobs"))
@flags.rate_limit(rate=10.0)  # Не чаще одного раза в 10 секунд
async def cmd_get_jobs(message: Message, session_factory: async_sessionmaker):
    async with session_factory() as session:
        user = await get_or_create_user(
            session, telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        jobs = await get_top_jobs_for_user(session, user, limit=10)

    if not jobs:
        await message.answer(
            "😕 По вашим фильтрам пока нет заказов.\n"
            "Попробуйте ослабить настройки: /settings",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        f"🔥 Найдено <b>{len(jobs)}</b> заказов по вашим фильтрам.\n"
        "Нажмите на карточку, чтобы посмотреть детали:",
        reply_markup=jobs_list_keyboard(jobs),
    )


@router.callback_query(F.data.startswith("job:view:"))
async def cb_job_view(callback: CallbackQuery, session_factory: async_sessionmaker):
    order_id_str = callback.data.split(":", 2)[2]
    try:
        order_id = UUID(order_id_str)
    except ValueError:
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    async with session_factory() as session:
        row = await get_job_by_id(session, order_id)

    if row is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order, analysis = row
    text = _format_job_card(order, analysis, full=True)
    await callback.message.edit_text(
        text, reply_markup=job_card_keyboard(order), disable_web_page_preview=True
    )
    await callback.answer()


@router.message(Command("job"))
async def cmd_job(message: Message, session_factory: async_sessionmaker):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: <code>/job &lt;uuid&gt;</code>")
        return

    try:
        order_id = UUID(args[1].strip())
    except ValueError:
        await message.answer("❌ Некорректный UUID.")
        return

    async with session_factory() as session:
        row = await get_job_by_id(session, order_id)

    if row is None:
        await message.answer("Заказ не найден.")
        return

    order, analysis = row
    text = _format_job_card(order, analysis, full=True)
    await message.answer(
        text, reply_markup=job_card_keyboard(order), disable_web_page_preview=True
    )