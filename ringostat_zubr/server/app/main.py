from contextlib import asynccontextmanager

import dependencies
from configuration.logger_setup import logger
from database import DatabaseInitializer,wait_for_db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from get_routes import router as get_router  # Import the new GET routes
from post_routes import router as post_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from get_routes import router as get_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_initializer = DatabaseInitializer()
    await wait_for_db()  # Убедитесь, что MySQL готов
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    yield
    await db_initializer.close_pool()


app = FastAPI(lifespan=lifespan)

# Подключаем маршруты API
app.include_router(get_router)

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],  # Явно указать методы
    allow_headers=["Authorization", "Content-Type"],  # Явно указать заголовки
)

# Логирование всех запросов для отладки


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug(f"Request path: {request.url.path}, method: {request.method}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response


# Подключение маршрутов
app.include_router(post_router)
app.include_router(get_router)  # Include the new router


if __name__ == "__main__":
    logger.debug("Запуск FastAPI сервера")
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        ssl_keyfile="/etc/ssl/private/key.pem",  # Укажите путь к ключу внутри контейнера
        ssl_certfile="/etc/ssl/private/cert.pem",  # Укажите путь к сертификату внутри контейнера
        log_level="debug",
    )
