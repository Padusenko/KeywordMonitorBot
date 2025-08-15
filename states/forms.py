# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class AddForm(StatesGroup):
    channel_url = State()
    keyword_name = State() # Для додавання з меню "Мої ключові слова"
    global_keyword_name = State() # Для додавання глобального слова з меню каналів
    new_keyword_for_channel = State() # Для додавання локального слова з меню каналу