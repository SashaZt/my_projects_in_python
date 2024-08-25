# dependencies.py
from typing import Optional
from database import DatabaseInitializer

db_initializer: Optional[DatabaseInitializer] = None
async def get_db():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    return db_initializer