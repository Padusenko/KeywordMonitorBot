from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter

router = Router()

# Цей обробник буде "ловити" будь-які текстові повідомлення,
# які не є командами і для яких користувач не перебуває в якомусь стані.
@router.message(StateFilter(None))
async def handle_unknown_text(message: Message):
    await message.answer(
        "Я вас не зовсім розумію. Будь ласка, використовуйте кнопки меню для взаємодії зі мною."
    )