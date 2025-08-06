from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Додати канал"),
            KeyboardButton(text="📝 Мої ключові слова")
        ],
        [
            KeyboardButton(text="ℹ️ Про бота")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Оберіть дію з меню...",
    one_time_keyboard=False
)