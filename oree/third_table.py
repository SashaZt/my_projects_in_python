import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pandas as pd
from sqlalchemy import create_engine

import html
from bs4 import BeautifulSoup
import mysql.connector
import time
from datetime import datetime, timedelta
import os
import sys
import json
import pandas as pd
from datetime import datetime


def load_connection_to_sql_vdr():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "connection_to_sql.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


def load_connection_to_sql_rdn():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "connection_to_sql_rdn.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


def get_sql_vdr():
    config_vdr = load_connection_to_sql_vdr()
    db_config_vdr = config_vdr["db_config"]
    use_table_vdr = config_vdr["other_config"]["use_table"]
    cnx_vdr = mysql.connector.connect(**db_config_vdr)
    cursor_vdr = cnx_vdr.cursor()
    current_date = str(datetime.now().strftime("%Y-%m-%d"))
    """Добавляем час для получение наднных без задержки"""
    current_hour = int(datetime.now().hour) + 2
    # current_hour = int(4)

    # query = f"SELECT CURDATE() as sales_date, sales_time, amount_time, price_time, delivery_date, delivery_time, data_and_time_data_download, hour FROM {use_table_vdr};"
    query = f"SELECT sales_date, sales_time, amount_time, price_time, delivery_date, delivery_time, data_and_time_data_download, hour FROM {use_table_vdr} WHERE delivery_date = '{current_date}' AND hour = '{current_hour}';"

    cursor_vdr.execute(query)

    # Получение результатов запроса
    results_vdr = cursor_vdr.fetchall()

    # Получение названий столбцов
    columns = [desc[0] for desc in cursor_vdr.description]

    # Конвертация результатов в DataFrame
    df_vdr = pd.DataFrame(results_vdr, columns=columns)
    # Преобразование sales_time в тип timedelta, если он ещё не такой
    df_vdr["sales_time"] = pd.to_timedelta(df_vdr["sales_time"])

    # Извлечение времени без даты
    df_vdr["sales_time"] = (
        df_vdr["sales_time"].dt.components.hours.astype(str).str.zfill(2)
        + ":"
        + df_vdr["sales_time"].dt.components.minutes.astype(str).str.zfill(2)
        + ":"
        + df_vdr["sales_time"].dt.components.seconds.astype(str).str.zfill(2)
    )

    cursor_vdr.close()

    if df_vdr.empty:
        print(f"Нету данныех за дату {current_date} и время {current_hour}")
        return None

    else:
        print("Есть данныее")
        return df_vdr


def get_sql_rdn():
    config_rdn = load_connection_to_sql_rdn()
    db_config_rdn = config_rdn["db_config"]
    use_table_rdn = config_rdn["other_config"]["use_table"]
    cnx_rdn = mysql.connector.connect(**db_config_rdn)
    cursor_rdn = cnx_rdn.cursor()

    query = f"SELECT delivery_date, hour, price, sales_volume, purchase_volume, declared_sales_volume, declared_volume_of_purchase FROM {use_table_rdn} WHERE delivery_date = CURDATE();"
    # query = f"SELECT CURDATE() as delivery_date, hour, price, sales_volume, purchase_volume, declared_sales_volume, declared_volume_of_purchase FROM {use_table_rdn};"
    cursor_rdn.execute(query)
    results_rdn = cursor_rdn.fetchall()
    # Получение названий столбцов
    columns = [desc[0] for desc in cursor_rdn.description]

    # Конвертация результатов в DataFrame
    df_rdn = pd.DataFrame(results_rdn, columns=columns)
    cursor_rdn.close()
    cnx_rdn.close()
    return df_rdn


def joining_tables():
    df_rdn = get_sql_rdn()
    df_vdr = get_sql_vdr()

    if df_vdr is not None and df_rdn is not None:
        current_date = str(datetime.now().strftime("%Y-%m-%d"))
        """Добавляем час для получение наднных без задержки"""
        current_hour = int(datetime.now().hour) + 2
        # current_hour = int(4)

        df_rdn["hour"] = df_rdn["hour"].astype(int)
        df_rdn["delivery_date"] = pd.to_datetime(df_rdn["delivery_date"])
        matching_rdn_row = df_rdn[
            (df_rdn["delivery_date"] == pd.to_datetime(current_date))
            & (df_rdn["hour"] == current_hour)
        ]
        print(
            f"Total columns: {len(df_vdr.columns)}, Unique columns: {len(set(df_vdr.columns))}"
        )

        matching_rdn_row = matching_rdn_row.add_suffix("_rdn")
        df_vdr["hour"] = df_vdr["hour"].astype(int)
        df_vdr["delivery_date"] = pd.to_datetime(df_vdr["delivery_date"])
        matching_vdr_row = df_vdr[
            (df_vdr["delivery_date"] == pd.to_datetime(current_date))
            & (df_vdr["hour"] == current_hour)
        ]

        matching_vdr_row = matching_vdr_row.add_suffix("_vdr")
        # Исключаем колонку hour_vdr из вывода
        matching_vdr_row = matching_vdr_row.drop(columns=["hour_vdr"])

        num_rows_to_duplicate = len(matching_vdr_row)
        duplicated_rdn_rows = pd.concat(
            [matching_rdn_row] * num_rows_to_duplicate, ignore_index=True
        )
        combined_df = pd.concat(
            [
                duplicated_rdn_rows.reset_index(drop=True),
                matching_vdr_row.reset_index(drop=True),
            ],
            axis=1,
        )

        # Находим индекс колонки 'declared_volume_of_purchase_rdn'
        idx = combined_df.columns.get_loc("declared_volume_of_purchase_rdn") + 1

        # Расчет разности и добавление новой колонки на нужное место
        combined_df.insert(
            idx,
            "difference_rdn",
            combined_df["declared_sales_volume_rdn"]
            - combined_df["declared_volume_of_purchase_rdn"],
        )
        combined_df["data_and_time_data_download_vdr"] = pd.to_datetime(
            combined_df["data_and_time_data_download_vdr"], format="%d.%m.%Y_%H:%M:%S"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        return combined_df
    else:
        combined_df = None
        print("пропускаем")


def write_to_sql():
    config_rdn = load_connection_to_sql_rdn()
    username = config_rdn["other_config"]["user"]
    password = config_rdn["other_config"]["password"]
    hostname = config_rdn["other_config"]["host"]
    database_name = config_rdn["other_config"]["database"]
    combined_df = joining_tables()
    if combined_df is not None:
        # Создание строки подключения
        database_connection_string = (
            f"mysql+mysqlconnector://{username}:{password}@{hostname}/{database_name}"
        )

        # Создание движка для подключения
        engine = create_engine(database_connection_string)

        # Подготовка DataFrame для записи. Здесь combined_df - ваш DataFrame
        combined_df["sales_date_vdr"] = combined_df["sales_date_vdr"].astype(str)
        combined_df["sales_time_vdr"] = combined_df["sales_time_vdr"].astype(str)
        combined_df["delivery_date_vdr"] = combined_df["delivery_date_vdr"].astype(str)
        combined_df["delivery_date_rdn"] = combined_df["delivery_date_rdn"].astype(str)

        # Запись DataFrame в SQL таблицу
        combined_df.to_sql("third_table", con=engine, if_exists="append", index=False)

    else:
        print("Пропускаем час")


# if __name__ == "__main__":
#     # joining_tables()
#     write_to_sql()



def run_at_specific_timee_ach_hour(target_minute, target_second):
    while True:
        now = datetime.now()
        target_time = now.replace(
            minute=target_minute, second=target_second, microsecond=0
        )

        # Если целевое время уже прошло, устанавливаем его на следующий час
        if target_time < now:
            target_time += timedelta(hours=1)

        print(f"Скрипт запланирован на {target_time}")

        # Ожидание до целевого времени
        while datetime.now() < target_time:
            time.sleep(1)
        # Вызов функции после достижения целевого времени
        write_to_sql()
        # get_data()
        # json_to_sql()
        time.sleep(1)  # Короткая пауза перед планированием следующего запуска


if __name__ == "__main__":
    run_at_specific_timee_ach_hour(5, 00)
    # write_to_sql()