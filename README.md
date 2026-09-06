# Order Analyzer – AI‑анализ заказов с фриланс‑бирж

Сервис на основе RAG (Retrieval-Augmented Generation) для классификации заказов по категориям Python/AI‑разработки, генерации вопросов заказчику и оценки популярности категорий.

## Требования
- Python 3.12+
- Docker & Docker Compose (опционально)
- PostgreSQL
- OpenAI‑совместимый API (например, через RouterAI)

## Установка и запуск

1. Склонируйте репозиторий.
2. Скопируйте `.env.example` в `.env` и заполните своими данными.
3. Запустите сервис:
   ```bash
   docker-compose up --build