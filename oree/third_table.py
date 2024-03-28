import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pandas as pd

import html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

    query = f"SELECT CURDATE() as sales_date, sales_time, amount_time, price_time, delivery_date, delivery_time, data_and_time_data_download, hour FROM {use_table_vdr};"
    cursor_vdr.execute(query)

    # Получение результатов запроса
    results_vdr = cursor_vdr.fetchall()

    # Получение названий столбцов
    columns = [desc[0] for desc in cursor_vdr.description]

    # Конвертация результатов в DataFrame
    df_vdr = pd.DataFrame(results_vdr, columns=columns)
    # Преобразование sales_time в тип timedelta, если он ещё не такой
    df_vdr['sales_time'] = pd.to_timedelta(df_vdr['sales_time'])

    # Извлечение времени без даты
    df_vdr['sales_time'] = df_vdr['sales_time'].dt.components.hours.astype(str).str.zfill(2) + ':' + df_vdr['sales_time'].dt.components.minutes.astype(str).str.zfill(2) + ':' + df_vdr['sales_time'].dt.components.seconds.astype(str).str.zfill(2)




    cursor_vdr.close()
    cnx_vdr.close()
    return df_vdr


def get_sql_rdn():
    config_rdn = load_connection_to_sql_rdn()
    db_config_rdn = config_rdn["db_config"]
    use_table_rdn = config_rdn["other_config"]["use_table"]
    cnx_rdn = mysql.connector.connect(**db_config_rdn)
    cursor_rdn = cnx_rdn.cursor()

    query =       f"SELECT CURDATE() as delivery_date, hour, price, sales_volume, purchase_volume, declared_sales_volume, declared_volume_of_purchase FROM {use_table_rdn};"
    cursor_rdn.execute(query)
    results_rdn = cursor_rdn.fetchall()
    # Получение названий столбцов
    columns = [desc[0] for desc in cursor_rdn.description]

    # Конвертация результатов в DataFrame
    df_rdn = pd.DataFrame(results_rdn, columns=columns)

    """Завтра включить"""
    # cursor_rdn.execute(
    #     f"SELECT delivery_date, hour, price, sales_volume, purchase_volume, declared_sales_volume, declared_volume_of_purchase FROM {use_table_rdn} WHERE delivery_date = CURDATE();"
    # )
    # Получение и вывод результатов
    cursor_rdn.close()
    cnx_rdn.close()
    return df_rdn

def joining_tables():
    rdn = get_sql_rdn()
    vdr = get_sql_vdr()
    
if __name__ == "__main__":
    joining_tables()