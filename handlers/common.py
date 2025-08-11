# handlers/common.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state

from keyboards.reply import main_menu
from database import add_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    
    welcome_text = (
        f"<b>Привіт, {message.from_user.full_name}!</b>\n\n"
        "Я ваш персональний бот для моніторингу ключових слів у Telegram-каналах.\n\n"
        "Щоб почати, використовуйте меню нижче."
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu)


@router.message(F.text == "ℹ️ Про бота")
async def cmd_about(message: Message):
    about_text = (
        "<b>Про бота</b>\n\n"
        "Цей бот створений для моніторингу ключових слів у публічних Telegram-каналах.\n\n"
        "<b>Як користуватися:</b>\n"
        "1. <b>Додайте канал:</b> Натисніть '➕ Додати канал' і дотримуйтесь інструкцій.\n"
        "2. <b>Додайте слова:</b> Натисніть '📝 Мої ключові слова' для додавання та видалення слів.\n"
        "3. <b>Отримуйте сповіщення:</b> Коли в каналі з'явиться пост з вашим словом, бот надішле сповіщення.\n\n"
        "Для скасування будь-якої дії використовуйте команду /cancel або кнопку '⬅️ Скасувати'."
    )
    await message.answer(about_text, parse_mode="HTML")


# Універсальний обробник для виходу зі станів
@router.message(StateFilter(any_state), F.text == "⬅️ Скасувати")
@router.message(StateFilter(any_state), Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Дію скасовано. Ви повернулися в головне меню.",
        reply_markup=main_menu # Повертаємо головну клавіатуру
    )