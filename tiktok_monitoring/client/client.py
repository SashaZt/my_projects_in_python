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
                    
                    logger.info(f"Saved {len(gifts_batch)} gifts to database")
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
        
        logger.info(f"Starting monitoring for {unique_id} (Cluster: {cluster})")
        
        # Переменная для отслеживания состояния подключения
        connected = False
        last_conn_attempt = 0
        max_offline_attempts = 5  # Максимальное количество попыток при offline статусе
        offline_attempts = 0
        
        # Список известных безопасных ошибок, которые можно игнорировать
        safe_error_messages = [
            "property 'type' of 'CompetitionEvent' object has no setter",
            "is offline",
        ]
        
        while not self.shutdown_event.is_set():
            client = None
            current_time = time.time()
            
            # Если мы уже подключены, просто ждем
            if connected:
                await asyncio.sleep(1)
                continue
                
            # Если с момента последней попытки прошло меньше check_online секунд, ждем
            if current_time - last_conn_attempt < check_online:
                await asyncio.sleep(1)
                continue
                
            # Обновляем время последней попытки
            last_conn_attempt = current_time
            
            try:
                # Создаем новый экземпляр клиента
                client = TikTokLiveClient(unique_id=unique_id)
                
                # Флаг для отслеживания успешного подключения
                connection_established = False
                
                @client.on(ConnectEvent)
                async def on_connect(event: ConnectEvent):
                    nonlocal connected, connection_established
                    try:
                        # Отмечаем, что подключение установлено
                        connected = True
                        connection_established = True
                        offline_attempts = 0  # Сбрасываем счетчик попыток
                        
                        # Безопасно извлекаем room_id
                        room_id = getattr(event, 'room_id', getattr(client, 'room_id', None))
                        logger.info(f"Connected to {unique_id} (Room ID: {room_id})")
                        
                        # Обновляем данные стримера в базе
                        if room_id:
                            # Преобразуем room_id в целое число, если это возможно
                            try:
                                user_id = int(room_id) if isinstance(room_id, str) and room_id.isdigit() else room_id
                                await self.db.update_streamer(streamer_id, user_id)
                            except Exception as e:
                                logger.error(f"Error updating streamer data: {e}")
                    except Exception as e:
                        logger.error(f"Error in on_connect: {e}")
                
                @client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    # Если мы здесь, значит мы точно подключены
                    nonlocal connected
                    connected = True
                    await self._process_gift(event, unique_id, cluster)
                
                @client.on(DisconnectEvent)
                async def on_disconnect(event: DisconnectEvent):
                    nonlocal connected
                    logger.info(f"Disconnected from {unique_id}")
                    connected = False
                
                # Запускаем клиент БЕЗ таймаута
                await client.start()
                
                # Если мы дошли до этой точки, значит клиент завершил работу сам
                # (например, стрим закончился)
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
                            # После нескольких попыток увеличиваем интервал для экономии ресурсов
                            wait_time = check_online * 2
                            logger.info(f"{unique_id} is offline after {offline_attempts} attempts. Will retry in {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                            offline_attempts = 0  # Сбрасываем счетчик
                            continue
                        else:
                            logger.info(f"{unique_id} is offline. Will retry in {check_online} seconds")
                    # Не логируем другие известные безопасные ошибки
                else:
                    logger.error(f"Error in monitoring {unique_id}: {error_message}")
            finally:
                # Явно освобождаем ресурсы клиента
                try:
                    if client:
                        await client.stop()
                except:
                    pass
                
                # Если был установлен флаг соединения, но не было события подключения,
                # сбрасываем флаг
                if not connection_established:
                    connected = False
            
            # Проверяем, не остановлен ли мониторинг
            if self.shutdown_event.is_set():
                break
            
            # Ждем перед повторным подключением
            if not connected:
                retry_interval = min(check_online, 10)  # Используем максимум 10 секунд для переподключения
                logger.info(f"Attempting to reconnect to {unique_id} in {retry_interval} seconds")
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