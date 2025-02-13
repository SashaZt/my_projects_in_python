import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from app.core.database import engine  # Подключение к базе данных.
from app.core.dependencies import get_db  # Зависимость для работы с базой.
from app.api.post_routes import router as post_router  # Роутер для POST-запросов.
from app.api.get_routes import router as get_routes  # Роутер для GET-запросов.
from fastapi.middleware.cors import CORSMiddleware  # Для настройки CORS.
from fastapi.responses import JSONResponse  # Формат ответа в JSON.
from app.core.config import SSL_KEYFILE, SSL_CERTFILE  # Настройки SSL.
from loguru import logger
from pathlib import Path
import sys
import uvicorn  # Запуск сервера.
from app.api.olx_routes import router as olx_router  
from app.api.olx_message_routes import router as olx_message_router
from app.api.olx_token_routes import router as olx_token_router



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


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Проверка подключения к базе
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda conn: logger.debug("Database connection successful")
            )
        yield
    except Exception as e:
        # Логирование ошибок на этапе старта приложения.
        logger.error(f"Failed during app startup: {e}")
        raise


# Создание приложения FastAPI
app = FastAPI(
    lifespan=lifespan
)  # lifespan: Связывается с жизненным циклом приложения для обработки событий запуска и завершения.

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


# # Подключение маршрутов
app.include_router(post_router)  # Роутер для POST-запросов.
app.include_router(get_routes)  # Роутер для GET-запросов.
app.include_router(olx_router)  # Добавляем OLX роутер
app.include_router(olx_message_router)
app.include_router(olx_token_router)



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
