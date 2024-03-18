import csv
import datetime
import glob
import json
import os
import random
import time
from datetime import datetime, timedelta
import numpy as np
import gspread
import mysql.connector
import pandas as pd
import requests
import schedule
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
from config import db_config, use_table_daily_sales, headers, host, user, password, database, use_table_payout_history, \
    use_table_monthly_sales, use_table_chat, spreadsheet_id, time_a, time_b
from proxi import proxies
from collections import defaultdict

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, 'cookies')
login_pass_path = os.path.join(temp_path, 'login_pass')
daily_sales_path = os.path.join(temp_path, 'daily_sales')
monthly_sales_path = os.path.join(temp_path, 'monthly_sales')
payout_history_path = os.path.join(temp_path, 'payout_history')
pending_custom_path = os.path.join(temp_path, 'pending_custom')


def get_id_models_csv():
    model_dict = {}

    # Открываем файл
    with open('model_id.csv', mode='r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')  # Используем точку с запятой как разделитель
        for row in reader:
            key = row[0]
            value = row[1]
            model_dict[key] = value

    # Теперь model_dict содержит данные из CSV
    return model_dict


def get_google():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds_file = os.path.join(current_directory, 'access.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


def get_id_models():
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Выполнение запроса для получения уникальных значений
    cursor.execute("SELECT DISTINCT model_fm, mvtoken FROM manyvids.daily_sales")

    dict_models = {}
    # Получение и вывод результатов
    results = cursor.fetchall()
    for row in results:
        model_id, mvtoken = row
        dict_models[model_id] = mvtoken
    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    return dict_models


def proxy_random():
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # Возвращаем словарь с прокси
    return {
        "http": formatted_proxy,
        "https": formatted_proxy
    }


def get_sql_check_chat():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute("""
        SELECT msg_last_id, CONCAT(date_part, ' ', time_part) AS datetime FROM manyvids.chat;
    """)
    data = {(row[0], row[1]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


def get_requests(month, filterYear):
    max_attempts = 5
    attempts = 0
    # def get_requests():
    filename_cookies = os.path.join(cookies_path, '*.json')
    files_json = glob.glob(filename_cookies)
    for item in files_json:
        sleep_time = random.randint(time_a, time_b)
        proxi = proxy_random()
        with open(item, 'r') as f:
            cookies_list = json.load(f)

        # # Заполнение словаря cookies

        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}

        session = requests.Session()
        session.cookies.update(cookies_dict)
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[1].replace('.json', '')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_datetime}] Модель {mvtoken}')
        data_day = {
            'mvtoken': mvtoken,
            'day': '',
            'month': month,
            'filterYear': filterYear,
        }
        # data_month = {
        #     'mvtoken': mvtoken,
        #     'year': filterYear,
        # }
        data_payout_history = {
            'mvtoken': mvtoken,
            'year': filterYear,
        }

        mvtoken_value = data_day['mvtoken']
        month_value = data_day['month']
        filterYear_value = data_day['filterYear']
        """День"""
        filename_day = os.path.join(daily_sales_path, f'{mvtoken_value}_{month_value}_{filterYear_value}.json')
        while attempts < max_attempts:
            try:
                response_day = session.post('https://www.manyvids.com/includes/get_earnings.php', headers=headers,
                                            proxies=proxi, data=data_day)
                break  # Если запрос успешен, выходим из цикла
            except requests.exceptions.ConnectionError as e:
                print(f"Попытка {attempts + 1} не удалась: {e}")
                attempts += 1
                time.sleep(sleep_time)  # Задержка перед следующей попыткой
        json_data_day = response_day.json()

        with open(filename_day, 'w', encoding='utf-8') as f:
            json.dump(json_data_day, f, ensure_ascii=False, indent=4)  # Записываем в файл

def get_sql_data_data_day():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute("""
        SELECT buyer_user_id, sales_date, sales_time, seller_commission_price FROM manyvids.daily_sales;
    """)
    data = {(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data

def get_sql_data_day():
    # Получение данных из SQL
    sql_data = get_sql_data_data_day()

    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # # Очистка таблицы перед вставкой новых данных
    # truncate_query = f"TRUNCATE TABLE {use_table_daily_sales}"
    # cursor.execute(truncate_query)
    # cnx.commit()  # Подтверждение изменений

    folder = os.path.join(daily_sales_path, '*.json')
    files_json = glob.glob(folder)
    models_fms = get_id_models_csv()

    for item in files_json:
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)

        try:
            dayItems = data_json['dayItems']
        except:
            continue
        try:
            buyer_username = dayItems[0]['buyer_username']
        except IndexError:

            print(f"dayItems пустой в файле {item}.")
            continue

        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]

        for day in dayItems:
            try:
                buyer_stage_name = day['buyer_stage_name']
                buyer_user_id = day['buyer_user_id']
                title = day['title']
                type_content = day['type']
                sales_date = day['sales_date'].replace('/', '.')
                sales_date = datetime.strptime(sales_date, '%d.%m.%Y').strftime('%Y-%m-%d')
                sales_time = day['sales_time']
                seller_commission_price = day['seller_commission_price']
                model_id = day['model_id']

                models_fm = [key for key, value in models_fms.items() if value == model_id]
                try:
                    model_fm = models_fm[0]
                except:
                    model_fm = None

                values = [buyer_username, buyer_stage_name, buyer_user_id, title, type_content, sales_date,
                          sales_time,
                          seller_commission_price, model_id, mvtoken, model_fm]

                json_sales_date_converted = datetime.strptime(sales_date, '%Y-%m-%d').date()

                # Преобразование времени в timedelta
                hours, minutes = map(int, sales_time.split(':'))
                json_sales_time_converted = timedelta(hours=hours, minutes=minutes)

                # Преобразование цены в строку (если это необходимо)
                json_seller_commission_price_converted = str(seller_commission_price)

                # Теперь данные из JSON имеют формат, схожий с данными из SQL
                json_data_tuple = (buyer_user_id, json_sales_date_converted, json_sales_time_converted,
                                   json_seller_commission_price_converted)
                if json_data_tuple in sql_data:
                    continue
                else:
                    # print("Новые данные, нужно добавить в SQL")

                    # SQL-запрос для вставки данных
                    insert_query = f"""
                    INSERT INTO {use_table_daily_sales} (buyer_username, buyer_stage_name, buyer_user_id, title, type_content, sales_date, sales_time,
                              seller_commission_price, model_id, mvtoken,model_fm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, values)
                    cnx.commit()  # Подтверждение изменений

            except mysql.connector.Error as err:
                print("Ошибка при добавлении данных:", err)
                break  # Прерываем цикл в случае ошибки

    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()

if __name__ == '__main__':
    print('Введите месяц')
    month = input()
    print('Введите год')
    filterYear = input()
    get_requests(month, filterYear)
    get_sql_data_day()
