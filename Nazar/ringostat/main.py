from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from configuration.logger_setup import logger
from database import DatabaseInitializer
import dependencies
from post_routes import router as post_router
from get_routes import router as get_router
from put_routes import router as put_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    dependencies.db_initializer = DatabaseInitializer()
    await dependencies.db_initializer.create_database()
    await dependencies.db_initializer.create_pool()
    await dependencies.db_initializer.init_db()
    yield
    await dependencies.db_initializer.close_pool()


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
app.include_router(get_router)
app.include_router(put_router)

if __name__ == "__main__":
    logger.debug("Запуск FastAPI сервера")
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        ssl_keyfile="/root/ringostat/key.pem",
        ssl_certfile="/root/ringostat/cert.pem",
        log_level="debug",
    )
