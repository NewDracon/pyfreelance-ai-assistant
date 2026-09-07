from sqlalchemy import Column, String, Boolean, Float, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid
from . import Base   # <-- импорт общего Base

class OrderAnalysis(Base):
    __tablename__ = "order_analyses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(PG_UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_relevant = Column(Boolean)
    category = Column(String(100))
    category_confidence = Column(Float)
    questions = Column(JSON)
    popularity_score = Column(Float)
    estimated_demand = Column(String(20))
    avg_response_time_days = Column(Float)
    analyzed_at = Column(TIMESTAMP, server_default="NOW()")

    order = relationship("Order", backref="analyses")