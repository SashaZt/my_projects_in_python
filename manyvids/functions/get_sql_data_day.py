import mysql.connector
from datetime import datetime, timedelta
import os
from loguru import logger
import logging
import glob
import json
from functions.get_id_models_from_sql import get_id_models
from functions.check_data_day import check_data_day
from config import (
    db_config,
    use_table_daily_sales,
)

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
daily_sales_path = os.path.join(temp_path, "daily_sales")

# Настройка базовой конфигурации логирования
logger.remove()  # Удаляем все ранее добавленные обработчики
logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",  # Формат сообщения
    level="DEBUG",  # Уровень логирования
    encoding="utf-8",  # Кодировка
    mode="w",  # Перезапись файла при каждом запуске
)


def get_sql_data_day():
    """
    Функция для отправки данных об дневных продажах в Mysql
    """
    # Получение данных из SQL
    sql_data = check_data_day()

    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # # Очистка таблицы перед вставкой новых данных
    # truncate_query = f"TRUNCATE TABLE {use_table_daily_sales}"
    # cursor.execute(truncate_query)
    # cnx.commit()  # Подтверждение изменений

    folder = os.path.join(daily_sales_path, "*.json")
    files_json = glob.glob(folder)
    models_fms = get_id_models()

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
            try:
                buyer_stage_name = day["buyer_stage_name"]
                buyer_user_id = day["buyer_user_id"]
                title = day["title"]
                type_content = day["type"]
                sales_date = day["sales_date"].replace("/", ".")
                sales_date = datetime.strptime(sales_date, "%d.%m.%Y").strftime(
                    "%Y-%m-%d"
                )
                sales_time = day["sales_time"]
                seller_commission_price = day["seller_commission_price"]
                model_id = day["model_id"]

                models_fm = [
                    key for key, value in models_fms.items() if value == model_id
                ]
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
                    # mvtoken,
                    model_fm,
                ]

                json_sales_date_converted = datetime.strptime(
                    sales_date, "%Y-%m-%d"
                ).date()

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
                    # log_message("Новые данные, нужно добавить в SQL")

                    # SQL-запрос для вставки данных
                    insert_query = f"""
                    INSERT INTO {use_table_daily_sales} (buyer_username, buyer_stage_name, buyer_user_id, title, type_content, sales_date, sales_time,
                              seller_commission_price, model_id, model_fm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, values)
                    cnx.commit()  # Подтверждение изменений

            except mysql.connector.Error as err:
                logging.info("Ошибка при добавлении данных:", err)
                break  # Прерываем цикл в случае ошибки

    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()
