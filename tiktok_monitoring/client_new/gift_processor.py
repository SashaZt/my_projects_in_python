# client/gift_processor.py
import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from queue import Queue

from logger import logger


class GiftProcessor:
    def __init__(self, db, shared_state):
        self.db = db
        self.gift_queue = Queue(maxsize=5000)
        self.shared_state = shared_state
        self.active_streamers = {}  # словарь {tik_tok_user_id: latest_room_id}
        # Упрощаем структуру - убираем ненужные кэши
        self.room_id_cache = (
            {}
        )  # Для быстрого поиска по room_id: {room_id: tik_tok_user_id}

    async def start(self):
        """Запускает обработчик подарков"""
        # Инициализируем кэш room_id при старте
        await self._init_room_id_cache()

        # Запускаем только основную задачу обработки подарков
        gift_queue_task = asyncio.create_task(self._process_gift_queue())

        # Задача обновления кэша (с меньшей частотой)
        cache_update_task = asyncio.create_task(self._periodic_cache_update())

        return [gift_queue_task, cache_update_task]

    async def _init_room_id_cache(self):
        """Инициализирует кэш room_id -> tik_tok_user_id"""
        try:
            # Получаем активные маппинги комнат
            mappings = await self.db.fetch(
                """
                SELECT room_id, tik_tok_user_id 
                FROM room_id_mapping
                ORDER BY last_updated DESC
                """
            )

            # Собираем кэш
            for mapping in mappings:
                room_id = mapping["room_id"]
                tik_tok_user_id = mapping["tik_tok_user_id"]
                self.room_id_cache[room_id] = tik_tok_user_id

            logger.info(
                f"Initialized room ID cache with {len(self.room_id_cache)} entries"
            )

            # Собираем также активных стримеров
            active_streamers = await self.db.fetch(
                """
                SELECT s.tik_tok_user_id, s.room_id
                FROM streamers s 
                WHERE s.is_live = TRUE AND s.room_id IS NOT NULL
                """
            )

            for streamer in active_streamers:
                tik_tok_user_id = streamer["tik_tok_user_id"]
                room_id = streamer["room_id"]
                self.active_streamers[tik_tok_user_id] = room_id

            logger.info(
                f"Initialized active streamers cache with {len(self.active_streamers)} entries"
            )

        except Exception as e:
            logger.error(f"Error initializing room ID cache: {e}")

    async def _periodic_cache_update(self):
        """Периодически обновляет кэши (с низкой частотой)"""
        while not self.shared_state.shutdown_event.is_set():
            try:
                # Обновляем кэш раз в час вместо каждых 5 минут
                await asyncio.sleep(3600)  # 1 час

                # Обновляем кэш room_id
                await self._init_room_id_cache()

                # Закрываем только стримы, которые очень старые (больше суток)
                # Это просто страховка на случай пропущенных вебхуков
                current_time = datetime.now(timezone.utc)
                one_day_ago = current_time - timedelta(days=1)

                closed_streams = await self.db.execute(
                    """
                    UPDATE streams
                    SET end_time = $1
                    WHERE end_time IS NULL 
                    AND start_time < $2
                    RETURNING id
                    """,
                    current_time,
                    one_day_ago,
                )

                if closed_streams:
                    logger.info(
                        f"Closed {len(closed_streams)} orphaned stream sessions (older than 1 day)"
                    )

            except Exception as e:
                logger.error(f"Error updating caches: {e}")
                await asyncio.sleep(300)  # При ошибке ждем 5 минут

    async def _process_gift(self, event, unique_id, cluster):
        """Обработка подарка с упрощенной логикой"""
        try:
            # Получаем room_id из события - это ключевой параметр
            client_room_id = getattr(event, "room_id", None)

            # Базовая обработка подарка
            gift = getattr(event, "gift", None)
            user = getattr(event, "user", getattr(event, "from_user", None))

            if not gift or not user:
                logger.warning(f"Недопустимые данные подарка для {unique_id}")
                return

            # Извлекаем основные данные подарка
            if isinstance(gift, dict):
                gift_id = gift.get("id")
                diamond_count = gift.get("diamond_count", 0)
                gift_name = gift.get("name", "Unknown Gift")
                gift_count = max(
                    1, gift.get("combo_count", 1), gift.get("repeat_count", 1)
                )
            else:
                gift_id = getattr(gift, "id", None)
                diamond_count = getattr(gift, "diamond_count", 0)
                gift_name = getattr(gift, "name", "Unknown Gift")
                gift_count = max(
                    1, getattr(gift, "combo_count", 1), getattr(gift, "repeat_count", 1)
                )

            # Данные пользователя
            if isinstance(user, dict):
                user_id = user.get("id", "0")
                user_unique_id = user.get("unique_id", f"user_{user_id}")
            else:
                user_id = getattr(user, "id", "0")
                user_unique_id = getattr(user, "unique_id", f"user_{user_id}")

            # Показываем базовую информацию
            logger.info(
                f"Подарок: {gift_name} x{gift_count} ({diamond_count} diamonds) от {user_unique_id} для {unique_id}"
            )

            # Находим стримера - ПРЯМОЙ ПОДХОД через room_id
            streamer_data = None

            if client_room_id:
                # Сначала пробуем из кэша для максимальной скорости
                if client_room_id in self.room_id_cache:
                    tik_tok_user_id = self.room_id_cache[client_room_id]

                    # Получаем streamer_id
                    streamer = await self.db.fetchrow(
                        "SELECT id FROM streamers WHERE tik_tok_user_id = $1",
                        tik_tok_user_id,
                    )

                    if streamer:
                        streamer_data = {
                            "id": streamer["id"],
                            "tik_tok_user_id": tik_tok_user_id,
                        }
                        # logger.info(
                        #     f"Найден стример через кэш room_id: {client_room_id}"
                        # )

                # Если не нашли в кэше, делаем прямой запрос
                if not streamer_data:
                    mapping = await self.db.fetchrow(
                        """
                        SELECT rm.tik_tok_user_id, s.id as streamer_id
                        FROM room_id_mapping rm
                        JOIN streamers s ON s.tik_tok_user_id = rm.tik_tok_user_id
                        WHERE rm.room_id = $1
                        """,
                        client_room_id,
                    )

                    if mapping:
                        # Сохраняем в кэш для будущих запросов
                        self.room_id_cache[client_room_id] = mapping["tik_tok_user_id"]

                        streamer_data = {
                            "id": mapping["streamer_id"],
                            "tik_tok_user_id": mapping["tik_tok_user_id"],
                        }
                        logger.info(
                            f"Найден стример через БД по room_id: {client_room_id}"
                        )

            # Только если не нашли по room_id, ищем по имени
            if not streamer_data:
                user_name = (
                    f"@{unique_id}" if not unique_id.startswith("@") else unique_id
                )

                streamer = await self.db.fetchrow(
                    """
                    SELECT s.id, s.tik_tok_user_id
                    FROM streamers s
                    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
                    WHERE ttu.name = $1 OR ttu.tiktok_id = $2
                    """,
                    user_name,
                    unique_id.lstrip("@"),
                )

                if streamer:
                    streamer_data = {
                        "id": streamer["id"],
                        "tik_tok_user_id": streamer["tik_tok_user_id"],
                    }
                    logger.info(f"Найден стример по имени: {unique_id}")

            # Формируем данные о подарке
            gift_unique_id = str(uuid.uuid4())
            gift_data = {
                "user_id": str(user_id),
                "unique_id": str(user_unique_id),
                "follow_role": 0,
                "is_new_gifter": False,
                "top_gifter_rank": None,
                "diamond_count": int(diamond_count),
                "gift_name": str(gift_name),
                "gift_count": int(gift_count),
                "receiver_unique_id": unique_id,
                "receiver_user_id": "",  # Будет установлено, если найдем стримера
                "cluster": str(cluster),
                "event_time": datetime.now(timezone.utc),
                "gift_unique_id": gift_unique_id,
            }

            # Добавляем данные стримера, если найдены
            if streamer_data:
                gift_data["streamer_id"] = streamer_data["id"]
                gift_data["receiver_tik_tok_user_id"] = streamer_data["tik_tok_user_id"]

                # Также получаем user_id стримера для лучшей связанности
                receiver_user = await self.db.fetchrow(
                    "SELECT user_id FROM tik_tok_users WHERE id = $1",
                    streamer_data["tik_tok_user_id"],
                )

                if receiver_user and receiver_user["user_id"]:
                    gift_data["receiver_user_id"] = receiver_user["user_id"]
            else:
                logger.warning(
                    f"Не найден стример для подарка {unique_id} (room_id: {client_room_id})"
                )

            # Добавляем в очередь для сохранения
            if not self.gift_queue.full():
                self.gift_queue.put(gift_data)
            else:
                logger.warning("Очередь подарков переполнена")

        except Exception as e:
            logger.error(f"Ошибка обработки подарка: {e}", exc_info=True)

    async def _process_gift_queue(self):
        """Обработка очереди подарков (без изменений)"""
        # Этот метод оставляем без изменений, так как он хорошо оптимизирован
        gifts_batch = []
        last_flush_time = time.time()
        stats = {"total_received": 0, "total_saved": 0, "duplicates": 0, "errors": 0}

        while not self.shared_state.shutdown_event.is_set():
            try:
                # Пытаемся получить подарок из очереди
                try:
                    gift = self.gift_queue.get_nowait()
                    stats["total_received"] += 1
                    gifts_batch.append(gift)
                    self.gift_queue.task_done()
                except:
                    pass

                current_time = time.time()

                # Сохраняем пакет если набралось достаточно или прошло время
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
                                receiver_user_id, receiver_unique_id, streamer_id, receiver_tik_tok_user_id, gift_unique_id) 
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                                """

                            # Защита от некорректных данных в пакете
                            safe_gifts_batch = []
                            for gift in gifts_batch:
                                try:
                                    # Проверяем наличие необходимых полей
                                    required_fields = [
                                        "event_time",
                                        "user_id",
                                        "unique_id",
                                        "follow_role",
                                        "is_new_gifter",
                                        "diamond_count",
                                        "gift_name",
                                        "gift_count",
                                        "receiver_user_id",
                                        "receiver_unique_id",
                                    ]

                                    if all(field in gift for field in required_fields):
                                        safe_gifts_batch.append(gift)
                                    else:
                                        missing = [
                                            f for f in required_fields if f not in gift
                                        ]
                                        logger.warning(
                                            f"Пропущен подарок с отсутствующими полями: {missing}"
                                        )
                                        stats["errors"] += 1
                                except:
                                    logger.warning(
                                        "Пропущен подарок с некорректной структурой"
                                    )
                                    stats["errors"] += 1

                            # Если после проверки остались подарки для вставки
                            if safe_gifts_batch:
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
                                        gift.get(
                                            "gift_unique_id", str(uuid.uuid4())
                                        ),  # Используем существующий UUID или создаем новый
                                    )
                                    for gift in safe_gifts_batch
                                ]

                                try:
                                    # Пытаемся выполнить пакетную вставку
                                    await conn.executemany(query, values)
                                    batch_size = len(safe_gifts_batch)
                                    stats["total_saved"] += batch_size
                                    # logger.info(
                                    #     f"Сохранено {batch_size} подарков в базу данных"
                                    # )
                                except Exception as e:
                                    # Обработка дубликатов
                                    if "duplicate key" in str(e):
                                        logger.info(
                                            f"Обнаружены дубликаты в пакете, обрабатываются индивидуально"
                                        )
                                        success_count = 0
                                        dupe_count = 0

                                        # Вставляем подарки по одному
                                        for i, gift_values in enumerate(values):
                                            try:
                                                async with conn.transaction():
                                                    await conn.execute(
                                                        query, *gift_values
                                                    )
                                                    success_count += 1
                                            except Exception as e2:
                                                if "duplicate key" in str(e2):
                                                    gift_info = safe_gifts_batch[i]
                                                    dupe_count += 1
                                                    logger.debug(
                                                        f"Пропущен дубликат подарка: {gift_info['gift_name']} "
                                                        f"x{gift_info['gift_count']} от {gift_info['unique_id']} "
                                                        f"для {gift_info['receiver_unique_id']}"
                                                    )
                                                else:
                                                    logger.error(
                                                        f"Ошибка вставки подарка: {e2}"
                                                    )
                                                    stats["errors"] += 1

                                        stats["total_saved"] += success_count
                                        stats["duplicates"] += dupe_count
                                        logger.info(
                                            f"Успешно вставлено {success_count} из {len(safe_gifts_batch)} подарков, "
                                            f"дубликатов: {dupe_count}"
                                        )
                                    else:
                                        # Логируем другие ошибки
                                        logger.error(
                                            f"Ошибка пакетной вставки подарков: {e}"
                                        )
                                        stats["errors"] += len(safe_gifts_batch)

                    # Очищаем пакет и обновляем время последней вставки
                    gifts_batch = []
                    last_flush_time = current_time

                # Небольшая пауза для снижения нагрузки на CPU
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Ошибка обработки очереди подарков: {e}")
                # Выводим дополнительную отладочную информацию
                if gifts_batch:
                    logger.error(f"Проблемные данные подарка: {gifts_batch[0]}")
                    stats["errors"] += len(gifts_batch)
                gifts_batch = []
                await asyncio.sleep(1)

    # # Добавил streakable
    # async def _process_gift(self, event, unique_id, cluster):
    #     """Обработка одиночного события подарка"""
    #     try:
    #         # Извлекаем данные из события
    #         gift = getattr(event, "gift", event)

    #         # Основные данные подарка
    #         gift_id = getattr(gift, "id", 0)
    #         gift_name = getattr(gift, "name", "Unknown")
    #         gift_cost = getattr(gift, "diamond_count", 0)
    #         gift_count = getattr(gift, "count", 1)
    #         gift_type = getattr(gift, "type", 0)

    #         # Дополнительная информация
    #         gift_info = getattr(gift, "info", None)
    #         combo_count = getattr(gift, "combo_count", 0) or getattr(gift, "repeat_count", 0)
    #         repeat_count = getattr(gift, "repeat_count", 0) or getattr(gift, "combo_count", 0)

    #         # Данные о пользователе
    #         sender = getattr(event, "user", None)
    #         user_id = getattr(sender, "user_id", "0") if sender else "0"
    #         nickname = getattr(sender, "nickname", "Unknown") if sender else "Unknown"
    #         unique_sender_id = getattr(sender, "uniqueId", "") if sender else ""

    #         # Данные для отслеживания подписчиков
    #         follow_info = getattr(sender, "follow_info", None) if sender else None
    #         follow_role = getattr(follow_info, "follow_role", 0) if follow_info else 0

    #         # Данные стримера и комнаты
    #         room_id = getattr(event, "room_id", None)
    #         receiver_user_id = getattr(event, "receiver_user_id", None) or getattr(event, "roomId", None) or room_id
    #         receiver_unique_id = unique_id

    #         # Определение стрикабельности
    #         streakable = False

    #         # Проверяем все возможные источники информации о стриках
    #         if isinstance(gift, dict):
    #             streakable = gift.get("streakable", False)
    #             if not streakable and gift_info:
    #                 streakable = gift_info.get("type", 0) == 1
    #             if not streakable:
    #                 streakable = gift.get("type", 0) == 1
    #         else:
    #             streakable = getattr(gift, "streakable", False)
    #             if not streakable and hasattr(gift, "info") and hasattr(gift.info, "type"):
    #                 streakable = gift.info.type == 1
    #             elif not streakable and hasattr(gift, "type"):
    #                 streakable = gift.type == 1

    #         # Дополнительная проверка gift_type
    #         streakable = streakable or (gift_type == 1)

    #         # Статус стрика
    #         if isinstance(gift, dict):
    #             is_repeating = gift.get("is_repeating", 0) == 1
    #         else:
    #             is_repeating = getattr(gift, "is_repeating", 0) == 1

    #         repeat_end = getattr(event, "repeat_end", 0) == 1
    #         streaking = getattr(event, "streaking", False)

    #         # Подробное логирование для отладки
    #         if self.shared_state.debug:
    #             logger.debug(
    #                 f"Информация о подарке: name={gift_name}, count={gift_count}, streakable={streakable}, "
    #                 + f"is_repeating={is_repeating}, repeat_end={repeat_end}, streaking={streaking}, "
    #                 + f"combo_count={combo_count}, repeat_count={repeat_count}, gift_type={gift_type}"
    #             )

    #         # Пропускаем промежуточные подарки в стрике
    #         if streakable:
    #             # Улучшенное условие для определения промежуточных подарков
    #             if (streaking or is_repeating) and not repeat_end:
    #                 if self.shared_state.debug:
    #                     logger.debug(f"Пропускаем промежуточный подарок в стрике: {gift_name} (count: {gift_count})")
    #                 return

    #         # Получаем дополнительные данные
    #         is_new_gifter = getattr(sender, "is_first_gift", False) if sender else False
    #         top_gifter_rank = getattr(sender, "top_gifter_rank", None) if sender else None

    #         # Формируем уникальный идентификатор подарка
    #         event_time = int(time.time())
    #         gift_unique_id = str(uuid.uuid4())  # Генерируем уникальный UUID для этого подарка

    #         # Получаем ID стримера, если возможно
    #         streamer_id = None
    #         receiver_tik_tok_user_id = None

    #         if room_id:
    #             # Преобразуем room_id в int, если возможно
    #             try:
    #                 room_id_int = int(room_id)
    #                 # Пытаемся найти стримера по room_id
    #                 mapping = await self.db.fetchrow(
    #                     "SELECT tik_tok_user_id FROM room_id_mapping WHERE room_id = $1",
    #                     room_id_int
    #                 )

    #                 if mapping:
    #                     receiver_tik_tok_user_id = mapping["tik_tok_user_id"]
    #                     # Получаем ID стримера
    #                     streamer = await self.db.fetchrow(
    #                         "SELECT id FROM streamers WHERE tik_tok_user_id = $1",
    #                         receiver_tik_tok_user_id
    #                     )

    #                     if streamer:
    #                         streamer_id = streamer["id"]
    #             except (ValueError, TypeError):
    #                 pass

    #         # Если не нашли по room_id, ищем по уникальному ID
    #         if not streamer_id and receiver_unique_id:
    #             try:
    #                 # Форматируем имя пользователя
    #                 user_name = f"@{receiver_unique_id}" if not receiver_unique_id.startswith("@") else receiver_unique_id

    #                 # Ищем tik_tok_user_id
    #                 tik_tok_user = await self.db.fetchrow(
    #                     "SELECT id FROM tik_tok_users WHERE name = $1 OR tiktok_id = $2",
    #                     user_name,
    #                     receiver_unique_id.lstrip("@")
    #                 )

    #                 if tik_tok_user:
    #                     receiver_tik_tok_user_id = tik_tok_user["id"]

    #                     # Получаем ID стримера
    #                     streamer = await self.db.fetchrow(
    #                         "SELECT id FROM streamers WHERE tik_tok_user_id = $1",
    #                         receiver_tik_tok_user_id
    #                     )

    #                     if streamer:
    #                         streamer_id = streamer["id"]
    #             except Exception as e:
    #                 logger.warning(f"Ошибка при поиске стримера по unique_id: {e}")

    #         # Формируем данные для сохранения
    #         gift_data = {
    #             "event_time": event_time,
    #             "user_id": user_id,
    #             "unique_id": unique_sender_id or nickname,
    #             "follow_role": follow_role,
    #             "is_new_gifter": is_new_gifter,
    #             "top_gifter_rank": top_gifter_rank,
    #             "diamond_count": gift_cost * gift_count,  # Учитываем количество подарков
    #             "gift_name": gift_name,
    #             "gift_count": gift_count,
    #             "receiver_user_id": receiver_user_id,
    #             "receiver_unique_id": receiver_unique_id,
    #             "streamer_id": streamer_id,
    #             "receiver_tik_tok_user_id": receiver_tik_tok_user_id,
    #             "gift_unique_id": gift_unique_id,
    #             "cluster": cluster,
    #         }

    #         # Добавляем в очередь обработки
    #         await self.gift_queue.put(gift_data)

    #         # Увеличиваем счетчик подарков для статистики
    #         self.shared_state.stats["gifts_received"] += 1

    #     except Exception as e:
    #         logger.error(f"Ошибка обработки подарка: {e}", exc_info=True)
    # async def _clean_gift_cache(self):
    #     """Периодическая очистка кэша подарков"""
    #     while not self.shared_state.shutdown_event.is_set():
    #         # Очищаем кэш каждые 6 часов
    #         await asyncio.sleep(6 * 60 * 60)
    #         logger.info(
    #             f"Cleaning gift cache, size before: {len(self.processed_gift_ids)}"
    #         )
    #         self.processed_gift_ids.clear()
    #         logger.info("Gift cache cleared")
