# api/main.py
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Импорт настроек и компонентов
from core.config import settings
from core.database import engine
from core.logger import logger

# Импорт эндпоинтов
from endpoints.user import router as user_router
from endpoints.stats import router as stats_router
from endpoints.live import router as live_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Настройка жизненного цикла приложения"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda conn: logger.debug("Успешное подключение к базе данных")
            )
        yield
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        raise


app = FastAPI(
    title="TikTok Analytics API",
    description="API для аналитики данных TikTok",
    version="1.0.0",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug(f"Получен запрос: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Отправлен ответ со статусом: {response.status_code}")
    return response


# Подключение маршрутов
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
app.include_router(live_router, prefix="/api/live", tags=["live"])


# Базовый маршрут для проверки здоровья API
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "API работает нормально"}


# Логирование зарегистрированных маршрутов
logger.debug("Зарегистрированные маршруты:")
for route in app.routes:
    if hasattr(route, "methods"):
        logger.debug(f"Маршрут: {route.path} [{', '.join(route.methods)}]")


if __name__ == "__main__":
    logger.debug("Запуск сервера FastAPI")
    
    # Проверяем наличие SSL-сертификатов
    ssl_keyfile = settings.SSL_KEYFILE
    ssl_certfile = settings.SSL_CERTFILE
    
    # Логируем информацию о файлах
    logger.debug(f"Путь к SSL ключу: {ssl_keyfile}")
    logger.debug(f"Путь к SSL сертификату: {ssl_certfile}")
    
    # Проверяем существование файлов
    if not os.path.exists(ssl_keyfile):
        logger.error(f"SSL ключ не найден по пути: {ssl_keyfile}")
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(ssl_keyfile), exist_ok=True)
        
        # Запускаем без SSL, если файлы не существуют
        logger.warning("Запуск без SSL из-за отсутствия сертификатов")
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level=settings.API_LOG_LEVEL,
        )
    else:
        # Запускаем с SSL
        logger.info("Запуск с SSL")
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            log_level=settings.API_LOG_LEVEL,
        )