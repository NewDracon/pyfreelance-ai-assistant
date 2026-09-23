from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from freelance_assistant.models.order import Order


def job_card_keyboard(order: Order) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Открыть на бирже", url=order.url),
            ],
            [
                InlineKeyboardButton(text="📋 Похожие", callback_data=f"job:similar:{order.id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="menu:jobs"),
            ],
        ]
    )


def jobs_list_keyboard(orders_with_analysis) -> InlineKeyboardMarkup:
    """Кнопки-ссылки на карточки заказов."""
    rows = []
    for i, (order, _) in enumerate(orders_with_analysis, 1):
        rows.append([
            InlineKeyboardButton(
                text=f"{i}. {order.title[:40]}",
                callback_data=f"job:view:{order.id}",
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)