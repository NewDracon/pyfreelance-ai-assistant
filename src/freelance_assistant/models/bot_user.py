from sqlalchemy import Column, String, BigInteger, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
import uuid
from . import Base


class BotUser(Base):
    __tablename__ = "bot_users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))

    # Настройки фильтрации
    categories = Column(JSONB, default=list, server_default="[]")
    min_budget = Column(Integer, default=0, server_default="0")
    sites = Column(JSONB, default=list, server_default="[]")

    # Подписка
    is_subscribed = Column(Boolean, default=False, server_default="false")
    subscribed_at = Column(TIMESTAMP)

    # Служебное
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_active_at = Column(TIMESTAMP, server_default=func.now())