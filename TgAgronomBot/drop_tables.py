import mysql.connector
from configuration.config import DB_CONFIG
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_connection():
    return mysql.connector.connect(**DB_CONFIG)


def drop_tables():
    connection = create_connection()
    cursor = connection.cursor()

    try:
        logger.info("Dropping table: user_raw_materials")
        cursor.execute("DROP TABLE IF EXISTS user_raw_materials")
        connection.commit()

        logger.info("Dropping table: user_regions")
        cursor.execute("DROP TABLE IF EXISTS user_regions")
        connection.commit()

        logger.info("Dropping table: users_tg_bot")
        cursor.execute("DROP TABLE IF EXISTS users_tg_bot")
        connection.commit()

        logger.info("Tables dropped successfully")

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    drop_tables()
