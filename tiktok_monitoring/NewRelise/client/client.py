# client/client.py
import asyncio
import json

import aiohttp
from aiohttp import web
from data_sync import DataSynchronizer
from gift_processor import GiftProcessor
from logger import logger
from shared_state import SharedState
from stream_monitor import StreamMonitor
from streamer_manager import StreamerManager
from TikTokLive.client.web.web_settings import WebDefaults


class TikTokMonitor:
    def __init__(self, db, api_key=None):
        # Инициализация общего состояния
        self.db = db
        self.api_key = api_key
        self.state = SharedState(db, api_key)

        # Инициализация компонентов
        self.gift_processor = GiftProcessor(db, self.state)
        self.data_sync = DataSynchronizer(db, self.state)
        self.stream_monitor = StreamMonitor(
            db, self.gift_processor, self.state, None
        )  # Временно None
        self.streamer_manager = StreamerManager(db, self.state, self.stream_monitor)

        # Устанавливаем связь stream_monitor с streamer_manager
        self.stream_monitor.streamer_manager = self.streamer_manager

        # Настройка API ключа для TikTokLive
        if api_key:
            WebDefaults.tiktok_sign_api_key = api_key
        else:
            logger.warning("No TikTokLive API key provided, connections may be limited")

    async def start(self):
        """Запуск мониторинга - только API сервер и процессор подарков"""
        self.tasks = []  # Очищаем список задач

        # Запускаем API сервер для вебхуков
        api_task = asyncio.create_task(self.start_api_server())
        self.tasks.append(api_task)

        # Запускаем процессор подарков
        gift_tasks = await self.gift_processor.start()
        self.tasks.extend(gift_tasks)

        # Запускаем только синхронизацию подарков (не проверяем стримеров)
        sync_task = asyncio.create_task(self.data_sync._schedule_periodic_sync())
        self.tasks.append(sync_task)

        logger.info("Мониторинг TikTok webhook успешно начат")
        logger.info(
            "Ожидание обратных вызовов веб-перехватчика для запуска/остановки мониторинга потока"
        )

        # Ожидаем завершения всех задач
        await asyncio.gather(*self.tasks)

    async def start_api_server(self):
        """Запуск API сервера для приема вебхуков"""
        app = web.Application()
        app.router.add_post("/api/stream", self.handle_stream_webhook)

        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, "0.0.0.0", 8081)
        await self.site.start()
        logger.info("API server started on port 8081")

        # Держим сервер запущенным до сигнала завершения
        while not self.state.shutdown_event.is_set():
            await asyncio.sleep(1)

        # Корректное завершение сервера
        await runner.cleanup()

    async def handle_stream_webhook(self, request):
        """Обработчик вебхуков о стримах"""
        try:
            data = await request.json()

            # Извлекаем данные
            room_info = data.get("data", {}).get("room_info", {})
            user_info = data.get("data", {}).get("user", {})

            unique_id = user_info.get("unique_id")
            room_id = room_info.get("id")
            numeric_uid = user_info.get("numeric_uid")
            is_live = room_info.get("is_live")
            status = room_info.get("status")
            info_data = {
                "unique_id": unique_id,
                "room_id": room_id,
                "numeric_uid": numeric_uid,
                "is_live": is_live,
                "status": status,
            }
            logger.info(json.dumps(info_data, indent=4, ensure_ascii=False))
            if not unique_id or not room_id:
                return web.json_response(
                    {"status": "error", "message": "Отсутствуют unique_id или room_id"},
                    status=400,
                )

            # Решаем, запускать или останавливать мониторинг
            if status == 2 and is_live == True:
                # Сначала обновляем данные в БД
                streamer_info = await self._update_streamer_data(
                    unique_id, room_id, numeric_uid
                )

                if streamer_info:
                    # Передаем управление стримером монитору
                    success = await self.stream_monitor.start_monitoring(streamer_info)

                    return web.json_response(
                        {
                            "status": "ok" if success else "error",
                            "message": f"Мониторинг {'запущен' if success else 'не удалось запустить'}",
                        }
                    )
                else:
                    return web.json_response(
                        {
                            "status": "error",
                            "message": "Ошибка обновления данных стримера",
                        }
                    )

            elif status == 4 and is_live == False:
                # Делегируем остановку мониторинга
                success = await self.stream_monitor.stop_monitoring(unique_id, room_id)

                return web.json_response(
                    {
                        "status": "ok" if success else "error",
                        "message": f"Мониторинг {'остановлен' if success else 'не удалось остановить'}",
                    }
                )
            else:
                return web.json_response(
                    {"status": "ok", "message": "Обновление статуса"}
                )

        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {e}", exc_info=True)
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def _update_streamer_data(self, unique_id, room_id, numeric_uid):
        """Обновление данных стримера в БД - ответственность TikTokMonitor"""
        try:
            # Преобразуем комнату в int
            room_id_int = int(room_id) if room_id else None

            # Определяем имя пользователя
            user_name = f"@{unique_id}" if not unique_id.startswith("@") else unique_id

            # Обработка TikTok пользователя
            tik_tok_user_id = await self.db.get_or_create_tiktok_user(
                user_name, str(numeric_uid), unique_id.lstrip("@")
            )

            if not tik_tok_user_id:
                logger.error(f"Ошибка создания TikTok пользователя для {unique_id}")
                return None

            # Получаем или создаем стримера
            streamer = await self.db.fetchrow(
                "SELECT id, cluster_id FROM streamers WHERE tik_tok_user_id = $1",
                tik_tok_user_id,
            )

            # Получаем кластер
            cluster_id = None
            if streamer:
                streamer_id = streamer["id"]
                cluster_id = streamer["cluster_id"]

                # Обновляем стримера
                await self.db.execute(
                    """
                    UPDATE streamers 
                    SET room_id = $1, status = 'Запущен', is_live = TRUE, 
                        last_activity = NOW(), last_check = NOW()
                    WHERE id = $2
                    """,
                    room_id_int,
                    streamer_id,
                )
            else:
                # Получаем дефолтный кластер
                cluster_id = await self.db.fetchval(
                    "SELECT id FROM clusters WHERE name = 'AGENCY' LIMIT 1"
                )

                if not cluster_id:
                    cluster_id = await self.db.fetchval(
                        "INSERT INTO clusters (name) VALUES ('AGENCY') RETURNING id"
                    )

                # Создаем стримера
                streamer_id = await self.db.fetchval(
                    """
                    INSERT INTO streamers 
                    (tik_tok_user_id, room_id, status, is_live, last_activity, last_check, cluster_id) 
                    VALUES ($1, $2, 'Запущен', TRUE, NOW(), NOW(), $3)
                    RETURNING id
                    """,
                    tik_tok_user_id,
                    room_id_int,
                    cluster_id,
                )

            # Обновляем маппинг комнаты
            if room_id_int and tik_tok_user_id:
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

            # Обновляем запись о стриме
            if streamer_id:
                existing_stream = await self.db.fetchrow(
                    "SELECT id FROM streams WHERE streamer_id = $1 AND end_time IS NULL",
                    streamer_id,
                )

                if existing_stream:
                    await self.db.execute(
                        "UPDATE streams SET room_id = $1, updated_at = NOW() WHERE id = $2",
                        room_id_int,
                        existing_stream["id"],
                    )
                else:
                    await self.db.fetchval(
                        """
                        INSERT INTO streams (streamer_id, tik_tok_user_id, room_id, start_time)
                        VALUES ($1, $2, $3, NOW()) RETURNING id
                        """,
                        streamer_id,
                        tik_tok_user_id,
                        room_id_int,
                    )

            # Получаем имя кластера
            cluster_name = (
                await self.db.fetchval(
                    "SELECT name FROM clusters WHERE id = $1", cluster_id
                )
                or "AGENCY"
            )

            # Возвращаем информацию для мониторинга
            return {
                "id": streamer_id,
                "unique_id": unique_id,
                "tik_tok_user_id": tik_tok_user_id,
                "room_id": room_id_int,
                "cluster": cluster_name,
                "check_online": 30,
                "numeric_uid": numeric_uid,
            }

        except Exception as e:
            logger.error(f"Ошибка обновления данных стримера: {e}", exc_info=True)
            return None

    async def _handle_stream_start(self, unique_id, room_id, numeric_uid):
        """Обработка начала стрима"""
        logger.info(
            f"Handling stream start: {unique_id} (room_id: {room_id}, user_id: {numeric_uid})"
        )
        try:
            # Преобразуем room_id в BIGINT, если это возможно
            room_id_int = None
            if room_id:
                try:
                    room_id_int = int(room_id)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert room_id to integer: {room_id}")

            # Определяем имя пользователя с @ в начале
            user_name = f"@{unique_id}" if not unique_id.startswith("@") else unique_id

            # 1. Ищем стримера сначала по numeric_uid (приоритет)
            streamer = None
            if numeric_uid:
                streamer = await self.db.fetchrow(
                    """
                    SELECT s.id, s.tik_tok_user_id, s.cluster_id
                    FROM streamers s
                    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                    WHERE ttu.user_id = $1
                    """,
                    str(numeric_uid),
                )

                if streamer:
                    logger.info(f"Найден стример по numeric_uid: {numeric_uid}")

            # 2. Если не нашли по numeric_uid, ищем по unique_id
            if not streamer:
                logger.info(f"Не найден стример по numeric_uid: {numeric_uid}")
                # streamer = await self.db.fetchrow(
                #     """
                #     SELECT s.id, s.tik_tok_user_id, s.cluster_id
                #     FROM streamers s
                #     JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                #     WHERE ttu.name = $1 OR ttu.tiktok_id = $2
                #     """,
                #     user_name,
                #     unique_id.lstrip("@"),  # Убираем @ если он есть
                # )

                # if streamer:
                #     logger.info(f"Found streamer by unique_id: {unique_id}")

            # # 3. Если до сих пор не нашли, ищем по room_id
            # if not streamer and room_id_int:
            #     streamer = await self.db.fetchrow(
            #         """
            #         SELECT s.id, s.tik_tok_user_id, s.cluster_id
            #         FROM streamers s
            #         WHERE s.room_id = $1
            #         """,
            #         room_id_int,
            #     )

            #     if streamer:
            #         logger.info(f"Found streamer by room_id: {room_id}")

            streamer_id = None
            tik_tok_user_id = None
            cluster_id = None

            if streamer:
                # Используем найденного стримера
                streamer_id = streamer["id"]
                tik_tok_user_id = streamer["tik_tok_user_id"]
                cluster_id = streamer["cluster_id"]

                # Обновляем данные стримера
                await self.db.execute(
                    """
                    UPDATE streamers 
                    SET room_id = $1, status = 'Запущен', is_live = TRUE, 
                        last_activity = NOW(), last_check = NOW()
                    WHERE id = $2
                    """,
                    room_id_int,
                    streamer_id,
                )

                # Обновляем маппинг room_id
                if room_id_int and tik_tok_user_id:
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

                # Обновляем пользователя TikTok с numeric_uid, если он был передан
                if numeric_uid:
                    await self.db.execute(
                        """
                        UPDATE tik_tok_users
                        SET user_id = $1, last_seen = NOW()
                        WHERE id = $2 AND (user_id IS NULL OR user_id != $1)
                        """,
                        str(numeric_uid),
                        tik_tok_user_id,
                    )

                logger.info(
                    f"Updated existing streamer with ID {streamer_id} for {unique_id}"
                )
            # else:
            #     # Если стример не найден, получаем или создаем пользователя TikTok
            #     # Проверяем существующего пользователя с учетом numeric_uid
            #     if numeric_uid:
            #         tik_tok_user = await self.db.fetchrow(
            #             "SELECT id FROM tik_tok_users WHERE user_id = $1",
            #             str(numeric_uid),
            #         )

            #         if tik_tok_user:
            #             tik_tok_user_id = tik_tok_user["id"]

            #             # Обновляем данные пользователя
            #             await self.db.execute(
            #                 """
            #                 UPDATE tik_tok_users
            #                 SET name = $1, tiktok_id = $2, last_seen = NOW()
            #                 WHERE id = $3
            #                 """,
            #                 user_name,
            #                 unique_id.lstrip("@"),
            #                 tik_tok_user_id,
            #             )

            #             logger.info(
            #                 f"Updated existing TikTok user with ID {tik_tok_user_id}"
            #             )
            #         else:
            #             # Создаем нового пользователя
            #             tik_tok_user_id = await self.db.fetchval(
            #                 """
            #                 INSERT INTO tik_tok_users (name, user_id, tiktok_id, first_seen, last_seen)
            #                 VALUES ($1, $2, $3, NOW(), NOW())
            #                 RETURNING id
            #                 """,
            #                 user_name,
            #                 str(numeric_uid),
            #                 unique_id.lstrip("@"),
            #             )

            #             logger.info(
            #                 f"Created new TikTok user with ID {tik_tok_user_id}"
            #             )
            #     else:
            #         # Если numeric_uid не был предоставлен, используем обычный метод get_or_create
            #         tik_tok_user_id = await self.db.get_or_create_tiktok_user(
            #             user_name, None, unique_id.lstrip("@")
            #         )

            #     if not tik_tok_user_id:
            #         logger.error(
            #             f"Failed to create or find TikTok user for {unique_id}"
            #         )
            #         return False

            #     # Получаем кластер AGENCY
            #     cluster_id = await self.db.fetchval(
            #         "SELECT id FROM clusters WHERE name = 'AGENCY' LIMIT 1"
            #     )

            #     if not cluster_id:
            #         logger.warning("AGENCY cluster not found, creating it")
            #         cluster_id = await self.db.fetchval(
            #             "INSERT INTO clusters (name) VALUES ('AGENCY') RETURNING id"
            #         )

            #     # Создаем стримера
            #     streamer_id = await self.db.fetchval(
            #         """
            #         INSERT INTO streamers
            #         (tik_tok_user_id, room_id, status, is_live, last_activity, last_check, cluster_id)
            #         VALUES ($1, $2, 'Запущен', TRUE, NOW(), NOW(), $3)
            #         RETURNING id
            #         """,
            #         tik_tok_user_id,
            #         room_id_int,
            #         cluster_id,
            #     )

            #     if room_id_int:
            #         # Создаем маппинг room_id
            #         await self.db.execute(
            #             """
            #             INSERT INTO room_id_mapping (room_id, tik_tok_user_id)
            #             VALUES ($1, $2)
            #             ON CONFLICT (room_id) DO NOTHING
            #             """,
            #             room_id_int,
            #             tik_tok_user_id,
            #         )

            #     logger.info(
            #         f"Created new streamer with ID {streamer_id} for {unique_id}"
            #     )

            # 4. Создаем или обновляем запись о стриме
            if streamer_id:
                # Проверяем, есть ли уже активный стрим
                existing_stream = await self.db.fetchrow(
                    """
                    SELECT id FROM streams 
                    WHERE streamer_id = $1 AND end_time IS NULL
                    """,
                    streamer_id,
                )

                if existing_stream:
                    stream_id = existing_stream["id"]
                    # Обновляем запись существующего стрима
                    await self.db.execute(
                        """
                        UPDATE streams
                        SET room_id = $1, updated_at = NOW()
                        WHERE id = $2
                        """,
                        room_id_int,
                        stream_id,
                    )
                    logger.info(f"Updated existing stream record with ID {stream_id}")
                else:
                    # Создаем новый стрим
                    stream_id = await self.db.fetchval(
                        """
                        INSERT INTO streams 
                        (streamer_id, tik_tok_user_id, room_id, start_time)
                        VALUES ($1, $2, $3, NOW())
                        RETURNING id
                        """,
                        streamer_id,
                        tik_tok_user_id,
                        room_id_int,
                    )
                    logger.info(
                        f"Created new stream record with ID {stream_id} for {unique_id}"
                    )

            # 5. Получаем имя кластера
            cluster_name = (
                await self.db.fetchval(
                    "SELECT name FROM clusters WHERE id = $1", cluster_id
                )
                if cluster_id
                else "AGENCY"
            )

            # 6. Запускаем мониторинг, если этот стример еще не отслеживается
            if unique_id not in self.state.monitored_streams:
                # Формируем информацию о стримере для мониторинга
                streamer_info = {
                    "id": streamer_id,
                    "unique_id": unique_id,
                    "tik_tok_user_id": tik_tok_user_id,
                    "room_id": room_id_int,
                    "cluster": cluster_name,
                    "check_online": 30,  # Интервал проверки
                    "is_live": True,
                    "is_numeric_id": False,
                    "name": user_name,
                    "numeric_uid": numeric_uid,  # Добавляем numeric_uid для использования в stream_monitor
                }

                # Запускаем задачу мониторинга
                task = asyncio.create_task(
                    self.stream_monitor._monitor_streamer(streamer_info)
                )
                self.state.monitored_streams[unique_id] = task
                logger.info(f"Started monitoring for {unique_id} (room_id: {room_id})")
            else:
                logger.info(f"Streamer {unique_id} is already being monitored")

            return True

        except Exception as e:
            logger.error(f"Error handling stream start: {e}", exc_info=True)
            return False

    async def _handle_stream_end(self, unique_id, room_id):
        """Обработка окончания стрима"""
        logger.info(f"Handling stream end: {unique_id} (room_id: {room_id})")
        try:
            # Преобразуем room_id в BIGINT
            room_id_int = None
            if room_id:
                try:
                    room_id_int = int(room_id)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert room_id to integer: {room_id}")

            # 1. Получаем ID стримера
            user_name = f"@{unique_id}" if not unique_id.startswith("@") else unique_id

            streamer = await self.db.fetchrow(
                """
                SELECT s.id
                FROM streamers s
                JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                WHERE ttu.name = $1 OR ttu.tiktok_id = $2 OR s.room_id = $3
                """,
                user_name,
                unique_id.lstrip("@"),
                room_id_int,
            )

            if streamer:
                streamer_id = streamer["id"]

                # 2. Обновляем статус стримера
                await self.db.execute(
                    """
                    UPDATE streamers
                    SET is_live = FALSE, last_activity = NOW(), last_check = NOW()
                    WHERE id = $1
                    """,
                    streamer_id,
                )

                # 3. Закрываем запись стрима
                await self.db.execute(
                    """
                    UPDATE streams
                    SET end_time = NOW(),
                        duration = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER,
                        updated_at = NOW()
                    WHERE streamer_id = $1 AND end_time IS NULL
                    """,
                    streamer_id,
                )

                logger.info(f"Updated stream end for streamer ID {streamer_id}")
            else:
                # Если не нашли по имени и ID, попробуем найти по room_id
                if room_id_int:
                    stream = await self.db.fetchrow(
                        """
                        SELECT id, streamer_id
                        FROM streams
                        WHERE room_id = $1 AND end_time IS NULL
                        """,
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
                            """
                            UPDATE streamers
                            SET is_live = FALSE, last_activity = NOW(), last_check = NOW()
                            WHERE id = $1
                            """,
                            stream["streamer_id"],
                        )

                        logger.info(
                            f"Updated stream end by room_id {room_id} for stream ID {stream['id']}"
                        )

            # 4. Останавливаем задачу мониторинга
            if unique_id in self.state.monitored_streams:
                task = self.state.monitored_streams.pop(unique_id)
                if task and not task.done():
                    task.cancel()
                    logger.info(f"Cancelled monitoring task for {unique_id}")

            return True

        except Exception as e:
            logger.error(f"Error handling stream end: {e}", exc_info=True)
            return False

    async def stop(self):
        """Остановка мониторинга"""
        logger.info("Shutting down parser...")

        # Устанавливаем флаг завершения
        self.state.shutdown_event.set()

        # Отменяем все задачи мониторинга
        for task in self.state.monitored_streams.values():
            task.cancel()

        # Ждем завершения обработки очереди подарков
        logger.info(
            f"Waiting for {self.gift_processor.gift_queue.qsize()} gifts to be processed"
        )

        # Ждем до 5 секунд для обработки оставшихся подарков
        try:
            for _ in range(50):  # 5 секунд (50 * 0.1)
                if self.gift_processor.gift_queue.empty():
                    break
                await asyncio.sleep(0.1)
        except Exception:
            pass

        logger.info("Monitor shutdown completed")

    # Проксируем методы из других классов для поддержания обратной совместимости
    async def sync_gift_streamers(self):
        return await self.data_sync.sync_gift_streamers()

    async def debug_tiktok_connection(self, username):
        return await self.streamer_manager.debug_tiktok_connection(username)
