# app/main.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logger import logger


# Создание приложения FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
app.include_router(api_router, prefix="/api/v1")


# Тестовый маршрут для проверки
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": f"Welcome to {settings.APP_NAME}"}


# Информация о маршрутах
@app.on_event("startup")
async def startup_log_routes():
    logger.debug("Зарегистрированные маршруты:")
    for route in app.routes:
        logger.debug(f"Маршрут: {route.path} [{', '.join(route.methods) if hasattr(route, 'methods') else '-'}]")


if __name__ == "__main__":
    logger.debug("Запуск сервера FastAPI")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        ssl_keyfile=settings.SSL_KEYFILE,
        ssl_certfile=settings.SSL_CERTFILE,
        log_level="debug",
    )