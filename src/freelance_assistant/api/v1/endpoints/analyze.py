from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func
from freelance_assistant.core.database import get_db
from freelance_assistant.core.config import settings
from freelance_assistant.services.order_fetcher import OrderFetcher
from freelance_assistant.services.rag_analyzer import RAGAnalyzer
from freelance_assistant.infrastructure.vector_store.chroma_client import ChromaClient
from freelance_assistant.schemas.order import AnalysisResult, CategoryStats
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis

router = APIRouter()

async def verify_api_key(api_key: str = Query(...)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.get("/analyze", response_model=List[AnalysisResult])
async def analyze_orders(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    fetcher = OrderFetcher(db)
    chroma = ChromaClient()
    analyzer = RAGAnalyzer(db, chroma)

    orders = await fetcher.get_unanalyzed_orders(limit)
    results = []
    for order in orders:
        analysis = await analyzer.analyze_order(order)
        results.append(AnalysisResult(
            order_id=analysis.order_id,
            is_relevant=analysis.is_relevant,
            category=analysis.category,
            category_confidence=analysis.category_confidence,
            questions=analysis.questions or [],
            popularity_score=analysis.popularity_score,
            estimated_demand=analysis.estimated_demand,
            avg_response_time_days=analysis.avg_response_time_days,
            analyzed_at=analysis.analyzed_at
        ))
    return results

@router.get("/analysis/{order_id}", response_model=AnalysisResult)
async def get_analysis(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    stmt = select(OrderAnalysis).where(OrderAnalysis.order_id == order_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResult(
        order_id=analysis.order_id,
        is_relevant=analysis.is_relevant,
        category=analysis.category,
        category_confidence=analysis.category_confidence,
        questions=analysis.questions or [],
        popularity_score=analysis.popularity_score,
        estimated_demand=analysis.estimated_demand,
        avg_response_time_days=analysis.avg_response_time_days,
        analyzed_at=analysis.analyzed_at
    )

@router.get("/categories/stats", response_model=List[CategoryStats])
async def category_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stmt = select(
        OrderAnalysis.category,
        func.count(Order.id).label('count'),
        func.avg(Order.answers).label('avg_answers'),
        func.avg(func.extract('epoch', Order.taken_at - Order.published_at) / 86400.0).label('avg_taken_days')
    ).join(Order, Order.id == OrderAnalysis.order_id)\
     .where(Order.published_at >= thirty_days_ago)\
     .where(OrderAnalysis.is_relevant == True)\
     .group_by(OrderAnalysis.category)

    result = await db.execute(stmt)
    rows = result.all()
    max_count = max([row.count for row in rows]) if rows else 1

    stats_list = []
    for row in rows:
        count = row.count
        avg_answers = row.avg_answers
        avg_taken_days = row.avg_taken_days
        popularity_score = count / max_count if max_count else 0.0

        if count > 10 and avg_answers and avg_answers > 5:
            estimated_demand = "high"
        elif count > 5 and avg_answers and avg_answers > 2:
            estimated_demand = "medium"
        else:
            estimated_demand = "low"

        stats_list.append(CategoryStats(
            category=row.category,
            count_last_30_days=count,
            avg_answers=avg_answers,
            avg_taken_days=avg_taken_days,
            popularity_score=popularity_score,
            estimated_demand=estimated_demand
        ))
    return stats_list