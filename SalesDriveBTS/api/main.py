#/api/main.py
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Импорт настроек и компонентов
from core.config import settings
from core.database import engine, create_tables
from core.logger import logger

# Импорт эндпоинтов
from endpoints.webhook import router as webhook_router
from endpoints import bts_webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Настройка жизненного цикла приложения"""
    try:
        # Пытаемся подключиться к базе данных
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda conn: logger.debug("Успешное подключение к базе данных")
            )
            
            # Если мы в режиме разработки, создаем таблицы
            if settings.ENVIRONMENT == "development":
                await create_tables()
                
        logger.info("Приложение запущено успешно")
        yield
        logger.info("Завершение работы приложения")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        raise


app = FastAPI(
    title="CRM-BTS Middleware",
    description="Сервис для обработки вебхуков CRM и передачи данных в BTS",
    version=settings.VERSION,
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
app.include_router(webhook_router, prefix="/api/crm/webhook", tags=["webhook"])
app.include_router(bts_webhook.router,prefix="/api/bts/webhook",tags=["bts"])

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
    
    # Проверяем существование файлов SSL
    ssl_exists = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)
    
    # Запускаем сервер с SSL или без, в зависимости от наличия сертификатов
    if ssl_exists:
        logger.info("Запуск с SSL")
        uvicorn.run(
            "main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            log_level=settings.API_LOG_LEVEL,
            reload=settings.ENVIRONMENT == "development",
        )
    else:
        logger.warning("Запуск без SSL (сертификаты не найдены)")
        uvicorn.run(
            "main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level=settings.API_LOG_LEVEL,
            reload=settings.ENVIRONMENT == "development",
        )