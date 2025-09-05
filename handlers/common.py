from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state

from keyboards.reply import main_menu
from database import add_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    await add_user(message.from_user.id)
    await message.answer(f"Я ваш персональний асистент для моніторингу ключових слів у Telegram-каналах.\n\n" "Щоб почати, використовуйте меню нижче.", parse_mode="HTML", reply_markup=main_menu)


@router.message(F.text == "ℹ️ Про бота")
async def cmd_about(message: Message):
    about_text = (
        "ℹ️ <b>Про бота та інструкція з використання</b>\n\n"
        "Цей бот дозволяє гнучко налаштовувати відстеження ключових слів у будь-яких публічних Telegram-каналах.\n\n"
        "<b>Основні поняття:</b>\n"
        "📄 <b>Локальне слово</b> — працює тільки в тих каналах, до яких ви його власноруч прив'язали.\n"
        "🌐 <b>Глобальне слово</b> — автоматично шукається у <u>всіх</u> каналах, які ви додали.\n\n"
        "--- --- ---\n\n"
        "<b>Крок 1: Керування каналами (меню '🗂️ Мої канали')</b>\n\n"
        "1. Натисніть <b>'➕ Додати новий канал'</b> та надішліть посилання на канал (напр., `@durov` або `https://t.me/durov`).\n"
        "2. Натисніть на <b>кнопку з назвою каналу</b>, щоб перейти до його налаштувань.\n"
        "3. У меню каналу ви можете:\n"
        "   - <b>'🔗 Прив'язати слово зі списку'</b>: побачити всі ваші слова та відмітити (✅), які з них мають працювати в цьому каналі.\n"
        "   - <b>'➕ Додати нове локальне слово'</b>: додати нове слово, яке одразу буде прив'язане тільки до цього каналу.\n"
        "   - <b>'🗑️ Видалити цей канал'</b>: повністю видалити канал з моніторингу.\n"
        "   - Натиснути на <b>'📄 Слово ❌'</b>, щоб швидко відв'язати локальне слово від каналу.\n\n"
        "--- --- ---\n\n"
        "<b>Крок 2: Керування ключовими словами (меню '📝 Мої ключові слова')</b>\n\n"
        "1. Це ваш <b>загальний словник</b>. Тут ви бачите всі слова, які ви коли-небудь додавали.\n"
        "2. Натисніть <b>'➕ Додати нове слово'</b>, щоб поповнити свій словник. Нові слова за замовчуванням є локальними (📄).\n"
        "3. Натисніть на <b>кнопку-слово з хрестиком (❌)</b>, щоб повністю видалити його з системи (включаючи всі прив'язки до каналів).\n\n"
        "--- --- ---\n\n"
        "💡 <b>Порада:</b> Щоб зробити слово глобальним, спершу додайте його через меню '🗂️ Мої канали' -> '🌐 Додати глобальне слово'.\n\n"
        "Для скасування будь-якої дії в процесі додавання (коли бот щось очікує) використовуйте кнопку <b>'⬅️ Скасувати'</b> або команду /cancel."
    )
    await message.answer(about_text, parse_mode="HTML")


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    main_menu_text = f"<b>Привіт, {callback.from_user.full_name}!</b>..."
    try:
        await callback.message.edit_text(main_menu_text, parse_mode="HTML", reply_markup=None)
    except Exception:
        await callback.message.answer(main_menu_text, parse_mode="HTML")
    await callback.answer()


@router.message(StateFilter(any_state), F.text == "⬅️ Скасувати")
@router.message(StateFilter(any_state), Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Дію скасовано.", reply_markup=main_menu)