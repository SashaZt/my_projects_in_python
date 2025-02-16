# app/main.py
import sys
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn

from core.database import engine
from core.logger import logger
from core.config import SSL_KEYFILE, SSL_CERTFILE
from fastapi.middleware.cors import CORSMiddleware

# Подключаем эндпоинты
from api.endpoints.transfer import router as transfer_router


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


app = FastAPI(lifespan=lifespan)

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
app.include_router(transfer_router)

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
