# client/data_sync.py
import asyncio

from logger import logger


class DataSynchronizer:
    def __init__(self, db, shared_state):
        self.db = db
        self.shared_state = shared_state

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
            # logger.info(
            #     # f"Synchronized gifts with streamers by room_id mapping: {result4}"
            # )

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

    # закрыл, проверю в необходимости
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
            # logger.info(f"Updated TikTok user_ids: {result}")

            return True
        except Exception as e:
            logger.error(f"Error syncing TikTok IDs: {e}")
            return False

    async def _schedule_periodic_sync(self):
        """Периодическая синхронизация подарков и стримеров"""
        while not self.shared_state.shutdown_event.is_set():

            try:
                await self.sync_gift_streamers()
            except Exception as e:
                logger.error(f"Error in periodic gift sync: {e}")

            # Синхронизируем каждую минуту чтобы не пропустить подарки
            await asyncio.sleep(60)
