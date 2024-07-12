import mysql.connector
import csv
from config import db_config, use_table_daily_sales
from loguru import logger

# Настройка логирования
logger.add("mysql_export.log", format="{time} {level} {message}", level="DEBUG")

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


# Функция для выгрузки данных в CSV
def export_mysql_to_csv():
    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        mysql_cursor.execute(
            f"SELECT buyer_user_id, sales_date, sales_time, seller_commission_price FROM {use_table_daily_sales}"
        )
        rows = mysql_cursor.fetchall()

        # Определение имени файла и полей
        csv_file = "mysql_daily_sales.csv"
        fieldnames = rows[0].keys() if rows else []

        # Запись данных в CSV
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Данные успешно выгружены в {csv_file}")

        mysql_cursor.close()
    except Exception as e:
        logger.error(f"Ошибка при выгрузке данных из MySQL: {e}")


# Выгрузка данных
export_mysql_to_csv()

# Закрытие подключения к MySQL
try:
    mysql_conn.close()
    logger.info("Подключение к MySQL закрыто")
except Exception as e:
    logger.error(f"Ошибка при закрытии подключения к MySQL: {e}")
