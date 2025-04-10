import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn  # Запуск сервера.
from app.api.auth_router_easyms import auth_router  # Роутер для EasySMS.
from app.api.get_routes import router as get_routes  # Роутер для GET-запросов.
from app.api.olx_message_routes import router as olx_message_router
from app.api.olx_routes import router as olx_router
from app.api.olx_token_routes import router as olx_token_router
from app.api.post_routes import router as post_router  # Роутер для POST-запросов.
from app.api.reservation_routes import (
    router as reservation_router,  # Добавляем роутер для бронирований
)
from app.api.webhook_routes import (
    router as webhook_router,  # Добавляем роутер для webhook
)
from app.core.config import SSL_CERTFILE, SSL_KEYFILE  # Настройки SSL.
from app.core.database import engine  # Подключение к базе данных.
from app.core.dependencies import get_db  # Зависимость для работы с базой.
from app.tasks.webhook_tasks import start_webhook_task
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # Для настройки CORS.
from fastapi.responses import JSONResponse  # Формат ответа в JSON.
from loguru import logger

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# Глобальная переменная для хранения задачи webhook
webhook_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Глобальная переменная для хранения задачи
    global webhook_task

    try:
        # Проверка подключения к базе
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda conn: logger.debug("Database connection successful")
            )

        # Запускаем задачу для обработки webhook каждую минуту
        logger.info("Starting webhook task")
        webhook_task = asyncio.create_task(start_webhook_task(interval_seconds=60))

        yield

        # Код выполняется при завершении работы приложения
        if webhook_task:
            logger.info("Cancelling webhook task")
            webhook_task.cancel()
            try:
                await webhook_task
            except asyncio.CancelledError:
                logger.info("Webhook task cancelled successfully")
    except Exception as e:
        # Логирование ошибок на этапе старта приложения.
        logger.error(f"Failed during app startup: {e}")
        raise


# Создание приложения FastAPI
app = FastAPI(lifespan=lifespan)  # lifespan обрабатывает события запуска и завершения

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Разрешены все домены, рекомендуется заменить на определённые.
    allow_credentials=True,  # Разрешён доступ с учётом аутентификации.
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],  # Разрешённые методы.
    allow_headers=["Authorization", "Content-Type"],  # Разрешённые заголовки.
)


# Логирование всех запросов
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug(f"Request path: {request.url.path}, method: {request.method}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response


# Подключение маршрутов
app.include_router(post_router)  # Роутер для POST-запросов.
app.include_router(get_routes)  # Роутер для GET-запросов.
app.include_router(olx_router)  # Добавляем OLX роутер
app.include_router(olx_message_router)
app.include_router(olx_token_router)
app.include_router(reservation_router)  # Добавляем роутер для бронирований
app.include_router(webhook_router)  # Добавляем роутер для webhook
app.include_router(auth_router)  # Роутер для EasySMS
app.include_router(webhook_router)
# Выводим все зарегистрированные маршруты
logger.debug("Registered routes:")
for route in app.routes:
    logger.debug(f"Route: {route.path} [{', '.join(route.methods)}]")

if __name__ == "__main__":
    logger.debug("Запуск FastAPI сервера")
    uvicorn.run(
        app,
        host="0.0.0.0",  # Слушать на всех интерфейсах.
        port=5000,  # Порт для запуска.
        ssl_keyfile=SSL_KEYFILE,  # Путь к файлу ключа SSL.
        ssl_certfile=SSL_CERTFILE,  # Путь к файлу сертификата SSL.
        log_level="debug",  # Уровень логирования.
        # reload=True  # Добавляем автоперезагрузку для разработки
    )
