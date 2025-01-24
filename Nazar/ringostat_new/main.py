import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from app.core.database import engine
from app.core.dependencies import get_db
from app.api.post_routes import router as post_router
from app.api.get_routes import router as get_routes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import SSL_KEYFILE, SSL_CERTFILE
from configuration.logger_setup import logger
import uvicorn


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
        logger.error(f"Failed during app startup: {e}")
        raise


app = FastAPI(lifespan=lifespan)

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените на список допустимых доменов
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# Логирование всех запросов
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug(f"Request path: {request.url.path}, method: {request.method}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response


# # Подключение маршрутов
app.include_router(post_router)
app.include_router(get_routes)

if __name__ == "__main__":
    # alembic_cfg = Config("alembic.ini")
    # Убираем это из асинхронного контекста
    # command.current(alembic_cfg)
    logger.debug("Запуск FastAPI сервера")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        ssl_keyfile=SSL_KEYFILE,
        ssl_certfile=SSL_CERTFILE,
        log_level="debug",
    )
