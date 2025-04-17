# client/client.py
import asyncio
from logger import logger
import os

import time
from datetime import datetime, timezone
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent
from queue import Queue


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
    
    async def start(self):
        """Запуск мониторинга"""
        # Запускаем обработку подарков
        gift_processor = asyncio.create_task(self._process_gift_queue())
        
        # Запускаем обновление списка стримеров
        updater = asyncio.create_task(self._update_streamers())
        
        # Запускаем очистку кэша подарков
        cleaner = asyncio.create_task(self._clean_gift_cache())
        
        # Ждем завершения всех задач
        await asyncio.gather(gift_processor, updater, cleaner)
    
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
                if len(gifts_batch) >= 100 or (current_time - last_flush_time > 3 and gifts_batch):
                    if self.db.pool:
                        async with self.db.pool.acquire() as conn:
                            async with conn.transaction():
                                # Оптимизированный запрос для вставки подарков
                                query = """
                                INSERT INTO gifts 
                                (event_time, user_id, unique_id, follow_role, is_new_gifter, 
                                top_gifter_rank, diamond_count, gift_name, gift_count, 
                                receiver_user_id, receiver_unique_id) 
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                """
                                
                                # Подготавливаем пакет данных с преобразованием типов
                                values = [
                                    (
                                        gift["event_time"],
                                        str(gift["user_id"]),  # Преобразуем в строку
                                        str(gift["unique_id"]),  # Преобразуем в строку
                                        int(gift["follow_role"]),  # Преобразуем в число
                                        bool(gift["is_new_gifter"]),  # Преобразуем в boolean
                                        None if gift["top_gifter_rank"] is None else int(gift["top_gifter_rank"]),
                                        int(gift["diamond_count"]),  # Преобразуем в число
                                        str(gift["gift_name"]),  # Преобразуем в строку
                                        int(gift["gift_count"]),  # Преобразуем в число
                                        str(gift["receiver_user_id"]),  # Преобразуем в строку
                                        str(gift["receiver_unique_id"])  # Преобразуем в строку
                                    )
                                    for gift in gifts_batch
                                ]
                                
                                # Выполняем пакетную вставку
                                await conn.executemany(query, values)
                    
                    # logger.info(f"Saved {len(gifts_batch)} gifts to database")
                    gifts_batch = []
                    last_flush_time = current_time
                
                # Небольшая пауза
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in gift queue processing: {e}")
                # Выводим дополнительную отладочную информацию
                if gifts_batch:
                    logger.error(f"Problematic gift data: {gifts_batch[0]}")
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
            
            except Exception as e:
                logger.error(f"Error updating streamers list: {e}")
            
            # Проверяем каждые 60 секунд
            await asyncio.sleep(60)
    
    async def _clean_gift_cache(self):
        """Периодическая очистка кэша подарков"""
        while not self.shutdown_event.is_set():
            # Очищаем кэш каждые 6 часов
            await asyncio.sleep(6 * 60 * 60)
            logger.info(f"Cleaning gift cache, size before: {len(self.processed_gift_ids)}")
            self.processed_gift_ids.clear()
            logger.info("Gift cache cleared")
    
    async def _monitor_streamer(self, streamer_info):
        unique_id = streamer_info["unique_id"]
        cluster = streamer_info["cluster"]
        check_online = streamer_info["check_online"]
        streamer_id = streamer_info["id"]
        tik_tok_user_id = streamer_info.get("tik_tok_user_id")
        room_id = streamer_info.get("room_id")
        
        logger.info(f"Starting monitoring for {unique_id} (Cluster: {cluster})")
        
        # Переменная для отслеживания состояния подключения
        connected = False
        last_conn_attempt = 0
        max_offline_attempts = 5  # Максимальное количество попыток при offline статусе
        offline_attempts = 0
        
        # Переменные для проверки активности
        last_activity_check = time.time()
        activity_check_interval = 300  # 5 минут
        
        # Список известных безопасных ошибок
        safe_error_messages = [
            "property 'type' of 'CompetitionEvent' object has no setter",
            "is offline",
        ]
        
        while not self.shutdown_event.is_set():
            client = None
            current_time = time.time()
            
            # Если подключены, проверяем активность стрима
            if connected:
                # Проверяем, нужно ли проверить активность
                if current_time - last_activity_check > activity_check_interval:
                    last_activity_check = current_time
                    logger.info(f"Checking activity for {unique_id}")
                    
                    # Обновляем данные в базе
                    try:
                        # Обновляем streamer
                        await self.db.execute(
                            """
                            UPDATE streamers 
                            SET last_activity = NOW(), last_check = NOW(), is_live = TRUE 
                            WHERE id = $1
                            """, 
                            streamer_id
                        )
                        
                        # Обновляем tik_tok_user
                        if tik_tok_user_id:
                            await self.db.execute(
                                "UPDATE tik_tok_users SET last_seen = NOW() WHERE id = $1",
                                tik_tok_user_id
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
                # Пытаемся подключиться с использованием разных идентификаторов
                name = streamer_info.get("name")
                connect_id = name if name and name.startswith('@') else unique_id
                client = TikTokLiveClient(unique_id=connect_id)
                logger.debug(f"Connecting with unique_id: {connect_id}")
                
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
                        last_activity_check = time.time()  # Сбрасываем таймер проверки активности
                        
                        # Безопасно извлекаем room_id и другие идентификаторы
                        event_room_id = getattr(event, 'room_id', getattr(client, 'room_id', None))
                        event_tiktok_id = getattr(event, 'unique_id', getattr(client, 'unique_id', None))
                        
                        logger.info(f"Connected to {unique_id} (Room ID: {event_room_id}, TikTok ID: {event_tiktok_id})")
                        
                        # Если получили ID от TikTokLive, используем его как user_id
                        user_id = None
                        if event_room_id:
                            user_id = str(event_room_id)
                        
                        # Обновляем данные стримера в базе
                        await self.db.update_streamer(
                            streamer_id, 
                            event_room_id or room_id, 
                            user_id, 
                            event_tiktok_id
                        )
                        
                        # Создаем запись в таблице streams
                        try:
                            # Проверяем, есть ли уже активный стрим для этого стримера
                            existing_stream = await self.db.fetchrow(
                                """
                                SELECT id FROM streams 
                                WHERE streamer_id = $1 AND end_time IS NULL
                                """,
                                streamer_id
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
                                    event_room_id or room_id
                                )
                                logger.info(f"Created new stream record with ID {stream_id}")
                            else:
                                # Обновляем существующий стрим
                                await self.db.execute(
                                    """
                                    UPDATE streams
                                    SET max_viewers = max_viewers + 1
                                    WHERE id = $1
                                    """,
                                    existing_stream['id']
                                )
                                logger.info(f"Updated existing stream record with ID {existing_stream['id']}")
                        except Exception as e:
                            logger.error(f"Error creating/updating stream record: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error in on_connect: {e}")
                
                # Добавляем обработчики для других событий (GiftEvent, DisconnectEvent)
                @client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    # Если мы здесь, значит мы точно подключены
                    nonlocal connected, last_activity_check
                    connected = True
                    last_activity_check = time.time()  # Обновляем время последней активности
                    await self._process_gift(event, unique_id, cluster)
                    
                @client.on(DisconnectEvent)
                async def on_disconnect(event: DisconnectEvent):
                    nonlocal connected
                    logger.info(f"Disconnected from {unique_id}")
                    connected = False
                    
                    # Закрываем запись о стриме
                    try:
                        # Обновляем streamer
                        await self.db.execute(
                            """
                            UPDATE streamers 
                            SET is_live = FALSE
                            WHERE id = $1
                            """, 
                            streamer_id
                        )
                        
                        # Закрываем текущий стрим
                        await self.db.execute(
                            """
                            UPDATE streams
                            SET end_time = NOW(),
                                duration = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER
                            WHERE streamer_id = $1 AND end_time IS NULL
                            """,
                            streamer_id
                        )
                    except Exception as e:
                        logger.error(f"Error updating stream end data: {e}")
                    
                # Запускаем клиент БЕЗ таймаута
                await client.start()
                
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
                        if offline_attempts > max_offline_attempts:
                            wait_time = check_online * 2
                            logger.info(f"{unique_id} is offline after {offline_attempts} attempts. Will retry in {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                            offline_attempts = 0
                            continue
                else:
                    logger.error(f"Error in monitoring {unique_id}: {error_message}")
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
        """Обработка подарка"""
        try:
            # Используем доступные атрибуты для формирования уникального ключа
            current_time = int(time.time() * 1000)
            
            # Безопасно получаем атрибуты
            gift = getattr(event, 'gift', None)
            user = getattr(event, 'user', getattr(event, 'from_user', None))
            
            if not gift or not user:
                logger.warning(f"Invalid gift event: missing gift or user data")
                return
            
            # Создаем уникальный ключ на основе доступных атрибутов
            gift_id = getattr(gift, 'id', current_time)
            diamond_count = getattr(gift, 'diamond_count', 0)
            user_id = getattr(user, 'id', '0')
            
            gift_key = f"{gift_id}_{diamond_count}_{user_id}_{unique_id}_{current_time}"
            
            # Проверяем, не обработан ли уже этот подарок
            if gift_key in self.processed_gift_ids:
                return
            
            # Добавляем ID подарка в кэш обработанных
            self.processed_gift_ids.add(gift_key)
            
            # Если кэш становится слишком большим, очищаем его частично
            if len(self.processed_gift_ids) > 10000:
                self.processed_gift_ids.difference_update(list(self.processed_gift_ids)[:5000])
            
            # Получаем остальные атрибуты безопасно
            gift_count = getattr(event, 'repeat_count', getattr(gift, 'repeat_count', 1))
            gift_name = getattr(gift, 'name', "Unknown Gift")
            user_unique_id = getattr(user, 'unique_id', f"user_{user_id}")
            
            follow_role = 0
            if hasattr(user, 'is_friend') and user.is_friend:
                follow_role = 2
            elif hasattr(user, 'is_subscriber') and user.is_subscriber:
                follow_role = 1
            
            is_new_gifter = False
            if hasattr(event, 'is_first_send_gift'):
                is_new_gifter = event.is_first_send_gift
            
            top_gifter_rank = getattr(user, 'gifter_level', None)
            receiver_user_id = getattr(event, 'to_member_id', unique_id.replace('@', ''))
            
            # Формируем данные о подарке с нормализованными типами
            gift_data = {
                "user_id": str(user_id),  # Преобразуем в строку
                "unique_id": str(user_unique_id),  # Преобразуем в строку
                "follow_role": int(follow_role),  # Преобразуем в число 
                "is_new_gifter": bool(is_new_gifter),  # Преобразуем в boolean
                "top_gifter_rank": None if top_gifter_rank is None else int(top_gifter_rank),
                "diamond_count": int(diamond_count),  # Преобразуем в число
                "gift_name": str(gift_name),  # Преобразуем в строку
                "gift_count": int(gift_count),  # Преобразуем в число
                "receiver_user_id": str(receiver_user_id),  # Преобразуем в строку
                "receiver_unique_id": str(unique_id),  # Преобразуем в строку
                "cluster": str(cluster),  # Преобразуем в строку
                "event_time": datetime.now(timezone.utc)
            }
            
            # Добавляем отладочную информацию
            logger.debug(f"Processing gift: {gift_name} x{gift_count} ({diamond_count} diamonds) from {user_unique_id}")
            
            # Добавляем подарок в очередь
            if not self.gift_queue.full():
                self.gift_queue.put(gift_data)
            else:
                logger.warning("Gift queue is full, skipping gift")
            
        except Exception as e:
            logger.error(f"Error processing gift: {e}", exc_info=True)
    
    async def import_streamers_from_file(self, file_path='tiktokers.txt', cluster_name='AGENCY', check_online=30):
        """Импорт стримеров из текстового файла"""
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} not found. Skipping import.")
            return
        
        try:
            # Читаем файл со стримерами
            with open(file_path, 'r') as f:
                streamers = f.read().split('\n')
            
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
    async def import_streamers_from_json(self, json_file_path='tiktokers.json', cluster_name='AGENCY', check_online=30):
        """Импорт стримеров из JSON файла"""
        if not os.path.exists(json_file_path):
            logger.warning(f"File {json_file_path} not found. Skipping import.")
            return
        
        try:
            # Читаем JSON файл
            import json
            with open(json_file_path, 'r', encoding='utf-8') as f:
                streamers_data = json.load(f)
            
            if not streamers_data:
                logger.warning(f"No streamers found in {json_file_path}")
                return
            
            logger.info(f"Found {len(streamers_data)} streamers in {json_file_path}")
            
            # Получаем ID кластера через объект базы данных
            cluster = await self.db.fetchrow("SELECT id FROM clusters WHERE name = $1", cluster_name)
            
            if not cluster:
                # Создаем кластер, если его нет
                logger.info(f"Создание кластера '{cluster_name}'")
                cluster_id = await self.db.fetchval(
                    "INSERT INTO clusters (name) VALUES ($1) RETURNING id", 
                    cluster_name
                )
            else:
                cluster_id = cluster['id']
            
            # Обрабатываем каждый элемент в JSON
            for streamer in streamers_data:
                # Получаем основные данные для идентификации
                user_name = streamer.get('user_name', '')
                user_id = streamer.get('user_id', '')
                tiktok_id = streamer.get('tiktok_id', '')
                
                if not user_name and not user_id and not tiktok_id:
                    logger.warning(f"Skipping streamer with no identifiable data: {streamer}")
                    continue
                    
                # Форматируем имя пользователя с @
                name = None
                if user_name:
                    name = user_name if user_name.startswith('@') else f"@{user_name}"
                
                # Создаем или получаем пользователя TikTok через объект базы данных
                tik_tok_user_id = await self.db.get_or_create_tiktok_user(name, user_id, tiktok_id)
                
                if not tik_tok_user_id:
                    logger.error(f"Failed to create TikTok user for {name or user_id or tiktok_id}")
                    continue
                    
                # Проверяем, есть ли уже стример с этим tik_tok_user_id
                existing = await self.db.fetchrow(
                    "SELECT id FROM streamers WHERE tik_tok_user_id = $1", 
                    tik_tok_user_id
                )
                
                # Получаем room_id, если он есть
                room_id = streamer.get('room_id', 0)
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
                            'Запущен',
                            check_online,
                            room_id if room_id and room_id > 0 else 0
                        )
                        logger.info(f"Добавлен новый стример: {name or user_id or tiktok_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при добавлении стримера {name or user_id or tiktok_id}: {e}")
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
                        params.append(existing['id'])
                        
                        await self.db.execute(query, *params)
                        logger.info(f"Обновлен существующий стример: {name or user_id or tiktok_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при обновлении стримера {name or user_id or tiktok_id}: {e}")
            
            logger.info(f"Successfully imported {len(streamers_data)} streamers from {json_file_path}")
            
        except Exception as e:
            logger.error(f"Error importing streamers from JSON: {e}", exc_info=True)