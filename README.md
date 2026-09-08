# Freelance Assistant — AI‑анализатор заказов с фриланс‑бирж

Сервис на основе RAG (Retrieval-Augmented Generation) для классификации заказов по категориям Python/AI‑разработки, генерации вопросов заказчику и оценки популярности категорий.

---

## Оглавление
- [Требования](#требования)
- [Установка и запуск](#установка-и-запуск)
- [Структура базы данных](#структура-базы-данных)
  - [Таблица `orders`](#таблица-orders)
  - [Таблица `order_analyses`](#таблица-order_analyses)
- [Заполнение таблицы `orders`](#заполнение-таблицы-orders)
- [API Endpoints](#api-endpoints)
- [Переменные окружения](#переменные-окружения)
- [Запуск анализа всех заказов](#запуск-анализа-всех-заказов)
- [Примечания](#примечания)

---

## Требования
- Python 3.12+
- Poetry (управление зависимостями)
- PostgreSQL (локально или через Docker)
- OpenAI‑совместимый API (например, RouterAI)
- Docker & Docker Compose (опционально, для быстрого развёртывания)

---

## Установка и запуск

1. **Склонируйте репозиторий** и перейдите в корневую папку:
   ```bash
   git clone <repo-url>
   cd public_repo
   ```

2. **Скопируйте** `.env.example` → `.env` и заполните реальными значениями:
   ```bash
   cp .env.example .env
   ```
   Обязательно укажите:
   - `DATABASE_URL` – строка подключения к PostgreSQL.
   - `OPENAI_API_KEY` – ваш ключ для RouterAI / OpenAI.
   - `API_KEY` – секретный ключ для авторизации запросов к API.

3. **Установите зависимости** через Poetry:
   ```bash
   poetry install
   ```

4. **Примените миграции** (создаст таблицу `order_analyses`):
   ```bash
   poetry run alembic upgrade head
   ```
   Если таблица `orders` ещё не создана, создайте её вручную (см. раздел [Таблица `orders`](#таблица-orders)).

5. **Запустите сервис**:
   ```bash
   poetry run uvicorn src.freelance_assistant.main:app --reload
   ```
   Сервер будет доступен по адресу `http://127.0.0.1:8000`.

**Альтернативно – через Docker Compose**:
```bash
docker-compose up --build
```

---

## Структура базы данных

Сервис использует две основные таблицы:

### Таблица `orders`
Хранит исходные заказы, загруженные парсером с фриланс‑бирж. **Эта таблица должна существовать до запуска анализа**, так как анализ читает данные именно из неё.

**SQL-скрипт создания** (используйте этот код для создания таблицы):
```sql
CREATE TABLE IF NOT EXISTS public.orders (
    id uuid NOT NULL,
    external_id character varying(255) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    url character varying(500) NOT NULL,
    site_name character varying(100) NOT NULL,
    published_at timestamp without time zone,
    budget character varying(100),
    created_at timestamp without time zone DEFAULT now(),
    answers integer,
    is_taken boolean,
    taken_at timestamp without time zone,
    CONSTRAINT orders_pkey PRIMARY KEY (id)
);
```

| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | UUID | Уникальный идентификатор заказа (первичный ключ). |
| `external_id` | VARCHAR(255) | ID заказа во внешней системе (биржа). |
| `title` | VARCHAR(500) | Заголовок заказа. |
| `description` | TEXT | Полное описание заказа. |
| `url` | VARCHAR(500) | Ссылка на страницу заказа. |
| `site_name` | VARCHAR(100) | Название биржи (например, `freelance.ru`). |
| `published_at` | TIMESTAMP | Дата публикации заказа. |
| `budget` | VARCHAR(100) | Бюджет заказа (может быть строкой, например, `"50000 руб."`). |
| `created_at` | TIMESTAMP | Дата добавления записи в БД (по умолчанию `NOW()`). |
| `answers` | INTEGER | Количество откликов/предложений на заказ. |
| `is_taken` | BOOLEAN | Был ли заказ взят исполнителем. |
| `taken_at` | TIMESTAMP | Дата, когда заказ был взят (если известно). |

---

### Таблица `order_analyses`
Содержит результаты анализа каждого заказа. Создаётся автоматически через Alembic при выполнении миграций.

| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | UUID | Уникальный идентификатор записи. |
| `order_id` | UUID | Внешний ключ на `orders.id`. |
| `is_relevant` | BOOLEAN | Релевантен ли заказ (Python/AI). |
| `category` | VARCHAR(100) | Категория заказа (например, `backend_api`). |
| `category_confidence` | FLOAT | Уверенность LLM в категории (0–1). |
| `questions` | JSONB | Список вопросов заказчику. |
| `popularity_score` | FLOAT | Оценка популярности категории (0–1). |
| `estimated_demand` | VARCHAR(20) | Оценка спроса (`high`/`medium`/`low`). |
| `avg_response_time_days` | FLOAT | Среднее время нахождения исполнителя (дни). |
| `analyzed_at` | TIMESTAMP | Дата и время анализа. |

---

## Заполнение таблицы `orders`

Анализатор работает с данными, уже загруженными в таблицу `orders`. Вы можете заполнить её любым удобным способом:

- **Парсером** – написать скрипт, который собирает заказы с бирж и вставляет их в БД.
- **Вручную** – добавить тестовые записи для проверки работы.

**Пример вставки тестового заказа**:
```sql
INSERT INTO public.orders (
    id,
    external_id,
    title,
    description,
    url,
    site_name,
    published_at,
    budget,
    answers,
    is_taken,
    taken_at
) VALUES (
    gen_random_uuid(),
    'test123',
    'Разработать парсер для сбора данных с сайта',
    'Нужно написать скрипт на Python, который будет собирать данные с сайта объявлений и сохранять в CSV. Использовать библиотеки requests, BeautifulSoup.',
    'https://example.com/order/123',
    'freelance.ru',
    NOW(),
    '50000 руб.',
    5,
    false,
    NULL
);
```

**Рекомендации**:
- Убедитесь, что поле `id` заполняется уникальными UUID.
- Поле `external_id` должно быть уникальным в пределах источника.
- Для корректного расчёта `avg_response_time_days` желательно заполнять `published_at`, `taken_at` и `is_taken`, если есть такая информация.

---

## API Endpoints

Все эндпоинты требуют передачу параметра `api_key` в query string (например, `?api_key=ваш_ключ`).

| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/api/v1/analyze?limit=10` | GET | Анализирует новые заказы (не более `limit`) и возвращает результаты. |
| `/api/v1/analysis/{order_id}` | GET | Возвращает сохранённый анализ для конкретного заказа. |
| `/api/v1/categories/stats` | GET | Возвращает статистику по категориям за последние 30 дней. |
| `/api/v1/health` | GET | Проверка работоспособности сервиса. |

Интерактивная документация доступна по адресу `/docs` (Swagger UI).

---

## Переменные окружения

| Переменная | Описание |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL DSN (asyncpg) |
| `OPENAI_API_KEY` | Ключ для OpenAI / RouterAI |
| `OPENAI_BASE_URL` | Базовый URL прокси (по умолчанию `https://routerai.ru/api/v1`) |
| `LLM_MODEL` | Модель для классификации (например, `qwen/qwen3.7-flash`) |
| `EMBEDDING_MODEL` | Модель для эмбеддингов (например, `voyageai/voyage-4-lite`) |
| `CHROMA_PERSIST_DIR` | Путь для сохранения векторов ChromaDB |
| `API_KEY` | Секретный ключ для авторизации запросов |

---

## Запуск анализа всех заказов

Для обработки всех заказов, накопленных в таблице `orders`, используйте скрипт:
```bash
poetry run python scripts/analyze_all_orders_sorted.py
```
Скрипт обрабатывает заказы в хронологическом порядке (сначала старые, потом новые), что улучшает качество классификации, так как новые заказы получают примеры из уже проанализированных старых.

---

## Примечания

- ChromaDB работает в локальном режиме (persistent). При первом запуске создаётся коллекция `orders`.
- Промт для LLM можно редактировать в `src/freelance_assistant/core/config.py` (переменная `PROMPT_TEMPLATE`).
- Для авторизации в Swagger нажмите кнопку **Authorize** и введите ваш `API_KEY`.
- Если вы используете модель `voyageai/voyage-4-lite`, убедитесь, что размерность эмбеддингов совпадает с коллекцией ChromaDB (при первом запуске создаётся автоматически).

---

## Лицензия

MIT