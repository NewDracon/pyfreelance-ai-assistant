from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Новая конфигурация для Pydantic v2
    model_config = ConfigDict(
        extra='ignore',          # игнорировать лишние переменные в .env
        env_file='.env',
        env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://routerai.ru/api/v1"
    LLM_MODEL: str = "qwen/qwen3.7-flash"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    API_KEY: str

settings = Settings()

# Промт шаблон (можно оставить здесь)
PROMPT_TEMPLATE = """Ты — эксперт по фриланс-заказам в сфере IT. Твоя задача — определить, относится ли заказ к разработке на Python или к AI/машинному обучению, и если да, то классифицировать его по одной из категорий.

**Релевантными считаются заказы, в которых требуется:**
- Разработка на Python (веб-фреймворки: Django, Flask, FastAPI; парсинг данных; автоматизация; скрипты; бэкенд API)
- Обработка данных, анализ данных, ETL, работа с базами данных (SQL, NoSQL, Pandas, NumPy)
- Машинное обучение, NLP, компьютерное зрение, глубокое обучение, AI-агенты, чат-боты (например, на основе GPT, RAG)
- Разработка Telegram, Discord, Slack ботов
- Веб-скрапинг (Scrapy, BeautifulSoup, Selenium)
- DevOps-задачи, если они связаны с развёртыванием Python-приложений (CI/CD, Docker, Kubernetes, настройка серверов)

**Нерелевантными считаются заказы, которые:**
- Связаны исключительно с фронтендом (HTML, CSS, JavaScript, React, Vue, Angular)
- Мобильная разработка (iOS, Android, Flutter, React Native) без участия Python
- Дизайн, верстка, копирайтинг, SMM, маркетинг, контент-менеджмент
- Разработка на других языках (Java, C#, PHP, Ruby, Go) без явного использования Python или AI
- Чистое администрирование серверов без скриптов на Python
- Заказы, не связанные с программированием (например, перевод, видеомонтаж)

Проанализируй заказ и верни строго JSON с полями:
{
  "is_relevant": true/false,
  "category": "backend_api|data_processing|ml_nlp|automation|devops|web_scraping|chatbots_ai_agents|other",
  "category_confidence": 0.0-1.0,
  "questions": ["string"],   // 3–5 вопросов, которые стоит задать заказчику (если is_relevant = true, иначе пустой массив)
  "popularity_score": 0.5,   // временное значение (будет пересчитано позже)
  "estimated_demand": "medium", // временное значение
  "avg_response_time_days": 5   // временное значение
}

Ниже приведены примеры похожих заказов с их категориями (используй их как подсказку):
{examples}

Теперь анализируй следующий заказ:
Title: {title}
Description: {description}
Site: {site_name}
Budget: {budget}

Верни только JSON, без дополнительного текста."""