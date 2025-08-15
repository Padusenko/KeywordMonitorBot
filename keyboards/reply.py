# keyboards/reply.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Головне меню, яке бачить користувач
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🗂️ Мої канали"),
            KeyboardButton(text="📝 Мої ключові слова")
        ],
        [
            KeyboardButton(text="ℹ️ Про бота")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Оберіть дію з меню..."
)

# Окрема клавіатура з однією кнопкою "Скасувати" для виходу зі станів
cancel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️ Скасувати")
        ]
    ],
    resize_keyboard=True
)