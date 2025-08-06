import aiosqlite
import os

if os.getenv('APP_MODE') == 'production':
    DB_NAME = '/data/bot_database.db'
else:
    DB_NAME = 'bot_database.db'


async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                subscription_end_date DATE
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_url TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE (user_id, channel_url)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                keyword TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE (user_id, keyword)
            )
        ''')

        await db.commit()
    print("Database tables created or already exist.")


async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, subscription_end_date) VALUES (?, ?)",
            (user_id, '9999-12-31')
        )
        await db.commit()


async def add_channel_for_user(user_id: int, channel_url: str):
    """Додає новий канал для конкретного користувача."""
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO user_channels (user_id, channel_url) VALUES (?, ?)",
                (user_id, channel_url)
            )
            await db.commit()
            return True  
        except aiosqlite.IntegrityError:
            return False
        

async def get_all_unique_channels() -> list[str]:
    """Повертає список всіх унікальних URL каналів з бази даних."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT DISTINCT channel_url FROM user_channels")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    

async def add_keyword_for_user(user_id: int, keyword: str) -> bool:
    """Додає ключове слово для користувача."""
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO user_keywords (user_id, keyword) VALUES (?, ?)",
                (user_id, keyword.lower()) # Зберігаємо ключові слова в нижньому регістрі
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def get_subscriptions_for_channel(channel_url: str) -> list[tuple[int, str]]:
    """
    Повертає список пар (user_id, keyword) для всіх користувачів,
    що підписані на вказаний канал.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT uk.user_id, uk.keyword
            FROM user_keywords uk
            JOIN user_channels uc ON uk.user_id = uc.user_id
            WHERE uc.channel_url = ?
        """
        cursor = await db.execute(query, (channel_url,))
        return await cursor.fetchall()
    

async def get_user_channels(user_id: int) -> list[tuple[int, str]]:
    """Повертає список каналів (id, url) для конкретного користувача."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, channel_url FROM user_channels WHERE user_id = ?", (user_id,))
        return await cursor.fetchall()

async def get_user_keywords(user_id: int) -> list[tuple[int, str]]:
    """Повертає список ключових слів (id, keyword) для конкретного користувача."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, keyword FROM user_keywords WHERE user_id = ?", (user_id,))
        return await cursor.fetchall()

async def delete_channel_by_id(channel_id: int):
    """Видаляє канал за його унікальним id в базі даних."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM user_channels WHERE id = ?", (channel_id,))
        await db.commit()

async def delete_keyword_by_id(keyword_id: int):
    """Видаляє ключове слово за його унікальним id в базі даних."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM user_keywords WHERE id = ?", (keyword_id,))
        await db.commit()