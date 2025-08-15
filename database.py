# database.py (повністю нова версія)

import asyncpg
from datetime import date
from config import DATABASE_URL

pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def create_tables():
    """Створює або оновлює таблиці для нової архітектури."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Таблиця користувачів (без змін)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                subscription_end_date DATE
            )
        ''')
        # 2. Таблиця каналів (без змін)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_channels (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                channel_url TEXT,
                UNIQUE (user_id, channel_url)
            )
        ''')
        # 3. Таблиця-словник ключових слів (змінена)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_keywords (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                keyword TEXT,
                is_global BOOLEAN DEFAULT FALSE,
                UNIQUE (user_id, keyword)
            )
        ''')
        # 4. НОВА таблиця зв'язків "канал-слово"
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS channel_keyword_links (
                id SERIAL PRIMARY KEY,
                channel_id INTEGER REFERENCES user_channels(id) ON DELETE CASCADE,
                keyword_id INTEGER REFERENCES user_keywords(id) ON DELETE CASCADE,
                UNIQUE (channel_id, keyword_id)
            )
        ''')
        print("Database tables for the new architecture are ready.")
    finally:
        await conn.close()

# --- Базові функції CRUD ---

async def add_user(user_id: int):
    pool = await get_pool()
    await pool.execute("INSERT INTO users (user_id, subscription_end_date) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING", user_id, date(9999, 12, 31))

async def add_channel_for_user(user_id: int, channel_url: str) -> int | None:
    pool = await get_pool()
    # Повертаємо ID новоствореного каналу
    return await pool.fetchval("INSERT INTO user_channels (user_id, channel_url) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING id", user_id, channel_url)

async def add_keyword_for_user(user_id: int, keyword: str, is_global: bool = False) -> int | None:
    pool = await get_pool()
    return await pool.fetchval("INSERT INTO user_keywords (user_id, keyword, is_global) VALUES ($1, $2, $3) ON CONFLICT (user_id, keyword) DO UPDATE SET keyword=EXCLUDED.keyword RETURNING id", user_id, keyword.lower(), is_global)

async def link_keyword_to_channel(channel_id: int, keyword_id: int):
    pool = await get_pool()
    await pool.execute("INSERT INTO channel_keyword_links (channel_id, keyword_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", channel_id, keyword_id)

async def delete_channel(channel_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM user_channels WHERE id = $1", channel_id)

async def delete_keyword(keyword_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM user_keywords WHERE id = $1", keyword_id)

# --- Функції для отримання списків ---

async def get_user_channels(user_id: int) -> list:
    pool = await get_pool()
    return await pool.fetch("SELECT id, channel_url FROM user_channels WHERE user_id = $1 ORDER BY id", user_id)

async def get_user_keywords(user_id: int) -> list:
    pool = await get_pool()
    # Повертає всі слова користувача з позначкою, чи є вони глобальними
    return await pool.fetch("SELECT id, keyword, is_global FROM user_keywords WHERE user_id = $1 ORDER BY id", user_id)

async def get_keywords_for_channel(channel_id: int) -> list:
    pool = await get_pool()
    query = """
        SELECT kw.id, kw.keyword, kw.is_global
        FROM user_keywords kw
        JOIN channel_keyword_links l ON kw.id = l.keyword_id
        WHERE l.channel_id = $1
    """
    return await pool.fetch(query, channel_id)

async def get_channels_for_keyword(keyword_id: int) -> list:
    pool = await get_pool()
    query = """
        SELECT ch.id, ch.channel_url
        FROM user_channels ch
        JOIN channel_keyword_links l ON ch.id = l.channel_id
        WHERE l.keyword_id = $1
    """
    return await pool.fetch(query, keyword_id)
    
async def find_keyword_in_user_list(user_id: int, keyword: str) -> int | None:
    pool = await get_pool()
    return await pool.fetchval("SELECT id FROM user_keywords WHERE user_id = $1 AND keyword = $2", user_id, keyword.lower())

# --- Логіка для моніторингу (Telethon) ---

async def get_all_unique_channels() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT channel_url FROM user_channels")
    return [row['channel_url'] for row in rows]

async def get_subscriptions_for_channel(channel_url: str) -> list:
    pool = await get_pool()
    query = """
        SELECT u.user_id, kw.keyword
        FROM users u
        JOIN user_channels ch ON u.user_id = ch.user_id AND ch.channel_url = $1
        LEFT JOIN channel_keyword_links l ON ch.id = l.channel_id
        LEFT JOIN user_keywords kw ON kw.id = l.keyword_id OR (kw.user_id = u.user_id AND kw.is_global = TRUE)
        WHERE kw.keyword IS NOT NULL
    """
    records = await pool.fetch(query, channel_url)
    return list(set([(r['user_id'], r['keyword']) for r in records])) # Видаляємо дублікати

async def unlink_keyword_from_channel_by_ids(channel_id: int, keyword_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM channel_keyword_links WHERE channel_id = $1 AND keyword_id = $2", channel_id, keyword_id)

async def set_keyword_global_status(keyword_id: int, is_global: bool):
    """Встановлює або знімає глобальний статус для ключового слова."""
    pool = await get_pool()
    await pool.execute("UPDATE user_keywords SET is_global = $1 WHERE id = $2", is_global, keyword_id)