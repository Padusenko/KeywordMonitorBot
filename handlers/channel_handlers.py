import re
import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from keyboards.inline import (
    channels_main_keyboard, channel_config_keyboard, link_keywords_keyboard, 
    MenuCallback, UnlinkCallback, ToggleLinkCallback
)
from states.forms import AddForm
from database import *
from keyboards.inline import *
from keyboards.reply import main_menu, cancel_menu

channels_router = Router()

# --- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ОНОВЛЕННЯ МЕНЮ ---

async def show_channel_list(message_or_callback: Message | CallbackQuery):
    """Надсилає або оновлює повідомлення зі списком каналів."""
    user_id = message_or_callback.from_user.id
    channels = await get_user_channels(user_id)
    text = "🗂️ **Ваші канали для моніторингу:**" if channels else "У вас ще немає доданих каналів."
    keyboard = channels_main_keyboard(channels)
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else: # Якщо це CallbackQuery
        try:
            await message_or_callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            # Якщо повідомлення неможливо змінити, надсилаємо нове
            await message_or_callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


async def show_channel_menu(callback: CallbackQuery, channel_id: int):
    """Надсилає або оновлює меню керування конкретним каналом."""
    user_id = callback.from_user.id
    # Отримуємо як прив'язані, так і всі глобальні слова користувача
    linked_keywords = await get_keywords_for_channel(channel_id)
    all_user_keywords = await get_user_keywords(user_id)
    global_keywords = [kw for kw in all_user_keywords if kw['is_global']]
    
    # Створюємо єдиний список, уникаючи дублікатів
    visible_keywords_dict = {kw['id']: kw for kw in linked_keywords}
    for kw in global_keywords:
        if kw['id'] not in visible_keywords_dict:
            visible_keywords_dict[kw['id']] = kw
    
    all_visible_keywords = list(visible_keywords_dict.values())

    channels = await get_user_channels(user_id)
    channel_url = next((ch['channel_url'] for ch in channels if ch['id'] == channel_id), "Невідомий канал")

    text = f"⚙️ **Керування каналом:**\n`{channel_url}`\n\n📄-локальне, 🌐-глобальне"
    keyboard = channel_config_keyboard(channel_id, all_visible_keywords)
    
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


# --- ОБРОБНИКИ НАВІГАЦІЇ ---

@channels_router.message(F.text == "🗂️ Мої канали")
async def channels_menu_command(message: Message):
    await show_channel_list(message)

# Обробник кнопок у головному меню каналів
@channels_router.callback_query(MenuCallback.filter(F.level == 'main_channels'))
async def navigate_channels_menu(callback: CallbackQuery, callback_data: MenuCallback, state: FSMContext, update_queue: asyncio.Queue):
    action = callback_data.action
    
    if action == 'add_channel':
        await callback.message.answer("Надішліть посилання на новий канал:", reply_markup=cancel_menu)
        await state.set_state(AddForm.channel_url)
    elif action == 'add_global_kw':
        await callback.message.answer("Надішліть нове **глобальне** ключове слово (буде шукатися у всіх каналах):", reply_markup=cancel_menu)
        await state.set_state(AddForm.global_keyword_name)
    elif action == 'view':
        await show_channel_list(callback)
    elif action == 'delete':
        await delete_channel(callback_data.item_id)
        await callback.answer("Канал видалено!", show_alert=True)
        await show_channel_list(callback)
        update_queue.put_nowait({'action': 'update_subscriptions'})
    await callback.answer()

# Обробник кнопок у меню конкретного каналу
@channels_router.callback_query(MenuCallback.filter(F.level == 'channel_config'))
async def navigate_channel_submenu(callback: CallbackQuery, callback_data: MenuCallback, state: FSMContext):
    action = callback_data.action
    channel_id = callback_data.item_id
    
    if action == 'view':
        await show_channel_menu(callback, channel_id)
    elif action == 'add_kw':
        await state.update_data(current_channel_id=channel_id)
        await callback.message.answer("Надішліть нове **локальне** слово для цього каналу:", reply_markup=cancel_menu)
        await state.set_state(AddForm.new_keyword_for_channel)
        await callback.answer()
    elif action == 'link':
        all_keywords = await get_user_keywords(callback.from_user.id)
        if not all_keywords:
            await callback.answer("У вас ще немає слів у загальному списку. Спочатку додайте їх через меню 'Мої ключові слова'.", show_alert=True)
            return
        linked_keywords = await get_keywords_for_channel(channel_id)
        linked_ids = [kw['id'] for kw in linked_keywords]
        text = "Оберіть слова для прив'язки до цього каналу (натисніть, щоб додати/видалити):"
        keyboard = link_keywords_keyboard(channel_id, all_keywords, linked_ids)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()


# --- ОБРОБНИКИ СТАНІВ (FSM) ---

@channels_router.message(AddForm.channel_url)
async def process_new_channel(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()
    match = re.match(r'(?:https?:\/\/)?(?:t(?:elegram)?\.me\/|@)([a-zA-Z0-9_]{5,32})', message.text.strip())
    
    if not match:
        await message.answer("❌ **Помилка.** Неправильний формат посилання.", reply_markup=main_menu)
        return
        
    formatted_url = f"https://t.me/{match.group(1)}"
    channel_id = await add_channel_for_user(message.from_user.id, formatted_url)
    
    if channel_id:
        await message.answer(f"✅ Канал <b>{formatted_url}</b> успішно додано.", parse_mode="HTML", reply_markup=main_menu)
        update_queue.put_nowait({'action': 'add_channel', 'url': formatted_url})
    else:
        await message.answer(f"⚠️ Канал <b>{formatted_url}</b> вже є у списку.", parse_mode="HTML", reply_markup=main_menu)
    await show_channel_list(message)

@channels_router.message(AddForm.global_keyword_name)
async def process_new_global_keyword(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()
    await add_keyword_for_user(message.from_user.id, message.text, is_global=True)
    await message.answer(f"✅ Глобальне слово '<b>{message.text}</b>' успішно додано.", parse_mode="HTML", reply_markup=main_menu)
    update_queue.put_nowait({'action': 'update_subscriptions'})
    await show_channel_list(message)

@channels_router.message(AddForm.new_keyword_for_channel)
async def process_new_local_keyword(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    data = await state.get_data()
    channel_id = data.get('current_channel_id')
    await state.clear()
    
    keyword_name = message.text
    user_id = message.from_user.id
    
    keyword_id = await add_keyword_for_user(user_id, keyword_name, is_global=False)
    if not keyword_id:
        keyword_id = await find_keyword_in_user_list(user_id, keyword_name)
    
    if keyword_id:
        await link_keyword_to_channel(channel_id, keyword_id)
        await message.answer(f"✅ Слово '<b>{keyword_name}</b>' додано та прив'язано до каналу.", parse_mode="HTML", reply_markup=main_menu)
        update_queue.put_nowait({'action': 'update_subscriptions'})
    
    # Повертаємо користувача в меню каналу
    fake_callback = types.CallbackQuery(id='fake', from_user=message.from_user, chat_instance='fake', message=message)
    await show_channel_menu(fake_callback, channel_id)


# --- ОБРОБНИКИ ДРІБНИХ КОЛБЕКІВ ---

@channels_router.callback_query(ToggleLinkCallback.filter())
async def toggle_keyword_link(callback: CallbackQuery, callback_data: ToggleLinkCallback, update_queue: asyncio.Queue):
    # Отримуємо дані безпечно з об'єкта callback_data
    channel_id = callback_data.channel_id
    keyword_id = callback_data.keyword_id
    
    linked_keywords = await get_keywords_for_channel(channel_id)
    is_linked = any(kw['id'] == keyword_id for kw in linked_keywords)
    
    if is_linked:
        await unlink_keyword_from_channel_by_ids(channel_id, keyword_id)
        await callback.answer("Прив'язку видалено")
    else:
        await link_keyword_to_channel(channel_id, keyword_id)
        await callback.answer("Слово прив'язано")
        
    # Оновлюємо клавіатуру, щоб показати зміни
    all_keywords = await get_user_keywords(callback.from_user.id)
    linked_keywords_new = await get_keywords_for_channel(channel_id)
    linked_ids = [kw['id'] for kw in linked_keywords_new]
    keyboard = link_keywords_keyboard(channel_id, all_keywords, linked_ids)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        # Може виникнути помилка, якщо клавіатура не змінилася. Просто ігноруємо.
        pass
    
    update_queue.put_nowait({'action': 'update_subscriptions'})


@channels_router.callback_query(UnlinkCallback.filter())
async def unlink_keyword(callback: CallbackQuery, callback_data: UnlinkCallback, update_queue: asyncio.Queue):
    # Тепер ми отримуємо дані безпечно, як об'єкт
    channel_id = callback_data.channel_id
    keyword_id = callback_data.keyword_id

    # Викликаємо функцію для видалення зв'язку з бази даних
    await unlink_keyword_from_channel_by_ids(channel_id, keyword_id)

    await callback.answer("Прив'язку слова видалено", show_alert=False)
    
    # Оновлюємо меню каналу, щоб показати зміни
    await show_channel_menu(callback, channel_id)
    
    # Надсилаємо сигнал в Telethon про необхідність оновити кеш
    update_queue.put_nowait({'action': 'update_subscriptions'})