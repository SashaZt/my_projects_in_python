import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
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
    def __init__(self):
        self.connection = self.create_connection()

    def create_connection(self):
        """
        Создание подключения к базе данных MySQL.
        """
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                logger.info("Connected to MySQL database")
                return connection
        except Error as e:
            logger.error(f"Error: {e}")
            return None

    def initialize_db(self):
        """
        Инициализация базы данных: создание таблицы users_tg_bot, если она не существует.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users_tg_bot (
            user_id BIGINT PRIMARY KEY,
            nickname VARCHAR(255),
            signup TIMESTAMP,
            trial_duration INT)"""
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS raw_materials (
                material_id INT AUTO_INCREMENT PRIMARY KEY,
                material_name VARCHAR(255)
            );"""
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS regions (
                region_id INT AUTO_INCREMENT PRIMARY KEY,
                region_name VARCHAR(255)
            );"""
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS user_raw_materials (
                user_id BIGINT,
                material_id INT,
                FOREIGN KEY (user_id) REFERENCES users_tg_bot(user_id),
                FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
            );"""
        )

        cursor.execute(
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
        ]

        # Проверка наличия данных в таблице raw_materials
        cursor.execute("SELECT COUNT(*) FROM raw_materials")
        count_raw_materials = cursor.fetchone()[0]
        if count_raw_materials == 0:
            for material in raw_materials:
                cursor.execute(
                    """INSERT INTO raw_materials (material_name)
                    VALUES (%s)
                    ON DUPLICATE KEY UPDATE material_name = VALUES(material_name)""",
                    (material,),
                )
            logger.info("Raw materials added to database")
        else:
            logger.info("Raw materials already exist in database")

        # Проверка наличия данных в таблице regions
        cursor.execute("SELECT COUNT(*) FROM regions")
        count_regions = cursor.fetchone()[0]
        if count_regions == 0:
            for region in regions:
                cursor.execute(
                    """INSERT INTO regions (region_name)
                    VALUES (%s)
                    ON DUPLICATE KEY UPDATE region_name = VALUES(region_name)""",
                    (region,),
                )
            logger.info("Regions added to database")
        else:
            logger.info("Regions already exist in database")

        self.connection.commit()
        # self.cursor.close()
        # self.connection.close()
        logger.info(
            "Таблицы users_tg_bot, raw_materials, regions созданы или уже существует."
        )

    def user_exists(self, user_id):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM users_tg_bot WHERE user_id = %s", (user_id,))
            exists = cursor.fetchone() is not None
            logger.info(f"User exists check for user_id {user_id}: {exists}")
            return exists
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при проверке существования пользователя: {err}")
        finally:
            cursor.close()
            connection.close()

    def add_user(self, user_id, nickname, signup_time):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            logger.info(
                f"Adding user {user_id} with nickname {nickname} and signup_time {signup_time}"
            )
            cursor.execute(
                """INSERT INTO users_tg_bot (user_id, nickname, signup)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                nickname = VALUES(nickname), signup = VALUES(signup)""",
                (user_id, nickname, signup_time),
            )
            connection.commit()
            logger.info(f"User {user_id} added to users_tg_bot")
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при добавлении пользователя: {err}")
        finally:
            cursor.close()
            connection.close()

    def add_user_raw_material(self, user_id, material_id):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            logger.info(f"Adding raw material {material_id} for user {user_id}")
            cursor.execute(
                """INSERT INTO user_raw_materials (user_id, material_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE material_id = VALUES(material_id)""",
                (user_id, material_id),
            )
            connection.commit()
            logger.info(
                f"User {user_id} with material {material_id} added to user_raw_materials"
            )
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при добавлении материала пользователя: {err}")
        finally:
            cursor.close()
            connection.close()

    def add_user_region(self, user_id, region_id):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            logger.info(f"Adding region {region_id} for user {user_id}")
            cursor.execute(
                """INSERT INTO user_regions (user_id, region_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE region_id = VALUES(region_id)""",
                (user_id, region_id),
            )
            connection.commit()
            logger.info(f"User {user_id} with region {region_id} added to user_regions")
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при добавлении региона пользователя: {err}")
        finally:
            cursor.close()
            connection.close()

    def get_product_id_by_name(self, product_name):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            logger.info(f"Getting product ID for product name: {product_name}")
            cursor.execute(
                "SELECT material_id FROM raw_materials WHERE material_name = %s",
                (product_name,),
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"Product ID {result[0]} found for product {product_name}")
            else:
                logger.error(f"Product ID not found for product: {product_name}")
            return result[0] if result else None
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при получении ID продукта: {err}")
        finally:
            cursor.close()
            connection.close()

    def get_region_id_by_name(self, region_name):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            logger.info(f"Getting region ID for region name: {region_name}")
            cursor.execute(
                "SELECT region_id FROM regions WHERE region_name = %s", (region_name,)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"Region ID {result[0]} found for region {region_name}")
            else:
                logger.error(f"Region ID not found for region: {region_name}")
            return result[0] if result else None
        except mysql.connector.Error as err:
            logger.error(f"Ошибка при получении ID региона: {err}")
        finally:
            cursor.close()
            connection.close()

    def get_signup_time(self, user_id):
        """
        Получение времени подписки пользователя.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT signup FROM users_tg_bot WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        signup_time = result[0] if result else None
        logger.debug(f"Время подписки пользователя {user_id}: {signup_time}")
        return signup_time

    def get_trial_duration(self, user_id):
        """
        Получение продолжительности пробного периода пользователя.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT trial_duration FROM users_tg_bot WHERE user_id = %s", (user_id,)
        )
        result = cursor.fetchone()
        trial_duration = result[0] if result else None
        logger.debug(
            f"Продолжительность пробного периода пользователя {user_id}: {trial_duration}"
        )
        return trial_duration

    def set_trial_duration(self, user_id, duration):
        """
        Установка продолжительности пробного периода для пользователя.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users_tg_bot SET trial_duration = %s WHERE user_id = %s",
            (duration, user_id),
        )
        self.connection.commit()
        logger.info(
            f"Установлена продолжительность пробного периода для пользователя {user_id}: {duration}"
        )
