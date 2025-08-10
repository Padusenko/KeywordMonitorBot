# generate_session.py
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# !!! ЗАМІНІТЬ ЦІ ЗНАЧЕННЯ НА ВАШІ ПРОДАКШН-КЛЮЧІ !!!
API_ID = 24119745  # ВАШ ПРОДАКШН API_ID
API_HASH = '1eb686d94f4123b4c31e8e1b227ba101'

print("\nЗапускаємо генерацію рядка сесії...")

# Створюємо клієнт з об'єктом StringSession
with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    # Авторизація відбудеться автоматично
    session_string = client.session.save()

print("\nАвторизація успішна!")
print("Ваш рядок сесії (скопіюйте його повністю, починаючи з '1Ag...'):\n")
print(session_string)
print("\nТепер додайте цей рядок як змінну оточення TELETHON_SESSION на Railway.")