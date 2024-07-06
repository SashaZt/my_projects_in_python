import mysql.connector
import os
from datetime import datetime
import logging
import glob
import json
from config import (
    db_config,
    use_table_chat,
)
from functions.get_id_models_from_sql import get_id_models_from_sql
from functions.check_chat import check_chat
from functions.get_latest_chat_date import get_latest_chat_date

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
chat_path = os.path.join(temp_path, "chat")

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)


def get_sql_chat():
    """
    Функция для отправки данных об чатах в Mysql
    """
    sql_data = check_chat()
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    latest_date = get_latest_chat_date()
    folder = os.path.join(chat_path, "*.json")
    files_json = glob.glob(folder)
    models_fms = get_id_models_from_sql()

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
            json_data = data_json["conversations"]
        except:
            json_data = None
            continue
        for dj in json_data["list"]:
            msg_last_id = dj["msg_last_id"]  # id чата
            sender_id = dj["sender_id"]  # id  модели
            user_id = dj["user_id"]  # id  клиента
            msg_date = dj["msg_date"]  # дата  чата
            msg_date = datetime.strptime(msg_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            # log_message(f'в Чате {msg_date} последняя дата {latest_date}')

            if msg_date == latest_date:
                should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
                logging.info("Стоп")
                break  # Прерываем внутренний цикл
            date_part, time_part = msg_date.split(" ")
            json_data_chat = (msg_last_id, msg_date)
            values = [msg_last_id, user_id, sender_id, date_part, time_part]

            if not json_data_chat in sql_data:
                # SQL-запрос для вставки данных
                insert_query = f"""
                    INSERT IGNORE INTO {use_table_chat}
                    (msg_last_id, user_id, sender_id, date_part, time_part)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                cursor.execute(insert_query, values)

                cnx.commit()  # Подтверждение изменений
            else:
                break
