import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
from database import create_tables
from handlers import common, channel_management, keyword_management, unknown_commands
from client_logic import client, start_client
from middlewares.data_provider import DataProviderMiddleware

# Черги
notification_queue = asyncio.Queue()
update_queue = asyncio.Queue()

async def notification_worker(bot: Bot):
    """Воркер, що обробляє чергу сповіщень."""
    while True:
        try:
            notification = await notification_queue.get()
            
            user_id = notification.get('user_id')
            message_text = notification.get('text')
            link = notification.get('link')

            keyboard = None
            if link:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Перейти до повідомлення ↗️", url=link)]
                ])

            await bot.send_message(user_id, message_text, parse_mode="HTML", reply_markup=keyboard)
            
            notification_queue.task_done()
            
        except asyncio.CancelledError:
            logging.info("Notification worker has been cancelled.")
            break
        except TelegramAPIError as e:
            user_id = notification.get('user_id', 'unknown')
            logging.error(f"Failed to send message to {user_id}: {e}")
        except Exception as e:
            logging.error(f"Error in notification worker: {e}")


async def main():
    # Налаштовуємо логування на самому початку
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Створюємо базу даних
    await create_tables()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Реєструємо middleware
    dp.update.middleware(DataProviderMiddleware(update_queue=update_queue))

    # Реєструємо роутери
    dp.include_router(common.router)
    dp.include_router(channel_management.router)
    dp.include_router(keyword_management.router)
    dp.include_router(unknown_commands.router)

    # Створюємо фонові завдання
    worker_task = asyncio.create_task(notification_worker(bot))
    client_task = asyncio.create_task(start_client(notification_queue, update_queue))

    try:
        # !!! КЛЮЧОВЕ ВИПРАВЛЕННЯ !!!
        # Перед запуском полінгу, видаляємо вебхук, щоб гарантовано отримувати оновлення
        await bot.delete_webhook(drop_pending_updates=True)
        
        print("Webhook deleted. Starting polling...")
        # Запускаємо опитування
        await dp.start_polling(bot)

    finally:
        print("Stopping services...")
        # Коректно зупиняємо всі компоненти
        client_task.cancel()
        worker_task.cancel()
        
        await asyncio.gather(client_task, worker_task, return_exceptions=True)
        
        if client.is_connected():
            await client.disconnect()
            print("Telethon client disconnected.")
            
        await bot.session.close()
        print("All services stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")