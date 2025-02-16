# dependencies.py
from core.database import get_session

# Унифицированное получение сессии базы данных.
async def get_db():
    async for session in get_session():
        yield session
