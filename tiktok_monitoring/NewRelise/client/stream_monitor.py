# client/stream_monitor.py
import asyncio
import time

from logger import logger
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent, GiftEvent


class StreamMonitor:
    def __init__(self, db, gift_processor, shared_state, streamer_manager):
        self.db = db
        self.gift_processor = gift_processor
        self.shared_state = shared_state
        self.streamer_manager = streamer_manager

    async def start_monitoring(self, streamer_info):
        """Запуск мониторинга стрима - ответственность StreamMonitor"""
        unique_id = streamer_info["unique_id"]

        try:
            # Проверяем, не запущен ли уже мониторинг
            if unique_id in self.shared_state.monitored_streams:
                logger.info(f"Мониторинг {unique_id} уже запущен")
                return True

            # Запускаем задачу мониторинга
            task = asyncio.create_task(self._monitor_streamer(streamer_info))
            self.shared_state.monitored_streams[unique_id] = task

            logger.info(f"Запущен мониторинг для {unique_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка запуска мониторинга {unique_id}: {e}", exc_info=True)
            return False

    async def stop_monitoring(self, unique_id, room_id=None):
        """Остановка мониторинга - ответственность StreamMonitor"""
        try:
            # Останавливаем задачу мониторинга
            if unique_id in self.shared_state.monitored_streams:
                task = self.shared_state.monitored_streams.pop(unique_id)
                if task and not task.done():
                    task.cancel()

                logger.info(f"Остановлен мониторинг для {unique_id}")

                # Обновляем статус в БД
                user_name = (
                    f"@{unique_id}" if not unique_id.startswith("@") else unique_id
                )

                streamer = await self.db.fetchrow(
                    """
                    SELECT s.id
                    FROM streamers s
                    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                    WHERE ttu.name = $1 OR ttu.tiktok_id = $2
                    """,
                    user_name,
                    unique_id.lstrip("@"),
                )

                if streamer:
                    # Обновляем статус стримера
                    await self.db.execute(
                        "UPDATE streamers SET is_live = FALSE, last_activity = NOW() WHERE id = $1",
                        streamer["id"],
                    )

                    # Закрываем стрим
                    await self.db.execute(
                        """
                        UPDATE streams
                        SET end_time = NOW(),
                            duration = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER,
                            updated_at = NOW()
                        WHERE streamer_id = $1 AND end_time IS NULL
                        """,
                        streamer["id"],
                    )

                # Если не нашли по имени, ищем по room_id
                elif room_id:
                    room_id_int = int(room_id) if room_id else None

                    if room_id_int:
                        stream = await self.db.fetchrow(
                            "SELECT id, streamer_id FROM streams WHERE room_id = $1 AND end_time IS NULL",
                            room_id_int,
                        )

                        if stream:
                            await self.db.execute(
                                """
                                UPDATE streams
                                SET end_time = NOW(),
                                    duration = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER,
                                    updated_at = NOW()
                                WHERE id = $1
                                """,
                                stream["id"],
                            )

                            await self.db.execute(
                                "UPDATE streamers SET is_live = FALSE WHERE id = $1",
                                stream["streamer_id"],
                            )

                return True
            else:
                logger.info(f"Мониторинг для {unique_id} не был запущен")
                return True

        except Exception as e:
            logger.error(
                f"Ошибка остановки мониторинга {unique_id}: {e}", exc_info=True
            )
            return False

    async def _monitor_streamer(self, streamer_info):
        """Упрощенный мониторинг стрима"""
        # Извлекаем только нужные данные
        unique_id = streamer_info["unique_id"]
        room_id = streamer_info.get("room_id")
        numeric_uid = streamer_info.get("numeric_uid")

        logger.info(f"Стартуем мониторинг для {unique_id} (room_id: {room_id})")

        # Переменные для контроля состояния
        connected = False
        last_attempt = 0

        while not self.shared_state.shutdown_event.is_set():
            try:
                # Проверяем нужно ли подключаться
                current_time = time.time()

                # Если уже подключены, просто ждем
                if connected:
                    await asyncio.sleep(1)
                    continue

                # Ограничиваем частоту попыток подключения
                if current_time - last_attempt < 15:  # Не чаще, чем раз в 15 секунд
                    await asyncio.sleep(1)
                    continue

                last_attempt = current_time

                # Создаем ID для подключения - простой подход
                connect_id = unique_id if unique_id.startswith("@") else f"@{unique_id}"

                # Создаем клиент TikTok
                client = TikTokLiveClient(unique_id=connect_id)

                # Обработчик подключения
                @client.on(ConnectEvent)
                async def on_connect(event):
                    nonlocal connected
                    connected = True

                    # Получаем room_id из клиента
                    client_room_id = getattr(client, "room_id", room_id)

                    logger.info(f"Подключено к {unique_id} (Room ID: {client_room_id})")

                    # Обновляем данные в БД
                    await self.db.execute(
                        "UPDATE streamers SET is_live = TRUE, last_activity = NOW() WHERE id = $1",
                        streamer_info["id"],
                    )

                # Обработчик подарков - самое важное
                @client.on(GiftEvent)
                async def on_gift(event):
                    # Важно - добавляем room_id к событию
                    if not hasattr(event, "room_id"):
                        # Приоритет: room_id из клиента > room_id из streamer_info
                        client_room_id = getattr(client, "room_id", room_id)
                        if client_room_id:
                            setattr(event, "room_id", client_room_id)

                    # Обработка подарка
                    await self.gift_processor._process_gift(
                        event, unique_id, streamer_info.get("cluster", "AGENCY")
                    )

                # Обработчик отключения
                @client.on(DisconnectEvent)
                async def on_disconnect(event):
                    nonlocal connected
                    connected = False
                    logger.info(f"Отключено от {unique_id}")

                # Запускаем клиент с таймаутом
                try:
                    await asyncio.wait_for(client.start(), timeout=60)
                except asyncio.TimeoutError:
                    logger.warning(f"Таймаут подключения к {unique_id}")
                    connected = False
                except Exception as e:
                    logger.warning(f"Ошибка подключения к {unique_id}: {str(e)}")
                    connected = False
                    await asyncio.sleep(30)  # При ошибке ждем дольше

                # Если дошли сюда, значит клиент завершился
                connected = False

            except Exception as e:
                logger.error(f"Ошибка мониторинга {unique_id}: {e}", exc_info=True)
                connected = False
                await asyncio.sleep(30)
            finally:
                # Очищаем ресурсы
                try:
                    if "client" in locals() and client:
                        await client.stop()
                except:
                    pass

                # Небольшая пауза перед повторной попыткой
                await asyncio.sleep(5)

        logger.info(f"Мониторинг для {unique_id} завершен")
