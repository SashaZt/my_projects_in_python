import mysql.connector
import os
import json
import glob
from datetime import datetime
from config import (
    db_config,
    use_table_payout_history,
)
from functions.get_id_models_from_sql import get_id_models
from functions.check_payout_history import check_payout_history

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
payout_history_path = os.path.join(temp_path, "payout_history")


def get_sql_payout_history():
    """
    Функция для отправки данных об истории в в Mysql
    """

    sql_data = check_payout_history()

    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    folder = os.path.join(payout_history_path, "*.json")
    files_json = glob.glob(folder)
    id_models = get_id_models()
    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            raw_json_str = f.read()
            try:
                data_json = json.loads(raw_json_str)
                data_json = json.loads(data_json)
            except json.JSONDecodeError as e:
                print(f"Ошибка декодирования JSON в файле {item}: {e}")
                continue
            except Exception as e:
                print(f"Произошла ошибка при работе с файлом {item}: {e}")
                continue
        try:
            mvtoken = str(data_json["user_id"])
        except:
            continue
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        try:
            payPeriodItems = data_json["payPeriodItems"]
        except:
            continue
        for item in payPeriodItems:
            payment_date = item["end_period_date"]
            paid = item["paid"]
            values = [model_id, payment_date, paid]
            json_sales_date_converted = datetime.strptime(
                payment_date, "%Y-%m-%d"
            ).date()
            json_seller_commission_price_converted = str(paid)
            json_data_tuple = (
                model_id,
                json_sales_date_converted,
                json_seller_commission_price_converted,
            )

            if json_data_tuple in sql_data:
                continue
            else:
                # SQL-запрос для вставки данных
                insert_query = f"""
                INSERT INTO {use_table_payout_history} (model_id, payment_date, paid)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, values)
            cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()
