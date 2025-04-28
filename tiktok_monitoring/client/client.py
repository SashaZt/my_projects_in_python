# client/client.py
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from queue import Queue

from logger import logger
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import (
    ConnectEvent,
    DisconnectEvent,
    GiftEvent,
    WebsocketResponseEvent,
)


class TikTokMonitor:
    def __init__(self, db, api_key=None):
        self.db = db
        self.monitored_streams = {}  # {unique_id: task}
        self.gift_queue = Queue(maxsize=5000)
        self.processed_gift_ids = set()
        self.shutdown_event = asyncio.Event()

        # Настройка API ключа для TikTokLive
        if api_key:
            WebDefaults.tiktok_sign_api_key = api_key
        else:
            logger.warning("No TikTokLive API key provided, connections may be limited")

    async def start(self):
        """Запуск мониторинга"""
        # Запускаем обработку подарков
        gift_processor = asyncio.create_task(self._process_gift_queue())

        # Запускаем обновление списка стримеров
        updater = asyncio.create_task(self._update_streamers())

        # Запускаем очистку кэша подарков
        cleaner = asyncio.create_task(self._clean_gift_cache())

        # Запускаем регулярную синхронизацию
        sync_task = asyncio.create_task(self._schedule_periodic_sync())

        # Ждем завершения всех задач
        await asyncio.gather(gift_processor, updater, cleaner, sync_task)

    async def stop(self):
        """Остановка мониторинга"""
        logger.info("Shutting down parser...")

        # Устанавливаем флаг завершения
        self.shutdown_event.set()

        # Отменяем все задачи мониторинга
        for task in self.monitored_streams.values():
            task.cancel()

        # Ждем завершения обработки очереди подарков
        logger.info(f"Waiting for {self.gift_queue.qsize()} gifts to be processed")

        # Ждем до 5 секунд для обработки оставшихся подарков
        try:
            for _ in range(50):  # 5 секунд (50 * 0.1)
                if self.gift_queue.empty():
                    break
                await asyncio.sleep(0.1)
        except Exception:
            pass

        logger.info("Monitor shutdown completed")

    # Создание отладочной функции

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
                        with open(
                            f"debug_{username}_{int(time.time())}.json", "w"
                        ) as f:
                            import json

                            json.dump(event.raw_data, f)
                        logger.info(f"Successfully saved raw data for {username}")
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

    async def update_streamer(self, streamer_id, room_id, user_id=None, tiktok_id=None):
        """Обновление данных стримера и сохранение связи между room_id и стримером"""
        try:
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

            # Преобразуем room_id в число
            room_id_int = 0
            if isinstance(room_id, str) and room_id.isdigit():
                room_id_int = int(room_id)
            elif isinstance(room_id, int):
                room_id_int = room_id

            # Обновляем запись стримера
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
            if room_id_int > 0:
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

            # Обновляем tik_tok_users с tiktok_id, если предоставлен
            if tiktok_id:
                await self.db.execute(
                    """
                    UPDATE tik_tok_users 
                    SET tiktok_id = $1, last_seen = NOW()
                    WHERE id = $2
                    """,
                    tiktok_id,
                    tik_tok_user_id,
                )
            else:
                await self.db.execute(
                    "UPDATE tik_tok_users SET last_seen = NOW() WHERE id = $1",
                    tik_tok_user_id,
                )

            # Обновляем user_id в tik_tok_users, если предоставлен и нужен
            if user_id and (not ttu_user_id or ttu_name.startswith("@user_")):
                await self.db.execute(
                    """
                    UPDATE tik_tok_users 
                    SET user_id = $1
                    WHERE id = $2 AND (user_id IS NULL OR name LIKE '@user_%')
                    """,
                    user_id,
                    tik_tok_user_id,
                )
                logger.info(f"Updated user_id to {user_id} for {ttu_name}")

            logger.info(
                f"Updated streamer ID {streamer_id} with room_id={room_id_int}, tiktok_id={tiktok_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating streamer data: {e}")
            return False

    async def _process_gift_queue(self):
        gifts_batch = []
        last_flush_time = time.time()

        while not self.shutdown_event.is_set():
            try:
                # Пытаемся получить подарок из очереди, не блокируя поток
                try:
                    gift = self.gift_queue.get_nowait()
                    gifts_batch.append(gift)
                    self.gift_queue.task_done()
                except:
                    # Если очередь пуста, продолжаем
                    pass

                current_time = time.time()

                # Сохраняем пакет подарков, если накопилось достаточно или прошло достаточно времени
                if len(gifts_batch) >= 100 or (
                    current_time - last_flush_time > 3 and gifts_batch
                ):
                    if self.db.pool:
                        async with self.db.pool.acquire() as conn:
                            # Оптимизированный запрос для вставки подарков
                            query = """
                            INSERT INTO gifts 
                            (event_time, user_id, unique_id, follow_role, is_new_gifter, 
                            top_gifter_rank, diamond_count, gift_name, gift_count, 
                            receiver_user_id, receiver_unique_id, streamer_id, receiver_tik_tok_user_id) 
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            """

                            # Подготавливаем пакет данных с преобразованием типов
                            values = [
                                (
                                    gift["event_time"],
                                    str(gift["user_id"]),
                                    str(gift["unique_id"]),
                                    int(gift["follow_role"]),
                                    bool(gift["is_new_gifter"]),
                                    (
                                        None
                                        if gift["top_gifter_rank"] is None
                                        else int(gift["top_gifter_rank"])
                                    ),
                                    int(gift["diamond_count"]),
                                    str(gift["gift_name"]),
                                    int(gift["gift_count"]),
                                    str(gift["receiver_user_id"]),
                                    str(gift["receiver_unique_id"]),
                                    gift.get("streamer_id"),  # Может быть None
                                    gift.get(
                                        "receiver_tik_tok_user_id"
                                    ),  # Может быть None
                                )
                                for gift in gifts_batch
                            ]

                            try:
                                # Пытаемся выполнить пакетную вставку
                                await conn.executemany(query, values)
                                logger.info(
                                    f"Сохранено {len(gifts_batch)} подарков в базу данных"
                                )
                            except Exception as e:
                                # Проверяем, является ли это ошибкой дублирования
                                if "duplicate key" in str(e):
                                    logger.info(
                                        f"Обнаружены дубликаты в пакете, обрабатываются индивидуально"
                                    )
                                    success_count = 0

                                    # Вставляем подарки по одному
                                    for i, gift_values in enumerate(values):
                                        try:
                                            async with conn.transaction():
                                                await conn.execute(query, *gift_values)
                                                success_count += 1
                                        except Exception as e2:
                                            if "duplicate key" in str(e2):
                                                gift_info = gifts_batch[i]
                                                logger.info(
                                                    f"Пропущен дубликат подарка: {gift_info['gift_name']} "
                                                    f"x{gift_info['gift_count']} от {gift_info['unique_id']} "
                                                    f"для {gift_info['receiver_unique_id']}"
                                                )
                                            else:
                                                logger.error(
                                                    f"Ошибка вставки подарка: {e2}"
                                                )

                                    logger.info(
                                        f"Успешно вставлено {success_count} из {len(gifts_batch)} подарков"
                                    )
                                else:
                                    # Логируем другие ошибки
                                    logger.error(
                                        f"Ошибка пакетной вставки подарков: {e}"
                                    )

                    # Очищаем пакет и обновляем время последней вставки
                    gifts_batch = []
                    last_flush_time = current_time

                # Небольшая пауза
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Ошибка обработки очереди подарков: {e}")
                # Выводим дополнительную отладочную информацию
                if gifts_batch:
                    logger.error(f"Проблемные данные подарка: {gifts_batch[0]}")
                gifts_batch = []
                await asyncio.sleep(1)

    async def _update_streamers(self):
        """Обновление списка отслеживаемых стримеров"""
        while not self.shutdown_event.is_set():
            try:
                # Получаем список активных стримеров
                streamers = await self.db.get_active_streamers()
                logger.info(f"Found {len(streamers)} active streamers")

                # Определяем, каких стримеров нужно добавить или удалить
                current_ids = set(self.monitored_streams.keys())
                new_ids = set(s["unique_id"] for s in streamers)

                # Стримеры для добавления и удаления
                to_add = new_ids - current_ids
                to_remove = current_ids - new_ids

                # Удаляем стримеров
                for unique_id in to_remove:
                    logger.info(f"Stopping monitoring for {unique_id}")
                    task = self.monitored_streams.pop(unique_id, None)
                    if task:
                        task.cancel()

                # Добавляем новых стримеров
                for streamer in streamers:
                    if streamer["unique_id"] in to_add:
                        logger.info(f"Starting monitoring for {streamer['unique_id']}")
                        task = asyncio.create_task(self._monitor_streamer(streamer))
                        self.monitored_streams[streamer["unique_id"]] = task
                        # Добавляем задержку между запусками (500ms)
                        await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error updating streamers list: {e}")

            # Проверяем каждые 60 секунд
            await asyncio.sleep(60)

    async def _clean_gift_cache(self):
        """Периодическая очистка кэша подарков"""
        while not self.shutdown_event.is_set():
            # Очищаем кэш каждые 6 часов
            await asyncio.sleep(6 * 60 * 60)
            logger.info(
                f"Cleaning gift cache, size before: {len(self.processed_gift_ids)}"
            )
            self.processed_gift_ids.clear()
            logger.info("Gift cache cleared")

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

        while not self.shutdown_event.is_set():
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

                # Создаем клиент
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
                        await self.update_streamer(
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

                # Обработчики для других событий - без изменений
                @client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    nonlocal connected, last_activity_check
                    connected = True
                    last_activity_check = time.time()
                    await self._process_gift(event, unique_id, cluster)

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
                    logger.error(
                        f"Error starting client for {connect_id}: {error_message}"
                    )
                    connected = False

                    # Попробуем выполнить отладочное подключение при серьезных ошибках
                    if "Expecting value" in error_message:
                        logger.info(f"Attempting debug connection for {connect_id}...")
                        await self.debug_tiktok_connection(connect_id)

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
            if self.shutdown_event.is_set():
                break

            # Ждем перед повторным подключением
            if not connected:
                retry_interval = min(check_online, 10)
                await asyncio.sleep(retry_interval)

    async def _process_gift(self, event, unique_id, cluster):
        """Обработка подарка с улучшенной идентификацией получателя"""
        try:
            # Базовая обработка атрибутов подарка
            current_time = int(time.time() * 1000)
            gift = getattr(event, "gift", None)
            user = getattr(event, "user", getattr(event, "from_user", None))

            if not gift or not user:
                logger.warning(f"Invalid gift event: missing gift or user data")
                return

            # Извлекаем базовые атрибуты
            gift_id = getattr(gift, "id", current_time)
            diamond_count = getattr(gift, "diamond_count", 0)
            user_id = getattr(user, "id", "0")
            gift_count = getattr(
                event, "repeat_count", getattr(gift, "repeat_count", 1)
            )
            gift_name = getattr(gift, "name", "Unknown Gift")
            user_unique_id = getattr(user, "unique_id", f"user_{user_id}")
            gift_type = getattr(gift, "info", {}).get(
                "type", getattr(gift, "type", None)
            )

            # Проверка на стрики в подарках
            streakable = getattr(gift, "streakable", False)
            if not streakable:
                if hasattr(gift, "info") and hasattr(gift.info, "type"):
                    streakable = gift.info.type == 1
                elif hasattr(gift, "type"):
                    streakable = gift.type == 1
            streakable = streakable or (gift_type == 1)
            is_repeating = getattr(gift, "is_repeating", 0) == 1
            repeat_end = getattr(event, "repeat_end", 0) == 1
            streaking = getattr(event, "streaking", False)
            logger.info("+" * 100)
            logger.debug(
                f"Информация о подарке: name={gift_name}, count={gift_count}, streakable={streakable}, "
                + f"is_repeating={is_repeating}, repeat_end={repeat_end}, streaking={streaking}"
            )
            # Для стрикабельных подарков учитываем только последний в серии
            if streakable:
                # Если подарок в стрике и это не конец стрика, пропускаем
                if (is_repeating and not repeat_end) or (streaking):
                    logger.debug(
                        f"Skipping intermediate streaking gift: {gift_name} (count: {gift_count})"
                    )
                    return

                # Формируем ключ для конечного подарка в серии с учетом количества
                gift_key = (
                    f"{gift_id}_{diamond_count}_{user_id}_{unique_id}_{gift_count}"
                )
            else:
                # Для не-стрикабельных подарков используем время для уникальности
                gift_key = (
                    f"{gift_id}_{diamond_count}_{user_id}_{unique_id}_{current_time}"
                )

            # Проверяем, не обрабатывали ли мы уже такой подарок
            if gift_key in self.processed_gift_ids:
                logger.debug(f"Skipping duplicate gift: {gift_key}")
                return

            self.processed_gift_ids.add(gift_key)
            if len(self.processed_gift_ids) > 50000:
                self.processed_gift_ids.difference_update(
                    list(self.processed_gift_ids)[:10000]
                )

            # Информация о роли пользователя
            follow_role = 0
            if hasattr(user, "is_friend") and user.is_friend:
                follow_role = 2
            elif hasattr(user, "is_subscriber") and user.is_subscriber:
                follow_role = 1

            is_new_gifter = getattr(event, "is_first_send_gift", False)
            top_gifter_rank = getattr(user, "gifter_level", None)

            # Получаем ID получателя из события
            raw_receiver_id = getattr(event, "to_member_id", unique_id.replace("@", ""))

            # Получаем room_id из события или клиента
            client_room_id = getattr(
                event,
                "room_id",
                getattr(getattr(event, "client", None), "room_id", None),
            )

            # Поиск стримера с идентификацией через room_id_mapping
            try:
                streamer_data = None
                actual_user_id = None

                # Проверяем, является ли unique_id числовым (room_id)
                numeric_id = None
                if isinstance(unique_id, str) and unique_id.isdigit():
                    numeric_id = int(unique_id)
                elif isinstance(unique_id, int):
                    numeric_id = unique_id

                # 1. Поиск через room_id_mapping по numeric_id, если он есть
                if numeric_id:
                    mapping_data = await self.db.fetchrow(
                        """
                        SELECT rm.tik_tok_user_id, ttu.user_id, ttu.name
                        FROM room_id_mapping rm
                        JOIN tik_tok_users ttu ON rm.tik_tok_user_id = ttu.id
                        WHERE rm.room_id = $1
                        """,
                        numeric_id,
                    )

                    if mapping_data:
                        # Нашли правильную связь через маппинг
                        streamer_data = await self.db.fetchrow(
                            """
                            SELECT s.id, s.tik_tok_user_id
                            FROM streamers s
                            WHERE s.tik_tok_user_id = $1
                            """,
                            mapping_data["tik_tok_user_id"],
                        )

                        # Устанавливаем правильный user_id
                        actual_user_id = mapping_data["user_id"]
                        logger.info(
                            f"Found user_id {actual_user_id} through room_id_mapping for room_id {numeric_id} (@{mapping_data['name']})"
                        )

                # 2. Поиск через client_room_id, если не нашли через numeric_id
                if not streamer_data and client_room_id:
                    # Ищем через room_id_mapping
                    mapping_data = await self.db.fetchrow(
                        """
                        SELECT rm.tik_tok_user_id, ttu.user_id, ttu.name
                        FROM room_id_mapping rm
                        JOIN tik_tok_users ttu ON rm.tik_tok_user_id = ttu.id
                        WHERE rm.room_id = $1
                        """,
                        client_room_id,
                    )

                    if mapping_data:
                        # Нашли правильную связь
                        streamer_data = await self.db.fetchrow(
                            """
                            SELECT s.id, s.tik_tok_user_id
                            FROM streamers s
                            WHERE s.tik_tok_user_id = $1
                            """,
                            mapping_data["tik_tok_user_id"],
                        )

                        # Устанавливаем правильный user_id
                        actual_user_id = mapping_data["user_id"]
                        logger.info(
                            f"Found user_id {actual_user_id} for client_room_id {client_room_id} (@{mapping_data['name']})"
                        )
                    else:
                        # Прямой поиск по room_id в streamers
                        streamer_data = await self.db.fetchrow(
                            """
                            SELECT s.id, s.tik_tok_user_id, ttu.user_id
                            FROM streamers s
                            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                            WHERE s.room_id = $1
                            """,
                            client_room_id,
                        )

                        if streamer_data:
                            actual_user_id = streamer_data["user_id"]
                            logger.info(
                                f"Found streamer by client_room_id={client_room_id}"
                            )

                # 3. Прямой поиск по room_id в streamers (для numeric_id)
                if not streamer_data and numeric_id:
                    streamer_data = await self.db.fetchrow(
                        """
                        SELECT s.id, s.tik_tok_user_id, ttu.user_id
                        FROM streamers s
                        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                        WHERE s.room_id = $1
                        """,
                        numeric_id,
                    )

                    if streamer_data:
                        actual_user_id = streamer_data["user_id"]
                        logger.info(f"Found streamer by numeric room_id={numeric_id}")

                # 4. Поиск по username
                if (
                    not streamer_data
                    and isinstance(unique_id, str)
                    and unique_id.startswith("@")
                ):
                    streamer_data = await self.db.fetchrow(
                        """
                        SELECT s.id, s.tik_tok_user_id, ttu.user_id
                        FROM streamers s
                        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                        WHERE ttu.name = $1
                        """,
                        unique_id,
                    )

                    if streamer_data:
                        actual_user_id = streamer_data["user_id"]
                        logger.info(f"Found streamer by username={unique_id}")

                # 5. Поиск по raw_receiver_id
                if not streamer_data and raw_receiver_id:
                    streamer_data = await self.db.fetchrow(
                        """
                        SELECT s.id, s.tik_tok_user_id, ttu.user_id
                        FROM streamers s
                        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                        WHERE ttu.user_id = $1
                        """,
                        raw_receiver_id,
                    )

                    if streamer_data:
                        actual_user_id = streamer_data["user_id"]
                        logger.info(
                            f"Found streamer by raw_receiver_id={raw_receiver_id}"
                        )

                # 6. Если все еще не нашли, пробуем через активные стримы
                if not streamer_data:
                    room_id_to_search = numeric_id if numeric_id else client_room_id
                    if room_id_to_search:
                        stream_data = await self.db.fetchrow(
                            """
                            SELECT streamer_id
                            FROM streams
                            WHERE room_id = $1 AND end_time IS NULL
                            ORDER BY start_time DESC
                            LIMIT 1
                            """,
                            room_id_to_search,
                        )

                        if stream_data:
                            streamer_data = await self.db.fetchrow(
                                """
                                SELECT s.id, s.tik_tok_user_id, ttu.user_id
                                FROM streamers s
                                JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                                WHERE s.id = $1
                                """,
                                stream_data["streamer_id"],
                            )

                            if streamer_data:
                                actual_user_id = streamer_data["user_id"]
                                logger.info(
                                    f"Found streamer through active stream with room_id={room_id_to_search}"
                                )

                # Определяем значение для receiver_unique_id
                receiver_unique_id = (
                    actual_user_id if actual_user_id else raw_receiver_id
                )

                # Формируем данные о подарке
                gift_data = {
                    "user_id": str(user_id),
                    "unique_id": str(user_unique_id),
                    "follow_role": int(follow_role),
                    "is_new_gifter": bool(is_new_gifter),
                    "top_gifter_rank": (
                        None if top_gifter_rank is None else int(top_gifter_rank)
                    ),
                    "diamond_count": int(diamond_count),
                    "gift_name": str(gift_name),
                    "gift_count": int(gift_count),
                    "receiver_user_id": str(
                        raw_receiver_id
                    ),  # Оригинальный ID из события
                    "receiver_unique_id": str(
                        receiver_unique_id
                    ),  # ID из таблицы tik_tok_users
                    "cluster": str(cluster),
                    "event_time": datetime.now(timezone.utc),
                }

                # Добавляем данные стримера к подарку
                if streamer_data:
                    gift_data["streamer_id"] = streamer_data["id"]
                    gift_data["receiver_tik_tok_user_id"] = streamer_data[
                        "tik_tok_user_id"
                    ]

                    log_info = []
                    if client_room_id:
                        log_info.append(f"room_id: {client_room_id}")
                    if numeric_id and numeric_id != client_room_id:
                        log_info.append(f"numeric_id: {numeric_id}")
                    if receiver_unique_id != raw_receiver_id:
                        log_info.append(f"mapped user_id: {receiver_unique_id}")
                    log_str = f" ({', '.join(log_info)})" if log_info else ""

                    logger.info(
                        f"Found streamer ID {streamer_data['id']} for gift to {unique_id}{log_str}"
                    )
                else:
                    logger.info("!" * 100)
                    logger.warning(
                        f"No streamer found for gift to {unique_id} (user_id: {raw_receiver_id}, room_id: {client_room_id})"
                    )

            except Exception as e:
                logger.warning(f"Error finding streamer for gift: {e}")
                # Создаем данные о подарке с базовой информацией
                gift_data = {
                    "user_id": str(user_id),
                    "unique_id": str(user_unique_id),
                    "follow_role": int(follow_role),
                    "is_new_gifter": bool(is_new_gifter),
                    "top_gifter_rank": (
                        None if top_gifter_rank is None else int(top_gifter_rank)
                    ),
                    "diamond_count": int(diamond_count),
                    "gift_name": str(gift_name),
                    "gift_count": int(gift_count),
                    "receiver_user_id": str(raw_receiver_id),
                    "receiver_unique_id": str(unique_id),
                    "cluster": str(cluster),
                    "event_time": datetime.now(timezone.utc),
                }
            logger.info("=" * 50)
            # Добавляем подарок в очередь
            logger.debug(
                f"Processing gift: {gift_name} x{gift_count} ({diamond_count} diamonds) from {user_unique_id}"
            )

            if not self.gift_queue.full():
                self.gift_queue.put(gift_data)
            else:
                logger.warning("Gift queue is full, skipping gift")

        except Exception as e:
            logger.error(f"Error processing gift: {e}", exc_info=True)

    async def import_streamers_from_file(
        self, file_path="tiktokers.txt", cluster_name="AGENCY", check_online=30
    ):
        """Импорт стримеров из текстового файла"""
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} not found. Skipping import.")
            return

        try:
            # Читаем файл со стримерами
            with open(file_path, "r") as f:
                streamers = f.read().split("\n")

            # Фильтруем пустые строки
            streamers = [s.strip() for s in streamers if s and s.strip()]

            if not streamers:
                logger.warning(f"No streamers found in {file_path}")
                return

            logger.info(f"Found {len(streamers)} streamers in {file_path}")

            # Импортируем стримеров в базу
            await self.db.import_streamers(streamers, cluster_name, check_online)

            logger.info(f"Successfully imported streamers from {file_path}")

        except Exception as e:
            logger.error(f"Error importing streamers: {e}")

    async def import_streamers_from_json(
        self, json_file_path="tiktokers.json", cluster_name="AGENCY", check_online=30
    ):
        """Импорт стримеров из JSON файла"""
        if not os.path.exists(json_file_path):
            logger.warning(f"File {json_file_path} not found. Skipping import.")
            return

        try:
            # Читаем JSON файл
            import json

            with open(json_file_path, "r", encoding="utf-8") as f:
                streamers_data = json.load(f)

            if not streamers_data:
                logger.warning(f"No streamers found in {json_file_path}")
                return

            logger.info(f"Found {len(streamers_data)} streamers in {json_file_path}")

            # Получаем ID кластера через объект базы данных
            cluster = await self.db.fetchrow(
                "SELECT id FROM clusters WHERE name = $1", cluster_name
            )

            if not cluster:
                # Создаем кластер, если его нет
                logger.info(f"Создание кластера '{cluster_name}'")
                cluster_id = await self.db.fetchval(
                    "INSERT INTO clusters (name) VALUES ($1) RETURNING id", cluster_name
                )
            else:
                cluster_id = cluster["id"]

            # Обрабатываем каждый элемент в JSON
            for streamer in streamers_data:
                # Получаем основные данные для идентификации
                user_name = streamer.get("user_name", "")
                user_id = streamer.get("user_id", "")
                tiktok_id = streamer.get("tiktok_id", "")

                if not user_name and not user_id and not tiktok_id:
                    logger.warning(
                        f"Skipping streamer with no identifiable data: {streamer}"
                    )
                    continue

                # Форматируем имя пользователя с @
                name = None
                if user_name:
                    name = user_name if user_name.startswith("@") else f"@{user_name}"

                # Создаем или получаем пользователя TikTok через объект базы данных
                tik_tok_user_id = await self.db.get_or_create_tiktok_user(
                    name, user_id, tiktok_id
                )

                if not tik_tok_user_id:
                    logger.error(
                        f"Failed to create TikTok user for {name or user_id or tiktok_id}"
                    )
                    continue

                # Проверяем, есть ли уже стример с этим tik_tok_user_id
                existing = await self.db.fetchrow(
                    "SELECT id FROM streamers WHERE tik_tok_user_id = $1",
                    tik_tok_user_id,
                )

                # Получаем room_id, если он есть
                room_id = streamer.get("room_id", 0)
                if isinstance(room_id, str) and room_id.isdigit():
                    room_id = int(room_id)

                if not existing:
                    # Добавляем нового стримера
                    try:
                        query = """
                        INSERT INTO streamers (tik_tok_user_id, cluster_id, status, check_online, room_id) 
                        VALUES ($1, $2, $3, $4, $5) RETURNING id
                        """

                        streamer_id = await self.db.fetchval(
                            query,
                            tik_tok_user_id,
                            cluster_id,
                            "Запущен",
                            check_online,
                            room_id if room_id and room_id > 0 else 0,
                        )
                        logger.info(
                            f"Добавлен новый стример: {name or user_id or tiktok_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Ошибка при добавлении стримера {name or user_id or tiktok_id}: {e}"
                        )
                else:
                    # Обновляем существующего стримера
                    try:
                        query = """
                        UPDATE streamers 
                        SET status = 'Запущен', cluster_id = $1, check_online = $2
                        """
                        params = [cluster_id, check_online]

                        # Если есть room_id, обновляем его
                        if room_id and room_id > 0:
                            query += f", room_id = ${len(params) + 1}"
                            params.append(room_id)

                        # Добавляем условие WHERE
                        query += f" WHERE id = ${len(params) + 1}"
                        params.append(existing["id"])

                        await self.db.execute(query, *params)
                        logger.info(
                            f"Обновлен существующий стример: {name or user_id or tiktok_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Ошибка при обновлении стримера {name or user_id or tiktok_id}: {e}"
                        )

            logger.info(
                f"Successfully imported {len(streamers_data)} streamers from {json_file_path}"
            )

        except Exception as e:
            logger.error(f"Error importing streamers from JSON: {e}", exc_info=True)

    async def sync_gift_streamers(self):
        """Улучшенная синхронизация подарков и стримеров"""
        try:
            # Сначала синхронизируем идентификаторы
            await self.sync_tiktok_ids()

            # Обновляем по имени (receiver_unique_id с @)
            query1 = """
            UPDATE gifts g
            SET 
                streamer_id = s.id,
                receiver_tik_tok_user_id = ttu.id
            FROM streamers s
            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
            WHERE g.receiver_unique_id = ttu.name AND g.streamer_id IS NULL;
            """
            result1 = await self.db.execute(query1)
            # logger.info(f"Synchronized gifts with streamers by name: {result1}")

            # Обновляем по user_id
            query2 = """
            UPDATE gifts g
            SET 
                streamer_id = s.id,
                receiver_tik_tok_user_id = ttu.id
            FROM streamers s
            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
            WHERE (g.receiver_user_id = ttu.user_id) 
            AND g.streamer_id IS NULL;
            """
            result2 = await self.db.execute(query2)
            # logger.info(f"Synchronized gifts with streamers by user_id: {result2}")

            # Обновляем по tiktok_id
            query3 = """
            UPDATE gifts g
            SET 
                streamer_id = s.id,
                receiver_tik_tok_user_id = ttu.id
            FROM streamers s
            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
            WHERE (g.receiver_unique_id LIKE '@%' AND REPLACE(g.receiver_unique_id, '@', '') = ttu.tiktok_id) 
            AND g.streamer_id IS NULL;
            """
            result3 = await self.db.execute(query3)
            # logger.info(f"Synchronized gifts with streamers by tiktok_id: {result3}")

            # Обновляем по room_id с использованием маппинга
            # Исправленный запрос - убираем ссылку на rm.user_id
            query4 = """
            UPDATE gifts g
            SET 
                streamer_id = s.id,
                receiver_tik_tok_user_id = rm.tik_tok_user_id
            FROM room_id_mapping rm
            JOIN streamers s ON s.tik_tok_user_id = rm.tik_tok_user_id
            WHERE CAST(NULLIF(g.receiver_user_id, '') AS BIGINT) = rm.room_id
            AND g.streamer_id IS NULL;
            """
            result4 = await self.db.execute(query4)
            logger.info(
                # f"Synchronized gifts with streamers by room_id mapping: {result4}"
            )

            # Исправляем автоматически сгенерированные имена
            query5 = """
            WITH proper_names AS (
                SELECT user_id, name
                FROM tik_tok_users
                WHERE user_id IS NOT NULL AND name NOT LIKE '@user_%'
            )
            UPDATE tik_tok_users t
            SET name = p.name
            FROM proper_names p
            WHERE t.user_id = p.user_id AND t.name LIKE '@user_%';
            """
            result5 = await self.db.execute(query5)
            # logger.info(f"Fixed auto-generated usernames: {result5}")

            return True
        except Exception as e:
            logger.error(f"Error syncing gifts with streamers: {e}")
            return False

    async def _schedule_periodic_sync(self):
        """Периодическая синхронизация подарков и стримеров"""
        while not self.shutdown_event.is_set():
            try:
                await self.sync_gift_streamers()
            except Exception as e:
                logger.error(f"Error in periodic gift sync: {e}")

            # Синхронизируем каждую минуту чтобы не пропустить подарки
            await asyncio.sleep(60)

    async def sync_tiktok_ids(self):
        """Синхронизация TikTok идентификаторов"""
        try:
            # Обновляем user_id для TikTok пользователей на основе полученных подарков
            query = """
            WITH numeric_ids AS (
                SELECT DISTINCT 
                    receiver_unique_id, 
                    unique_id
                FROM gifts
                WHERE unique_id ~ '^[0-9]+$' 
                AND receiver_unique_id LIKE '@%'
            )
            UPDATE tik_tok_users t
            SET user_id = n.unique_id
            FROM numeric_ids n
            WHERE t.name = n.receiver_unique_id
            AND (t.user_id IS NULL OR t.user_id != n.unique_id);
            """

            result = await self.db.execute(query)
            logger.info(f"Updated TikTok user_ids: {result}")

            return True
        except Exception as e:
            logger.error(f"Error syncing TikTok IDs: {e}")
            return False
            logger.error(f"Error syncing TikTok IDs: {e}")
            return False
