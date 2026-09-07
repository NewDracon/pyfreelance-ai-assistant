import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from openai import AsyncOpenAI
from freelance_assistant.core.config import settings, PROMPT_TEMPLATE
from freelance_assistant.models.order import Order
from freelance_assistant.models.analysis import OrderAnalysis
from freelance_assistant.infrastructure.vector_store.chroma_client import ChromaClient

class RAGAnalyzer:
    def __init__(self, session: AsyncSession, chroma_client: ChromaClient):
        self.session = session
        self.chroma = chroma_client
        self.openai = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.llm_model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    async def _get_embedding(self, text: str) -> List[float]:
        text = text[:8000]
        response = await self.openai.embeddings.create(
            model=self.embedding_model,
            input=text,
            dimensions=512,  # Опционально: 256, 512, 1024 (по умолчанию), 2048
            encoding_format="float"
        )
        return response.data[0].embedding

    async def _get_similar_orders(self, embedding: List[float], n: int = 5) -> List[Dict[str, Any]]:
        results = self.chroma.query(embedding, n_results=n)
        metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
        return metadatas

    def _build_prompt(self, order: Order, similar: List[Dict[str, Any]]) -> str:
        examples = ""
        for i, meta in enumerate(similar, 1):
            examples += (
                f"Пример {i}:\n"
                f"Title: {meta.get('title', '')}\n"
                f"Description: {meta.get('description', '')}\n"
                f"Site: {meta.get('site_name', '')}\n"
                f"Budget: {meta.get('budget', '')}\n"
                f"Category: {meta.get('category', 'unknown')}\n\n"
            )
        return PROMPT_TEMPLATE.format(
            examples=examples,
            title=order.title,
            description=order.description or '',
            site_name=order.site_name,
            budget=order.budget or ''
        )

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        response = await self.openai.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON from LLM")

    async def _get_category_stats(self, category: str) -> Dict[str, Any]:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stmt = select(
            func.count(Order.id).label('count'),
            func.avg(Order.answers).label('avg_answers'),
            func.avg(func.extract('epoch', Order.taken_at - Order.published_at) / 86400.0).label('avg_taken_days')
        ).join(OrderAnalysis, OrderAnalysis.order_id == Order.id)\
         .where(OrderAnalysis.category == category)\
         .where(Order.published_at >= thirty_days_ago)
        result = await self.session.execute(stmt)
        row = result.first()
        return {
            'count': row.count or 0 if row else 0,
            'avg_answers': row.avg_answers if row else None,
            'avg_taken_days': row.avg_taken_days if row else None
        }

    async def _compute_popularity_metrics(self, category: str) -> Dict[str, Any]:
        stats = await self._get_category_stats(category)
        count = stats['count']
        avg_answers = stats['avg_answers']
        avg_taken_days = stats['avg_taken_days']

        max_count_stmt = select(
            func.max(subq.c.category_count)
        ).select_from(
            select(
                OrderAnalysis.category,
                func.count().label('category_count')
            )
            .join(Order, Order.id == OrderAnalysis.order_id)
            .where(Order.published_at >= (datetime.utcnow() - timedelta(days=30)))
            .group_by(OrderAnalysis.category)
            .subquery('subq')
        )
        max_result = await self.session.execute(max_count_stmt)
        max_count = max_result.scalar() or 1

        popularity_score = count / max_count if max_count else 0.0

        if count > 10 and avg_answers and avg_answers > 5:
            estimated_demand = "high"
        elif count > 5 and avg_answers and avg_answers > 2:
            estimated_demand = "medium"
        else:
            estimated_demand = "low"

        return {
            'popularity_score': popularity_score,
            'estimated_demand': estimated_demand,
            'avg_response_time_days': avg_taken_days,
            'count': count,
            'avg_answers': avg_answers,
        }

    async def analyze_order(self, order: Order) -> OrderAnalysis:
        text_for_embedding = f"{order.title} {order.description or ''}"
        embedding = await self._get_embedding(text_for_embedding)

        similar = await self._get_similar_orders(embedding, n=5)
        prompt = self._build_prompt(order, similar)
        llm_result = await self._call_llm(prompt)

        is_relevant = llm_result.get('is_relevant', False)
        category = llm_result.get('category', 'other')
        category_confidence = llm_result.get('category_confidence', 0.5)
        questions = llm_result.get('questions', [])

        popularity_score = None
        estimated_demand = None
        avg_response_time_days = None
        if is_relevant:
            metrics = await self._compute_popularity_metrics(category)
            popularity_score = metrics['popularity_score']
            estimated_demand = metrics['estimated_demand']
            avg_response_time_days = metrics['avg_response_time_days']

        analysis = OrderAnalysis(
            order_id=order.id,
            is_relevant=is_relevant,
            category=category if is_relevant else None,
            category_confidence=category_confidence if is_relevant else None,
            questions=questions if is_relevant else [],
            popularity_score=popularity_score,
            estimated_demand=estimated_demand,
            avg_response_time_days=avg_response_time_days,
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)

        # Добавляем эмбеддинг в ChromaDB
        metadata = {
            'order_id': str(order.id),
            'title': order.title,
            'description': order.description or '',
            'site_name': order.site_name,
            'budget': order.budget or '',
            'category': category if is_relevant else 'other',
            'is_relevant': is_relevant,
        }
        self.chroma.add_embedding(
            doc_id=str(order.id),
            embedding=embedding,
            metadata=metadata
        )

        return analysis