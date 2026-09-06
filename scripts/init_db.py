import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from freelance_assistant.core.config import settings
from freelance_assistant.models.analysis import Base

async def init():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Создаём таблицу order_analyses (если orders уже существует)
        await conn.run_sync(Base.metadata.create_all)
        # Проверим, что таблица orders существует – если нет, можно создать отдельно
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init())