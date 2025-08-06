from aiogram.fsm.state import State, StatesGroup

class AddKeyword(StatesGroup):
    waiting_for_keyword = State()