from app.core.database import get_session


# Унифицированное получение сессии
async def get_db():
    async for session in get_session():
        yield session
