# handlers/channel_management.py

import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states.channel import AddChannel
from database import add_channel_for_user, get_user_channels, delete_channel_by_id
from keyboards.inline import get_list_keyboard, DeleteCallback

router = Router()

# Цей обробник тепер показує список каналів при натисканні на кнопку з головного меню
@router.message(F.text == "➕ Додати канал")
async def show_channels(message: Message):
    user_id = message.from_user.id
    channels = await get_user_channels(user_id)
    
    if not channels:
        text = "У вас ще немає доданих каналів. Бажаєте додати перший?"
        # Створюємо клавіатуру лише з однією кнопкою "Додати"
        keyboard = get_list_keyboard([], 'del_channel')
    else:
        text = "Ваш список каналів для моніторингу:"
        keyboard = get_list_keyboard(channels, 'del_channel')
        
    await message.answer(text, reply_markup=keyboard)

# Цей обробник спрацьовує при натисканні на inline-кнопку "Додати новий канал"
@router.callback_query(F.data == "add_channel")
async def start_add_channel_callback(callback: CallbackQuery, state: FSMContext):
    # Використовуємо edit_text, щоб змінити поточне повідомлення
    await callback.message.edit_text(
        "Будь ласка, надішліть посилання на Telegram-канал.\n"
        "Наприклад: https://t.me/telegram або @telegram"
    )
    # Встановлюємо стан очікування URL
    await state.set_state(AddChannel.waiting_for_url)
    await callback.answer()

# Цей обробник спрацьовує, коли користувач надсилає URL, перебуваючи у стані AddChannel.waiting_for_url
@router.message(AddChannel.waiting_for_url)
async def process_channel_url(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    # Виходимо зі стану, щоб уникнути подальших спрацювань
    await state.clear()
    
    channel_url = message.text
    user_id = message.from_user.id

    # Додаємо http-префікс, якщо його немає
    if not channel_url.startswith(('http://', 'https://')):
        channel_url = f"https://t.me/{channel_url.replace('@', '')}"

    is_added = await add_channel_for_user(user_id, channel_url)

    if is_added:
        await message.answer(f"✅ Чудово! Канал <b>{channel_url}</b> успішно додано.", parse_mode="HTML")
        # Надсилаємо сигнал в Telethon про оновлення
        update_queue.put_nowait({'action': 'add_channel', 'url': channel_url})
    else:
        await message.answer(f"⚠️ Цей канал вже є у вашому списку.")
        
    # Повертаємо користувача до списку каналів
    await show_channels(message)


# Обробник для видалення каналу (реагує на колбек з префіксом 'delete' та action 'del_channel')
@router.callback_query(DeleteCallback.filter(F.action == "del_channel"))
async def delete_channel(callback: CallbackQuery, callback_data: DeleteCallback, update_queue: asyncio.Queue):
    channel_id_to_delete = callback_data.item_id
    await delete_channel_by_id(channel_id_to_delete)
    
    # Оновлюємо список каналів у тому ж повідомленні
    user_id = callback.from_user.id
    channels = await get_user_channels(user_id)
    
    # Створюємо нову клавіатуру
    text = "Канал видалено. Ваш оновлений список:"
    if not channels:
        text = "Усі канали видалено. Бажаєте додати новий?"
    
    keyboard = get_list_keyboard(channels, 'del_channel')
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    
    # Надсилаємо сигнал на повне оновлення кешу в Telethon
    update_queue.put_nowait({'action': 'update_subscriptions'})
    await callback.answer(text="Канал видалено!", show_alert=False)