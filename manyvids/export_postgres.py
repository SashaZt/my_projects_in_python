import psycopg2
import csv
from pg_config import postgres_config, use_table_transactions
from loguru import logger

# Настройка логирования
logger.add("postgres_export.log", format="{time} {level} {message}", level="DEBUG")

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


# Функция для выгрузки данных в CSV
def export_postgres_to_csv():
    try:
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute(
            f"SELECT buyer_user_id, sales_date, sales_time, seller_commission_price FROM {use_table_transactions}"
        )
        rows = pg_cursor.fetchall()

        # Определение имен полей
        colnames = [desc[0] for desc in pg_cursor.description]
        csv_file = "postgres_transactions.csv"

        # Запись данных в CSV
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(colnames)
            writer.writerows(rows)

        logger.info(f"Данные успешно выгружены в {csv_file}")

        pg_cursor.close()
    except Exception as e:
        logger.error(f"Ошибка при выгрузке данных из PostgreSQL: {e}")


# Выгрузка данных
export_postgres_to_csv()

# Закрытие подключения к PostgreSQL
try:
    pg_conn.close()
    logger.info("Подключение к PostgreSQL закрыто")
except Exception as e:
    logger.error(f"Ошибка при закрытии подключения к PostgreSQL: {e}")
