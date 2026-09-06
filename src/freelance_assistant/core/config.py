from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://routerai.ru/api/v1"
    LLM_MODEL: str = "qwen/qwen3.7-flash"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Промт для LLM (хранится здесь, можно править без перезапуска)
PROMPT_TEMPLATE = """Ты — эксперт по фриланс-заказам в сфере IT. Проанализируй следующий заказ и верни строго JSON с полями:
{{
  "is_relevant": true/false,
  "category": "backend_api|data_processing|ml_nlp|automation|devops|web_scraping|chatbots_ai_agents|frontend|mobile|other",
  "category_confidence": 0.0-1.0,
  "questions": ["string"],
  "popularity_score": 0.0-1.0,
  "estimated_demand": "high|medium|low",
  "avg_response_time_days": number
}}

Вот несколько примеров похожих заказов и их категорий:
{examples}

Теперь анализируй следующий заказ:
Title: {title}
Description: {description}
Site: {site_name}
Budget: {budget}
"""