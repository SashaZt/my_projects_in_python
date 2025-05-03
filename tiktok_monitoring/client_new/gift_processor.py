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
        self.processed_gift_ids = set()
        self.shared_state = shared_state  # Добавить shared_state
        self.active_streamers = {}  # словарь {tik_tok_user_id: latest_room_id}
        self.last_streamers_check = time.time()
        self.streamers_check_interval = 300  # 5 минут
        self.recent_gifts = {}
        self.streamer_gifts = {}

    async def start(self):
        """Запускает обработчик подарков"""
        # Обновляем кэш активных стримеров при старте
        await self._update_active_streamers()

        # Запускаем задачи
        gift_queue_task = asyncio.create_task(self._process_gift_queue())
        gift_cache_task = asyncio.create_task(self._clean_gift_cache())
        gifts_caches_task = asyncio.create_task(self._clean_gifts_caches())
        streamers_check_task = asyncio.create_task(self._periodic_streamers_check())

        return [
            gift_queue_task,
            gift_cache_task,
            gifts_caches_task,
            streamers_check_task,
        ]

    async def _periodic_streamers_check(self):
        """Периодически проверяет и обновляет статус стримеров и сессий"""
        while not self.shared_state.shutdown_event.is_set():
            await self._update_active_streamers()
            await asyncio.sleep(self.streamers_check_interval)

    async def _clean_gifts_caches(self):
        """Периодически очищает кэши подарков"""
        while not self.shared_state.shutdown_event.is_set():
            try:
                now = time.time()

                # Очистка кэша недавних подарков
                if hasattr(self, "recent_gifts"):
                    keys_to_remove = []
                    for key, (timestamp, _) in self.recent_gifts.items():
                        if now - timestamp > 60:  # Удаляем записи старше 1 минуты
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        self.recent_gifts.pop(key, None)

                    logger.debug(
                        f"Cleaned recent_gifts cache, removed {len(keys_to_remove)} entries, remaining: {len(self.recent_gifts)}"
                    )

                # Очистка кэша подарков по стримеру
                if hasattr(self, "streamer_gifts"):
                    keys_to_remove = []
                    for key, (timestamp, _) in self.streamer_gifts.items():
                        if now - timestamp > 60:  # Удаляем записи старше 1 минуты
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        self.streamer_gifts.pop(key, None)

                    logger.debug(
                        f"Cleaned streamer_gifts cache, removed {len(keys_to_remove)} entries, remaining: {len(self.streamer_gifts)}"
                    )

                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
            except Exception as e:
                logger.error(f"Error cleaning gifts caches: {e}")
                await asyncio.sleep(60)  # При ошибке проверяем реже

    # Добавьте этот метод для обновления активных стримеров

    async def _update_active_streamers(self):
        """Обновляет кэш активных стримеров, предпочитая последние сессии"""
        try:
            # Получаем список активных комнат
            active_rooms = await self.db.fetch(
                """
                SELECT rm.tik_tok_user_id, rm.room_id, rm.last_updated
                FROM room_id_mapping rm
                JOIN streamers s ON rm.tik_tok_user_id = s.tik_tok_user_id
                ORDER BY rm.last_updated DESC
            """
            )

            # Обновляем словарь активных стримеров
            new_active_streamers = {}
            seen_streamers = set()

            for room in active_rooms:
                streamer_id = room["tik_tok_user_id"]
                # Берем только самую новую комнату для каждого стримера
                if streamer_id not in seen_streamers:
                    new_active_streamers[streamer_id] = room["room_id"]
                    seen_streamers.add(streamer_id)

            self.active_streamers = new_active_streamers
            logger.info(
                f"Updated active streamers cache: {len(self.active_streamers)} active streamers"
            )
            # Закрываем старые сессии стримов
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=6)
            # Найти и закрыть старые стримы
            closed_streams = await self.db.execute(
                """
                UPDATE streams
                SET end_time = $1
                WHERE end_time IS NULL 
                AND start_time < $2
                RETURNING id
            """,
                current_time,
                cutoff_time,
            )

            if closed_streams:
                logger.info(f"Closed {len(closed_streams)} old stream sessions")

        except Exception as e:
            logger.error(f"Error updating active streamers: {e}")

    async def _process_gift(self, event, unique_id, cluster):
        """Обработка подарка с улучшенной идентификацией получателя и дедупликацией"""
        try:
            # Базовая обработка атрибутов подарка
            current_time = int(time.time() * 1000)
            current_timestamp = int(time.time())  # Секунды в Unix timestamp
            gift = getattr(event, "gift", None)
            user = getattr(event, "user", getattr(event, "from_user", None))

            if not gift or not user:
                logger.warning(
                    "Недопустимое событие подарка: отсутствует подарок или данные пользователя"
                )
                return

            # Более детальное логирование для анализа
            # logger.debug(f"Event type: {type(event)}, Gift type: {type(gift)}")
            if isinstance(gift, dict):
                logger.debug(f"Gift keys: {gift.keys()}")
            gift_type_id = None
            send_timestamp = None

            # Извлекаем базовые атрибуты
            if isinstance(gift, dict):
                gift_id = gift.get("id", current_time)
                gift_type_id = gift.get("gift_id") or gift.get("id")
                send_timestamp = gift.get("send_gift_req_start_ms")

                diamond_count = gift.get("diamond_count", 0)
                gift_name = gift.get("name", "Unknown Gift")
                combo_count = gift.get("combo_count", 1)
                repeat_count = gift.get("repeat_count", 1)
            else:
                gift_id = getattr(gift, "id", current_time)
                gift_type_id = getattr(gift, "gift_id", None) or getattr(
                    gift, "id", None
                )
                send_timestamp = int(time.time() * 1000)
                diamond_count = getattr(gift, "diamond_count", 0)
                gift_name = getattr(gift, "name", "Unknown Gift")
                combo_count = getattr(gift, "combo_count", 1)
                repeat_count = getattr(gift, "repeat_count", 1)

            # Используем максимальное значение для количества
            gift_count = max(
                1,
                combo_count,
                repeat_count,
                getattr(event, "repeat_count", 1) if not isinstance(event, dict) else 1,
            )

            # Данные о пользователе
            if isinstance(user, dict):
                user_id = user.get("id", "0")
                user_unique_id = user.get("unique_id", f"user_{user_id}")
            else:
                user_id = getattr(user, "id", "0")
                user_unique_id = getattr(user, "unique_id", f"user_{user_id}")

            # Получаем информацию о типе подарка
            gift_info = {}
            if isinstance(gift, dict) and "info" in gift:
                gift_info = gift.get("info", {})
            elif hasattr(gift, "info"):
                gift_info = gift.info if isinstance(gift.info, dict) else {}

            gift_type = None
            if gift_info:
                gift_type = gift_info.get("type")
            elif isinstance(gift, dict):
                gift_type = gift.get("type")
            else:
                gift_type = getattr(gift, "type", None)

            # Определение стрикабельности
            streakable = False

            # Проверяем все возможные источники информации о стриках
            if isinstance(gift, dict):
                streakable = gift.get("streakable", False)
                if not streakable and gift_info:
                    streakable = gift_info.get("type", 0) == 1
                if not streakable:
                    streakable = gift.get("type", 0) == 1
            else:
                streakable = getattr(gift, "streakable", False)
                if (
                    not streakable
                    and hasattr(gift, "info")
                    and hasattr(gift.info, "type")
                ):
                    streakable = gift.info.type == 1
                elif not streakable and hasattr(gift, "type"):
                    streakable = gift.type == 1

            # Дополнительная проверка gift_type
            streakable = streakable or (gift_type == 1)

            # Статус стрика
            if isinstance(gift, dict):
                is_repeating = gift.get("is_repeating", 0) == 1
            else:
                is_repeating = getattr(gift, "is_repeating", 0) == 1

            repeat_end = getattr(event, "repeat_end", 0) == 1
            streaking = getattr(event, "streaking", False)

            # Подробное логирование для отладки
            logger.info("+" * 100)
            logger.debug(
                f"Информация о подарке: name={gift_name}, count={gift_count}, streakable={streakable}, "
                + f"is_repeating={is_repeating}, repeat_end={repeat_end}, streaking={streaking}, "
                + f"combo_count={combo_count}, repeat_count={repeat_count}, gift_type={gift_type}"
            )

            # Пропускаем промежуточные подарки в стрике
            if streakable:
                # Улучшенное условие для определения промежуточных подарков
                if (streaking or is_repeating) and not repeat_end:
                    logger.debug(
                        f"Skipping intermediate streaking gift: {gift_name} (count: {gift_count})"
                    )
                    return

            # Получаем ID получателя из события
            raw_receiver_id = getattr(event, "to_member_id", unique_id.replace("@", ""))

            # Получаем room_id из события или клиента
            client_room_id = getattr(
                event,
                "room_id",
                getattr(getattr(event, "client", None), "room_id", None),
            )

            # Создаем ключ для временного окна дедупликации (10 секунд)
            dedup_window_seconds = 10  # Окно дедупликации в секундах
            now = time.time()
            time_bucket = int(now) // 10  # Округляем до 10-секундных интервалов

            # Используем текущее время в секундах для большей точности
            current_timestamp = int(time.time())
            time_bucket = current_timestamp // 10  # 10-секундные интервалы

            # Получаем более точные идентификаторы подарка
            gift_id = None
            if isinstance(gift, dict):
                gift_id = gift.get("id") or gift.get("gift_id")
            else:
                gift_id = getattr(gift, "id", None) or getattr(gift, "gift_id", None)

            # Если у нас нет ID подарка, используем временную метку в качестве резервной опции
            if not gift_id:
                gift_id = current_timestamp
            time_bucket = (
                send_timestamp // 10000
            )

            # Создаем уникальный ключ для дедупликации, используя все доступные данные
            # Обратите внимание, что мы используем gift_id в начале ключа
            dedup_key = f"{gift_type_id}_{user_id}_{gift_name}_{diamond_count}_{gift_count}_{raw_receiver_id}_{time_bucket}"

            # Проверяем, был ли такой подарок в этом временном интервале
            if hasattr(self, "recent_gifts") and dedup_key in self.recent_gifts:
                logger.info(
                    f"Временная дедупликация: пропускаем подарок {gift_name} с ID {gift_id} от {user_unique_id} для {raw_receiver_id}"
                )
                return

            # Инициализируем словарь недавних подарков, если его еще нет
            if not hasattr(self, "recent_gifts"):
                self.recent_gifts = {}

            # Сохраняем информацию о текущем подарке с подробным логированием
            gift_unique_id = str(uuid.uuid4())
            self.recent_gifts[dedup_key] = (current_timestamp, gift_unique_id)
            logger.debug(f"Зарегистрирован новый подарок с ключом: {dedup_key}")

            # Очищаем старые записи из словаря недавних подарков
            keys_to_remove = []
            for key, (timestamp, _) in self.recent_gifts.items():
                if (
                    now - timestamp > dedup_window_seconds * 3
                ):  # Удаляем записи старше 3*окно
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self.recent_gifts.pop(key, None)

            # Генерируем уникальный идентификатор для дедупликации в памяти и БД
            # gift_key = f"{gift_id}_{diamond_count}_{user_id}_{unique_id}_{gift_count}_{current_time}_{gift_unique_id[:8]}"
            # time_bucket = int(time.time()) // 10
            time_bucket = (
                send_timestamp // 10000
            )  # 10-секундный интервал в миллисекундах
            gift_key = f"{gift_type_id}_{gift_id}_{diamond_count}_{user_id}_{unique_id}_{gift_count}_{time_bucket}_{gift_unique_id[:8]}"
            logger.info("*" * 100)
            logger.info(gift_key)
            # Проверяем, не обрабатывали ли мы уже такой подарок в памяти
            if gift_key in self.processed_gift_ids:
                logger.debug(f"Пропускаем дубликат подарка в памяти: {gift_key}")
                return

            self.processed_gift_ids.add(gift_key)
            # Обрезаем набор, если он стал слишком большим
            if len(self.processed_gift_ids) > 50000:
                self.processed_gift_ids.difference_update(
                    list(self.processed_gift_ids)[:10000]
                )

            # Информация о роли пользователя
            follow_role = 0
            if isinstance(user, dict):
                if user.get("is_friend", False):
                    follow_role = 2
                elif user.get("is_subscriber", False):
                    follow_role = 1
            else:
                if hasattr(user, "is_friend") and user.is_friend:
                    follow_role = 2
                elif hasattr(user, "is_subscriber") and user.is_subscriber:
                    follow_role = 1

            # Первый подарок от пользователя
            is_new_gifter = getattr(event, "is_first_send_gift", False)

            # Ранг пользователя-донатера
            if isinstance(user, dict):
                top_gifter_rank = user.get("gifter_level")
            else:
                top_gifter_rank = getattr(user, "gifter_level", None)

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
                            f"Found user_id {actual_user_id} through room_id_mapping for room_id {numeric_id} ({mapping_data['name']})"
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

                # Дополнительная проверка на дубликаты с использованием streamer_id, если найден
                if streamer_data:
                    streamer_id = streamer_data["id"]

                    # Используем gift_id для более точной идентификации
                    streamer_dedup_key = f"{gift_type_id}_{user_id}_{gift_count}_{streamer_id}_{time_bucket}"
                    logger.info("*" * 100)
                    logger.info(streamer_dedup_key)
                    if (
                        hasattr(self, "streamer_gifts")
                        and streamer_dedup_key in self.streamer_gifts
                    ):
                        logger.info(
                            f"Дедупликация по стримеру: подарок {gift_name} с ID {gift_id} от {user_unique_id} уже получен стримером {streamer_id}"
                        )
                        return

                    # Инициализируем кэш подарков по стримерам
                    if not hasattr(self, "streamer_gifts"):
                        self.streamer_gifts = {}

                    # Сохраняем информацию
                    self.streamer_gifts[streamer_dedup_key] = (
                        current_timestamp,
                        gift_unique_id,
                    )
                    logger.debug(
                        f"Зарегистрирован подарок для стримера с ключом: {streamer_dedup_key}"
                    )

                    # Очищаем старые записи - сохраняем эту логику для автоматической очистки
                    keys_to_remove = []
                    for key, (timestamp, _) in self.streamer_gifts.items():
                        if now - timestamp > dedup_window_seconds * 3:
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        self.streamer_gifts.pop(key, None)
                # if streamer_data:
                #     streamer_id = streamer_data["id"]
                #     # Обновляем ключ дедупликации с учетом информации о стримере
                #     # streamer_dedup_key = f"{user_id}_{gift_name}_{diamond_count}_{gift_count}_{streamer_id}"
                #     streamer_dedup_key = f"{user_id}_{gift_name}_{diamond_count}_{gift_count}_{streamer_id}_{current_timestamp // 10}"

                #     if (
                #         hasattr(self, "streamer_gifts")
                #         and streamer_dedup_key in self.streamer_gifts
                #     ):
                #         last_time, last_gift_id = self.streamer_gifts.get(
                #             streamer_dedup_key, (0, None)
                #         )
                #         if now - last_time < dedup_window_seconds:
                #             logger.info(
                #                 f"Дедупликация по стримеру: пропускаем похожий подарок для streamer_id={streamer_id}, "
                #                 f"{gift_name} от {user_unique_id} в окне {dedup_window_seconds}с"
                #             )
                #             return

                #     # Инициализируем словарь подарков по стримеру, если его еще нет
                #     if not hasattr(self, "streamer_gifts"):
                #         self.streamer_gifts = {}

                #     # Сохраняем информацию о текущем подарке по стримеру
                #     self.streamer_gifts[streamer_dedup_key] = (now, gift_unique_id)

                #     # Очищаем старые записи
                #     keys_to_remove = []
                #     for key, (timestamp, _) in self.streamer_gifts.items():
                #         if now - timestamp > dedup_window_seconds * 3:
                #             keys_to_remove.append(key)

                #     for key in keys_to_remove:
                #         self.streamer_gifts.pop(key, None)

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
                    "receiver_user_id": str(raw_receiver_id),
                    "receiver_unique_id": str(receiver_unique_id),
                    "cluster": str(cluster),
                    "event_time": datetime.now(timezone.utc),
                    "gift_unique_id": gift_unique_id,
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
                    "gift_unique_id": gift_unique_id,
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

    async def _process_gift_queue(self):
        """
        Обрабатывает очередь подарков и сохраняет их в базу данных.
        Реализует пакетную обработку для оптимизации производительности
        и обработку дубликатов.
        """
        gifts_batch = []
        last_flush_time = time.time()
        stats = {"total_received": 0, "total_saved": 0, "duplicates": 0, "errors": 0}

        while not self.shared_state.shutdown_event.is_set():
            try:
                # Пытаемся получить подарок из очереди, не блокируя поток
                try:
                    gift = self.gift_queue.get_nowait()
                    stats["total_received"] += 1

                    # Добавляем в пакет и отмечаем задачу как выполненную
                    gifts_batch.append(gift)
                    self.gift_queue.task_done()

                    # Периодически логируем статистику
                    if stats["total_received"] % 1000 == 0:
                        logger.info(f"Статистика обработки подарков: {stats}")
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
                                    logger.info(
                                        f"Сохранено {batch_size} подарков в базу данных"
                                    )
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

    async def _clean_gift_cache(self):
        """Периодическая очистка кэша подарков"""
        while not self.shared_state.shutdown_event.is_set():
            # Очищаем кэш каждые 6 часов
            await asyncio.sleep(6 * 60 * 60)
            logger.info(
                f"Cleaning gift cache, size before: {len(self.processed_gift_ids)}"
            )
            self.processed_gift_ids.clear()
            logger.info("Gift cache cleared")
