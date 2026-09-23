import re
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis
from freelance_assistant.models.bot_user import BotUser


def parse_budget(budget: str | None) -> int:
    """Извлекает первое число из строки бюджета. 0, если не удалось."""
    if not budget:
        return 0
    match = re.search(r"\d+", budget.replace(" ", "").replace("\u00a0", ""))
    return int(match.group()) if match else 0


async def get_top_jobs_for_user(
    session: AsyncSession, user: BotUser, limit: int = 10
):
    """Возвращает список (Order, OrderAnalysis), отфильтрованный под настройки пользователя."""
    stmt = (
        select(Order, OrderAnalysis)
        .join(OrderAnalysis, OrderAnalysis.order_id == Order.id)
        .where(OrderAnalysis.is_relevant.is_(True))
        .where((Order.is_taken.is_(None)) | (Order.is_taken.is_(False)))
        .order_by(desc(OrderAnalysis.popularity_score), desc(Order.published_at))
        .limit(200)  # запас под фильтрацию
    )
    rows = (await session.execute(stmt)).all()

    filtered = []
    for order, analysis in rows:
        if user.categories and analysis.category not in user.categories:
            continue
        if user.sites and order.site_name not in user.sites:
            continue
        if user.min_budget > 0:
            if parse_budget(order.budget) < user.min_budget:
                continue
        filtered.append((order, analysis))
        if len(filtered) >= limit:
            break
    return filtered


async def get_job_by_id(session: AsyncSession, order_id: UUID):
    stmt = (
        select(Order, OrderAnalysis)
        .outerjoin(OrderAnalysis, OrderAnalysis.order_id == Order.id)
        .where(Order.id == order_id)
    )
    return (await session.execute(stmt)).first()


async def get_all_sites(session: AsyncSession) -> list[str]:
    stmt = select(Order.site_name).distinct().order_by(Order.site_name)
    result = await session.execute(stmt)
    return [row[0] for row in result.all() if row[0]]