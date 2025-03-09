import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn

# Исправленные импорты для API маршрутов
from app.api.get_routes import router as get_routes
from app.api.post_routes import router as post_routes

# Подключаем базу данных
from app.db import engine
from app.logger import logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Пути к SSL сертификатам
SSL_KEYFILE = "/etc/ssl/private/key.pem"
SSL_CERTFILE = "/etc/ssl/private/cert.pem"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda conn: logger.debug("Успешное подключение к базе данных")
            )
        yield
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        raise


# Создание приложения FastAPI
app = FastAPI(
    title="Kaufland API",
    description="API для управления продуктами",
    version="1.0.0",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Рекомендуется указать конкретные домены в production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug(f"Получен запрос: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Отправлен ответ со статусом: {response.status_code}")
    return response


# Подключение маршрутов
app.include_router(get_routes, prefix="/get", tags=["GET Endpoints"])
app.include_router(post_routes, prefix="/post", tags=["POST Endpoints"])


# Тестовый маршрут для проверки
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to Kaufland API"}


logger.debug("Зарегистрированные маршруты:")
for route in app.routes:
    logger.debug(f"Маршрут: {route.path} [{', '.join(route.methods)}]")

if __name__ == "__main__":
    logger.debug("Запуск сервера FastAPI")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        ssl_keyfile=SSL_KEYFILE,
        ssl_certfile=SSL_CERTFILE,
        log_level="debug",
    )
