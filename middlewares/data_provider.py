from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import asyncio

class DataProviderMiddleware(BaseMiddleware):
    def __init__(self, update_queue: asyncio.Queue):
        self.update_queue = update_queue

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Додаємо нашу чергу в словник `data`,
        # який потім буде доступний в обробниках
        data['update_queue'] = self.update_queue
        return await handler(event, data)