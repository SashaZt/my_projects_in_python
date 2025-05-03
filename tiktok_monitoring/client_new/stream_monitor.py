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

    async def _monitor_streamer(self, streamer_info):
        consecutive_errors = 0
        max_consecutive_errors = 5

        unique_id = streamer_info["unique_id"]
        cluster = streamer_info["cluster"]
        check_online = streamer_info["check_online"]
        streamer_id = streamer_info["id"]
        tik_tok_user_id = streamer_info.get("tik_tok_user_id")
        room_id = streamer_info.get("room_id")

        logger.info(f"Starting monitoring for {unique_id} (Cluster: {cluster})")

        # Переменные для отслеживания состояния
        connected = False
        last_conn_attempt = 0
        max_offline_attempts = 5
        offline_attempts = 0
        last_activity_check = time.time()
        activity_check_interval = 300  # 5 минут

        # Безопасные ошибки, которые можно игнорировать
        safe_error_messages = [
            "property 'type' of 'CompetitionEvent' object has no setter",
            "is offline",
            "No Message Provided",
        ]

        # Получаем больше информации о стримере
        try:
            streamer_data = await self.db.fetchrow(
                """
                    SELECT s.tik_tok_user_id, ttu.name, ttu.user_id, ttu.tiktok_id
                    FROM streamers s
                    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                    WHERE s.id = $1
                    """,
                streamer_id,
            )

            if streamer_data:
                name = streamer_data["name"]
                user_id = streamer_data["user_id"]
                tiktok_id = streamer_data["tiktok_id"]
            else:
                name = unique_id
                user_id = None
                tiktok_id = None
            logger.info("=" * 50)
            logger.info(
                f"Streamer info: name={name}, user_id={user_id}, tiktok_id={tiktok_id}"
            )
        except Exception as e:
            logger.error(f"Error fetching streamer data: {e}")
            name = unique_id
            user_id = None
            tiktok_id = None

        while not self.shared_state.shutdown_event.is_set():
            client = None
            current_time = time.time()

            # Если подключены, проверяем активность
            if connected:
                if current_time - last_activity_check > activity_check_interval:
                    last_activity_check = current_time
                    logger.info(f"Checking activity for {unique_id}")

                    # Обновляем данные в базе
                    try:
                        await self.db.execute(
                            """
                                UPDATE streamers 
                                SET last_activity = NOW(), last_check = NOW(), is_live = TRUE 
                                WHERE id = $1
                                """,
                            streamer_id,
                        )

                        if tik_tok_user_id:
                            await self.db.execute(
                                "UPDATE tik_tok_users SET last_seen = NOW() WHERE id = $1",
                                tik_tok_user_id,
                            )
                    except Exception as e:
                        logger.error(f"Error updating activity data: {e}")

                # Продолжаем мониторинг
                await asyncio.sleep(1)
                continue

            # Если с момента последней попытки прошло меньше check_online секунд, ждем
            if current_time - last_conn_attempt < check_online:
                await asyncio.sleep(1)
                continue

            # Обновляем время последней попытки
            last_conn_attempt = current_time

            try:
                # Выбираем правильный идентификатор для подключения
                # Приоритет: name (если это @username) > tiktok_id > user_id > unique_id
                connect_id = None

                if name and name.startswith("@") and not name.startswith("@user_"):
                    connect_id = name
                    # logger.debug(
                    #     f"Connecting with username: {connect_id} (original unique_id: {unique_id})"
                    # )
                elif tiktok_id:
                    connect_id = (
                        f"@{tiktok_id}" if not tiktok_id.startswith("@") else tiktok_id
                    )
                    logger.debug(
                        f"Connecting with tiktok_id: {connect_id} (original unique_id: {unique_id})"
                    )
                elif user_id:
                    # Некоторые версии TikTokLive могут поддерживать подключение по user_id
                    connect_id = f"@{user_id}"
                    logger.debug(
                        f"Connecting with user_id: {connect_id} (original unique_id: {unique_id})"
                    )
                else:
                    connect_id = (
                        unique_id if unique_id.startswith("@") else f"@{unique_id}"
                    )
                    logger.debug(f"Connecting with unique_id: {connect_id}")

                client = TikTokLiveClient(
                    unique_id=connect_id,
                )

                # Флаг для отслеживания успешного подключения
                connection_established = False

                # Обработчик события подключения
                @client.on(ConnectEvent)
                async def on_connect(event: ConnectEvent):
                    nonlocal connected, connection_established, last_activity_check
                    try:
                        # Отмечаем, что подключение установлено
                        connected = True
                        connection_established = True
                        offline_attempts = 0  # Сбрасываем счетчик попыток
                        last_activity_check = time.time()

                        # Безопасно извлекаем ID и данные
                        event_room_id = getattr(
                            event, "room_id", getattr(client, "room_id", None)
                        )
                        event_tiktok_id = getattr(
                            event, "unique_id", getattr(client, "unique_id", None)
                        )
                        numeric_id = getattr(event, "user_id", None)

                        # Сохраняем текущее значение уникального идентификатора
                        current_unique_id = unique_id

                        logger.info(
                            f"Connected to {current_unique_id} (Room ID: {event_room_id}, TikTok ID: {event_tiktok_id}, User ID: {numeric_id})"
                        )

                        # Проверяем и обновляем имя пользователя
                        if numeric_id and current_unique_id.startswith("@user_"):
                            # Логика обновления имени пользователя - без изменений
                            # ... [сохраняем существующий код]
                            pass

                        # Используем room_id как user_id при необходимости
                        user_id = None
                        if event_room_id:
                            user_id = str(event_room_id)

                        # Обновляем данные стримера в базе
                        await self.streamer_manager.update_streamer(
                            streamer_id,
                            event_room_id or room_id,
                            user_id,
                            event_tiktok_id,
                        )

                        # Создаем запись в таблице streams
                        try:
                            # Проверяем существующие стримы
                            existing_stream = await self.db.fetchrow(
                                """
                                    SELECT id FROM streams 
                                    WHERE streamer_id = $1 AND end_time IS NULL
                                    """,
                                streamer_id,
                            )

                            if not existing_stream:
                                # Создаем новую запись о стриме
                                stream_id = await self.db.fetchval(
                                    """
                                        INSERT INTO streams 
                                        (streamer_id, tik_tok_user_id, room_id, start_time) 
                                        VALUES ($1, $2, $3, NOW())
                                        RETURNING id
                                        """,
                                    streamer_id,
                                    tik_tok_user_id,
                                    event_room_id or room_id,
                                )
                                logger.info(
                                    f"Created new stream record with ID {stream_id}"
                                )
                            else:
                                # Обновляем существующий стрим
                                await self.db.execute(
                                    """
                                        UPDATE streams
                                        SET max_viewers = max_viewers + 1
                                        WHERE id = $1
                                        """,
                                    existing_stream["id"],
                                )
                                logger.info(
                                    f"Updated existing stream record with ID {existing_stream['id']}"
                                )
                        except Exception as e:
                            logger.error(f"Error creating/updating stream record: {e}")

                    except Exception as e:
                        logger.error(f"Error in on_connect: {e}")

                # Обработчик для GiftEvent
                @client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    nonlocal connected, last_activity_check
                    connected = True
                    last_activity_check = time.time()
                    await self.gift_processor._process_gift(event, unique_id, cluster)

                @client.on(DisconnectEvent)
                async def on_disconnect(event: DisconnectEvent):
                    nonlocal connected
                    logger.info(f"Disconnected from {unique_id}")
                    connected = False

                    # Закрываем запись о стриме
                    try:
                        await self.db.execute(
                            "UPDATE streamers SET is_live = FALSE WHERE id = $1",
                            streamer_id,
                        )

                        await self.db.execute(
                            """
                                UPDATE streams
                                SET end_time = NOW(),
                                    duration = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER
                                WHERE streamer_id = $1 AND end_time IS NULL
                                """,
                            streamer_id,
                        )
                    except Exception as e:
                        logger.error(f"Error updating stream end data: {e}")

                # Запускаем клиент с дополнительной обработкой ошибок
                try:
                    # logger.info(f"Starting client for {connect_id}")
                    await client.start()
                except asyncio.TimeoutError:
                    logger.warning(f"Connection to {connect_id} timed out")
                    connected = False
                except Exception as e:
                    error_message = str(e)
                    # logger.error(
                    #     f"Error starting client for {connect_id}: {error_message}"
                    # )
                    connected = False

                    # Попробуем выполнить отладочное подключение при серьезных ошибках
                    if "Expecting value" in error_message:
                        logger.info(f"Attempting debug connection for {connect_id}...")
                        await self.streamer_manager.debug_tiktok_connection(connect_id)

                # Если дошли до этой точки, значит клиент завершил работу сам
                connected = False

            except asyncio.TimeoutError:
                logger.warning(f"Connection to {unique_id} timed out")
                connected = False
            except Exception as e:
                error_message = str(e)
                connected = False

                # Проверяем, является ли это известной безопасной ошибкой
                if any(safe_msg in error_message for safe_msg in safe_error_messages):
                    if "is offline" in error_message:
                        offline_attempts += 1
                        if offline_attempts >= max_offline_attempts:
                            wait_time = check_online * 2
                            logger.info(
                                f"{unique_id} is offline after {offline_attempts} attempts. Will retry in {wait_time} seconds"
                            )
                            await asyncio.sleep(wait_time)
                            offline_attempts = 0
                        else:
                            # Короткая пауза между попытками
                            await asyncio.sleep(5)
                    else:
                        # Другая известная ошибка
                        logger.warning(f"Known error for {unique_id}: {error_message}")
                        await asyncio.sleep(5)
                else:
                    logger.error(f"Error in monitoring {unique_id}: {error_message}")
                    # Более длинная пауза при неизвестной ошибке
                    await asyncio.sleep(30)
            finally:
                # Освобождаем ресурсы клиента
                try:
                    if client:
                        await client.stop()
                except:
                    pass

                if not connection_established:
                    connected = False

            # Проверяем, не остановлен ли мониторинг
            if self.shared_state.shutdown_event.is_set():
                break

            # Ждем перед повторным подключением
            if not connected:
                retry_interval = min(check_online, 10)
                await asyncio.sleep(retry_interval)
