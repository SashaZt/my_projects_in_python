import sqlite3

from config.config import DB_PATH
from config.logger_setup import logger


def init_db():
    """
    Инициализация базы данных.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Логируем начало создания таблиц
        logger.info("Инициализация базы данных начата.")

        # Создаем таблицу для групп
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_link TEXT UNIQUE,
                subscription_status BOOLEAN DEFAULT 0
            )
        """
        )

        logger.info("Таблица 'groups' успешно создана (или уже существует).")

        # Создаем таблицу для сообщений
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        logger.info("Таблица 'messages' успешно создана (или уже существует).")

        conn.commit()
        logger.info("Инициализация базы данных завершена успешно.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто.")


def get_connection():
    """
    Получить соединение с базой данных.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        logger.info("Успешное подключение к базе данных.")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise
