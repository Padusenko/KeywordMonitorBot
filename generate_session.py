from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = 24119745
API_HASH = '1eb686d94f4123b4c31e8e1b227ba101'

print("\nЗапускаємо генерацію рядка сесії...")
print("Будь ласка, введіть ваш номер телефону та код з Telegram.")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session_string = client.session.save()

print("\n✅ Авторизація успішна!")
print("Ваш рядок сесії (скопіюйте його повністю, починаючи з '1A...'):\n")
print(session_string)
print("\nТепер додайте цей рядок як змінну оточення TELETHON_SESSION на Railway.")