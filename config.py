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

if not all([BOT_TOKEN, API_ID, API_HASH]):
    raise ValueError("One or more environment variables are not set. Check your .env file.")