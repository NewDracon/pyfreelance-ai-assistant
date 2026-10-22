import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from freelance_assistant.models.bot_user import BotUser
from freelance_assistant.bot.services.job_service import get_top_jobs_for_user


@pytest.mark.asyncio
async def test_chatbots_jobs_visible():
    # Подключение к тестовой БД
    engine = create_async_engine(
        "postgresql+asyncpg://user:xxx@localhost:5432/freelance_db"
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        # Эмулируем пользователя, выбравшего "Чат-боты"
        user = BotUser(
            telegram_id=999999,
            categories=["чат-боты"],
            min_budget=0,
            sites=[],
        )

        jobs = await get_top_jobs_for_user(session, user, limit=10)

        # Отладочный вывод — сразу увидим, что вернулось
        print(f"\nНайдено заказов: {len(jobs)}")
        for order, analysis in jobs:
            print(f"  - {order.title[:50]}, cat={analysis.category}, taken={order.is_taken}")

        assert len(jobs) > 0, "Должны быть chatbots-заказы, но их нет"

    await engine.dispose()