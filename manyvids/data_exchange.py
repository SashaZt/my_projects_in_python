import mysql.connector
import psycopg2
from loguru import logger
from pg_config import postgres_config, use_table_transactions
from config import db_config, use_table_daily_sales
import schedule
import time

# Настройка логирования
logger.add("data_transfer.log", format="{time} {level} {message}", level="DEBUG")


def connect_to_mysql():
    try:
        mysql_conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
        )
        logger.info("Успешное подключение к MySQL")
        return mysql_conn
    except mysql.connector.Error as err:
        logger.error(f"Ошибка подключения к MySQL: {err}")
        raise


def connect_to_postgresql():
    try:
        pg_conn = psycopg2.connect(
            dbname=postgres_config["dbname"],
            user=postgres_config["user"],
            password=postgres_config["password"],
            host=postgres_config["host"],
            port=postgres_config["port"],
        )
        logger.info("Успешное подключение к PostgreSQL")
        return pg_conn
    except psycopg2.Error as err:
        logger.error(f"Ошибка подключения к PostgreSQL: {err}")
        raise


def get_existing_records(pg_conn):
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute(
        f"""
        SELECT buyer_user_id, sales_date, TO_CHAR(sales_time, 'HH24:MI:SS') as sales_time, seller_commission_price 
        FROM {use_table_transactions}
        """
    )
    existing_records = pg_cursor.fetchall()
    pg_cursor.close()
    logger.info(f"Извлечено {len(existing_records)} записей из PostgreSQL")

    return set(
        (str(record[0]), record[1], record[2], str(record[3]))
        for record in existing_records
    )


def transfer_new_data():
    mysql_conn = connect_to_mysql()
    pg_conn = connect_to_postgresql()

    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        pg_cursor = pg_conn.cursor()

        mysql_cursor.execute(
            f"SELECT buyer_username, model_id, buyer_stage_name, buyer_user_id, title, type_content, sales_date, TIME_FORMAT(sales_time, '%H:%i:%s') as sales_time, seller_commission_price, mvtoken, model_fm FROM {use_table_daily_sales}"
        )
        all_data = mysql_cursor.fetchall()
        logger.info(f"Получено {len(all_data)} записей из MySQL")

        existing_records = get_existing_records(pg_conn)

        new_records_count = 0
        for row in all_data:
            record = (
                str(row["buyer_user_id"]),
                row["sales_date"],
                row["sales_time"],
                str(row["seller_commission_price"]),
            )
            if record not in existing_records:
                pg_cursor.execute(
                    f"""
                    INSERT INTO {use_table_transactions} (buyer_username, model_id, buyer_stage_name, buyer_user_id, title, 
                                                          type_content, sales_date, sales_time, seller_commission_price, mvtoken, model_fm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
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
                new_records_count += 1

        pg_conn.commit()
        logger.info(f"Добавлено {new_records_count} новых записей в PostgreSQL")

        mysql_cursor.close()
        pg_cursor.close()
    except Exception as e:
        logger.error(f"Ошибка при переносе новых данных: {e}")
        raise
    finally:
        mysql_conn.close()
        pg_conn.close()


def main_exchange():
    try:
        transfer_new_data()
    except Exception as e:
        logger.error(f"Не удалось перенести новые данные: {e}")


main_exchange()

schedule.every(30).minutes.do(main_exchange)

while True:
    schedule.run_pending()
    time.sleep(1)
