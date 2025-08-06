from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

# Фабрика колбеків для видалення. 'action' може бути 'del_channel' або 'del_keyword'.
class DeleteCallback(CallbackData, prefix="delete"):
    action: str
    item_id: int

def get_list_keyboard(items: list[tuple[int, str]], action_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for item_id, item_name in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {item_name}", 
                callback_data=DeleteCallback(action=action_prefix, item_id=item_id).pack()
            )
        ])
    
    # Додаємо кнопку для додавання нового елемента
    add_button_text = "➕ Додати новий канал" if action_prefix == "del_channel" else "➕ Додати нове слово"
    buttons.append([
        InlineKeyboardButton(text=add_button_text, callback_data=f"add_{action_prefix.split('_')[1]}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)