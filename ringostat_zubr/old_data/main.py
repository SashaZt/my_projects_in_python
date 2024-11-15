from contextlib import asynccontextmanager

import dependencies
from configuration.logger_setup import logger
from database import DatabaseInitializer
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from get_routes import router as get_router  # Import the new GET routes
from post_routes import router as post_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    yield
    await db_initializer.close_pool()


app = FastAPI(lifespan=lifespan)

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
        ssl_keyfile="/root/ringostat_zubr/key.pem",
        ssl_certfile="/root/ringostat_zubr/cert.pem",
        log_level="debug",
    )
