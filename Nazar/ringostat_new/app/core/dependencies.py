from app.core.database import (
    get_session,
)  # Импорт функции для создания асинхронной сессии.


# Унифицированное получение сессии базы данных.
# Используется как зависимость для маршрутов в FastAPI.
async def get_db():
    async for session in get_session():
        # Возвращаем сессию для использования в обработчиках.
        yield session
