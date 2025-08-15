from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any

# --- Фабрика колбеків ---
class MenuCallback(CallbackData, prefix="menu"):
    level: str
    action: str
    item_id: int | None = None

class UnlinkCallback(CallbackData, prefix="unlink"):
    channel_id: int
    keyword_id: int

class ToggleLinkCallback(CallbackData, prefix="toggle_link"):
    channel_id: int
    keyword_id: int

# --- Меню "Мої канали" ---
def channels_main_keyboard(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for channel in channels:
        builder.button(
            text=channel['channel_url'],
            callback_data=MenuCallback(level='channel_config', action='view', item_id=channel['id']).pack() # <-- .pack() ДОДАНО
        )
    builder.adjust(1)
    
    builder.row(InlineKeyboardButton(
        text="➕ Додати новий канал",
        callback_data=MenuCallback(level='main_channels', action='add_channel').pack() # <-- .pack() ДОДАНО
    ))
    builder.row(InlineKeyboardButton(
        text="🌐 Додати глобальне слово",
        callback_data=MenuCallback(level='main_channels', action='add_global_kw').pack() # <-- .pack() ДОДАНО
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад до головного меню",
        callback_data="back_to_main_menu"
    ))
    
    return builder.as_markup()

# --- Меню керування конкретним каналом ---
def channel_config_keyboard(channel_id: int, keywords: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if keywords:
        for kw in keywords:
            status = "🌐" if kw['is_global'] else "📄"
            if not kw['is_global']:
                builder.button(
                    text=f"{status} {kw['keyword']} ❌",
                    # Використовуємо нову, надійну фабрику
                    callback_data=UnlinkCallback(channel_id=channel_id, keyword_id=kw['id']).pack()
                )
            else:
                builder.button(
                    text=f"{status} {kw['keyword']}",
                    callback_data="ignore_global_kw"
                )
        builder.adjust(2)

    builder.row(InlineKeyboardButton(
        text="🔗 Прив'язати слово зі списку",
        callback_data=MenuCallback(level='channel_config', action='link', item_id=channel_id).pack() # <-- .pack() ДОДАНО
    ))

    builder.row(InlineKeyboardButton(
        text="➕ Додати нове локальне слово",
        callback_data=MenuCallback(level='channel_config', action='add_kw', item_id=channel_id).pack() # <-- .pack() ДОДАНО
    ))

    builder.row(InlineKeyboardButton(
        text="🗑️ Видалити цей канал",
        callback_data=MenuCallback(level='main_channels', action='delete', item_id=channel_id).pack() # <-- .pack() ДОДАНО
    ))

    builder.row(InlineKeyboardButton(
        text="⬅️ Назад до списку каналів",
        callback_data=MenuCallback(level='main_channels', action='view').pack() # <-- .pack() ДОДАНО
    ))
    
    return builder.as_markup()

# --- Меню "Мої ключові слова" ---
def keywords_main_keyboard(keywords: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for kw in keywords:
        status = "🌐" if kw['is_global'] else "📄"
        builder.button(
            text=f"{status} {kw['keyword']} ❌",
            callback_data=MenuCallback(level='main_keywords', action='delete', item_id=kw['id']).pack() # <-- .pack() ДОДАНО
        )
    builder.adjust(2)
    
    builder.row(InlineKeyboardButton(
        text="➕ Додати нове слово",
        callback_data=MenuCallback(level='main_keywords', action='add').pack() # <-- .pack() ДОДАНО
    ))

    builder.row(InlineKeyboardButton(
        text="⬅️ Назад до головного меню",
        callback_data="back_to_main_menu"
    ))

    return builder.as_markup()

# --- Допоміжна клавіатура для прив'язки слів ---
def link_keywords_keyboard(channel_id: int, all_keywords: list, linked_keywords_ids: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for kw in all_keywords:
        text = f"{'✅' if kw['id'] in linked_keywords_ids else ' '}{'🌐' if kw['is_global'] else '📄'} {kw['keyword']}"
        builder.button(
            text=text,
            # Використовуємо нову, надійну фабрику
            callback_data=ToggleLinkCallback(channel_id=channel_id, keyword_id=kw['id']).pack()
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад до меню каналу", 
        callback_data=MenuCallback(level='channel_config', action='view', item_id=channel_id).pack()
    ))
    return builder.as_markup()