from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
import asyncio

class DataProviderMiddleware(BaseMiddleware):
    # приймаємо і чергу, і бота
    def __init__(self, update_queue: asyncio.Queue, bot: Bot):
        self.update_queue = update_queue
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Додаємо обидва об'єкти в дані, доступні для обробників
        data['update_queue'] = self.update_queue
        data['bot'] = self.bot
        return await handler(event, data)