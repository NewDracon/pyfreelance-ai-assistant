from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from freelance_assistant.models.bot_user import BotUser

# Список категорий и их человекочитаемые названия
CATEGORIES = [
    ("backend_api", "Backend API"),
    ("data_processing", "Data Processing"),
    ("ml_nlp", "ML/NLP"),
    ("automation", "Автоматизация"),
    ("devops", "DevOps"),
    ("web_scraping", "Веб-скрапинг"),
    ("chatbots_ai_agents", "Чат-боты / AI-агенты"),
]

BUDGET_PRESETS = [
    (0, "Без ограничений"),
    (10000, "от 10 000 ₽"),
    (30000, "от 30 000 ₽"),
    (50000, "от 50 000 ₽"),
    (100000, "от 100 000 ₽"),
]


def settings_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Категории", callback_data="settings:categories")],
            [InlineKeyboardButton(text="💰 Минимальный бюджет", callback_data="settings:budget")],
            [InlineKeyboardButton(text="🌐 Сайты", callback_data="settings:sites")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu:main")],
        ]
    )


def categories_keyboard(user: BotUser) -> InlineKeyboardMarkup:
    selected = set(user.categories or [])
    rows = []
    for code, title in CATEGORIES:
        mark = "✅" if code in selected else "⬜"
        rows.append([
            InlineKeyboardButton(text=f"{mark} {title}", callback_data=f"cat:toggle:{code}")
        ])
    rows.append([InlineKeyboardButton(text="💾 Готово", callback_data="settings:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def budget_keyboard(user: BotUser) -> InlineKeyboardMarkup:
    rows = []
    for amount, title in BUDGET_PRESETS:
        mark = "✅" if user.min_budget == amount else "⬜"
        rows.append([
            InlineKeyboardButton(text=f"{mark} {title}", callback_data=f"budget:set:{amount}")
        ])
    rows.append([InlineKeyboardButton(text="💾 Готово", callback_data="settings:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sites_keyboard(user: BotUser, all_sites: list[str]) -> InlineKeyboardMarkup:
    selected = set(user.sites or [])
    rows = []
    for site in all_sites:
        mark = "✅" if site in selected else "⬜"
        rows.append([
            InlineKeyboardButton(text=f"{mark} {site}", callback_data=f"site:toggle:{site}")
        ])
    rows.append([InlineKeyboardButton(text="💾 Готово", callback_data="settings:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)