from sqlalchemy import Column, String, Text, TIMESTAMP, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    site_name = Column(String(100), nullable=False)
    published_at = Column(TIMESTAMP)
    budget = Column(String(100))
    created_at = Column(TIMESTAMP, server_default="NOW()")
    answers = Column(Integer)
    is_taken = Column(Boolean, default=False)
    taken_at = Column(TIMESTAMP)