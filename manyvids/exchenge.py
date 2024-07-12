import mysql.connector
import psycopg2
from datetime import datetime
from loguru import logger
from pg_config import postgres_config, use_table_transactions
from config import db_config, use_table_daily_sales

# Настройка логирования
logger.add("info.log", format="{time} {level} {message}", level="DEBUG")

# Подключение к MySQL
try:
    mysql_conn = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
    )
    logger.info("Успешное подключение к MySQL")
except mysql.connector.Error as err:
    logger.error(f"Ошибка подключения к MySQL: {err}")
    raise

# Подключение к PostgreSQL
try:
    pg_conn = psycopg2.connect(
        dbname=postgres_config["dbname"],
        user=postgres_config["user"],
        password=postgres_config["password"],
        host=postgres_config["host"],
        port=postgres_config["port"],
    )
    logger.info("Успешное подключение к PostgreSQL")
except psycopg2.Error as err:
    logger.error(f"Ошибка подключения к PostgreSQL: {err}")
    raise


def transfer_all_data():
    try:
        # Создание курсоров для работы с базами данных
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        pg_cursor = pg_conn.cursor()

        # Получение всех данных из MySQL
        mysql_cursor.execute(f"SELECT * FROM {use_table_daily_sales}")
        all_data = mysql_cursor.fetchall()
        logger.info(f"Получено {len(all_data)} записей из MySQL")

        # Очистка таблицы в PostgreSQL перед переносом всех данных (опционально)
        pg_cursor.execute(f"TRUNCATE TABLE {use_table_transactions}")
        logger.info(f"Таблица {use_table_transactions} очищена в PostgreSQL")

        # Перенос данных в PostgreSQL
        for row in all_data:
            pg_cursor.execute(
                f"""
                INSERT INTO {use_table_transactions} (id, buyer_username, model_id, buyer_stage_name, buyer_user_id, title, 
                                                      type_content, sales_date, sales_time, seller_commission_price, mvtoken, model_fm)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["id"],
                    row["buyer_username"],
                    row["model_id"],
                    row["buyer_stage_name"],
                    row["buyer_user_id"],
                    row["title"],
                    row["type_content"],
                    row["sales_date"],
                    row["sales_time"],
                    row["seller_commission_price"],
                    row["mvtoken"],
                    row["model_fm"],
                ),
            )

        # Фиксация изменений в PostgreSQL
        pg_conn.commit()
        logger.info(f"Все данные успешно перенесены в PostgreSQL")

        # Закрытие курсоров
        mysql_cursor.close()
        pg_cursor.close()
    except Exception as e:
        logger.error(f"Ошибка при переносе всех данных: {e}")
        raise


def transfer_new_data(last_transfer_date, last_transfer_time):
    try:
        # Создание курсоров для работы с базами данных
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        pg_cursor = pg_conn.cursor()

        # Получение новых данных из MySQL
        mysql_cursor.execute(
            f"""
            SELECT * FROM {use_table_daily_sales}
            WHERE sales_date > %s OR (sales_date = %s AND sales_time > %s)
            """,
            (last_transfer_date, last_transfer_date, last_transfer_time),
        )
        new_data = mysql_cursor.fetchall()
        logger.info(f"Получено {len(new_data)} новых записей из MySQL")

        # Перенос новых данных в PostgreSQL
        for row in new_data:
            pg_cursor.execute(
                f"""
                INSERT INTO {use_table_transactions} (id, buyer_username, model_id, buyer_stage_name, buyer_user_id, title, 
                                                      type_content, sales_date, sales_time, seller_commission_price, mvtoken, model_fm)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["id"],
                    row["buyer_username"],
                    row["model_id"],
                    row["buyer_stage_name"],
                    row["buyer_user_id"],
                    row["title"],
                    row["type_content"],
                    row["sales_date"],
                    row["sales_time"],
                    row["seller_commission_price"],
                    row["mvtoken"],
                    row["model_fm"],
                ),
            )

        # Фиксация изменений в PostgreSQL
        pg_conn.commit()
        logger.info(f"Новые данные успешно перенесены в PostgreSQL")

        # Закрытие курсоров
        mysql_cursor.close()
        pg_cursor.close()
    except Exception as e:
        logger.error(f"Ошибка при переносе новых данных: {e}")
        raise


# Перенос всех данных (первоначальная настройка)
try:
    transfer_all_data()
except Exception as e:
    logger.error(f"Не удалось перенести все данные: {e}")

# Перенос только новых данных
try:
    last_transfer_date = datetime.strptime("2023-01-01", "%Y-%m-%d").date()
    last_transfer_time = datetime.strptime("00:00:00", "%H:%M:%S").time()
    transfer_new_data(last_transfer_date, last_transfer_time)
except Exception as e:
    logger.error(f"Не удалось перенести новые данные: {e}")

# Закрытие подключений к базам данных
try:
    mysql_conn.close()
    pg_conn.close()
    logger.info("Подключения к базам данных закрыты")
except Exception as e:
    logger.error(f"Ошибка при закрытии подключений к базам данных: {e}")
