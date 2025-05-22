# app/websockets/dashboard.py
import asyncio
import logging

from config import settings
from database import db
from fastapi import WebSocket, WebSocketDisconnect
from services.statistics import get_dashboard_statistics

logger = logging.getLogger(__name__)

# Активные соединения WebSocket
active_connections = []
streamers_connections = []


async def dashboard_websocket_endpoint(websocket: WebSocket):
    """Конечная точка WebSocket для дашборда"""
    await websocket.accept()
    active_connections.append(websocket)

    logger.info(
        f"WebSocket connection established. Active connections: {len(active_connections)}"
    )

    try:
        while True:
            # Получаем актуальную статистику
            data = await get_dashboard_statistics()

            # Отправляем данные
            await websocket.send_json(data)

            # Ждем перед следующим обновлением
            await asyncio.sleep(settings.WS_UPDATE_INTERVAL)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(
            f"WebSocket connection closed. Active connections: {len(active_connections)}"
        )
    except Exception as e:
        active_connections.remove(websocket)
        logger.error(f"WebSocket error: {e}")


async def streamers_websocket_endpoint(websocket: WebSocket):
    """Конечная точка WebSocket для страницы стримеров"""
    await websocket.accept()
    streamers_connections.append(websocket)

    logger.info(
        f"Streamers WebSocket connection established. Active connections: {len(streamers_connections)}"
    )

    try:
        while True:
            # Получаем актуальный список стримеров
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

            # Формируем данные для отправки
            streamers_data = []
            for streamer in streamers:
                streamers_data.append(
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

            # Отправляем данные
            await websocket.send_json(
                {
                    "streamers": streamers_data,
                    "total_streamers": total_streamers,
                    "active_streamers": active_streamers,
                }
            )

            # Ждем перед следующим обновлением
            await asyncio.sleep(settings.WS_UPDATE_INTERVAL)

    except WebSocketDisconnect:
        streamers_connections.remove(websocket)
        logger.info(
            f"Streamers WebSocket connection closed. Active connections: {len(streamers_connections)}"
        )
    except Exception as e:
        if websocket in streamers_connections:
            streamers_connections.remove(websocket)
        logger.error(f"Streamers WebSocket error: {e}")
