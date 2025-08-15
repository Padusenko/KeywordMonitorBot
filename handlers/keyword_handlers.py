import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states.forms import AddForm
from database import get_user_keywords, add_keyword_for_user, delete_keyword
from keyboards.inline import keywords_main_keyboard, MenuCallback
from keyboards.reply import main_menu, cancel_menu

keywords_router = Router()

async def show_keyword_list(message_or_callback: Message | CallbackQuery):
    """Надсилає або оновлює повідомлення зі списком усіх ключових слів."""
    user_id = message_or_callback.from_user.id
    keywords = await get_user_keywords(user_id)
    text = (
        "📝 **Ваші ключові слова:**\n\n"
        "Натисніть на слово, щоб видалити його."
    ) if keywords else "У вас ще немає доданих ключових слів."
    keyboard = keywords_main_keyboard(keywords)
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else: # Якщо це CallbackQuery
        try:
            await message_or_callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            await message_or_callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@keywords_router.message(F.text == "📝 Мої ключові слова")
async def keywords_menu_command(message: Message):
    await show_keyword_list(message)


@keywords_router.callback_query(MenuCallback.filter(F.level == 'main_keywords'))
async def navigate_keywords_menu(callback: CallbackQuery, callback_data: MenuCallback, state: FSMContext, update_queue: asyncio.Queue):
    action = callback_data.action
    
    if action == 'add':
        await callback.message.answer("Надішліть нове слово (воно буде додано як локальне, його можна буде прив'язати до каналів):", reply_markup=cancel_menu)
        await state.set_state(AddForm.keyword_name)
        await callback.answer()
    
    elif action == 'delete':
        await delete_keyword(callback_data.item_id)
        await callback.answer("Слово видалено!", show_alert=True)
        await show_keyword_list(callback)
        update_queue.put_nowait({'action': 'update_subscriptions'})


@keywords_router.message(AddForm.keyword_name)
async def process_new_keyword(message: Message, state: FSMContext, update_queue: asyncio.Queue):
    await state.clear()
    keyword_name = message.text
    user_id = message.from_user.id
    
    keyword_id = await add_keyword_for_user(user_id, keyword_name, is_global=False)
    
    if keyword_id:
        await message.answer(f"✅ Слово '<b>{keyword_name}</b>' додано до вашого загального списку.", parse_mode="HTML", reply_markup=main_menu)
        update_queue.put_nowait({'action': 'update_subscriptions'})
    else:
        await message.answer(f"⚠️ Слово '<b>{keyword_name}</b>' вже є у вашому списку.", parse_mode="HTML", reply_markup=main_menu)
        
    await show_keyword_list(message)