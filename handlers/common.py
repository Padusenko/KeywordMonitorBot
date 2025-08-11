from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message
from keyboards.reply import main_menu
from database import add_user
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id)

    welcome_text = (
        f"<b>Привіт, {message.from_user.full_name}!</b>\n\n"
        "Я ваш персональний бот для моніторингу ключових слів у Telegram-каналах.\n\n"
        "Щоб почати, додайте канали та ключові слова, за якими я буду стежити."
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu)


@router.message(F.text == "ℹ️ Про бота")
async def cmd_about(message: Message):
    about_text = (
        "<b>Про бота</b>\n\n"
        "Цей бот створений для моніторингу ключових слів у публічних Telegram-каналах.\n\n"
        "<b>Як користуватися:</b>\n"
        "1. <b>Додайте канал:</b> Натисніть кнопку '➕ Додати канал' і надішліть посилання на канал у форматі `https://t.me/channel_name` або `@channel_name`.\n"
        "2. <b>Додайте ключові слова:</b> Натисніть '📝 Мої ключові слова' і надішліть слово або фразу, яку бот має шукати.\n"
        "3. <b>Отримуйте сповіщення:</b> Коли в доданому каналі з'явиться повідомлення з вашим ключовим словом, бот миттєво надішле вам сповіщення з посиланням на пост.\n\n"
        "Ви можете додавати декілька каналів та багато ключових слів."
    )
    await message.answer(about_text, parse_mode="HTML")


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