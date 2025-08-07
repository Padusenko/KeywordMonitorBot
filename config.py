import os
from dotenv import load_dotenv

APP_MODE = os.getenv('APP_MODE', 'development')

if APP_MODE == 'production':
    dotenv_path = '.env.prod'
    print("Loading PRODUCTION configuration...")
else:
    dotenv_path = '.env.dev'
    print("Loading DEVELOPMENT configuration...")

load_dotenv(dotenv_path=dotenv_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TELETHON_SESSION = os.getenv('TELETHON_SESSION')

print("-" * 20)
print(f"APP_MODE: {APP_MODE}")
print(f"BOT_TOKEN loaded: {'Yes' if BOT_TOKEN else 'No'}")
print(f"API_ID loaded: {'Yes' if API_ID else 'No'}")
print(f"API_HASH loaded: {'Yes' if API_HASH else 'No'}")
print(f"TELETHON_SESSION loaded: {'Yes' if TELETHON_SESSION else 'No'}")
print(f"TELETHON_SESSION content (first 10 chars): {str(TELETHON_SESSION)[:10] if TELETHON_SESSION else 'None'}")
print("-" * 20)

if not all([BOT_TOKEN, API_ID, API_HASH]):
    raise ValueError("One or more environment variables are not set. Check your .env file.")