# # main.py
# from contextlib import asynccontextmanager

# import socketio
# import uvicorn
# from config import settings
# from database import db
# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from logger import logger
# from routes import clusters, dashboard, gifts, streamers

# # Создаем экземпляр Socket.IO
# sio = socketio.AsyncServer(
#     async_mode="asgi",
#     cors_allowed_origins="*",
#     transports=["polling"],  # Только polling, без WebSocket
#     allowUpgrades=False,  # Запретить переход на WebSocket
# )
# socket_app = socketio.ASGIApp(sio)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Код, выполняемый при запуске
#     logger.info("Starting the application")
#     await db.connect()

#     yield  # Здесь происходит выполнение приложения

#     # Код, выполняемый при остановке
#     logger.info("Shutting down the application")
#     await db.close()


# app = FastAPI(title="TikTok Dashboard", lifespan=lifespan)

# # Настройка CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Монтируем Socket.IO под путём /socket.io
# app.mount("/socket.io", socket_app)

# # Подключение статических файлов
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# # Шаблоны
# templates = Jinja2Templates(directory="templates")

# # Подключение маршрутов
# app.include_router(dashboard.router, tags=["dashboard"])
# app.include_router(streamers.router, prefix="/streamers", tags=["streamers"])
# app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
# app.include_router(gifts.router, prefix="/gifts", tags=["gifts"])
# import socketio_handlers as socketio_handlers
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app", host=settings.HOST, port=settings.PORT, reload=True, ws="none"
#     )
# import asyncio


# from contextlib import asynccontextmanager

# import socketio
# import uvicorn
# from config import settings
# from database import db
# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from logger import logger
# from routes import clusters, dashboard, gifts, streamers
# from statistics_updater import run_statistics_updater

# # Создаем экземпляр Socket.IO
# sio = socketio.AsyncServer(
#     async_mode="asgi",
#     cors_allowed_origins="*",
#     transports=["polling"],  # Только polling, без WebSocket
#     allowUpgrades=False,  # Запретить переход на WebSocket
# )
# socket_app = socketio.ASGIApp(sio)

# # Keep track of background tasks
# background_tasks = set()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Код, выполняемый при запуске
#     logger.info("Starting the application")
#     await db.connect()

#     # Start the statistics updater in the background
#     statistics_task = asyncio.create_task(run_statistics_updater())
#     background_tasks.add(statistics_task)
#     # Remove the task when it's done
#     statistics_task.add_done_callback(background_tasks.discard)

#     logger.info("Statistics updater started")

#     yield  # Здесь происходит выполнение приложения

#     # Код, выполняемый при остановке
#     logger.info("Shutting down the application")

#     # Cancel all background tasks
#     for task in background_tasks:
#         task.cancel()

#     await db.close()


# app = FastAPI(title="TikTok Dashboard", lifespan=lifespan)

# # Настройка CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Монтируем Socket.IO под путём /socket.io
# app.mount("/socket.io", socket_app)

# # Подключение статических файлов
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# # Шаблоны
# templates = Jinja2Templates(directory="templates")

# # Подключение маршрутов
# app.include_router(dashboard.router, tags=["dashboard"])
# app.include_router(streamers.router, prefix="/streamers", tags=["streamers"])
# app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
# app.include_router(gifts.router, prefix="/gifts", tags=["gifts"])
# import socketio_handlers as socketio_handlers

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app", host=settings.HOST, port=settings.PORT, reload=True, ws="none"
#     )
import asyncio
from contextlib import asynccontextmanager

import socketio
import uvicorn
from auth import ALGORITHM, SECRET_KEY, get_user_by_username
from config import settings
from database import db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from logger import logger
from routes import auth, clusters, dashboard, gifts, streamers
from services.statistics import get_dashboard_statistics

# Создаем экземпляр Socket.IO
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    transports=["polling"],
    allowUpgrades=False,
)
socket_app = socketio.ASGIApp(sio)

# Keep track of background tasks
background_tasks = set()


# Определяем broadcast_stats на уровне модуля
async def broadcast_stats():
    while True:
        try:
            data = await get_dashboard_statistics()
            # Добавим логирование для отладки
            # logger.info(f"Broadcasting dashboard stats: {data}")
            await sio.emit("dashboard_stats", data)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error broadcasting stats: {e}")
            await asyncio.sleep(1)


async def refresh_stats():
    try:
        # Используем async with для получения соединения из пула
        async with db.pool.acquire() as conn:
            await conn.execute("SELECT refresh_dashboard_statistics();")
            logger.info("Statistics refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing statistics: {e}")


async def run_statistics_updater():
    while True:
        try:
            await refresh_stats()
            await asyncio.sleep(1)  # Обновляем каждые 5 секунд
        except Exception as e:
            logger.error(f"Error in statistics updater: {e}")
            await asyncio.sleep(1)  # Даже при ошибке ждём 5 секунд


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting the application")

        # Подключение к базе данных
        connected = await db.connect()
        if not connected:
            logger.error("Failed to connect to database")
            raise RuntimeError("Database connection failed")

        logger.info("Connected to database successfully")

        # Start the statistics updater in the background
        statistics_task = asyncio.create_task(run_statistics_updater())
        background_tasks.add(statistics_task)
        statistics_task.add_done_callback(background_tasks.discard)

        # Start broadcasting statistics to Socket.IO clients
        broadcast_task = asyncio.create_task(broadcast_stats())
        background_tasks.add(broadcast_task)
        broadcast_task.add_done_callback(background_tasks.discard)

        logger.info("Statistics updater and broadcaster started")
        yield

    except Exception as e:
        logger.error(f"Error during application lifespan: {e}")
        raise
    finally:
        logger.info("Shutting down the application")
        for task in background_tasks:
            task.cancel()
        try:
            await db.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")


app = FastAPI(title="TikTok Dashboard", lifespan=lifespan)


# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Путь к статическим файлам и маршруты авторизации не требуют авторизации
    exempt_paths = [
        "/static",
        "/login",
        "/register",
        "/logout",
        "/favicon.ico",
        "/socket.io",  # Разрешаем socket.io без авторизации
    ]

    if any(request.url.path.startswith(path) for path in exempt_paths):
        return await call_next(request)

    # Проверяем авторизацию
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")

    # Проверяем токен
    try:
        # Декодируем с минимальными проверками для совместимости
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},  # Отключаем проверку аудитории
        )
        username = payload.get("sub")
        if username is None:
            return RedirectResponse(url="/login")

        # Добавляем пользователя в state для доступа в шаблонах
        user = await get_user_by_username(username)
        request.state.user = user

    except Exception as e:
        # Для отладки
        from logger import logger

        logger.error(f"JWT Error: {str(e)}")
        return RedirectResponse(url="/login")

    return await call_next(request)


# Монтируем Socket.IO под путём /socket.io
app.mount("/socket.io", socket_app)

# ВАЖНО: Пути к статическим файлам и шаблонам должны быть правильными
# Проверьте структуру вашего проекта
app.mount("/static", StaticFiles(directory="static"), name="static")

# Шаблоны - указываем абсолютный путь к директории templates
templates = Jinja2Templates(directory="templates")

# Регистрируем шаблоны в контексте приложения
app.state.templates = templates

# Подключение маршрутов
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(streamers.router, prefix="/streamers", tags=["streamers"])
app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
app.include_router(gifts.router, prefix="/gifts", tags=["gifts"])
app.include_router(auth.router, tags=["auth"])


# Подключение обработчиков Socket.IO
import socketio_handlers


# Событие подключения к Socket.IO
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    # Сразу отправляем текущую статистику новому клиенту
    try:
        data = await get_dashboard_statistics()
        await sio.emit("dashboard_stats", data, room=sid)
    except Exception as e:
        logger.error(f"Error sending initial stats to {sid}: {e}")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=True, ws="none"
    )
