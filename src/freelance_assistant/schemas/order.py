from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AnalysisResult(BaseModel):
    order_id: UUID
    is_relevant: bool
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    questions: List[str] = []
    popularity_score: Optional[float] = None
    estimated_demand: Optional[str] = None
    avg_response_time_days: Optional[float] = None
    analyzed_at: datetime

class CategoryStats(BaseModel):
    category: str
    count_last_30_days: int
    avg_answers: Optional[float] = None
    avg_taken_days: Optional[float] = None
    popularity_score: float
    estimated_demand: str