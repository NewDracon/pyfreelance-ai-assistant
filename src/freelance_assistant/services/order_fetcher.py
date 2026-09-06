from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis

class OrderFetcher:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_unanalyzed_orders(self, limit: int = 10):
        subq = select(OrderAnalysis.order_id).subquery()
        stmt = select(Order).where(Order.id.not_in(subq)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()