# bot/middlewares/throttling.py
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from collections import defaultdict
from aiogram.dispatcher.flags import get_flag
from aiogram import flags

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_rate: float = 0.5):
        self.default_rate = default_rate
        # Храним время последнего запроса для каждой пары (user_id, handler)
        self.last_call: Dict[tuple, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        #print(f"[throttle] event from {event.from_user.id}")
        if event.from_user is None:
            return await handler(event, data)

        # Получаем индивидуальный лимит для хендлера, если он задан
        rate = self.default_rate
        flag = get_flag(data, "rate_limit")
        if flag is not None:
            rate = flag.get("rate", self.default_rate)

        # Ключ: ID пользователя + конкретный хендлер
        # Это предотвращает блокировку одного хендлера другим
        handler_callback = data["handler"].callback
        key = (event.from_user.id, handler_callback)
        now = time.monotonic()

        last = self.last_call.get(key, 0)
        if now - last < rate:
            # Слишком часто — игнорируем сообщение
            # Можно уведомить пользователя, но лучше не спамить в ответ
            return None

        self.last_call[key] = now
        return await handler(event, data)