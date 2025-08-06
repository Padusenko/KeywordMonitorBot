# handlers/keyword_management.py

import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states.keyword import AddKeyword
from database import add_keyword_for_user, get_user_keywords, delete_keyword_by_id
from keyboards.inline import get_list_keyboard, DeleteCallback

router = Router()


# Цей обробник тепер показує список ключових слів
@router.message(F.text == "📝 Мої ключові слова")
async def show_keywords(message: Message):
    user_id = message.from_user.id
    keywords = await get_user_keywords(user_id)
    
    if not keywords:
        text = "У вас ще немає ключових слів. Бажаєте додати перше?"
        keyboard = get_list_keyboard([], 'del_keyword')
    else:
        text = "Ваші ключові слова для відстеження:"
        keyboard = get_list_keyboard(keywords, 'del_keyword')
    
    await message.answer(text, reply_markup=keyboard)

# Обробник для кнопки "Додати нове слово"
@router.callback_query(F.data == "add_keyword")
async def start_add_keyword_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Надішліть ключове слово або фразу, яку будемо шукати.")
    await state.set_state(AddKeyword.waiting_for_keyword)
    await callback.answer()

# Обробник, коли користувач надсилає слово, перебуваючи у стані AddKeyword.waiting_for_keyword
@router.message(AddKeyword.waiting_for_keyword)
async def process_keyword(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()

    keyword = message.text
    user_id = message.from_user.id
    
    is_added = await add_keyword_for_user(user_id, keyword)
    
    if is_added:
        await message.answer(f"✅ Слово '<b>{keyword}</b>' додано до списку відстеження.", parse_mode="HTML")
        # Надсилаємо сигнал на оновлення
        update_queue.put_nowait({'action': 'update_subscriptions'})
    else:
        await message.answer(f"⚠️ Слово '<b>{keyword}</b>' вже є у вашому списку.", parse_mode="HTML")
    
    # Повертаємо користувача до списку слів
    await show_keywords(message)


# Обробник для видалення ключового слова
@router.callback_query(DeleteCallback.filter(F.action == "del_keyword"))
async def delete_keyword(callback: CallbackQuery, callback_data: DeleteCallback, update_queue: asyncio.Queue):
    keyword_id_to_delete = callback_data.item_id
    await delete_keyword_by_id(keyword_id_to_delete)
    
    user_id = callback.from_user.id
    keywords = await get_user_keywords(user_id)
    
    text = "Ключове слово видалено. Ваш оновлений список:"
    if not keywords:
        text = "Усі ключові слова видалено. Бажаєте додати нове?"
        
    keyboard = get_list_keyboard(keywords, 'del_keyword')
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    
    update_queue.put_nowait({'action': 'update_subscriptions'})
    await callback.answer(text="Слово видалено!", show_alert=False)