import asyncio
import logging
import os
from telethon.sync import TelegramClient
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel
from config import API_ID, API_HASH
from database import get_all_unique_channels, get_subscriptions_for_channel
from config import API_ID, API_HASH, TELETHON_SESSION
from telethon.sessions import StringSession

logging.getLogger('telethon').setLevel(logging.WARNING)

session = None
if TELETHON_SESSION:
    # Якщо змінна оточення існує, створюємо об'єкт StringSession
    session = StringSession(TELETHON_SESSION)
else:
    # Якщо ми працюємо локально, використовуємо назву файлу
    session = 'keyword_monitor_session'

client = TelegramClient(session, API_ID, API_HASH)

# Глобальний кеш для зберігання підписок: { 'url1': [(user_id, keyword), ...], 'url2': ... }
channel_subscriptions = {}

async def update_subscriptions_cache():
    """Повністю оновлює кеш підписок з бази даних."""
    global channel_subscriptions
    urls = await get_all_unique_channels()
    new_subscriptions = {}
    for url in urls:
        new_subscriptions[url] = await get_subscriptions_for_channel(url)
    channel_subscriptions = new_subscriptions
    print("Subscriptions cache has been updated.")


async def update_worker(update_queue: asyncio.Queue):
    """Воркер, що слухає чергу оновлень і динамічно реагує на них."""
    while True:
        try:
            update = await update_queue.get()
            action = update.get('action')
            
            if action == 'add_channel':
                url = update.get('url')
                print(f"Update worker: Received new channel to join -> {url}")
                try:
                    await client(JoinChannelRequest(url.split('/')[-1]))
                    print(f"Successfully joined new channel: {url}")
                except Exception as e:
                    # Ігноруємо помилку, якщо вже є учасником або канал не існує
                    if "user_already_participant" not in str(e).lower():
                        print(f"Could not join channel {url}: {e}")
                # У будь-якому випадку оновлюємо кеш
                await update_subscriptions_cache()

            elif action == 'update_subscriptions':
                print("Update worker: Received full subscription update signal.")
                await update_subscriptions_cache()
                
            update_queue.task_done()
        except Exception as e:
            logging.error(f"Error in update_worker: {e}")


@client.on(events.NewMessage)
async def handle_new_message(event: events.NewMessage.Event):
    """Обробляє нові повідомлення та шукає збіги за ключовими словами."""
    if not isinstance(event.chat, Channel) or not hasattr(event.chat, 'username') or not event.chat.username:
        return
    
    channel_url = f"https://t.me/{event.chat.username}"
    
    # Перевіряємо, чи є підписки на цей канал, і чи є текст у повідомленні
    if channel_url not in channel_subscriptions or not event.message.text:
        return

    message_text_lower = event.message.text.lower()
    
    # Використовуємо .get() для безпечного отримання списку підписок
    for user_id, keyword in channel_subscriptions.get(channel_url, []):
        if keyword in message_text_lower:
            print(f"Found keyword '{keyword}' for user {user_id} in channel {channel_url}")
            
            message_link = f"https://t.me/{event.chat.username}/{event.message.id}"
            
            notification_text = (
                f"🔥 <b>Знайдено збіг!</b>\n\n"
                f"<b>Канал:</b> {event.chat.title}\n"
                f"<b>Ключове слово:</b> {keyword}"
            )
            
            # Кладемо сповіщення в чергу
            asyncio.get_event_loop().notification_queue.put_nowait({
                'user_id': user_id,
                'text': notification_text,
                'link': message_link
            })


async def start_client(notif_queue: asyncio.Queue, upd_queue: asyncio.Queue):
    """Ініціалізує та запускає Telethon клієнта та його воркери."""
    print("Starting Telethon client...")
    # Зберігаємо черги в циклі подій для доступу з будь-якого місця
    loop = asyncio.get_event_loop()
    loop.notification_queue = notif_queue
    loop.update_queue = upd_queue # Хоча ми передаємо її напряму у воркер
    
    # Запускаємо воркер оновлень у фоні
    asyncio.create_task(update_worker(upd_queue))
    
    await client.start()
    print("Telethon client authorized.")

    # Первинне заповнення кешу та підписка на канали
    await update_subscriptions_cache()
    for url in channel_subscriptions.keys():
        try:
            await client(JoinChannelRequest(url.split('/')[-1]))
        except Exception:
            pass
            
    print("Telethon client is running and listening for messages...")
    #  await client.run_until_disconnected()