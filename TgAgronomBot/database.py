import aiomysql
import asyncio
from configuration.config import DB_CONFIG
from loguru import logger
import os

# Настройка логирования
log_directory = os.getcwd()
log_file_path = os.path.join(log_directory, "info.log")

logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
)

logger.info("Логирование настроено и работает корректно.")


class Database:
    def __init__(self, loop):
        self.loop = loop
        self.connection = None

    async def create_connection(self):
        """
        Создание подключения к базе данных MySQL.
        """
        try:
            self.connection = await aiomysql.connect(loop=self.loop, **DB_CONFIG)
            if self.connection:
                logger.info("Connected to MySQL database")
                return self.connection
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    async def initialize_db(self):
        """
        Инициализация базы данных: создание таблицы users_tg_bot, если она не существует.
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS users_tg_bot (
                    user_id BIGINT PRIMARY KEY,
                    nickname VARCHAR(255),
                    signup TIMESTAMP,
                    trial_duration INT,
                    role VARCHAR(255),
                    temporary_status BOOLEAN DEFAULT TRUE,
                    start_status BOOLEAN DEFAULT TRUE
                )"""
            )

            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS raw_materials (
                    material_id INT AUTO_INCREMENT PRIMARY KEY,
                    material_name VARCHAR(255)
                );"""
            )
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS last_check (
                        user_id BIGINT PRIMARY KEY,
                        last_check_time TIMESTAMP
                );"""
            )

            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS regions (
                    region_id INT AUTO_INCREMENT PRIMARY KEY,
                    region_name VARCHAR(255)
                );"""
            )

            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS user_raw_materials (
                    user_id BIGINT,
                    material_id INT,
                    FOREIGN KEY (user_id) REFERENCES users_tg_bot(user_id),
                    FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
                );"""
            )

            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS user_regions (
                    user_id BIGINT,
                    region_id INT,
                    FOREIGN KEY (user_id) REFERENCES users_tg_bot(user_id),
                    FOREIGN KEY (region_id) REFERENCES regions(region_id)
                );"""
            )
            # Инициализация данных
            raw_materials = [
                "Пшениця",
                "Соняшник",
                "Соя",
                "Ріпак",
                "Жито",
                "Тритикале",
                "Кукурудза",
                "Ячмінь",
                "Горох",
                "Овес",
                "Гречка",
                "Нішеві",
            ]

            regions = [
                "Київська",
                "Львівська",
                "Одеська",
                "Харківська",
                "Дніпропетровська",
                "Запорізька",
                "Вінницька",
                "Полтавська",
                "Миколаївська",
                "Чернігівська",
                "Сумська",
                "Житомирська",
                "Черкаська",
                "Рівненська",
                "Івано-Франківська",
                "Волинська",
                "Тернопільська",
                "Хмельницька",
                "Кіровоградська",
                "Луганська",
                "Донецька",
                "Закарпатська",
                "Чернівецька",
                "Херсонська",
            ]

            # Проверка наличия данных в таблице raw_materials
            await cursor.execute("SELECT COUNT(*) FROM raw_materials")
            count_raw_materials = (await cursor.fetchone())[0]
            if count_raw_materials == 0:
                for material in raw_materials:
                    await cursor.execute(
                        """INSERT INTO raw_materials (material_name)
                        VALUES (%s)
                        ON DUPLICATE KEY UPDATE material_name = VALUES(material_name)""",
                        (material,),
                    )
                logger.info("Raw materials added to database")
            else:
                logger.info("Raw materials already exist in database")

            # Проверка наличия данных в таблице regions
            await cursor.execute("SELECT COUNT(*) FROM regions")
            count_regions = (await cursor.fetchone())[0]
            if count_regions == 0:
                for region in regions:
                    await cursor.execute(
                        """INSERT INTO regions (region_name)
                        VALUES (%s)
                        ON DUPLICATE KEY UPDATE region_name = VALUES(region_name)""",
                        (region,),
                    )
                logger.info("Regions added to database")
            else:
                logger.info("Regions already exist in database")

            await self.connection.commit()

        logger.info(
            "Таблицы users_tg_bot, raw_materials, regions созданы или уже существуют."
        )

    # async def user_exists(self, user_id):
    #     connection = await self.create_connection()
    #     async with connection.cursor() as cursor:
    #         try:
    #             await cursor.execute(
    #                 "SELECT * FROM users_tg_bot WHERE user_id = %s", (user_id,)
    #             )
    #             exists = await cursor.fetchone() is not None
    #             logger.info(f"User exists check for user_id {user_id}: {exists}")
    #             return exists
    #         except Exception as err:
    #             logger.error(f"Ошибка при проверке существования пользователя: {err}")
    #         finally:
    #             connection.close()
    async def user_exists(self, user_id):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT 1 FROM users_tg_bot WHERE user_id = %s LIMIT 1", (user_id,)
                )
                exists = await cursor.fetchone() is not None
                logger.info(f"User exists check for user_id {user_id}: {exists}")
                return exists
            except Exception as err:
                logger.error(f"Ошибка при проверке существования пользователя: {err}")
                return False
            finally:
                connection.close()

    async def add_user_start(self, user_id, nickname):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(f"Adding user {user_id} with nickname {nickname}")
                await cursor.execute(
                    """INSERT INTO users_tg_bot (user_id, nickname)
                    VALUES (%s, %s)
                    AS new
                    ON DUPLICATE KEY UPDATE nickname = new.nickname """,
                    (
                        user_id,
                        nickname,
                    ),
                )
                await connection.commit()
                logger.info(
                    f"User {user_id} added to users_tg_bot with nickname {nickname}"
                )
            except Exception as err:
                logger.error(f"Ошибка при добавлении пользователя: {err}")
            finally:
                connection.close()

    async def add_user(self, user_id, nickname, signup_time, role):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(
                    f"Updating user {user_id} with nickname {nickname}, signup_time {signup_time}, and role {role}"
                )
                await cursor.execute(
                    """UPDATE users_tg_bot
                    SET nickname = %s, signup = %s, trial_duration = %s, role = %s
                    WHERE user_id = %s""",
                    (nickname, signup_time, 172800, role, user_id),
                )
                if cursor.rowcount > 0:
                    logger.info(
                        f"User {user_id} updated in users_tg_bot with role {role}"
                    )
                else:
                    logger.info(f"User {user_id} not found for updating")
                await connection.commit()
            except Exception as err:
                logger.error(f"Ошибка при обновлении данных пользователя: {err}")
            finally:
                await connection.ensure_closed()

    async def add_user_raw_material(self, user_id, material_id):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(
                    f"Preparing to add raw material {material_id} for user {user_id}"
                )
                await cursor.execute(
                    """INSERT INTO user_raw_materials (user_id, material_id)
                    VALUES (%s, %s)
                    AS new
                    ON DUPLICATE KEY UPDATE material_id = new.material_id""",
                    (user_id, material_id),
                )
                await connection.commit()
                logger.info(
                    f"User {user_id} with material {material_id} added to user_raw_materials"
                )
            except Exception as err:
                logger.error(f"Ошибка при добавлении материала пользователя: {err}")
            finally:
                await connection.ensure_closed()

    async def add_user_region(self, user_id, region_id):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(f"Preparing to add region {region_id} for user {user_id}")
                await cursor.execute(
                    """INSERT INTO user_regions (user_id, region_id)
                    VALUES (%s, %s)
                    AS new
                    ON DUPLICATE KEY UPDATE region_id = new.region_id""",
                    (user_id, region_id),
                )
                await connection.commit()
                logger.info(
                    f"User {user_id} with region {region_id} added to user_regions"
                )
            except Exception as err:
                logger.error(f"Ошибка при добавлении региона пользователя: {err}")
            finally:
                await connection.ensure_closed()

    async def get_product_id_by_name(self, product_name):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(f"Getting product ID for product name: {product_name}")
                await cursor.execute(
                    "SELECT material_id FROM raw_materials WHERE material_name = %s",
                    (product_name,),
                )
                result = await cursor.fetchone()
                if result:
                    logger.info(
                        f"Product ID {result[0]} found for product {product_name}"
                    )
                else:
                    logger.error(f"Product ID not found for product: {product_name}")
                return result[0] if result else None
            except Exception as err:
                logger.error(f"Ошибка при получении ID продукта: {err}")
            finally:
                connection.close()

    async def get_region_id_by_name(self, region_name):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            try:
                logger.info(f"Getting region ID for region name: {region_name}")
                await cursor.execute(
                    "SELECT region_id FROM regions WHERE region_name = %s",
                    (region_name,),
                )
                result = await cursor.fetchone()
                if result:
                    logger.info(f"Region ID {result[0]} found for region {region_name}")
                else:
                    logger.error(f"Region ID not found for region: {region_name}")
                return result[0] if result else None
            except Exception as err:
                logger.error(f"Ошибка при получении ID региона: {err}")
            finally:
                connection.close()

    async def get_signup_time(self, user_id):
        """
        Получение времени подписки пользователя.
        """
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT signup FROM users_tg_bot WHERE user_id = %s", (user_id,)
            )
            result = await cursor.fetchone()
            signup_time = result[0] if result else None
            logger.debug(f"Время подписки пользователя {user_id}: {signup_time}")
            return signup_time

    async def get_trial_duration(self, user_id):
        """
        Получение продолжительности пробного периода пользователя.
        """
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT trial_duration FROM users_tg_bot WHERE user_id = %s", (user_id,)
            )
            result = await cursor.fetchone()
            trial_duration = result[0] if result else None
            logger.debug(
                f"Продолжительность пробного периода пользователя {user_id}: {trial_duration}"
            )
            return trial_duration

    async def set_trial_duration(self, user_id, duration):
        """
        Установка продолжительности пробного периода для пользователя.
        """
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE users_tg_bot SET trial_duration = %s WHERE user_id = %s",
                (duration, user_id),
            )
            await connection.commit()
            logger.info(
                f"Установлена продолжительность пробного периода для пользователя {user_id}: {duration}"
            )
