# Freelance Assistant — AI‑анализатор заказов с фриланс‑бирж

Сервис на основе RAG (Retrieval-Augmented Generation) для классификации заказов по категориям Python/AI‑разработки, генерации вопросов заказчику и оценки популярности категорий.

Работает в паре с парсером фриланс‑бирж: парсер складывает заказы в таблицу `orders`, а сервис автоматически их анализирует (через PostgreSQL LISTEN/NOTIFY) и сохраняет результаты в `order_analyses`.

---

## Оглавление
- [Требования](#требования)
- [Установка и запуск](#установка-и-запуск)
- [Структура базы данных](#структура-базы-данных)
  - [Таблица `orders`](#таблица-orders)
  - [Таблица `order_analyses`](#таблица-order_analyses)
- [Заполнение таблицы `orders`](#заполнение-таблицы-orders)
- [Автоматический анализ новых заказов (LISTEN/NOTIFY)](#автоматический-анализ-новых-заказов-listennotify)
  - [Как это работает](#как-это-работает)
  - [Настройка триггера в БД](#настройка-триггера-в-бд)
  - [Ограничение параллелизма](#ограничение-параллелизма)
- [API Endpoints](#api-endpoints)
- [Переменные окружения](#переменные-окружения)
- [Запуск анализа всех заказов](#запуск-анализа-всех-заказов)
- [Обновление на сервере](#обновление-на-сервере)
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

5. **Установите триггер NOTIFY** для автоматического анализа новых заказов (см. раздел [Настройка триггера в БД](#настройка-триггера-в-бд)).

6. **Запустите сервис**:
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

**Триггер на INSERT** в этой таблице отправляет `NOTIFY` в канал `new_orders`, что запускает фоновый анализ нового заказа (см. [Автоматический анализ](#автоматический-анализ-новых-заказов-listennotify)).

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

**Если вы вставляете много заказов сразу** – сервис обработает их асинхронно через очередь, но с ограничением параллелизма (см. ниже).

---

## Автоматический анализ новых заказов (LISTEN/NOTIFY)

Сервис умеет **мгновенно реагировать на новые заказы**, не дожидаясь cron-запуска. Используется встроенный механизм PostgreSQL `LISTEN/NOTIFY` — это не требует дополнительной инфраструктуры (RabbitMQ, Redis) и не требует доступа к Docker-сокету.

### Как это работает

```
Парсер вставляет заказ в `orders`
        ↓
Триггер `after_order_insert` вызывает `pg_notify('new_orders', order_id)`
        ↓
Анализатор (уже подписан на канал 'new_orders') получает уведомление
        ↓
order_id попадает в asyncio-очередь
        ↓
N воркеров параллельно анализируют заказы через LLM
        ↓
Результат сохраняется в `order_analyses` и ChromaDB
```

**Ключевые особенности:**
- **Мгновенная реакция** – задержка между вставкой и началом анализа: миллисекунды.
- **Не блокирует парсер** – NOTIFY асинхронный, парсер просто вставляет данные.
- **Безопасно** – не требует монтирования `/var/run/docker.sock`.
- **Асинхронно** – не блокирует HTTP-эндпоинты FastAPI.

**Важно:** уведомление доставляется **после COMMIT** транзакции вставки. Это гарантирует, что к моменту получения уведомления заказ уже виден в БД.

### Настройка триггера в БД

Примените SQL-скрипт `scripts/create_notify_trigger.sql` один раз на вашей базе:

```sql
-- Функция, отправляющая уведомление в канал 'new_orders'
CREATE OR REPLACE FUNCTION notify_new_order()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('new_orders', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер срабатывает после вставки в таблицу orders
DROP TRIGGER IF EXISTS after_order_insert ON orders;
CREATE TRIGGER after_order_insert
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION notify_new_order();
```

Применение через Docker:
```bash
docker exec -i <имя_контейнера_бд> psql -U <пользователь> -d orders_db < scripts/create_notify_trigger.sql
```

Проверка, что триггер создан:
```sql
SELECT tgname, tgrelid::regclass, tgenabled
FROM pg_trigger
WHERE tgname = 'after_order_insert';
```

Ожидаемый результат: одна строка с `tgenabled = 'O'`.

> **Замечание про `DROP TRIGGER IF EXISTS`:** при первом применении скрипт выдаст *«триггера не существует, пропускается»* — это нормально, `CREATE TRIGGER` выполнится следом. Скрипт идемпотентен: его можно запускать многократно.

### Ограничение параллелизма

Чтобы не упереться в rate limit LLM-провайдера при всплеске заказов (например, парсер вставил 50 записей за 10 секунд), слушатель **не запускает анализ напрямую**. Вместо этого:

1. Уведомления складываются в `asyncio.Queue`.
2. **3 воркера** (настраивается в `services/notification_listener.py`) параллельно разбирают очередь.

**Что это даёт:**
- Не более 3 одновременных запросов к LLM.
- Всплеск заказов буферизуется в памяти (до 1000 записей).
- Память стабильна, event loop не блокируется.

**Настройки** (в `src/freelance_assistant/services/notification_listener.py`):
```python
MAX_PARALLEL_ANALYSES = 3      # сколько заказов анализируется одновременно
QUEUE_MAX_SIZE = 1000          # защита от неограниченного роста очереди
```

**Рекомендации по `MAX_PARALLEL_ANALYSES`:**
| Провайдер | Лимит | Рекомендация |
| :--- | :--- | :--- |
| RouterAI | 10–60 req/min | 3–5 |
| OpenAI tier 1 | 500 RPM | 5–10 |
| OpenAI free | 3 RPM | 1 |

**Если очередь переполнилась** — в логах появится `⚠️ Queue full, dropping order <uuid>`. Это значит, что парсер опережает анализатор на >1000 заказов. Решение — раз в сутки запускать скрипт `analyze_all_orders_sorted.py`, который «догонит» пропущенные заказы.

**Важно:** запускайте Uvicorn с **одним воркером** (`--workers 1`). Если запустить несколько, каждый процесс создаст свой LISTEN-коннект и получит одинаковые уведомления → заказ будет проанализирован несколько раз (это лишние траты на LLM).

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

Эндпоинт `/api/v1/analyze` — «добор»: он не нужен для основного потока (LISTEN/NOTIFY справляется сам), но полезен для:
- Разового анализа старых заказов.
- Восстановления после сбоев.
- Тестирования.

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

Если нужно разово обработать все накопленные заказы (например, при первом запуске), используйте скрипт:

```bash
poetry run python scripts/analyze_all_orders_sorted.py
```

На сервере (через Docker):
```bash
docker-compose run --rm analyzer python scripts/analyze_all_orders_sorted.py
```

Скрипт обрабатывает заказы в хронологическом порядке (сначала старые, потом новые). Это улучшает качество классификации: новые заказы получают примеры из уже проанализированных старых.

---

## Обновление на сервере

Полный цикл обновления после `git push`:

```bash
cd ~/freelance-analyzer
git pull origin main
docker-compose build --no-cache
docker-compose up -d --force-recreate
docker-compose logs -f analyzer
```

Если изменилась структура БД — примените миграции:
```bash
docker-compose run --rm analyzer alembic upgrade head
```

**Автоматизация (GitHub Actions):** добавьте секреты `SERVER_HOST`, `SERVER_USER`, `SSH_PRIVATE_KEY` в настройках репозитория, и workflow `.github/workflows/deploy.yml` выполнит те же шаги автоматически при пуше в `main`.

---

## Примечания

- ChromaDB работает в локальном режиме (persistent). При первом запуске создаётся коллекция `orders`.
- Промт для LLM можно редактировать в `src/freelance_assistant/core/config.py` (переменная `PROMPT_TEMPLATE`).
- Для авторизации в Swagger нажмите кнопку **Authorize** и введите ваш `API_KEY`.
- Если вы используете модель `voyageai/voyage-4-lite`, убедитесь, что размерность эмбеддингов совпадает с коллекцией ChromaDB (при первом запуске создаётся автоматически; при смене модели удалите папку `chroma_data`).
- **Не запускайте Uvicorn с `--workers > 1`** при активном LISTEN/NOTIFY — это приведёт к дублированию анализа.
- Триггер `after_order_insert` должен существовать в БД. Если его нет — автоанализ не сработает, но эндпоинт `/analyze` продолжит работать.

---

## Лицензия

MIT