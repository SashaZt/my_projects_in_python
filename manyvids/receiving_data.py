import csv
import glob
import json
import os
import random
from collections import defaultdict
from datetime import datetime

import gspread
import mysql.connector
import pandas as pd
import requests
from oauth2client.service_account import ServiceAccountCredentials

from config import db_config, use_bd, use_table_daily_sales, use_table_monthly_sales, use_table_payout_history, \
    use_table_login_pass, headers
from proxi import proxies
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, 'cookies')
login_pass_path = os.path.join(temp_path, 'login_pass')
daily_sales_path = os.path.join(temp_path, 'daily_sales')
monthly_sales_path = os.path.join(temp_path, 'monthly_sales')
payout_history_path = os.path.join(temp_path, 'payout_history')


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


def get_requests_daily_sales():
    proxi = proxy_random()
    filename_cookies = os.path.join(cookies_path, '*.json')
    files_json = glob.glob(filename_cookies)
    for item in files_json:
        with open(item, 'r') as f:
            cookies = json.load(f)
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[1].replace('.json', '')
        # Создание сессии
        session = requests.Session()

        # Добавление кук в сессию
        for name, value in cookies_dict.items():
            session.cookies.set(name, value)

        data = {
            'mvtoken': mvtoken,
            'day': '',
            'month': '1',
            'filterYear': '2024',
        }
        mvtoken_value = data['mvtoken']
        month_value = data['month']
        filterYear_value = data['filterYear']
        filename = os.path.join(daily_sales_path, f'{mvtoken_value}_{month_value}_{filterYear_value}.json')
        if not os.path.exists(filename):
            response = session.post('https://www.manyvids.com/includes/get_earnings.php', headers=headers,
                                    proxies=proxi, data=data)

            json_data = response.json()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        # Подключение к базе данных
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        folder = os.path.join(daily_sales_path, '*.json')
        files_json = glob.glob(folder)
        models_fms = get_id_models_csv()
        for item in files_json:
            with open(item, 'r', encoding="utf-8") as f:
                data_json = json.load(f)

            dayItems = data_json['dayItems']
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


def get_requests_monthly_sales():
    proxi = proxy_random()
    filename_cookies = os.path.join(cookies_path, '*.json')
    files_json = glob.glob(filename_cookies)
    for item in files_json:
        with open(item, 'r') as f:
            cookies = json.load(f)
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[1].replace('.json', '')
        session = requests.Session()

        # Добавление кук в сессию
        for name, value in cookies.items():
            session.cookies.set(name, value)

        data = {
            'mvtoken': mvtoken,
            'year': '2023',
        }

        response = session.post('https://www.manyvids.com/includes/get_earnings.php', headers=headers,
                                data=data, proxies=proxi)
        json_data = response.json()
        mvtoken_value = data['mvtoken']
        filterYear_value = data['year']
        filename = os.path.join(monthly_sales_path, f'{mvtoken_value}_{filterYear_value}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def get_requests_payout_history():
    proxi = proxy_random()
    filename_cookies = os.path.join(cookies_path, '*.json')
    files_json = glob.glob(filename_cookies)
    for item in files_json:
        with open(item, 'r') as f:
            cookies = json.load(f)
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[1].replace('.json', '')
        session = requests.Session()

        # Добавление кук в сессию
        for name, value in cookies.items():
            session.cookies.set(name, value)

        data = {
            'mvtoken': mvtoken,
            'year': '2023',
        }
        mvtoken_value = data['mvtoken']
        filterYear_value = data['year']
        filename = os.path.join(payout_history_path, f'{mvtoken_value}_{filterYear_value}.json')
        if not os.path.exists(filename):
            response = session.post(
                'https://www.manyvids.com/includes/get_payperiod_earnings.php',
                headers=headers,
                data=data,
                proxies=proxi
            )

            json_data = response.json()

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


if __name__ == '__main__':
    get_requests_daily_sales()
    get_requests_monthly_sales()
    get_requests_payout_history()
