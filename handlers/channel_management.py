# handlers/channel_management.py

import asyncio
import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states.channel import AddChannel
from database import add_channel_for_user, get_user_channels, delete_channel_by_id
from keyboards.inline import get_list_keyboard, DeleteCallback
from keyboards.reply import main_menu, cancel_menu

router = Router()


# Допоміжна функція для показу списку каналів
async def show_channel_list(message: types.User | Message | CallbackQuery, user_id: int):
    channels = await get_user_channels(user_id)
    text = "Ваш список каналів для моніторингу:" if channels else "У вас ще немає доданих каналів."
    keyboard = get_list_keyboard(channels, 'del_channel')
    
    # Визначаємо, як надіслати повідомлення: новим чи відредагувати існуюче
    if isinstance(message, Message):
        await message.answer(text, reply_markup=keyboard)
    else: # Якщо це CallbackQuery
        await message.message.edit_text(text, reply_markup=keyboard)


# Спрацьовує на кнопку "Додати канал"
@router.message(F.text == "➕ Додати канал")
async def show_channels_command(message: Message):
    await show_channel_list(message, message.from_user.id)


# Спрацьовує на inline-кнопку "Додати новий канал"
@router.callback_query(F.data == "add_channel")
async def start_add_channel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Будь ласка, надішліть посилання на Telegram-канал.\n"
        "Наприклад: https://t.me/telegram",
        reply_markup=cancel_menu
    )
    await state.set_state(AddChannel.waiting_for_url)
    await callback.answer() # Закриваємо "годинник" на кнопці


# Обробляє посилання, надіслане користувачем
@router.message(AddChannel.waiting_for_url)
async def process_channel_url(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()
    
    channel_url = message.text.strip()
    pattern = r'(?:https?:\/\/)?(?:t(?:elegram)?\.me\/|@)([a-zA-Z0-9_]{5,32})'
    match = re.match(pattern, channel_url)

    if not match:
        await message.answer(
            "❌ **Помилка.** Неправильний формат посилання. Спробуйте ще раз.",
            reply_markup=main_menu
        )
        return

    clean_username = match.group(1)
    formatted_url = f"https://t.me/{clean_username}"
    user_id = message.from_user.id
    is_added = await add_channel_for_user(user_id, formatted_url)

    response_text = ""
    if is_added:
        response_text = f"✅ Канал <b>{formatted_url}</b> успішно додано."
        update_queue.put_nowait({'action': 'add_channel', 'url': formatted_url})
    else:
        response_text = f"⚠️ Канал <b>{formatted_url}</b> вже є у вашому списку."
    
    # Надсилаємо повідомлення про результат і одразу повертаємо головне меню
    await message.answer(response_text, parse_mode="HTML", reply_markup=main_menu)
    # Показуємо оновлений список каналів
    await show_channel_list(message, user_id)


# Обробляє натискання на кнопку "Видалити"
@router.callback_query(DeleteCallback.filter(F.action == "del_channel"))
async def delete_channel(callback: CallbackQuery, callback_data: DeleteCallback, update_queue: asyncio.Queue):
    await delete_channel_by_id(callback_data.item_id)
    
    await callback.answer(text="Канал видалено!", show_alert=False)
    
    # Оновлюємо список, редагуючи повідомлення
    await show_channel_list(callback, callback.from_user.id)
    
    update_queue.put_nowait({'action': 'update_subscriptions'})