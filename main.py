import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from config import BOT_TOKEN
from database import create_tables
from handlers import common, channel_management, keyword_management
from client_logic import client, start_client
from middlewares.data_provider import DataProviderMiddleware

# Створюємо чергу для сповіщень
notification_queue = asyncio.Queue()
update_queue = asyncio.Queue()


async def notification_worker(bot: Bot):
    """Воркер, що обробляє чергу сповіщень. (Виправлена версія)"""
    while True:
        try:
            notification = await notification_queue.get()
            
            user_id = notification.get('user_id')
            message_text = notification.get('text')
            link = notification.get('link') 

            keyboard = None
            if link:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Перейти до повідомлення ↗️", url=link)]
                ])

            await bot.send_message(user_id, message_text, parse_mode="HTML", reply_markup=keyboard)
            
            notification_queue.task_done()
            
        except asyncio.CancelledError:
            logging.info("Notification worker has been cancelled.")
            break
        except TelegramAPIError as e:
            logging.error(f"Failed to send message to {user_id}: {e}")
        except Exception as e:
            logging.error(f"Error in notification worker: {e}")


async def main():
    await create_tables()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DataProviderMiddleware(update_queue=update_queue))

    dp.include_router(common.router)
    dp.include_router(channel_management.router)
    dp.include_router(keyword_management.router)

    worker_task = asyncio.create_task(notification_worker(bot))
    
    try:
        print("Bot is running...")
        await asyncio.gather(
            dp.start_polling(bot),
            start_client(notification_queue, update_queue)
        )
    finally:
        worker_task.cancel()
        if client.is_connected():
            await client.disconnect()
            print("Telethon client disconnected.")
        await bot.session.close()
        print("\nBot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass