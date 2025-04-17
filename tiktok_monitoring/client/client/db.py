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
    
    # async def get_active_streamers(self):
    #     """Получение списка активных стримеров"""
    #     query = """
    #     SELECT s.id, s.name, s.room_id, s.user_id, s.username, 
    #         c.name as cluster, s.check_online, s.last_check
    #     FROM streamers s
    #     JOIN clusters c ON s.cluster_id = c.id
    #     WHERE s.status = 'Запущен'
    #     """
        
    #     try:
    #         streamers = await self.fetch(query)
    #         result = []
            
    #         for s in streamers:
    #             # Определяем идентификатор для TikTokLive
    #             tiktok_id = None
    #             is_numeric_id = False
                
    #             # Приоритет: room_id > user_id > name
    #             if s['room_id'] and s['room_id'] > 0:
    #                 tiktok_id = str(s['room_id'])
    #                 is_numeric_id = True
    #             elif s['user_id'] and s['user_id'].strip():
    #                 tiktok_id = s['user_id']
    #                 is_numeric_id = not tiktok_id.startswith('@')
    #             else:
    #                 tiktok_id = s['name'] if s['name'].startswith('@') else f"@{s['name']}"
    #                 is_numeric_id = False
                    
    #             result.append({
    #                 "unique_id": tiktok_id,
    #                 "id": s['id'],
    #                 "cluster": s['cluster'],
    #                 "check_online": s['check_online'],
    #                 "is_numeric_id": is_numeric_id,
    #                 "room_id": s['room_id'],
    #                 "user_id": s['user_id'],
    #                 "username": s['username'],
    #                 "name": s['name'],
    #                 "last_check": s['last_check']
    #             })
            
    #         return result
    #     except Exception as e:
    #         logger.error(f"Error fetching streamers: {e}")
    #         return []
    async def get_active_streamers(self):
        """Получение списка активных стримеров"""
        query = """
        SELECT s.id, s.tik_tok_user_id, 
            t.name, t.user_id, t.tiktok_id,
            c.name as cluster, s.check_online, s.last_check, s.room_id, s.is_live
        FROM streamers s
        JOIN tik_tok_users t ON s.tik_tok_user_id = t.id
        JOIN clusters c ON s.cluster_id = c.id
        WHERE s.status = 'Запущен'
        """
        
        try:
            streamers = await self.fetch(query)
            result = []
            
            for s in streamers:
                # Определяем идентификатор для TikTokLive
                tiktok_id = None
                is_numeric_id = False
                
                # Приоритет: room_id > tiktok_id > user_id > name
                if s['room_id'] and s['room_id'] > 0:
                    tiktok_id = str(s['room_id'])
                    is_numeric_id = True
                elif s['tiktok_id'] and s['tiktok_id'].strip():
                    tiktok_id = s['tiktok_id']
                    is_numeric_id = not tiktok_id.startswith('@')
                elif s['user_id'] and s['user_id'].strip():
                    tiktok_id = s['user_id']
                    is_numeric_id = not tiktok_id.startswith('@')
                else:
                    tiktok_id = s['name'] if s['name'].startswith('@') else f"@{s['name']}"
                    is_numeric_id = False
                    
                result.append({
                    "id": s['id'],
                    "unique_id": tiktok_id,
                    "name": s['name'],  # Возвращаем имя пользователя (с @)
                    "user_id": s['user_id'],
                    "tiktok_id": s['tiktok_id'],
                    "tik_tok_user_id": s['tik_tok_user_id'],
                    "cluster": s['cluster'],
                    "check_online": s['check_online'],
                    "is_numeric_id": is_numeric_id,
                    "room_id": s['room_id'],
                    "is_live": s['is_live'],
                    "last_check": s['last_check']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error fetching streamers: {e}")
            return []
    async def update_streamer(self, streamer_id, room_id, user_id=None, tiktok_id=None):
        """Обновление данных стримера"""
        try:
            # Получаем связанный tik_tok_user_id
            tik_tok_user_id = await self.fetchval(
                "SELECT tik_tok_user_id FROM streamers WHERE id = $1",
                streamer_id
            )
            
            if not tik_tok_user_id:
                logger.error(f"No tik_tok_user_id found for streamer {streamer_id}")
                return
            
            # Преобразуем room_id в целое число
            room_id_int = 0
            if isinstance(room_id, str):
                room_id_int = int(room_id) if room_id.isdigit() else 0
            else:
                room_id_int = room_id if room_id else 0
            
            # Обновляем streamer
            streamer_query = """
            UPDATE streamers 
            SET room_id = $1, last_activity = NOW(), last_check = NOW(), is_live = TRUE 
            WHERE id = $2
            """
            
            await self.execute(streamer_query, room_id_int, streamer_id)
            
            # Обновляем данные в tik_tok_users
            tik_tok_query = "UPDATE tik_tok_users SET last_seen = NOW()"
            params = []
            
            if user_id:
                tik_tok_query += f", user_id = ${len(params) + 1}"
                params.append(user_id)
                
            if tiktok_id:
                tik_tok_query += f", tiktok_id = ${len(params) + 1}"
                params.append(tiktok_id)
                
            tik_tok_query += f" WHERE id = ${len(params) + 1}"
            params.append(tik_tok_user_id)
            
            await self.execute(tik_tok_query, *params)
            
            logger.info(f"Updated streamer ID {streamer_id} with room_id={room_id_int}, user_id={user_id}, tiktok_id={tiktok_id}")
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
    async def import_streamers_with_details(self, streamers, cluster_name='AGENCY', check_online=30):
        """Импорт стримеров с подробной информацией в базу данных"""
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
        for streamer_data in streamers:
            name = streamer_data.get('name', '')
            room_id = streamer_data.get('room_id', 0)
            user_id = streamer_data.get('user_id', '')
            username = streamer_data.get('username', '')
            
            # Определяем условие поиска существующего стримера
            where_conditions = []
            where_params = []
            
            if name:
                where_conditions.append(f"name = ${len(where_params) + 1}")
                where_params.append(name)
            
            if room_id and room_id > 0:
                where_conditions.append(f"room_id = ${len(where_params) + 1}")
                where_params.append(room_id)
                
            if user_id:
                where_conditions.append(f"user_id = ${len(where_params) + 1}")
                where_params.append(user_id)
            
            if not where_conditions:
                logger.warning(f"Skipping streamer with no identifiable data: {streamer_data}")
                continue
                
            where_clause = " OR ".join(where_conditions)
            
            # Проверяем, есть ли стример в базе
            existing = None
            if where_params:
                existing_query = f"SELECT id FROM streamers WHERE {where_clause}"
                existing = await self.fetchrow(existing_query, *where_params)
            
            if not existing:
                # Добавляем нового стримера
                insert_fields = ["cluster_id", "status", "check_online"]
                insert_values = [cluster_id, 'Запущен', check_online]
                
                # Добавляем другие поля
                if name:
                    insert_fields.append("name")
                    insert_values.append(name)
                
                if room_id and room_id > 0:
                    insert_fields.append("room_id")
                    insert_values.append(room_id)
                    
                if user_id:
                    insert_fields.append("user_id")
                    insert_values.append(user_id)
                    
                if username:
                    insert_fields.append("username")
                    insert_values.append(username)
                
                # Формируем запрос
                placeholders = [f"${i+1}" for i in range(len(insert_values))]
                insert_query = f"""
                INSERT INTO streamers ({', '.join(insert_fields)}) 
                VALUES ({', '.join(placeholders)}) RETURNING id
                """
                
                streamer_id = await self.fetchval(insert_query, *insert_values)
                logger.info(f"Добавлен новый стример: {name or user_id or room_id}")
            else:
                # Обновляем статус существующего стримера
                update_fields = ["status = 'Запущен'", "cluster_id = $1", "check_online = $2"]
                update_values = [cluster_id, check_online]
                
                # Добавляем обновления для других полей
                if room_id and room_id > 0:
                    update_fields.append(f"room_id = ${len(update_values) + 1}")
                    update_values.append(room_id)
                    
                if user_id:
                    update_fields.append(f"user_id = ${len(update_values) + 1}")
                    update_values.append(user_id)
                    
                if username:
                    update_fields.append(f"username = ${len(update_values) + 1}")
                    update_values.append(username)
                
                # Добавляем ID в конец
                update_values.append(existing['id'])
                
                # Формируем запрос
                update_query = f"""
                UPDATE streamers 
                SET {', '.join(update_fields)}
                WHERE id = ${len(update_values)}
                """
                
                await self.execute(update_query, *update_values)
                logger.info(f"Обновлен существующий стример: {name or user_id or room_id}")
    async def get_or_create_tiktok_user(self, name, user_id=None, tiktok_id=None):
        """Получение или создание пользователя TikTok"""
        try:
            # Проверяем, существует ли пользователь с таким именем или user_id
            query = "SELECT id FROM tik_tok_users WHERE "
            params = []
            
            conditions = []
            if name:
                conditions.append(f"name = ${len(params) + 1}")
                params.append(name)
            
            if user_id:
                conditions.append(f"user_id = ${len(params) + 1}")
                params.append(user_id)
                
            if tiktok_id:
                conditions.append(f"tiktok_id = ${len(params) + 1}")
                params.append(tiktok_id)
                
            if not conditions:
                logger.error("No valid identifiers provided for TikTok user lookup")
                return None
                
            query += " OR ".join(conditions)
            
            # Выполняем запрос
            existing = await self.fetchrow(query, *params)
            
            if existing:
                # Обновляем данные пользователя
                update_query = """
                UPDATE tik_tok_users SET last_seen = NOW()
                """
                update_params = []
                
                # Если предоставлены дополнительные данные, обновляем их
                if user_id and name:
                    update_query += f", user_id = ${len(update_params) + 1}"
                    update_params.append(user_id)
                    
                if tiktok_id and name:
                    update_query += f", tiktok_id = ${len(update_params) + 1}"
                    update_params.append(tiktok_id)
                    
                # Добавляем условие WHERE
                update_query += f" WHERE id = ${len(update_params) + 1} RETURNING id"
                update_params.append(existing['id'])
                
                # Выполняем обновление и возвращаем ID
                return await self.fetchval(update_query, *update_params)
            else:
                # Создаем нового пользователя
                insert_query = """
                INSERT INTO tik_tok_users (name, user_id, tiktok_id) 
                VALUES ($1, $2, $3) RETURNING id
                """
                return await self.fetchval(insert_query, name, user_id, tiktok_id)
                
        except Exception as e:
            logger.error(f"Error getting or creating TikTok user: {e}")
            return None

    async def update_tiktok_user(self, user_id, data):
        """Обновление данных пользователя TikTok"""
        try:
            if not user_id:
                logger.error("No user_id provided for TikTok user update")
                return False
                
            # Формируем запрос и параметры
            update_query = "UPDATE tik_tok_users SET "
            update_parts = []
            params = []
            
            for key, value in data.items():
                if key in ['name', 'user_id', 'tiktok_id', 'followers_count', 'following_count', 'likes_count', 'is_verified']:
                    update_parts.append(f"{key} = ${len(params) + 1}")
                    params.append(value)
                    
            if not update_parts:
                logger.warning("No valid fields to update for TikTok user")
                return False
                
            # Добавляем обновление last_seen
            update_parts.append("last_seen = NOW()")
            
            # Собираем запрос
            update_query += ", ".join(update_parts)
            update_query += f" WHERE id = ${len(params) + 1}"
            params.append(user_id)
            
            # Выполняем запрос
            await self.execute(update_query, *params)
            return True
                
        except Exception as e:
            logger.error(f"Error updating TikTok user data: {e}")
            return False

    async def get_tiktok_user_by_name(self, name):
        """Получение пользователя TikTok по имени"""
        try:
            query = "SELECT * FROM tik_tok_users WHERE name = $1"
            return await self.fetchrow(query, name)
        except Exception as e:
            logger.error(f"Error getting TikTok user by name: {e}")
            return None

    async def get_tiktok_user_by_user_id(self, user_id):
        """Получение пользователя TikTok по ID пользователя"""
        try:
            query = "SELECT * FROM tik_tok_users WHERE user_id = $1"
            return await self.fetchrow(query, user_id)
        except Exception as e:
            logger.error(f"Error getting TikTok user by user_id: {e}")
            return None