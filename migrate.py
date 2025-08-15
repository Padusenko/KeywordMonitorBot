# migrate.py (більш надійна версія)
import asyncio
import asyncpg
import os

async def main():
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("ПОМИЛКА: Змінна оточення DATABASE_URL не знайдена!")
        return

    print("Підключення до бази даних...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Підключення успішне.")

    try:
        # --- Транзакція: або все, або нічого ---
        async with conn.transaction():
            print("Крок 1: Оновлення таблиці user_keywords...")
            # Перевіряємо, чи існує колонка, перш ніж додавати
            column_exists = await conn.fetchval('''
                SELECT EXISTS (
                   SELECT FROM information_schema.columns
                   WHERE table_name = 'user_keywords' AND column_name = 'is_global'
                );
            ''')
            if not column_exists:
                await conn.execute("ALTER TABLE user_keywords ADD COLUMN is_global BOOLEAN DEFAULT FALSE;")
                print("  - Колонка is_global успішно додана.")
            else:
                print("  - Колонка is_global вже існує.")
            
            print("Крок 2: Створення таблиці channel_keyword_links...")
            # Ця команда вже ідемпотентна завдяки "IF NOT EXISTS", залишаємо її
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS channel_keyword_links (
                    id SERIAL PRIMARY KEY,
                    channel_id INTEGER REFERENCES user_channels(id) ON DELETE CASCADE,
                    keyword_id INTEGER REFERENCES user_keywords(id) ON DELETE CASCADE,
                    UNIQUE (channel_id, keyword_id)
                )
            ''')
            print("  - Таблиця channel_keyword_links створена або вже існує.")

            print("Крок 3: Перенесення існуючих зв'язків...")
            migration_query = """
                INSERT INTO channel_keyword_links (channel_id, keyword_id)
                SELECT uc.id, uk.id
                FROM user_channels uc
                JOIN user_keywords uk ON uc.user_id = uk.user_id
                ON CONFLICT (channel_id, keyword_id) DO NOTHING;
            """
            result = await conn.execute(migration_query)
            print(f"  - Міграцію завершено. {result.split()[-1]} зв'язків було створено.")
        
        print("\nМіграція успішно завершена в рамках транзакції.")

    except Exception as e:
        print(f"\nСТАЛАСЯ ПОМИЛКА ПІД ЧАС МІГРАЦІЇ: {e}")
    finally:
        await conn.close()
        print("\nЗ'єднання з базою даних закрито. Скрипт завершив роботу.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())