import asyncio
import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from keyboards.reply import cancel_menu
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
    await callback.message.answer(
        "Будь ласка, надішліть посилання на Telegram-канал.\n"
        "Наприклад: https://t.me/telegram або @telegram",
        reply_markup=cancel_menu # <--- Показуємо кнопку "Скасувати"
    )
    await state.set_state(AddChannel.waiting_for_url)
    await callback.answer()

# Цей обробник спрацьовує, коли користувач надсилає URL, перебуваючи у стані AddChannel.waiting_for_url
@router.message(AddChannel.waiting_for_url)
async def process_channel_url(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    channel_url = message.text.strip() # Одразу прибираємо зайві пробіли

    # Регулярний вираз для перевірки посилань t.me/ або @username
    pattern = r'(?:https?:\/\/)?(?:t(?:elegram)?\.me\/|@)([a-zA-Z0-9_]{5,32})'
    match = re.match(pattern, channel_url)

    if not match:
        # Якщо текст не відповідає патерну, просимо ввести ще раз
        await message.answer("❌ **Помилка.** Це не схоже на правильне посилання на Telegram-канал. \nБудь ласка, надішліть посилання у форматі `https://t.me/channel_name` або `@channel_name`.")
        # Важливо: ми не виходимо зі стану, даючи користувачеві ще одну спробу
        return

    # Якщо валідація пройшла, виходимо зі стану
    await state.clear()
    
    # Форматуємо посилання до єдиного вигляду
    clean_username = match.group(1)
    formatted_url = f"https://t.me/{clean_username}"

    user_id = message.from_user.id
    is_added = await add_channel_for_user(user_id, formatted_url)

    if is_added:
        await message.answer(f"✅ Чудово! Канал <b>{formatted_url}</b> успішно додано.", parse_mode="HTML")
        update_queue.put_nowait({'action': 'add_channel', 'url': formatted_url})
    else:
        await message.answer(f"⚠️ Канал <b>{formatted_url}</b> вже є у вашому списку.", parse_mode="HTML")
        
     # Повідомляємо, що все гаразд (це можна навіть прибрати, якщо хочете менше повідомлень)
    await message.answer("Ви повернулися в головне меню.", reply_markup=main_menu)
    
    # Показуємо оновлений список каналів (вже без Reply-клавіатури)
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