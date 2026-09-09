FROM python:3.12-slim

WORKDIR /app

# Устанавливаем poetry
RUN pip install --no-cache-dir poetry

# Копируем только файлы зависимостей для кэширования
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root --without dev

# Копируем исходники
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY scripts/ /app/scripts/

# Стартуем приложение
CMD ["uvicorn", "src.freelance_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"]