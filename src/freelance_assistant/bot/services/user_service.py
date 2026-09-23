from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from freelance_assistant.models.bot_user import BotUser


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> BotUser:
    stmt = select(BotUser).where(BotUser.telegram_id == telegram_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None:
        user = BotUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user(session: AsyncSession, telegram_id: int, **kwargs) -> BotUser | None:
    stmt = select(BotUser).where(BotUser.telegram_id == telegram_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user