import mysql.connector
from datetime import datetime, timedelta
import os
import logging
import glob
import json
from functions.get_id_models_from_sql import get_id_models_from_sql
from functions.check_data_day_zcnx import check_data_day_zcnx
import psycopg2
from psycopg2 import sql
from pg_config import postgres_config, use_table_transactions
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
daily_sales_path = os.path.join(temp_path, "daily_sales")


def insert_data_to_postgres():
    sql_data = check_data_day_zcnx()

    # Подключение к базе данных
    connection = psycopg2.connect(**postgres_config)
    cursor = connection.cursor()

    logging.info("Соединение с PostgreSQL установлено")
    folder = os.path.join(daily_sales_path, "*.json")
    files_json = glob.glob(folder)
    models_fms = get_id_models_from_sql()

    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            raw_json_str = f.read()
            data_json = json.loads(raw_json_str)
            data_json = json.loads(data_json)
        try:
            dayItems = data_json["dayItems"]
        except:
            continue
        try:
            buyer_username = dayItems[0]["buyer_username"]
        except IndexError:
            logging.info(f"dayItems пустой в файле {item}.")
            continue

        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]

        for day in dayItems:
            buyer_stage_name = day["buyer_stage_name"]
            buyer_user_id = day["buyer_user_id"]
            title = day["title"]
            type_content = day["type"]
            sales_date = day["sales_date"].replace("/", ".")
            sales_date = datetime.strptime(sales_date, "%d.%m.%Y").strftime("%Y-%m-%d")
            sales_time = day["sales_time"]
            seller_commission_price = day["seller_commission_price"]
            model_id = day["model_id"]

            models_fm = [key for key, value in models_fms.items() if value == model_id]
            try:
                model_fm = models_fm[0]
            except:
                model_fm = None

            values = [
                buyer_username,
                buyer_stage_name,
                buyer_user_id,
                title,
                type_content,
                sales_date,
                sales_time,
                seller_commission_price,
                model_id,
                mvtoken,
                model_fm,
            ]

            json_sales_date_converted = datetime.strptime(sales_date, "%Y-%m-%d").date()

            # Преобразование времени в timedelta
            hours, minutes = map(int, sales_time.split(":"))
            json_sales_time_converted = timedelta(hours=hours, minutes=minutes)

            # Преобразование цены в строку (если это необходимо)
            json_seller_commission_price_converted = str(seller_commission_price)

            # Теперь данные из JSON имеют формат, схожий с данными из SQL
            json_data_tuple = (
                buyer_user_id,
                json_sales_date_converted,
                json_sales_time_converted,
                json_seller_commission_price_converted,
            )
            if json_data_tuple in sql_data:
                continue
            else:
                # Формирование запроса для вставки данных
                insert_query = sql.SQL(
                    """
                    INSERT INTO {table} (
                        buyer_username, buyer_stage_name, buyer_user_id, title, type_content, sales_date, sales_time,
                        seller_commission_price, model_id, mvtoken, model_fm
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                ).format(table=sql.Identifier("public", use_table_transactions))

                # Выполнение запроса для каждой строки данных
                cursor.execute(insert_query, values)

                # Фиксация изменений
                connection.commit()
                logging.info("Данные успешно вставлены")

    cursor.close()
    connection.close()
    logging.info("Соединение с PostgreSQL закрыто")
