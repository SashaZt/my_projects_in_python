# client/db.py
import asyncpg
from logger import logger
import os
from datetime import datetime


class Database:
    def __init__(self, config=None):
        self.config = config or {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "user": os.getenv("POSTGRES_USER", "user_bd"),
            "password": os.getenv("POSTGRES_PASSWORD", "password"),
            "database": os.getenv("POSTGRES_DB", "tiktok_monitoring")
        }
        self.pool = None
        
    async def connect(self):
        """Подключение к базе данных PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(**self.config)
            logger.info("Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return False
    
    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")
    
    async def execute(self, query, *args):
        """Выполнение SQL-запроса"""
        if not self.pool:
            logger.error("Database not connected")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None
    
    async def fetch(self, query, *args):
        """Получение данных из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return []
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return []
    
    async def fetchval(self, query, *args):
        """Получение одного значения из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Database fetchval error: {e}")
            return None
    
    async def fetchrow(self, query, *args):
        """Получение одной строки из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Database fetchrow error: {e}")
            return None
    
    async def executemany(self, query, args):
        """Пакетное выполнение запросов"""
        if not self.pool:
            logger.error("Database not connected")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    return await conn.executemany(query, args)
        except Exception as e:
            logger.error(f"Database executemany error: {e}")
            return None
    
    async def get_active_streamers(self):
        """Получение списка активных стримеров"""
        query = """
        SELECT s.name, s.id, c.name as cluster, s.check_online 
        FROM streamers s
        JOIN clusters c ON s.cluster_id = c.id
        WHERE s.status = 'Запущен'
        """
        
        try:
            streamers = await self.fetch(query)
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
    
    async def update_streamer(self, streamer_id, room_id):
        """Обновление данных стримера"""
        try:
            # Проверяем тип room_id - строка или число
            if isinstance(room_id, str):
                # Если строка - проверяем, можно ли преобразовать в число
                user_id = int(room_id) if room_id.isdigit() else 0
            else:
                # Если уже число - используем как есть
                user_id = room_id
            
            query = """
            UPDATE streamers 
            SET user_id = $1, last_activity = NOW() 
            WHERE id = $2
            """
            
            await self.execute(query, user_id, streamer_id)
        except Exception as e:
            logger.error(f"Error updating streamer data: {e}")
    
    async def save_gifts_batch(self, gifts_batch):
        """Сохранение пакета подарков в базу"""
        if not gifts_batch:
            return
            
        query = """
        INSERT INTO gifts 
        (event_time, user_id, unique_id, follow_role, is_new_gifter, 
        top_gifter_rank, diamond_count, gift_name, gift_count, 
        receiver_user_id, receiver_unique_id) 
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
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
        
        await self.executemany(query, values)
        logger.info(f"Saved {len(gifts_batch)} gifts to database")
    
    async def import_streamers(self, streamers, cluster_name='AGENCY', check_online=30):
        """Импорт стримеров в базу данных"""
        if not streamers:
            return
            
        # Получаем ID кластера
        cluster = await self.fetchrow("SELECT id FROM clusters WHERE name = $1", cluster_name)
        
        if not cluster:
            # Создаем кластер, если его нет
            logger.info(f"Создание кластера '{cluster_name}'")
            cluster_id = await self.fetchval(
                "INSERT INTO clusters (name) VALUES ($1) RETURNING id", 
                cluster_name
            )
        else:
            cluster_id = cluster['id']
        
        # Добавляем стримеров в базу данных
        for streamer_name in streamers:
            formatted_name = streamer_name if streamer_name.startswith('@') else f"@{streamer_name}"
            
            # Проверяем, есть ли стример в базе
            existing = await self.fetchrow(
                "SELECT id FROM streamers WHERE name = $1", 
                formatted_name
            )
            
            if not existing:
                # Добавляем нового стримера
                streamer_id = await self.fetchval(
                    """
                    INSERT INTO streamers (name, cluster_id, status, check_online) 
                    VALUES ($1, $2, $3, $4) RETURNING id
                    """,
                    formatted_name,
                    cluster_id,
                    'Запущен',
                    check_online
                )
                logger.info(f"Добавлен новый стример: {formatted_name}")
            else:
                # Обновляем статус существующего стримера
                await self.execute(
                    """
                    UPDATE streamers 
                    SET status = 'Запущен', cluster_id = $1, check_online = $2
                    WHERE id = $3
                    """,
                    cluster_id,
                    check_online,
                    existing['id']
                )
                logger.info(f"Обновлен существующий стример: {formatted_name}")