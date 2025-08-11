# handlers/keyword_management.py

import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states.keyword import AddKeyword
from database import add_keyword_for_user, get_user_keywords, delete_keyword_by_id
from keyboards.inline import get_list_keyboard, DeleteCallback
from keyboards.reply import main_menu, cancel_menu

router = Router()


# Допоміжна функція для показу списку слів
async def show_keyword_list(message: types.User | Message | CallbackQuery, user_id: int):
    keywords = await get_user_keywords(user_id)
    text = "Ваші ключові слова для відстеження:" if keywords else "У вас ще немає ключових слів."
    keyboard = get_list_keyboard(keywords, 'del_keyword')

    if isinstance(message, Message):
        await message.answer(text, reply_markup=keyboard)
    else: # Якщо це CallbackQuery
        await message.message.edit_text(text, reply_markup=keyboard)


# Спрацьовує на кнопку "Мої ключові слова"
@router.message(F.text == "📝 Мої ключові слова")
async def show_keywords_command(message: Message):
    await show_keyword_list(message, message.from_user.id)


# Спрацьовує на inline-кнопку "Додати нове слово"
@router.callback_query(F.data == "add_keyword")
async def start_add_keyword_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Надішліть ключове слово або фразу, яку будемо шукати.",
        reply_markup=cancel_menu
    )
    await state.set_state(AddKeyword.waiting_for_keyword)
    await callback.answer()


# Обробляє слово, надіслане користувачем
@router.message(AddKeyword.waiting_for_keyword)
async def process_keyword(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()

    keyword = message.text
    user_id = message.from_user.id
    is_added = await add_keyword_for_user(user_id, keyword)
    
    response_text = ""
    if is_added:
        response_text = f"✅ Слово '<b>{keyword}</b>' додано до списку відстеження."
        update_queue.put_nowait({'action': 'update_subscriptions'})
    else:
        response_text = f"⚠️ Слово '<b>{keyword}</b>' вже є у вашому списку."
        
    await message.answer(response_text, parse_mode="HTML", reply_markup=main_menu)
    await show_keyword_list(message, user_id)


# Обробляє натискання на кнопку "Видалити"
@router.callback_query(DeleteCallback.filter(F.action == "del_keyword"))
async def delete_keyword(callback: CallbackQuery, callback_data: DeleteCallback, update_queue: asyncio.Queue):
    await delete_keyword_by_id(callback_data.item_id)
    
    await callback.answer(text="Слово видалено!", show_alert=False)
    
    await show_keyword_list(callback, callback.from_user.id)

    update_queue.put_nowait({'action': 'update_subscriptions'})