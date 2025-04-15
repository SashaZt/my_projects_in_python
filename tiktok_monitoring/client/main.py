# parser/main.py
import asyncio
from logger import logger
import sys
import signal
import time
from datetime import datetime, timezone
from queue import Queue
import threading
import asyncpg
import os
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent


# Настройки подключения к PostgreSQL
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5431)),
    "user": os.getenv("POSTGRES_USER", "user_bd"),
    "password": os.getenv("POSTGRES_PASSWORD", "Pqm36q1kmcAlsVMIp2glEdfwNnj69X"),
    "database": os.getenv("POSTGRES_DB", "tiktok_monitoring")
}

# Настройка API ключа для TikTokLive
WebDefaults.tiktok_sign_api_key = "ODBkM2NlYTU2NWIxYTdkYjM1M2NiMzA5MTM1MmVmOTk4M2E4MDM4YzYzZTIzZTBkN2RkODU5"

# Глобальные переменные
monitored_streams = {}  # Словарь отслеживаемых стримеров
gift_queue = Queue(maxsize=5000)  # Очередь для асинхронной записи подарков
pool = None  # Пул соединений с БД
processed_gift_ids = set()  # Кэш для дедупликации подарков
shutdown_event = threading.Event()  # Событие для graceful shutdown

async def import_streamers_from_file(file_path='tiktokers.txt', cluster_name='AGENCY', check_online=30):
    """Импорт стримеров из текстового файла в базу данных"""
    
    if not os.path.exists(file_path):
        logger.warning(f"Файл {file_path} не найден. Импорт стримеров пропущен.")
        return
    
    try:
        # Получаем ID кластера
        async with pool.acquire() as conn:
            cluster = await conn.fetchrow("SELECT id FROM clusters WHERE name = $1", cluster_name)
            
            if not cluster:
                # Создаем кластер, если его нет
                logger.info(f"Создание кластера '{cluster_name}'")
                cluster_id = await conn.fetchval(
                    "INSERT INTO clusters (name) VALUES ($1) RETURNING id", 
                    cluster_name
                )
            else:
                cluster_id = cluster['id']
            
            # Читаем файл со стримерами
            with open(file_path, 'r') as f:
                streamers = f.read().split('\n')
            
            # Фильтруем пустые строки
            streamers = [s.strip() for s in streamers if s and s.strip()]
            
            if not streamers:
                logger.warning(f"В файле {file_path} не найдено стримеров.")
                return
            
            logger.info(f"Найдено {len(streamers)} стримеров в файле {file_path}")
            
            # Добавляем стримеров в базу данных
            for streamer_name in streamers:
                # Проверяем, есть ли стример в базе
                existing = await conn.fetchrow(
                    "SELECT id FROM streamers WHERE name = $1", 
                    streamer_name if streamer_name.startswith('@') else f"@{streamer_name}"
                )
                
                if not existing:
                    # Добавляем нового стримера
                    streamer_id = await conn.fetchval(
                        """
                        INSERT INTO streamers (name, cluster_id, status, check_online) 
                        VALUES ($1, $2, $3, $4) RETURNING id
                        """,
                        streamer_name if streamer_name.startswith('@') else f"@{streamer_name}",
                        cluster_id,
                        'Запущен',
                        check_online
                    )
                    logger.info(f"Добавлен новый стример: {streamer_name}")
                else:
                    # Обновляем статус существующего стримера
                    await conn.execute(
                        """
                        UPDATE streamers 
                        SET status = 'Запущен', cluster_id = $1, check_online = $2
                        WHERE id = $3
                        """,
                        cluster_id,
                        check_online,
                        existing['id']
                    )
                    logger.info(f"Обновлен существующий стример: {streamer_name}")
        
        logger.info(f"Импорт стримеров из файла {file_path} завершен успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при импорте стримеров: {e}")

# Функция для подключения к базе данных
async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(**DB_CONFIG)
        logger.info("Connected to PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return False

# Функция для получения активных стримеров из базы данных
async def get_active_streamers():
    try:
        if not pool:
            return []
        
        query = """
        SELECT s.name, s.id, c.name as cluster, s.check_online 
        FROM streamers s
        JOIN clusters c ON s.cluster_id = c.id
        WHERE s.status = 'Запущен'
        """
        
        streamers = await pool.fetch(query)
        return [
            {
                "unique_id": s['name'] if s['name'].startswith('@') else f"@{s['name']}",
                "id": s['id'],
                "cluster": s['cluster'],
                "check_online": s['check_online']
            }
            for s in streamers
        ]
    except Exception as e:
        logger.error(f"Error fetching streamers: {e}")
        return []

# Обработчик подарков
# Обработчик подарков
async def on_gift(event: GiftEvent, unique_id: str, cluster: str):
    try:
        # Используем доступные атрибуты для формирования уникального ключа
        current_time = int(time.time() * 1000)
        
        # Судя по отладке, нам доступны следующие поля:
        gift_id = getattr(event.gift, 'id', None) or getattr(event, 'order_id', None) or current_time
        diamond_count = getattr(event.gift, 'diamond_count', 0)
        user_id = getattr(event.from_user, 'id', getattr(event.user, 'id', '0'))
        
        # Создаем уникальный ключ
        gift_key = f"{gift_id}_{diamond_count}_{user_id}_{current_time}"
        
        # Проверяем, не обработан ли уже этот подарок
        if gift_key in processed_gift_ids:
            return
        
        # Добавляем ID подарка в кэш обработанных
        processed_gift_ids.add(gift_key)
        
        # Если кэш становится слишком большим, очищаем его частично
        if len(processed_gift_ids) > 10000:
            processed_gift_ids.difference_update(list(processed_gift_ids)[:5000])
        
        # Безопасно получаем все необходимые атрибуты
        gift_count = getattr(event, 'repeat_count', 1)
        try:
            gift_name = event.gift.name
        except AttributeError:
            gift_name = "Unknown Gift"
        
        # Получаем unique_id пользователя
        try:
            user_unique_id = event.user.unique_id
        except AttributeError:
            try:
                user_unique_id = event.from_user.unique_id
            except AttributeError:
                user_unique_id = "unknown_user"
        
        # Определяем follow_role
        follow_role = 0
        try:
            if event.user.is_friend:
                follow_role = 2
            elif event.user.is_subscriber:
                follow_role = 1
        except AttributeError:
            pass
        
        # Определяем is_new_gifter
        is_new_gifter = False
        try:
            is_new_gifter = event.is_first_send_gift
        except AttributeError:
            pass
        
        # Получаем top_gifter_rank
        top_gifter_rank = None
        try:
            top_gifter_rank = event.user.gifter_level
        except AttributeError:
            pass
        
        # Получаем receiver_user_id
        receiver_user_id = getattr(event, 'to_member_id', unique_id.replace('@', ''))
        
        # Формируем данные о подарке
        gift_data = {
            "user_id": user_id,
            "unique_id": user_unique_id,
            "follow_role": follow_role,
            "is_new_gifter": is_new_gifter,
            "top_gifter_rank": top_gifter_rank,
            "diamond_count": diamond_count,
            "gift_name": gift_name,
            "gift_count": gift_count,
            "receiver_user_id": receiver_user_id,
            "receiver_unique_id": unique_id,
            "cluster": cluster,
            "event_time": datetime.now(timezone.utc)
        }
        
        # Добавляем подарок в очередь
        if not gift_queue.full():
            gift_queue.put(gift_data)
        else:
            logger.warning("Gift queue is full, skipping gift")
        
    except Exception as e:
        logger.error(f"Error processing gift: {e}", exc_info=True)

# Функция для обработки очереди подарков
async def process_gift_queue():
    gifts_batch = []
    last_flush_time = time.time()
    
    while not shutdown_event.is_set():
        try:
            # Пытаемся получить подарок из очереди, не блокируя поток
            try:
                gift = gift_queue.get_nowait()
                gifts_batch.append(gift)
                gift_queue.task_done()
            except:
                # Если очередь пуста, продолжаем
                pass
            
            current_time = time.time()
            
            # Сохраняем пакет подарков, если накопилось достаточно или прошло достаточно времени
            if len(gifts_batch) >= 100 or (current_time - last_flush_time > 3 and gifts_batch):
                if pool:
                    async with pool.acquire() as conn:
                        async with conn.transaction():
                            # Оптимизированный запрос для вставки подарков
                            query = """
                            INSERT INTO gifts 
                            (event_time, user_id, unique_id, follow_role, is_new_gifter, 
                            top_gifter_rank, diamond_count, gift_name, gift_count, 
                            receiver_user_id, receiver_unique_id) 
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            """
                            
                            # Подготавливаем пакет данных
                            values = [
                                (
                                    gift["event_time"],
                                    gift["user_id"],
                                    gift["unique_id"],
                                    gift["follow_role"],
                                    gift["is_new_gifter"],
                                    gift["top_gifter_rank"],
                                    gift["diamond_count"],
                                    gift["gift_name"],
                                    gift["gift_count"],
                                    gift["receiver_user_id"],
                                    gift["receiver_unique_id"]
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
            gifts_batch = []
            await asyncio.sleep(1)

# Функция для мониторинга стримера
async def monitor_streamer(streamer_info):
    unique_id = streamer_info["unique_id"]
    cluster = streamer_info["cluster"]
    check_online = streamer_info["check_online"]
    streamer_id = streamer_info["id"]
    
    logger.info(f"Starting monitoring for {unique_id} (Cluster: {cluster})")
    
    while not shutdown_event.is_set():
        client = None
        try:
            # Создаем новый экземпляр клиента для каждой попытки подключения
            client = TikTokLiveClient(unique_id=unique_id)
            
            # Регистрируем обработчик подключения
            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                try:
                    # Безопасно извлекаем room_id
                    room_id = getattr(event, 'room_id', None)
                    logger.info(f"Connected to {unique_id} (Room ID: {room_id})")
                    
                    # Обновляем данные стримера в базе
                    if pool and room_id:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                "UPDATE streamers SET user_id = $1, last_activity = NOW() WHERE id = $2",
                                str(room_id), streamer_id
                            )
                except Exception as e:
                    logger.error(f"Error updating streamer data: {e}", exc_info=True)
            
            # Регистрируем обработчик подарков
            @client.on(GiftEvent)
            async def _on_gift(event: GiftEvent):
                await on_gift(event, unique_id, cluster)
            
            # Регистрируем обработчик отключения
            @client.on(DisconnectEvent)
            async def on_disconnect(event: DisconnectEvent):
                logger.info(f"Disconnected from {unique_id}")
            
            # Запускаем клиент с таймаутом
            await asyncio.wait_for(client.start(), timeout=300)  # 5 минут таймаут
            
        except asyncio.TimeoutError:
            logger.warning(f"Connection to {unique_id} timed out after 5 minutes")
        except Exception as e:
            error_message = str(e)
            # Логируем ошибку кратко, если это просто оффлайн-состояние
            if "is offline" in error_message:
                logger.info(f"{unique_id} is offline. Will retry in {check_online} seconds")
            else:
                logger.error(f"Error in monitoring {unique_id}: {error_message}")
        finally:
            # Явно освобождаем ресурсы клиента
            try:
                if client:
                    await client.stop()
            except:
                pass
        
        # Проверяем, не остановлен ли мониторинг
        if shutdown_event.is_set():
            break
        
        # Ждем перед повторным подключением
        logger.info(f"Attempting to reconnect to {unique_id} in {check_online} seconds")
        for _ in range(check_online):
            if shutdown_event.is_set():
                break
            await asyncio.sleep(1)

# Функция обновления списка отслеживаемых стримеров
async def update_streamers():
    while not shutdown_event.is_set():
        try:
            # Получаем список активных стримеров
            streamers = await get_active_streamers()
            logger.info(f"Found {len(streamers)} active streamers")
            
            # Определяем, каких стримеров нужно добавить или удалить
            current_ids = set(monitored_streams.keys())
            new_ids = set(s["unique_id"] for s in streamers)
            
            # Стримеры для добавления и удаления
            to_add = new_ids - current_ids
            to_remove = current_ids - new_ids
            
            # Удаляем стримеров
            for unique_id in to_remove:
                logger.info(f"Stopping monitoring for {unique_id}")
                task = monitored_streams.pop(unique_id, None)
                if task:
                    task.cancel()
            
            # Добавляем новых стримеров
            for streamer in streamers:
                if streamer["unique_id"] in to_add:
                    logger.info(f"Starting monitoring for {streamer['unique_id']}")
                    task = asyncio.create_task(monitor_streamer(streamer))
                    monitored_streams[streamer["unique_id"]] = task
        
        except Exception as e:
            logger.error(f"Error updating streamers list: {e}")
        
        # Проверяем каждые 60 секунд
        for _ in range(60):
            if shutdown_event.is_set():
                break
            await asyncio.sleep(1)

# Функция для периодической очистки кэша подарков
async def clean_gift_cache():
    while not shutdown_event.is_set():
        # Очищаем кэш каждые 6 часов
        await asyncio.sleep(6 * 60 * 60)
        logger.info(f"Cleaning gift cache, size before: {len(processed_gift_ids)}")
        processed_gift_ids.clear()
        logger.info("Gift cache cleared")

# Функция для graceful shutdown
async def shutdown():
    logger.info("Shutting down parser...")
    
    # Устанавливаем флаг завершения
    shutdown_event.set()
    
    # Отменяем все задачи мониторинга
    for task in monitored_streams.values():
        task.cancel()
    
    # Ждем завершения обработки очереди подарков
    logger.info(f"Waiting for {gift_queue.qsize()} gifts to be processed")
    if not gift_queue.empty():
        try:
            gift_queue.join()
        except Exception:
            pass
    
    # Закрываем пул соединений с базой данных
    if pool:
        logger.info("Closing database connection pool")
        await pool.close()
    
    logger.info("Shutdown completed")

# Главная функция
async def main():
    # Инициализируем обработчики сигналов для graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    
    # Инициализируем подключение к базе данных
    db_ready = await init_db()
    if not db_ready:
        logger.error("Failed to connect to database. Exiting.")
        return
    # Проверяем наличие файла tiktokers.txt и импортируем стримеров
    if os.path.exists('tiktokers.txt'):
        logger.info("Найден файл tiktokers.txt. Импортирую стримеров...")
        await import_streamers_from_file('tiktokers.txt')
    # Запускаем основные задачи
    tasks = [
        asyncio.create_task(process_gift_queue()),
        asyncio.create_task(update_streamers()),
        asyncio.create_task(clean_gift_cache())
    ]
    
    # Ждем завершения всех задач
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        logger.info("Main tasks cancelled")
    finally:
        await shutdown()

# Точка входа в программу
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")