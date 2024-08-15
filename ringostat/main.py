# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from configuration.logger_setup import logger
from database import DatabaseInitializer
import dependencies  # Импортируем модуль для хранения зависимостей
from post_routes import router as post_router
from get_routes import router as get_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    dependencies.db_initializer = DatabaseInitializer()
    await dependencies.db_initializer.create_database()
    await dependencies.db_initializer.create_pool()
    await dependencies.db_initializer.init_db()
    yield
    await dependencies.db_initializer.close_pool()

app = FastAPI(lifespan=lifespan)

app.include_router(post_router)
app.include_router(get_router)

if __name__ == "__main__":
    logger.debug("Запуск FastAPI сервера")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
