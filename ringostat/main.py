# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from configuration.logger_setup import logger
from database import DatabaseInitializer
import dependencies  # Импортируем модуль для хранения зависимостей
from post_routes import router as post_router
from get_routes import router as get_router
from put_routes import router as put_router  # Импортируем маршруты из put_routes
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    dependencies.db_initializer = DatabaseInitializer()
    await dependencies.db_initializer.create_database()
    await dependencies.db_initializer.create_pool()
    await dependencies.db_initializer.init_db()
    yield
    await dependencies.db_initializer.close_pool()


app = FastAPI(lifespan=lifespan)

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Разрешить запросы с любых источников (можно указать конкретные домены)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить любые методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешить любые заголовки
)
app.include_router(post_router)  # Подключаем маршруты post_router
app.include_router(get_router)  # Подключаем маршруты put_routes
app.include_router(put_router)  # Подключаем маршруты get_router


if __name__ == "__main__":
    logger.debug("Запуск FastAPI сервера")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
