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
        self.connection.commit()
        logger.info("Таблица users_tg_bot создана или уже существует.")

    def user_exists(self, user_id):
        """
        Проверка, существует ли пользователь с данным user_id в базе данных.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users_tg_bot WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone() is not None
        logger.debug(f"Пользователь {user_id} существует: {user_exists}")
        return user_exists

    def add_user(self, user_id, nickname, signup_time):
        """
        Добавление нового пользователя в базу данных.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users_tg_bot (user_id, nickname, signup, trial_duration) VALUES (%s, %s, %s, %s)",
            (user_id, nickname, signup_time, 2 * 24 * 60 * 60),
        )  # 2 дня в секундах
        self.connection.commit()
        logger.info(
            f"Добавлен новый пользователь: {user_id}, {nickname}, {signup_time}"
        )

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
