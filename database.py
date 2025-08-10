import asyncpg
from config import DATABASE_URL

# Пул з'єднань для ефективної роботи
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def create_tables():
    """Створює таблиці в базі даних PostgreSQL, якщо вони ще не існують."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # SERIAL - це аналог AUTOINCREMENT для PostgreSQL
        # BIGINT - для зберігання великих user_id
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                subscription_end_date DATE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_channels (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                channel_url TEXT,
                UNIQUE (user_id, channel_url)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_keywords (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                keyword TEXT,
                UNIQUE (user_id, keyword)
            )
        ''')
        print("Database tables for PostgreSQL created or already exist.")
    finally:
        await conn.close()

# --- Функції, переписані для asyncpg ---

async def add_user(user_id: int):
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO users (user_id, subscription_end_date) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
        user_id, '9999-12-31'
    )

async def add_channel_for_user(user_id: int, channel_url: str) -> bool:
    pool = await get_pool()
    try:
        await pool.execute("INSERT INTO user_channels (user_id, channel_url) VALUES ($1, $2)", user_id, channel_url)
        return True
    except asyncpg.UniqueViolationError:
        return False

async def get_user_channels(user_id: int) -> list:
    pool = await get_pool()
    return await pool.fetch("SELECT id, channel_url FROM user_channels WHERE user_id = $1 ORDER BY id", user_id)

async def delete_channel_by_id(channel_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM user_channels WHERE id = $1", channel_id)

async def add_keyword_for_user(user_id: int, keyword: str) -> bool:
    pool = await get_pool()
    try:
        await pool.execute("INSERT INTO user_keywords (user_id, keyword) VALUES ($1, $2)", user_id, keyword.lower())
        return True
    except asyncpg.UniqueViolationError:
        return False

async def get_user_keywords(user_id: int) -> list:
    pool = await get_pool()
    return await pool.fetch("SELECT id, keyword FROM user_keywords WHERE user_id = $1 ORDER BY id", user_id)

async def delete_keyword_by_id(keyword_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM user_keywords WHERE id = $1", keyword_id)

async def get_all_unique_channels() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT channel_url FROM user_channels")
    return [row['channel_url'] for row in rows]

async def get_subscriptions_for_channel(channel_url: str) -> list:
    pool = await get_pool()
    query = """
        SELECT uk.user_id, uk.keyword
        FROM user_keywords uk
        JOIN user_channels uc ON uk.user_id = uc.user_id
        WHERE uc.channel_url = $1
    """
    # asyncpg.fetch повертає список записів, схожих на словники
    records = await pool.fetch(query, channel_url)
    return [(r['user_id'], r['keyword']) for r in records]