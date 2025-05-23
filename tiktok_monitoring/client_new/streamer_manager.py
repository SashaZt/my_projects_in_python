# /streamer_manager.py
import asyncio
import time

from logger import logger
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import WebsocketResponseEvent


class StreamerManager:
    def __init__(self, db, shared_state, stream_monitor=None):
        self.db = db
        self.shared_state = shared_state
        self.stream_monitor = stream_monitor  # Может быть None при инициализации

    async def _update_streamers(self):
        """Обновление списка отслеживаемых стримеров"""
        while not self.shared_state.shutdown_event.is_set():
            try:
                # Получаем список активных стримеров
                streamers = await self.db.get_active_streamers()
                logger.info(f"Found {len(streamers)} active streamers")

                # Определяем, каких стримеров нужно добавить или удалить
                current_ids = set(self.shared_state.monitored_streams.keys())

                new_ids = set(s["unique_id"] for s in streamers)

                # Стримеры для добавления и удаления
                to_add = new_ids - current_ids
                to_remove = current_ids - new_ids

                # Удаляем стримеров
                for unique_id in to_remove:
                    logger.info(f"Stopping monitoring for {unique_id}")
                    task = self.shared_state.monitored_streams.pop(unique_id, None)

                    if task:
                        task.cancel()

                # Добавляем новых стримеров
                for streamer in streamers:
                    if streamer["unique_id"] in to_add:
                        logger.info(f"Starting monitoring for {streamer['unique_id']}")
                        task = asyncio.create_task(
                            self.stream_monitor._monitor_streamer(streamer)
                        )
                        self.shared_state.monitored_streams[streamer["unique_id"]] = (
                            task
                        )
                        # Добавляем задержку между запусками (500ms)
                        await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error updating streamers list: {e}")

            # Проверяем каждые 120 секунд
            await asyncio.sleep(120)

    async def update_streamer(self, streamer_id, room_id, user_id=None, tiktok_id=None):
        """Обновление данных стримера и сохранение связи между room_id и стримером"""
        try:
            if not streamer_id:
                logger.error("No streamer_id provided for update")
                return False

            # Преобразуем room_id в целое число
            room_id_int = None
            if room_id:
                try:
                    room_id_int = int(room_id)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert room_id to integer: {room_id}")

            # Получаем tik_tok_user_id и связанные данные
            streamer_data = await self.db.fetchrow(
                """
                    SELECT s.tik_tok_user_id, ttu.name, ttu.user_id
                    FROM streamers s
                    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                    WHERE s.id = $1
                    """,
                streamer_id,
            )

            if not streamer_data:
                logger.error(f"No data found for streamer {streamer_id}")
                return False

            tik_tok_user_id = streamer_data["tik_tok_user_id"]
            ttu_name = streamer_data["name"]
            ttu_user_id = streamer_data["user_id"]

            # Обновляем запись стримера только если room_id_int имеет значение
            if room_id_int:
                await self.db.execute(
                    """
                    UPDATE streamers 
                    SET room_id = $1, last_activity = NOW(), last_check = NOW(), is_live = TRUE 
                    WHERE id = $2
                    """,
                    room_id_int,
                    streamer_id,
                )

                # Создаем маппинг между room_id и tik_tok_user_id
                await self.db.execute(
                    """
                    INSERT INTO room_id_mapping (room_id, tik_tok_user_id)
                    VALUES ($1, $2)
                    ON CONFLICT (room_id) DO UPDATE 
                    SET tik_tok_user_id = $2, last_updated = NOW()
                    """,
                    room_id_int,
                    tik_tok_user_id,
                )
                logger.info(
                    f"Mapped room_id {room_id_int} to tik_tok_user_id {tik_tok_user_id}"
                )
            else:
                # Обновляем только активность и статус, если room_id_int не определен
                await self.db.execute(
                    """
                    UPDATE streamers 
                    SET last_activity = NOW(), last_check = NOW(), is_live = TRUE 
                    WHERE id = $1
                    """,
                    streamer_id,
                )

            # Обновляем tik_tok_users с tiktok_id, если предоставлен
            user_update_parts = []
            user_update_params = []

            if tiktok_id:
                user_update_parts.append(f"tiktok_id = ${len(user_update_params) + 1}")
                user_update_params.append(tiktok_id)

            # Обновляем user_id, если предоставлен и отличается от текущего
            if user_id and (not ttu_user_id or ttu_user_id != user_id):
                user_update_parts.append(f"user_id = ${len(user_update_params) + 1}")
                user_update_params.append(user_id)
                logger.info(f"Updating user_id to {user_id} for {ttu_name}")

            if user_update_parts:
                # Всегда обновляем last_seen
                user_update_parts.append("last_seen = NOW()")

                # Формируем и выполняем запрос
                update_query = f"""
                UPDATE tik_tok_users 
                SET {', '.join(user_update_parts)}
                WHERE id = ${len(user_update_params) + 1}
                """
                user_update_params.append(tik_tok_user_id)

                await self.db.execute(update_query, *user_update_params)
            else:
                # Если нет других обновлений, просто обновляем last_seen
                await self.db.execute(
                    "UPDATE tik_tok_users SET last_seen = NOW() WHERE id = $1",
                    tik_tok_user_id,
                )

            logger.info(
                f"Updated streamer ID {streamer_id} with room_id={room_id_int}, tiktok_id={tiktok_id}, user_id={user_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating streamer data: {e}")
            return False

    async def debug_tiktok_connection(self, username):
        """Отладочная функция для проверки соединения с TikTok и получения ответа"""
        try:
            # Создаем базовый клиент для проверки

            # Добавляем отладочную информацию
            logger.info(f"Trying to debug connection for: {username}")
            logger.info(f"Current API key: {WebDefaults.tiktok_sign_api_key}")
            logger.info(f"WebDefaults settings: {vars(WebDefaults)}")

            # Создаем клиент
            client = TikTokLiveClient(unique_id=username)

            # Регистрируем обработчик для всех ответов
            @client.on(WebsocketResponseEvent)
            async def on_any_websocket(event):
                logger.info(f"Received WebSocket response: {str(event)[:200]}...")
                try:
                    # Пытаемся получить сырые данные
                    if hasattr(event, "raw_data"):
                        # Проверяем, что данные не пусты
                        if event.raw_data:
                            with open(
                                f"debug_{username}_{int(time.time())}.json", "w"
                            ) as f:
                                import json

                                json.dump(event.raw_data, f)
                            logger.info(f"Successfully saved raw data for {username}")
                        else:
                            logger.warning(f"Received empty raw_data for {username}")
                except Exception as e:
                    logger.error(f"Error saving debug data: {e}")

            # Подключаемся с таймаутом
            try:
                logger.info(f"Attempting connection to {username} for debug...")
                await asyncio.wait_for(client.connect(), timeout=15)
            except asyncio.TimeoutError:
                logger.info(f"Debug connection timed out for {username}")
            finally:
                await client.disconnect()
                logger.info(f"Debug session completed for {username}")

            return True
        except Exception as e:
            logger.error(f"Debug connection error: {e}")
            return False
