# database/connection.py
import aiosqlite
import asyncio
import logging
import os

DATABASE_PATH = "data/database.db"

async def init_database():
    """Инициализация базы данных"""
    # Создаем директорию если не существует
    os.makedirs("data", exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                location TEXT NOT NULL,
                max_participants INTEGER DEFAULT 4,
                price INTEGER DEFAULT 90,
                created_by INTEGER REFERENCES users(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                group_message_id INTEGER,
                weekday INTEGER DEFAULT 0
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id),
                user_id INTEGER REFERENCES users(id),
                status TEXT CHECK(status IN ('registered', 'cancelled')) DEFAULT 'registered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cancelled_at TIMESTAMP,
                UNIQUE(event_id, user_id)
            )
        ''')
        
        # Добавляем новые колонки к существующей таблице events если их нет
        try:
            await db.execute('ALTER TABLE events ADD COLUMN group_message_id INTEGER')
            print("✅ Добавлена колонка group_message_id")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️ Колонка group_message_id уже существует")
            else:
                print(f"⚠️ Ошибка при добавлении group_message_id: {e}")
        
        try:
            await db.execute('ALTER TABLE events ADD COLUMN weekday INTEGER DEFAULT 0')
            print("✅ Добавлена колонка weekday")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️ Колонка weekday уже существует")
            else:
                print(f"⚠️ Ошибка при добавлении weekday: {e}")
        
        await db.commit()
        logging.info("База данных инициализирована")

def get_db():
    """Получение соединения с БД"""
    return aiosqlite.connect(DATABASE_PATH)