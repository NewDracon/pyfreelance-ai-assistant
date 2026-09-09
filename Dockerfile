FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости для сборки C++ расширений
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем poetry
RUN pip install --no-cache-dir poetry

# Копируем файлы зависимостей для кэширования слоёв
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости (без dev)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

# Копируем исходники
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY scripts/ /app/scripts/
COPY alembic.ini /app/alembic.ini

# Стартуем приложение
CMD ["uvicorn", "src.freelance_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"]