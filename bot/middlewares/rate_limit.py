# bot/middlewares/rate_limit.py
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate: int = 5, per_seconds: int = 10):
        self.rate = rate
        self.per  = per_seconds
        self._user_timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not hasattr(event, "from_user") or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()

        # Keep only timestamps within window
        self._user_timestamps[user_id] = [
            t for t in self._user_timestamps[user_id]
            if now - t < self.per
        ]

        if len(self._user_timestamps[user_id]) >= self.rate:
            await event.answer(
                "⏳ <b>Sekinroq!</b> Ko'p xabar yuboryapsiz.\n"
                f"<i>{self.per} soniyada {self.rate} ta xabar chegarasi.</i>",
                parse_mode="HTML"
            )
            return

        self._user_timestamps[user_id].append(now)
        return await handler(event, data)
