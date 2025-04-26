# import asyncio

# import socketio

# # Используем экземпляр Socket.IO из main.py
# from main import sio
# from services.statistics import get_dashboard_statistics

# # События Socket.IO


# @sio.event
# async def connect(sid, environ):
#     """Обработчик подключения клиента"""
#     print(f"Client connected: {sid}")
#     # Запускаем фоновую задачу для отправки обновлений
#     sio.start_background_task(background_task, sid)


# @sio.event
# async def disconnect(sid):
#     """Обработчик отключения клиента"""
#     print(f"Client disconnected: {sid}")


# @sio.event
# async def connect(sid, environ):
#     """Обработчик подключения клиента"""
#     print(f"Client connected: {sid}")
#     # Запускаем фоновую задачу отправки обновлений
#     asyncio.create_task(send_dashboard_updates(sid))


# @sio.event
# async def disconnect(sid):
#     """Обработчик отключения клиента"""
#     print(f"Client disconnected: {sid}")


# async def send_dashboard_updates(sid):
#     """Отправка обновлений дашборда клиенту"""
#     try:
#         while True:
#             # Получаем актуальные данные
#             data = await get_dashboard_statistics()

#             # Отправляем данные клиенту
#             await sio.emit("dashboard_update", data, room=sid)

#             # Пауза между обновлениями
#             await asyncio.sleep(3)
#     except Exception as e:
#         print(f"Error sending updates: {e}")


# async def background_task(sid):
#     """Фоновая задача для отправки обновлений клиенту"""
#     while True:
#         try:
#             # Проверяем, подключен ли еще клиент
#             if not await sio.get_session(sid):
#                 break

#             # Получаем актуальные данные
#             data = await get_dashboard_statistics()

#             # Отправляем данные клиенту
#             await sio.emit("dashboard_update", data, room=sid)

#             # Пауза между обновлениями
#             await asyncio.sleep(3)
#         except Exception as e:
#             print(f"Error in background task: {e}")
#             break
import asyncio

import socketio
from database import db

# Используем экземпляр Socket.IO из main.py
from main import sio
from services.statistics import get_dashboard_statistics

# События Socket.IO


@sio.event
async def connect(sid, environ):
    """Обработчик подключения клиента"""
    print(f"Клиент подключен: {sid}")
    # Запускаем фоновую задачу отправки обновлений
    asyncio.create_task(send_dashboard_updates(sid))


@sio.event
async def disconnect(sid):
    """Обработчик отключения клиента"""
    print(f"Клиент отключен: {sid}")


async def send_dashboard_updates(sid):
    """Отправка обновлений дашборда клиенту"""
    try:
        while True:
            # Получаем актуальные данные из предварительно рассчитанной таблицы
            data = await get_dashboard_statistics()

            # Отправляем данные клиенту
            await sio.emit("dashboard_update", data, room=sid)

            # Пауза между обновлениями
            # Так как статистика обновляется автоматически и хранится в базе данных,
            # мы можем увеличить интервал между запросами для уменьшения нагрузки
            await asyncio.sleep(3)
    except Exception as e:
        print(f"Ошибка при отправке обновлений: {e}")


@sio.event
async def join_streamers_room(sid):
    """Обработчик подключения клиента к комнате со стримерами"""
    print(f"Клиент {sid} подключился к комнате стримеров")
    sio.enter_room(sid, "streamers")
    # Отправляем начальные данные сразу после подключения
    await send_streamers_update(sid)
    # Запускаем фоновую задачу для регулярных обновлений
    asyncio.create_task(send_streamers_updates(sid))


async def send_streamers_update(sid):
    """Отправка обновления информации о стримерах конкретному клиенту"""
    try:
        # Получаем данные о стримерах из базы
        streamers = await db.fetch(
            """
            SELECT s.id, ttu.name, s.room_id, c.name as cluster_name, 
                   s.status, s.check_online, s.last_activity
            FROM streamers s
            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
            LEFT JOIN clusters c ON s.cluster_id = c.id
            ORDER BY ttu.name
            """
        )

        # Преобразуем данные для отправки
        formatted_streamers = []
        for streamer in streamers:
            formatted_streamers.append(
                {
                    "id": streamer["id"],
                    "name": streamer["name"],
                    "room_id": streamer["room_id"],
                    "cluster_name": streamer["cluster_name"],
                    "status": streamer["status"],
                    "check_online": streamer["check_online"],
                    "last_activity": (
                        streamer["last_activity"].isoformat()
                        if streamer["last_activity"]
                        else None
                    ),
                }
            )

        total_streamers = len(streamers)
        active_streamers = sum(1 for s in streamers if s["status"] == "Запущен")

        # Отправляем данные клиенту
        await sio.emit(
            "streamers_update",
            {
                "streamers": formatted_streamers,
                "total_streamers": total_streamers,
                "active_streamers": active_streamers,
            },
            room=sid,
        )

    except Exception as e:
        print(f"Ошибка при отправке обновления о стримерах: {e}")


async def send_streamers_updates(sid):
    """Периодическая отправка обновлений о стримерах клиенту"""
    try:
        while True:
            # Отправляем обновление
            await send_streamers_update(sid)
            # Пауза между обновлениями (5 секунд)
            await asyncio.sleep(5)
    except Exception as e:
        print(f"Ошибка при отправке обновлений о стримерах: {e}")
