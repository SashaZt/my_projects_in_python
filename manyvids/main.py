import csv
import glob
import time
from collections import defaultdict
import numpy as np
import pandas as pd
import json
import os
import random
from collections import defaultdict
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
from bs4 import BeautifulSoup

import gspread
import mysql.connector
import pandas as pd
import requests
from oauth2client.service_account import ServiceAccountCredentials

from config import db_config, use_bd, use_table_daily_sales, use_table_monthly_sales, use_table_payout_history, \
    use_table_login_pass, headers, host, user, password, database,use_table_chat
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
pending_custom_path = os.path.join(temp_path, 'pending_custom')
chat_path = os.path.join(temp_path, 'chat')


def get_google():
    spreadsheet_id = '145mee2ZsApZXiTnASng4lTzbocYCJWM5EDksTx_FVYY'
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\scrap_tutorial-master\\manyvids\\access.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    return client, spreadsheet


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, daily_sales_path, monthly_sales_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [daily_sales_path, monthly_sales_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


# def proxy_random():
#     proxy = random.choice(proxies)
#     proxy_host = proxy[0]
#     proxy_port = proxy[1]
#     proxy_user = proxy[2]
#     proxy_pass = proxy[3]
#     formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
#
#     # Возвращаем словарь с прокси
#     return {
#         "http": formatted_proxy,
#         "https": formatted_proxy
#     }


"""Создание БД"""

"""Скачивание данных"""

"""Загрузка данных в БД"""


def parsing_daily_sales():
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

                values = [buyer_username, buyer_stage_name, buyer_user_id, title, type_content, sales_date, sales_time,
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


def parsing_monthly_sales():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    # Инициализация словаря для хранения сумм по месяцам
    monthly_sums = defaultdict(float)

    # Получение словаря id_models
    id_models = get_id_models()

    folder = os.path.join(monthly_sales_path, '*.json')
    files_json = glob.glob(folder)

    for item in files_json:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]

        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)

        monthItems = data_json['monthItems']

        for month in monthItems:
            sales_date = month['sales_date'].replace('/', '.')
            sales_date = datetime.strptime(sales_date, '%d.%m.%Y')
            sales_month = sales_date.month
            sales_year = sales_date.year

            seller_commission_price = float(month['seller_commission_price'])

            # Формирование ключа в формате "(model_id, Месяц Год)"
            # month_year = sales_date.strftime("%b %Y")
            key = (model_id, sales_month, sales_year)
            monthly_sums[key] += seller_commission_price
            print()

        # Вывод суммы по каждой модели и месяцу

    for (model_id, sales_month, sales_year), total_sum in monthly_sums.items():
        formatted_total_sum = "{:.2f}".format(total_sum)
        values = [model_id, sales_month, sales_year, formatted_total_sum]
        # SQL-запрос для вставки данных
        insert_query = f"""
                        INSERT INTO {use_table_monthly_sales} (model_id, sales_month,sales_year, total_sum)
                        VALUES (%s,%s, %s, %s)
                        """
        cursor.execute(insert_query, values)
        cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()


def parsing_payout_history():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_payout_history}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений

    folder = os.path.join(payout_history_path, '*.json')
    files_json = glob.glob(folder)
    id_models = get_id_models()
    for item in files_json:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]

        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
        try:
            payPeriodItems = data_json['payPeriodItems']
        except:
            continue
        for item in payPeriodItems:
            payment_date = item['end_period_date']
            paid = item['paid']
            values = [model_id, payment_date, paid]
            # print(values)

            # SQL-запрос для вставки данных
            insert_query = f"""
                            INSERT INTO {use_table_payout_history} (model_id, payment_date, paid)
                            VALUES (%s, %s, %s)
                            """
            cursor.execute(insert_query, values)
        cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()


"""Формирование отчетов"""


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


def get_table_02_to_google():
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
        SELECT model_id, sales_month,sales_year,total_sum FROM manyvids.monthly_sales
        ORDER BY model_id, sales_year, sales_month;

    """)

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    df['sales_month'] = df['sales_month'].astype(int)
    # df['sales_year'] = df['sales_year'].astype(str)
    # df['month_year'] = pd.to_datetime(df['sales_month'] + '.' + df['sales_year'], format='%m.%Y')
    df['total_sum'] = pd.to_numeric(df['total_sum'])
    # # Создание сводной таблицы
    pivot_df = df.pivot_table(index='model_id', columns='sales_month', values='total_sum', fill_value=0)
    #
    # # Вывод результата
    #
    # # Сохранение в CSV
    pivot_df.to_csv('monthly_sales.csv')

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    """Запись в Google Таблицу"""
    client, spreadsheet_id = get_google()
    df = pd.read_csv('monthly_sales.csv')
    columns_to_check = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]  # Список колонок для проверки

    for col in columns_to_check:
        if col in df.columns:
            # Определяем индекс листа на основе номера колонки
            sheet_index = int(col) if col.isdigit() else 0
            sheet = client.open_by_key(spreadsheet_id).get_worksheet(sheet_index)

            # Выбираем только колонки 'model_id' и текущую колонку
            df_subset = df[['model_id', col]]

            # Преобразуем DataFrame в список списков и вставляем заголовки колонок
            values = [df_subset.columns.tolist()] + df_subset.values.tolist()

            # Очищаем лист и записываем данные
            sheet.clear()
            sheet.update(values, 'A1')
    # # Проверяем наличие колонки с названием "1" и выбираем соответствующий лист
    # if "1" in df.columns:
    #     sheet02 = client.open_by_key(spreadsheet_id).get_worksheet(1)  # Первый лист для daily_sales
    #     # Выбираем только колонки 'model_id' и '1'
    #     df_subset = df[['model_id', '1']]
    #     # Преобразуем DataFrame в список списков и вставляем заголовки колонок
    #     values = [df_subset.columns.tolist()] + df_subset.values.tolist()
    #
    #     # Очищаем лист и записываем данные
    #     sheet02.clear()
    #     sheet02.update(values, 'A1')
    # if "11" in df.columns:
    #     sheet11 = client.open_by_key(spreadsheet_id).get_worksheet(11)  # Первый лист для daily_sales
    #     # Выбираем только колонки 'model_id' и '1'
    #     df_subset = df[['model_id', '11']]
    #     # Преобразуем DataFrame в список списков и вставляем заголовки колонок
    #     values = [df_subset.columns.tolist()] + df_subset.values.tolist()
    #
    #     # Очищаем лист и записываем данные
    #     sheet11.clear()
    #     sheet11.update(values, 'A1')
    # if "12" in df.columns:
    #     sheet12 = client.open_by_key(spreadsheet_id).get_worksheet(12)  # Первый лист для daily_sales
    #     # Выбираем только колонки 'model_id' и '1'
    #     df_subset = df[['model_id', '12']]
    #     # Преобразуем DataFrame в список списков и вставляем заголовки колонок
    #     values = [df_subset.columns.tolist()] + df_subset.values.tolist()
    #
    #     # Очищаем лист и записываем данные
    #     sheet12.clear()
    #     sheet12.update(values, 'A1')

    # client, spreadsheet_id = get_google()
    #
    # sheet = client.open_by_key(spreadsheet_id).sheet1  # Первый лист в книге daily_sales
    #
    # # Читаем CSV файл
    # df = pd.read_csv('daily_sales.csv')
    #
    # # Конвертируем DataFrame в список списков
    # values = df.values.tolist()
    #
    # # Добавляем заголовки столбцов в начало списка
    # values.insert(0, df.columns.tolist())
    # # Очистка всего листа
    #
    # sheet.clear()
    # # Обновляем данные в Google Sheets
    # sheet.update(values, 'A1')


def get_table_03_to_google():
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
        SELECT model_id,  payment_date, paid FROM manyvids.payout_history
        ORDER BY model_id, payment_date;

    """)

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    pivot_df = df.pivot(index='model_id', columns='payment_date', values='paid')
    pivot_df.to_csv('payout_history.csv')

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet('payout_history')

    # Читаем CSV файл
    df = pd.read_csv('payout_history.csv')
    df.fillna(0, inplace=True)
    df = df.astype(str)
    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    # Очистка всего листа
    sheet_payout_history.clear()
    # Обновляем данные в Google Sheets
    sheet_payout_history.update(values, 'A1')


def get_table_04_to_google():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
           SELECT 
    buyer_stage_name, 
    buyer_user_id, 
    ROUND(SUM(seller_commission_price), 2) AS total_commission, 
    COUNT(*) AS total_count, 
    ROUND(AVG(seller_commission_price), 2) AS average_commission,
    GROUP_CONCAT(DISTINCT model_fm SEPARATOR ', ') AS all_buyer_usernames
FROM manyvids.daily_sales
GROUP BY buyer_stage_name, buyer_user_id;



        """)

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv('withdrawals.csv', index=False)
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet('clients')

    # Читаем CSV файл
    df = pd.read_csv('withdrawals.csv')
    df.fillna(0, inplace=True)
    df = df.astype(str)
    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    # Очистка всего листа
    sheet_payout_history.clear()
    # Обновляем данные в Google Sheets
    sheet_payout_history.update(values, 'A1')


def get_to_google():
    proxi = proxy_random()
    import requests
    import json

    with open('cookies.json', 'r') as f:
        cookies = json.load(f)

    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    # Выполнение запроса с использованием сессии, кук, заголовков и прокси
    response = session.get('https://www.manyvids.com/View-my-earnings/', headers=headers, proxies=proxi)
    src = response.text

    # Сохранение ответа в файл
    filename = "cookies.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


"""Загрузка логи и пароля в БД"""


def get_login_pass_to_sql():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_login_pass}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений

    csv_file_path = os.path.join(login_pass_path, 'login_pass.csv')
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for c in csv_reader:
            identifier = f'{c[0]}'
            login = c[1]
            password = c[2]
            values = [identifier, login, password]

            # SQL-запрос для вставки данных
            insert_query = f"""
            INSERT INTO {use_table_login_pass} (identifier, login,pass)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, values)
            cnx.commit()  # Подтверждение изменений
    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()


"""Полученние логин и пароля с БД"""


def login_pass():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
        SELECT identifier, login, pass FROM manyvids.login_pass;
    """)

    # Получение всех записей
    records = cursor.fetchall()

    # Список для хранения данных
    data_list = []

    for record in records:
        # Создание словаря для каждой строки и добавление его в список
        data_dict = {'identifier': record[0], 'login': record[1], 'password': record[2]}
        data_list.append(data_dict)

    cursor.close()
    cnx.close()
    return data_list


def check_json():
    # Загрузка данных из файла JSON
    with open('output.json', 'r') as json_file:
        data = json.load(json_file)

    # Извлечение первой пары ключ-значение
    file_names, credentials = list(data.items())[0]

    # Извлечение логина и пароля
    logi, passw = list(credentials.items())[0]

    print(f"file_names = {file_names}")
    print(f"logi = {logi}")
    print(f"pass = {passw}")


def get_sql_data_payout_history():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute("""
        SELECT model_id,payment_date,paid  FROM manyvids.payout_history;
    """)
    data = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


def get_sql_payout_history():
    sql_data = get_sql_data_payout_history()

    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    folder = os.path.join(payout_history_path, '*.json')
    files_json = glob.glob(folder)
    id_models = get_id_models()
    for item in files_json:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]

        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
        try:
            payPeriodItems = data_json['payPeriodItems']
        except:
            continue
        for item in payPeriodItems:
            payment_date = item['end_period_date']
            paid = item['paid']
            values = [model_id, payment_date, paid]
            json_sales_date_converted = datetime.strptime(payment_date, '%Y-%m-%d').date()
            json_seller_commission_price_converted = str(paid)
            json_data_tuple = (model_id, json_sales_date_converted, json_seller_commission_price_converted)
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


def parsing_monthly_sales_in_daily():
    # Подключение к базе данных и выполнение запроса
    # cnx = mysql.connector.connect(**db_config)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)

    # Выполнение запроса и чтение данных в DataFrame
    query = """
        SELECT 
            model_fm, 
            EXTRACT(YEAR FROM sales_date) AS year, 
            EXTRACT(MONTH FROM sales_date) AS month, 
            ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
        FROM 
            manyvids.daily_sales
        GROUP BY 
            model_fm, year, month
        ORDER BY 
            model_fm ASC, year ASC, month ASC;
    """
    df = pd.read_sql_query(query, engine)

    # Создание сводной таблицы
    pivot_df = df.pivot_table(index='model_fm', columns='month', values='total_seller_commission', fill_value=0)

    # Округление значений до двух знаков после запятой
    pivot_df = pivot_df.round(2)

    pivot_df.to_csv('monthly_sales.csv')
    engine.dispose()

    """Запись в Google Таблицу"""
    client, spreadsheet_id = get_google()
    df = pd.read_csv('monthly_sales.csv')
    columns_to_check = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]  # Список колонок для проверки

    for col in columns_to_check:
        if col in df.columns:
            # Определяем индекс листа на основе номера колонки
            sheet_index = int(col) if col.isdigit() else 0
            sheet = client.open_by_key(spreadsheet_id).get_worksheet(sheet_index)

            # Выбираем только колонки 'model_id' и текущую колонку
            df_subset = df[['model_fm', col]]

            # Преобразуем DataFrame в список списков и вставляем заголовки колонок
            values = [df_subset.columns.tolist()] + df_subset.values.tolist()

            # Очищаем лист и записываем данные
            sheet.clear()
            sheet.update(values, 'A1')


# def pending_custom():
# cookies = {
#     'KGID': 'w53da6862v',
#     'userPreferredContent': '1p2p3p',
#     'dataSectionTemp': '0',
#     'contentPopup': 'false',
#     'fp_token_7c6a6574-f011-4c9a-abdd-9894a102ccef': '7ZUNMg94yJb0rYhr9h1xadCa0UrCSklvSZFu+l9ga0w=',
#     '_hjSessionUser_665482': 'eyJpZCI6IjdiODIzZjNlLTUyMGQtNTg0ZS05OWUzLWY5ZDQ2OGRhOWFmNSIsImNyZWF0ZWQiOjE3MDA1NTY2ODMxMjQsImV4aXN0aW5nIjp0cnVlfQ==',
#     '_gat': '1',
#     '_hjIncludedInSessionSample_665482': '0',
#     '_hjAbsoluteSessionInProgress': '0',
#     '_ga': 'GA1.1.2068449578.1700556678',
#     'privacyPolicyRead': '1',
#     '_gat_UA-45103406-1': '1',
#     '_gid': 'GA1.2.1226392186.1706397645',
#     'timezone': 'Europe%2FAmsterdam',
#     '_gid': 'GA1.1.1226392186.1706397645',
#     '_hjSessionUser_665482': 'eyJpZCI6IjdiODIzZjNlLTUyMGQtNTg0ZS05OWUzLWY5ZDQ2OGRhOWFmNSIsImNyZWF0ZWQiOjE3MDA1NTY2ODMxMjQsImV4aXN0aW5nIjp0cnVlfQ==',
#     '_hjSession_665482': 'eyJpZCI6ImI0MjA0ODk5LTM1OGMtNGFiYS05MDE0LTM1Njk3MTE3ODdlNyIsImMiOjE3MDY2MjMxMDAxMTIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=',
#     '_ga_K93D8HD50B': 'deleted',
#     '_ga_K93D8HD50B': 'deleted',
#     'mvAnnouncement': 'hOO4ocGWnUIp%3AznWO55r6b3IP%3A5WtyRa6ByFOs%3AuAoc7dHVypWP%3A0pZdcf4j8AM7%3ArlUvKHZyXhy4%3AkVZfGcleqyVt%3AJWyKCvZPRv1W%3AaROanT5TyikV%3AeSVyu9J2xjFh',
#     'seenWarningPage': 'eyJpdiI6IldIaVNRTVwvb2Y0R3BROVdcL1JGaFhqQT09IiwidmFsdWUiOiJDMG9UM0MrUzhPR3BJbnFmXC9hM0FCZz09IiwibWFjIjoiYjlkZWUxODk3YzE3YzEzNjE2ODdiOWZmYzMwYjc3NmIxM2U0ZjZlMDY0OWRiM2RlYzhkNmI5MWMyY2Y5NDM2MSJ9',
#     'PHPSESSID': 'ujpt080d7kvdeh4v3cn2ifg2aomdjl835kivih0u',
#     'API_KEY': 'W6syvhgNxhB1zYwTiMlnjOaOiP3uwqAhgu5NYW77d13IDn1oZ5OMWf6GkZxIs4qb',
#     'KGID': '2e3fcde2-6671-5bf6-896a-8743cecda114',
#     'XSRF-TOKEN': 'eyJpdiI6IkZcL0JVeHEwT0c4UENkcVwvZzVCeWdpQT09IiwidmFsdWUiOiIwd09KY2pFenYwNVZiTHorM2tQRGRwTk9KUjNtRCthM3dQOGtISXNyTVRJM1JNTko3NzFGVkhnUkVGSWZCZzJQIiwibWFjIjoiYjMzMTU2OWFkYWE1YWNjODgyNWVkMDE1NDFlYjVhNzEzZTQ2ZjA5OGRkNTVlNjA2NWQ2MGRlNGYzZDFjZWIyOSJ9',
#     '_ga': 'GA1.2.2068449578.1700556678',
#     'AWSALB': 'k3CC00Ic3jmNKUyINo5PWhIt6To93EL5tf7iCctpbt6wvy4SVcqiHKYHyb8UHTbjHKr5b1HG4GYKP1HPFdIQ1jn7wN3Kho8y2FLQzRQvQHL5xf/Hxvrsb1dGaaB5ISirIOiog+kqt8TMtNxMtD+VaM9odplpiV6wYjotPZVK3F6ekdyBlD/6LNiIIJYzOw==',
#     'AWSALBCORS': 'k3CC00Ic3jmNKUyINo5PWhIt6To93EL5tf7iCctpbt6wvy4SVcqiHKYHyb8UHTbjHKr5b1HG4GYKP1HPFdIQ1jn7wN3Kho8y2FLQzRQvQHL5xf/Hxvrsb1dGaaB5ISirIOiog+kqt8TMtNxMtD+VaM9odplpiV6wYjotPZVK3F6ekdyBlD/6LNiIIJYzOw==',
#     '_ga_K93D8HD50B': 'GS1.1.1706865940.27.0.1706865940.60.0.0',
#     '_dd_s': '',
# }
#
# response = requests.get('https://www.manyvids.com/View-my-earnings/', cookies=cookies, headers=headers)
#
# src = response.text
# cnx = mysql.connector.connect(**db_config)
# cursor = cnx.cursor()

# # Очистка таблицы перед вставкой новых данных
# truncate_query = f"TRUNCATE TABLE {use_table_payout_history}"
# cursor.execute(truncate_query)
# cnx.commit()  # Подтверждение изменений

# folder = os.path.join(payout_history_path, '*.json')
# files_json = glob.glob(folder)
# id_models = get_id_models()
# for item in files_json:
#     filename = os.path.basename(item)
#     parts = filename.split("_")
#     mvtoken = parts[0]
#
#     # Ищем, какому ключу соответствует mvtoken
#     models_id = [key for key, value in id_models.items() if value == mvtoken]
#     try:
#         model_id = models_id[0]
#     except:
#         model_id = None
#     with open(item, 'r', encoding="utf-8") as f:
#         data_json = json.load(f)
#     try:
#         payPeriodItems = data_json['payPeriodItems']
#     except:
#         continue
#     for item in payPeriodItems:
#         payment_date = item['end_period_date']
#         paid = item['paid']
#         values = [model_id, payment_date, paid]
#         # print(values)
#
#         # SQL-запрос для вставки данных
#         insert_query = f"""
#                                 INSERT INTO {use_table_payout_history} (model_id, payment_date, paid)
#                                 VALUES (%s, %s, %s)
#                                 """
#         cursor.execute(insert_query, values)
#     cnx.commit()  # Подтверждение изменений
# cursor.close()
# cnx.close()

def pend_proba():
    spreadsheet_id = '145mee2ZsApZXiTnASng4lTzbocYCJWM5EDksTx_FVYY'
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\scrap_tutorial-master\\manyvids\\access.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
                  SELECT model_fm,
                EXTRACT(YEAR FROM sales_date) AS year,
                EXTRACT(MONTH FROM sales_date) AS month,
                ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
            FROM
                manyvids.daily_sales
            GROUP BY
                model_fm, year, month
            ORDER BY
                model_fm ASC, year ASC, month ASC;




                """)
    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv('monthly_sales.csv', index=False)
    # Чтение CSV файла
    df = pd.read_csv('monthly_sales.csv')

    # Переименование столбцов в DataFrame для соответствия таблице в БД
    df.rename(columns={
        'model_fm': 'model_id',
        'year': 'sales_year',
        'month': 'sales_month',  # Убедитесь, что названия столбцов соответствуют вашему CSV файлу
        'total_seller_commission': 'total_sum'
    }, inplace=True)

    # # Создание строки подключения
    # connection_string = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}'

    # Создание движка SQLAlchemy

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()


    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_monthly_sales}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()

    # Запись DataFrame в таблицу MySQL
    df.to_sql(name='monthly_sales', con=engine, if_exists='append', index=False)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    clear_pending_query = """
            UPDATE manyvids.monthly_sales
            SET pending_custom = NULL
            WHERE sales_month != %s;
        """
    cursor.execute(clear_pending_query, (month,))
    cnx.commit()
    id_models = get_id_models()
    folder = os.path.join(pending_custom_path, '*.html')

    files_html = glob.glob(folder)
    for item in files_html:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        custom_vids_body = soup.find_all('div', id="customVidsBody")
        for c in custom_vids_body:
            # Извлекаем все строки таблицы внутри найденного div
            rows = c.find_all('tr')

            # Проходимся по каждой строке и извлекаем содержимое шестой ячейки с элементом strong
            for row in rows:
                # Предполагая, что каждая строка содержит как минимум 6 ячеек
                if len(row.find_all('td')) >= 6:
                    strong_tag = row.find_all('td')[5].find(
                        'strong')  # Индексация начинается с 0, поэтому шестая ячейка это индекс 5
                    if strong_tag:
                        pending = strong_tag.get_text(strip=True).replace('$', '')
                        values = [model_id, month, pending]
                        # Убедитесь, что 'pending' преобразуется в числовой формат, если колонка 'pending_custom' ожидает число
                        try:
                            pending_value = float(pending)
                            # Подготовка и выполнение SQL запроса на обновление
                            update_query = """
                                                    UPDATE manyvids.monthly_sales
                                                    SET pending_custom = %s
                                                    WHERE model_id = %s AND sales_month = %s;
                                                """
                            cursor.execute(update_query, (pending_value, model_id, month))
                            cnx.commit()
                        except ValueError:
                            print(
                                f"Невозможно преобразовать '{pending}' в число для model_id {model_id} и месяца {month}.")
                    else:
                        print("Strong tag not found in the 6th cell")
    """Запись в Google Таблицу"""
    # Подключение к базе данных и выполнение запроса
    # cnx = mysql.connector.connect(**db_config)
    # database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"



    # Выполнение запроса и чтение данных в DataFrame
    query = """
        SELECT model_id, sales_month, total_sum, pending_custom FROM manyvids.monthly_sales;
    """
    df = pd.read_sql_query(query, engine)

    # Преобразование DataFrame
    df_pivot = df.pivot_table(index='model_id',
                              columns='sales_month',
                              values=['total_sum', 'pending_custom'],
                              aggfunc='first').reset_index()

    df_pivot.columns = ['_'.join(str(i) for i in col).strip() for col in df_pivot.columns.values]

    # Вывод преобразованного DataFrame для проверки
    # Запись в CSV
    csv_file_path = 'path_to_your_output_csv_file.csv'
    df_pivot.to_csv(csv_file_path, index=False)

    # # Создание сводной таблицы
    # pivot_df = df.pivot_table(index='model_id', columns='sales_month', values='total_sum', fill_value=0)
    #
    # # Округление значений до двух знаков после запятой
    # pivot_df = pivot_df.round(2)
    #
    # pivot_df.to_csv('monthly_sales.csv')


    """Запись в Google Таблицу"""
    # client, spreadsheet = get_google()
    df = pd.read_csv('path_to_your_output_csv_file.csv')
    # Список месяцев для проверки
    months = range(1, 13)  # От 1 до 12
    for month in months:
        sheet_name = f'{month:02}_monthly_sales'

        # Подготовка данных для записи
        columns = ['model_id_']
        data_columns = []

        # Добавляем колонки в список, если они существуют в DataFrame
        pending_custom_col = f'pending_custom_{month}'
        total_sum_col = f'total_sum_{month}'
        if pending_custom_col in df.columns:
            columns.append(pending_custom_col)
            data_columns.append(pending_custom_col)
        if total_sum_col in df.columns:
            columns.append(total_sum_col)
            data_columns.append(total_sum_col)

        # Если нет ни одной из специфичных колонок для месяца, пропускаем итерацию
        if not data_columns:
            continue

        df_subset = df[columns].copy()
        df_subset.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

        # Получаем или создаем лист для текущего месяца
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

        values = [df_subset.columns.tolist()] + df_subset.values.tolist()

        worksheet.clear()
        worksheet.update(values,'A1')
    engine.dispose()

    # client, spreadsheet_id = get_google()
    # sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet('clients')
    #
    # # Читаем CSV файл
    # df = pd.read_csv('withdrawals.csv')
    # df.fillna(0, inplace=True)
    # df = df.astype(str)
    # # Конвертируем DataFrame в список списков
    # values = df.values.tolist()
    #
    # # Добавляем заголовки столбцов в начало списка
    # values.insert(0, df.columns.tolist())
    #
    # # Очистка всего листа
    # sheet_payout_history.clear()
    # # Обновляем данные в Google Sheets
    # sheet_payout_history.update(values, 'A1')


def pending_custom():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
               SELECT 
        buyer_stage_name, 
        buyer_user_id,
        ROUND(SUM(seller_commission_price), 2) AS total_commission, 
        COUNT(*) AS total_count, 
        ROUND(AVG(seller_commission_price), 2) AS average_commission,
        GROUP_CONCAT(DISTINCT model_fm SEPARATOR ', ') AS all_buyer_usernames
    FROM 
        manyvids.daily_sales
    GROUP BY 
        buyer_stage_name, 
        buyer_user_id
    ORDER BY 
        total_commission DESC;




            """)

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv('withdrawals.csv', index=False)
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet('clients')

    # Читаем CSV файл
    df = pd.read_csv('withdrawals.csv')
    df.fillna(0, inplace=True)
    df = df.astype(str)
    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    # Очистка всего листа
    sheet_payout_history.clear()
    # Обновляем данные в Google Sheets
    sheet_payout_history.update(values, 'A1')

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    clear_pending_query = """
        UPDATE manyvids.monthly_sales
        SET pending_custom = NULL
        WHERE sales_month != %s;
    """
    cursor.execute(clear_pending_query, (month,))
    cnx.commit()
    id_models = get_id_models()
    folder = os.path.join(pending_custom_path, '*.html')

    files_html = glob.glob(folder)
    for item in files_html:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        custom_vids_body = soup.find_all('div', id="customVidsBody")
        for c in custom_vids_body:
            # Извлекаем все строки таблицы внутри найденного div
            rows = c.find_all('tr')

            # Проходимся по каждой строке и извлекаем содержимое шестой ячейки с элементом strong
            for row in rows:
                # Предполагая, что каждая строка содержит как минимум 6 ячеек
                if len(row.find_all('td')) >= 6:
                    strong_tag = row.find_all('td')[5].find(
                        'strong')  # Индексация начинается с 0, поэтому шестая ячейка это индекс 5
                    if strong_tag:
                        pending = strong_tag.get_text(strip=True).replace('$', '')
                        values = [model_id, month, pending]
                        # Убедитесь, что 'pending' преобразуется в числовой формат, если колонка 'pending_custom' ожидает число
                        try:
                            pending_value = float(pending)
                            # Подготовка и выполнение SQL запроса на обновление
                            update_query = """
                                                UPDATE manyvids.monthly_sales
                                                SET pending_custom = %s
                                                WHERE model_id = %s AND sales_month = %s;
                                            """
                            cursor.execute(update_query, (pending_value, model_id, month))
                            cnx.commit()
                        except ValueError:
                            print(
                                f"Невозможно преобразовать '{pending}' в число для model_id {model_id} и месяца {month}.")
                    else:
                        print("Strong tag not found in the 6th cell")


def parsing_pending():
    # Подключение к базе данных и выполнение запроса
    # cnx = mysql.connector.connect(**db_config)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)

    # Выполнение запроса и чтение данных в DataFrame
    query_pending = """
        SELECT model_id, sales_month, pending_custom
        FROM manyvids.monthly_sales
        WHERE pending_custom IS NOT NULL AND pending_custom != '';
    """
    df = pd.read_sql_query(query_pending, engine)

    # # Создание сводной таблицы
    pivot_df = df.pivot_table(index='model_id', columns='sales_month', values='pending_custom', fill_value=0)

    # Округление значений до двух знаков после запятой
    pivot_df = pivot_df.round(2)

    pivot_df.to_csv('pending_custom.csv')
    engine.dispose()

    """Запись в Google Таблицу"""
    client, spreadsheet_id = get_google()
    df = pd.read_csv('pending_custom.csv')
    columns_to_check = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]  # Список колонок для проверки

    for col in columns_to_check:
        if col in df.columns:
            # Определяем индекс листа на основе номера колонки
            sheet_index = int(col) if col.isdigit() else 0
            sheet = client.open_by_key(spreadsheet_id).get_worksheet(sheet_index)

            # Выбираем только колонки 'model_id' и текущую колонку
            df_subset = df[['model_id', col]]

            # Преобразуем DataFrame в список списков и вставляем заголовки колонок
            values = [df_subset.columns.tolist()] + df_subset.values.tolist()
            print(values)

            #
            # # Очищаем лист и записываем данные
            ######## sheet.clear()
            # sheet.update(values, 'A1')


def pen():
    # Настройка подключения к базе данных
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"
    engine = create_engine(database_uri)
    query_pending = """
           SELECT model_id, sales_month, pending_custom
           FROM manyvids.monthly_sales
           WHERE pending_custom IS NOT NULL AND pending_custom != '';
       """
    query = """
               SELECT model_fm,
                   EXTRACT(YEAR FROM sales_date) AS year, 
                   EXTRACT(MONTH FROM sales_date) AS month, 
                   ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
               FROM 
                   manyvids.daily_sales
               GROUP BY 
                   model_fm, year, month
               ORDER BY 
                   model_fm ASC, year ASC, month ASC;
           """
    # Предположим, что df1 - это ваш первый DataFrame, а df2 - второй DataFrame
    df1 = pd.read_sql_query(query, engine)
    df2 = pd.read_sql_query(query_pending, engine)

    # Преобразование 'sales_month' в числовой тип
    df2['sales_month'] = pd.to_numeric(df2['sales_month'])

    # Объединение данных
    df_merged = pd.merge(df1, df2, how='left', left_on=['model_fm', 'month'], right_on=['model_id', 'sales_month'])

    # Удаление лишних столбцов и заполнение NaN нулями
    df_merged.drop(['model_id', 'sales_month'], axis=1, inplace=True)
    df_merged['pending_custom'] = df_merged['pending_custom'].fillna(0)

    # Показать результат
    print(df1)
    # # Выполнение первого запроса
    # df_sales = pd.read_sql_query(query, engine)
    #
    # # Выполнение второго запроса
    # df_pending = pd.read_sql_query(query_pending, engine)
    # df_sales['model_fm'] = df_sales['model_fm'].str.strip()
    # df_pending['model_id'] = df_pending['model_id'].str.strip()
    # # Преобразование sales_month в числовой тип для обоих DataFrame
    # df_pending['sales_month'] = pd.to_numeric(df_pending['sales_month'])
    #
    # # Объединение данных
    # df_merged = pd.merge(df_sales, df_pending, how='left', left_on=['model_fm', 'month'],
    #                      right_on=['model_id', 'sales_month'])
    #
    # # Удаление лишних столбцов и заполнение NaN нулями или подходящим значением
    # df_merged.drop(['model_id', 'sales_month'], axis=1, inplace=True)
    # df_merged['pending_custom'] = df_merged['pending_custom'].fillna(0)
    #
    # # Переименование столбцов для соответствия ожидаемому формату
    # df_merged.rename(columns={'total_seller_commission': 'Total Seller Commission', 'pending_custom': 'Pending Custom'},
    #                  inplace=True)
    #
    # # Показать результат
    # print(df_merged.head())

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



def message_check():
    """Для скачиванния"""

    cookies = {
        'KGID': 'vw81enngnq',
        'contentPopup': 'false',
        'fp_token_7c6a6574-f011-4c9a-abdd-9894a102ccef': 'oix6rQRGBtS6uFahjigPvPhEKbgJi3Tr5BC8yJsspR8=',
        '_hjSessionUser_665482': 'eyJpZCI6ImJkMWRiNzI1LWNhNzItNWNiNS1hYjlmLTA2ODU1MGE3ZTc4ZCIsImNyZWF0ZWQiOjE2OTg3NDg4Mjg5NDQsImV4aXN0aW5nIjp0cnVlfQ==',
        '_ga': 'GA1.1.1303883953.1698748820',
        'privacyPolicyRead': '1',
        '_gat': '1',
        'userPreferredContent': '1p2p3p',
        'dataSectionTemp': '0',
        'MSG_LEG_TKN': 'IS6Q61g8WwFJn9vjnRwKqA==',
        '_gat_UA-45103406-1': '1',
        '_hjSessionUser_665482': 'eyJpZCI6ImJkMWRiNzI1LWNhNzItNWNiNS1hYjlmLTA2ODU1MGE3ZTc4ZCIsImNyZWF0ZWQiOjE2OTg3NDg4Mjg5NDQsImV4aXN0aW5nIjp0cnVlfQ==',
        '_ga_K93D8HD50B': 'deleted',
        '_hjIncludedInSessionSample_665482': '0',
        'KGID': '28b938dd-8db9-57a6-b5d9-6d96c6b8af21',
        '_hjAbsoluteSessionInProgress': '0',
        '_hjDonePolls': '977734%2C977740',
        '_hjIncludedInSessionSample_665482': '0',
        'seenWarningPage': 'eyJpdiI6ImpycUVnWWxzWkRoZW1FZ0tBQlJPRlE9PSIsInZhbHVlIjoibXVlUnBHOGRmXC8renhublI0SWZHMUE9PSIsIm1hYyI6IjhmZWZhZjJkZTUwNGZkZGI2YzhlYWVjMWQwNTczZWM5YTEzZmYzOWU4N2E0YTU2ZjhhZDM4MDExYjZlOTBiZjMifQ%3D%3D',
        'manyvh': 'th7WJdHKAwbYHEUUwWYGGaWfahAob0Lh0sem',
        '_ga_K93D8HD50B': 'deleted',
        '_hjSession_665482': 'eyJpZCI6IjVjODQwNTEyLTJmMGMtNGNjMC05MmNhLTU0ZDlhYTRmNDFkOSIsImMiOjE3MDYyNjExNTk0MDcsInMiOjAsInIiOjAsInNiIjoxLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=',
        'PHPSESSID': '96girgvco6k90si5g5g20kot5k5t777i6j9ihbog',
        'API_KEY': 'jCB4ak45V0MCGQpCABcBIbmpVs59371MH3NyIU2d%2FCTZtgCtIe7BbMSpM4G4oQ6E',
        '_gid': 'GA1.1.79581497.1705419542',
        '_gid': 'GA1.2.79581497.1705419542',
        'mvAnnouncement': '25iVwOy8aWq9%3Abp4KInQIqIh6',
        'timezone': 'Europe%2FAmsterdam',
        'XSRF-TOKEN': 'eyJpdiI6IjVmMmc2OFB6QzNmRVB5MXBlUldoQmc9PSIsInZhbHVlIjoiSVBsbVZMbHJhVEFBR1hUZ2U2cTFkUGlQREp2RE9ocU5tNEpxSVNLeWdCQURobjlLZFgyMm9BTGhFeUN3NmVYWCIsIm1hYyI6IjY1OTMyMGVhOWIxMTAzMzNmZjQ0NGVkNGM0MmIxZWEwNDIxN2U1MTkwZTFhMGM5M2QzNDAxNmM0NjJhMmEwM2IifQ%3D%3D',
        '_ga': 'GA1.1.1303883953.1698748820',
        '_hjSession_665482': 'eyJpZCI6IjVjMWE4ZGE2LWVmNGMtNDM2Yy04ZGU1LTdhNmRjNzA3ZmY2YiIsImMiOjE3MDcxMzk4OTcxNTQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=',
        '_dd_s': 'logs=1&id=3ba72fcf-baa7-4e48-b7fa-02c98b5d37c8&created=1707139882017&expire=1707140796562',
        'AWSALB': 'FsRlh/dAlvv9T+qndTkwFNyxlAsWQiPVTSTvMGB8q2uqvDxGIHFGQUgpFecloc0FBE7FLqu6xtjvU7oTnlIVAQZh9F1UO+RGwjSeZEPLd/bmErMQpyKhO1df5uZyQGRPMoh8+IW6iXpwdVa42pIT8wVezcfTRyKmaGAXMuaadKQZ4k/p8skTBKjlEQWQZA==',
        'AWSALBCORS': 'FsRlh/dAlvv9T+qndTkwFNyxlAsWQiPVTSTvMGB8q2uqvDxGIHFGQUgpFecloc0FBE7FLqu6xtjvU7oTnlIVAQZh9F1UO+RGwjSeZEPLd/bmErMQpyKhO1df5uZyQGRPMoh8+IW6iXpwdVa42pIT8wVezcfTRyKmaGAXMuaadKQZ4k/p8skTBKjlEQWQZA==',
        '_ga_K93D8HD50B': 'GS1.1.1707139882.9.1.1707139903.39.0.0',
    }

    headers = {
        'authority': 'www.manyvids.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'pl',
        # 'cookie': 'userPreferredContent=1p2p3p; PHPSESSID=r5rg9qet1fej253h4cor8fkkeiog6pj1jepv06gf; _gid=GA1.2.85593227.1706965896; timezone=Europe%2FAmsterdam; dataSectionTemp=0; contentPopup=false; fp_token_7c6a6574-f011-4c9a-abdd-9894a102ccef=mvA1hVkZx8gVlun4eAYfE/tx3WVoVcFiG1wmuOKm7zo=; KGID=863f6b0b-124b-564d-8198-d3e814b10314; _hjSessionUser_665482=eyJpZCI6IjU4MjYyNjdiLWQ2MmUtNTE5MC05NGEwLTIwNWY1NzBlODI1NCIsImNyZWF0ZWQiOjE3MDY5NjU4OTY4MTEsImV4aXN0aW5nIjp0cnVlfQ==; _ga=GA1.1.1061737518.1706965896; _gid=GA1.1.85593227.1706965896; privacyPolicyRead=1; XSRF-TOKEN=eyJpdiI6ImF1NzFCRWVvTW9jXC9ZWE9OK3p3NWpBPT0iLCJ2YWx1ZSI6InNvNnhEMlZqUGJKXC9NRXZqcXZETTVzYnNmQ1p1a1lUXC9lR1Y1bXZaQVwvbkE0TnR2WGp6aDRNSFwvZjJDRzF3NWVsIiwibWFjIjoiYWE2NDE5OTkxMjEzZDM2YjU2Nzg1YWUzOTEyODhhMjI5MmMzNWUzY2U1Zjg5MDFhOWRmNGJjNDk5OWM4YjQyZiJ9; _hjSession_665482=eyJpZCI6IjI3NGMzOTQxLWNmMWMtNGNiOS1iZTBiLTVjYjExOTNjMWM0NCIsImMiOjE3MDY5OTMzOTUzMTksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _dd_s=logs=1&id=657f648a-f812-4f98-b897-e45663fb2f37&created=1706993360879&expire=1706994432291; AWSALB=Vj6qUEhHE0j/+Lm4KyLXFCdZ3AapuOlEedLPNJ5uJY8G3bNVZgccFURYNelQu+wpeOxKJwuxlctAft0oO5YWoDroFHY9Y5ExMZYRoqPM5J2ob5rPw/xCM9Aac39cuFON5BvGTwSH0NBwDGHY4dTDzOXpYiGY87zJvZevFEpMBzSxT5/G4eItXxWwgUGGew==; AWSALBCORS=Vj6qUEhHE0j/+Lm4KyLXFCdZ3AapuOlEedLPNJ5uJY8G3bNVZgccFURYNelQu+wpeOxKJwuxlctAft0oO5YWoDroFHY9Y5ExMZYRoqPM5J2ob5rPw/xCM9Aac39cuFON5BvGTwSH0NBwDGHY4dTDzOXpYiGY87zJvZevFEpMBzSxT5/G4eItXxWwgUGGew==; _gat=1; _ga=GA1.1.1061737518.1706965896; _ga_K93D8HD50B=GS1.1.1706993394.4.1.1706993533.59.0.0',
        'referer': 'https://www.manyvids.com/Inbox/',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'mvtoken': '65bafffd95a79963053324',
        'typeMessage': 'private',
        'action': 'clc',
        'isMobile': '0',
    }
    proxi = proxy_random()
    session = requests.Session()
    session.cookies.update(cookies)
    response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                            headers=headers)
    json_data = response.json()
    data_json = json_data['conversations']
    total_msg = int(data_json['meta']['total'])
    total_pages = (total_msg // 13) + 2
    offset = 0
    print(f'Итого файлов будет {total_pages}')
    for i in range(total_pages):
        if i == 1:
            params = {
                'mvtoken': '65bafffd95a79963053324',
                'typeMessage': 'private',
                'action': 'clc',
                'isMobile': '0',
            }
            mvtoken_value = params['mvtoken']
            filename_day = os.path.join(chat_path, f'{mvtoken_value}_0{i}.json')
            if not os.path.exists(filename_day):
                response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                                       headers=headers,proxies=proxi)
                json_data = response.json()
                with open(filename_day, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
                print(f'Сохранил {filename_day}')
                time.sleep(10)
        if i > 1:
            offset += 13
            params = {
                'mvtoken': '65bafffd95a79963053324',
                'typeMessage': 'private',
                'action': 'cl',
                'offset': offset,
                'type': 'all',
                'isMobile': '0',
            }
            mvtoken_value = params['mvtoken']
            filename_day = os.path.join(chat_path, f'{mvtoken_value}_0{i}.json')
            if not os.path.exists(filename_day):
                response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                                       headers=headers, proxies=proxi)
                json_data = response.json()
                with open(filename_day, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
                print(f'Сохранил {filename_day}')
                time.sleep(10)






    """Парсинг json"""
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    folder = os.path.join(chat_path, '*.json')

    files_html = glob.glob(folder)
    heandler = ['msg_last_id','user_id','sender_id','date_part','time_part']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html:
            with open(item, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            data_json = json_data['conversations']
            total_msg = data_json['meta']['total']
            # print(total_msg)
            try:
                for i in data_json['list']:
                    msg_last_id = i['msg_last_id'] # id чата
                    sender_id = i['sender_id'] #id  модели
                    user_id = i['user_id']#id  клиента
                    msg_date= i['msg_date']#дата  чата
                    date_part, time_part = msg_date.split(' ')

                    values = [msg_last_id,user_id,sender_id,date_part,time_part]
                    # SQL-запрос для вставки данных
                    insert_query = f"""
                                    INSERT IGNORE INTO {use_table_chat} (msg_last_id, user_id, sender_id, date_part, time_part)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """
                    cursor.execute(insert_query, values)
                    cnx.commit()  # Подтверждение изменений

                    cnx.commit()  # Подтверждение изменений

            except mysql.connector.Error as err:
                print("Ошибка при добавлении данных:", err)
                break  # Прерываем цикл в случае ошибки

            # Закрытие соединения с базой данных
        cursor.close()
        cnx.close()
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()


def update_chat():
    sql_data = get_sql_check_chat()
    # Используем max() для поиска кортежа с максимальной датой
    # Для сравнения дат преобразуем их в объекты datetime
    latest_date_tuple = max(sql_data, key=lambda x: datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S'))
    latest_date = latest_date_tuple[1]  # Извлекаем дату из кортежа
    print(f'Последняя дата в БД {latest_date}')


    cookies = {
        'KGID': 'w53da6862v',
        'userPreferredContent': '1p2p3p',
        'dataSectionTemp': '0',
        'contentPopup': 'false',
        'fp_token_7c6a6574-f011-4c9a-abdd-9894a102ccef': '7ZUNMg94yJb0rYhr9h1xadCa0UrCSklvSZFu+l9ga0w=',
        '_hjSessionUser_665482': 'eyJpZCI6IjdiODIzZjNlLTUyMGQtNTg0ZS05OWUzLWY5ZDQ2OGRhOWFmNSIsImNyZWF0ZWQiOjE3MDA1NTY2ODMxMjQsImV4aXN0aW5nIjp0cnVlfQ==',
        '_gat': '1',
        '_hjIncludedInSessionSample_665482': '0',
        '_hjAbsoluteSessionInProgress': '0',
        '_ga': 'GA1.1.2068449578.1700556678',
        'privacyPolicyRead': '1',
        '_gat_UA-45103406-1': '1',
        '_hjSessionUser_665482': 'eyJpZCI6IjdiODIzZjNlLTUyMGQtNTg0ZS05OWUzLWY5ZDQ2OGRhOWFmNSIsImNyZWF0ZWQiOjE3MDA1NTY2ODMxMjQsImV4aXN0aW5nIjp0cnVlfQ==',
        '_hjSession_665482': 'eyJpZCI6ImI0MjA0ODk5LTM1OGMtNGFiYS05MDE0LTM1Njk3MTE3ODdlNyIsImMiOjE3MDY2MjMxMDAxMTIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=',
        '_ga_K93D8HD50B': 'deleted',
        'MSG_LEG_TKN': 'IZz+3rIXtQutSZzNwN+dNw==',
        'KGID': 'b48c47a9-bbbc-56b8-8944-58aea17ad295',
        'seenWarningPage': 'eyJpdiI6IlBSSkw2MDgrenBmTFhHQXN0UGgzWWc9PSIsInZhbHVlIjoic0J3VDNuXC9vNGU5MFU0UWl2dnFONVE9PSIsIm1hYyI6IjcwMmQ3OTUyNWUwOTg4NWI1YzYxZTU5YzY4MjU2YTYyNzQ1MWExMWU1NjcwM2I2MzFkZTlkZDM5ZDk0MTMwMTkifQ%3D%3D',
        'PHPSESSID': '1tglv6futtrph0ue28mq35nukp4t9qctoj07rm6d',
        'API_KEY': 'L8PiCIxCWo5ExWkUpU%2BAJt2%2BpUypuKd4SDx5Umy9T%2B1pbLWoTe%2BtoPg25lPMAknO',
        'mvAnnouncement': 'hOO4ocGWnUIp%3AznWO55r6b3IP%3A5WtyRa6ByFOs%3AuAoc7dHVypWP%3A0pZdcf4j8AM7%3ArlUvKHZyXhy4%3AkVZfGcleqyVt%3AJWyKCvZPRv1W%3AaROanT5TyikV%3AeSVyu9J2xjFh%3A25iVwOy8aWq9',
        '_ga_K93D8HD50B': 'deleted',
        '_gid': 'GA1.2.1102768810.1707073978',
        '_gid': 'GA1.1.1102768810.1707073978',
        'timezone': 'Europe%2FAmsterdam',
        'XSRF-TOKEN': 'eyJpdiI6Ikd1aFwvQTlXZmtcL2tRUW1cL0hsZjFmaGc9PSIsInZhbHVlIjoiVjNSOWg2YmhUNkxyYll3dFpoYXJCeXdcL3RjSkN1ZjQ0bWx5VkVWTFdKMnRTaUYzckk3bFlsU1FpcU1MMUN4NXEiLCJtYWMiOiIzNjg2Zjg0OWU0YzVlODgzZWZkYjNmNWZmNWExYWJkMTc2NDRmNGUyMjBiZjIwOWJhNmE5YjliNDY3ZWYyNDM2In0%3D',
        '_hjSession_665482': 'eyJpZCI6ImE1NTE2OWExLTNhOWUtNDBjYi04MTVjLWU2Y2ZhMDJjYzk2MCIsImMiOjE3MDcwNzUxMTAyODksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=',
        '_dd_s': 'logs=1&id=0b419de8-4220-430c-9298-92150021dbf8&created=1707073975304&expire=1707076027277',
        'AWSALB': 'uJ1WixTeqaiA9Du800sm1xL7GZKmoVRUrR226AnNe6IPZfL8wiOHqOVHzNEYd/jr4cZX9CRgTyXl/A1ShUfEri5hX6E8qBo/3oM/fEXu5zdpxZg42CNAjWX7PfY0CJMDPEdTLHAaZKmb5YS0bDe3O3QmZFRFT7wfh4Ie1ioy9WRWnwk6sJXo0nHD3gmE+Q==',
        'AWSALBCORS': 'uJ1WixTeqaiA9Du800sm1xL7GZKmoVRUrR226AnNe6IPZfL8wiOHqOVHzNEYd/jr4cZX9CRgTyXl/A1ShUfEri5hX6E8qBo/3oM/fEXu5zdpxZg42CNAjWX7PfY0CJMDPEdTLHAaZKmb5YS0bDe3O3QmZFRFT7wfh4Ie1ioy9WRWnwk6sJXo0nHD3gmE+Q==',
        '_ga_K93D8HD50B': 'GS1.1.1707073978.27.1.1707075127.21.0.0',
        '_ga': 'GA1.2.2068449578.1700556678',
    }



    params = {
        'mvtoken': '65ba81c2be5d2888504754',
        'typeMessage': 'private',
        'action': 'clc',
        'isMobile': '0',
    }
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    proxi = proxy_random()
    session = requests.Session()
    session.cookies.update(cookies)
    response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                            headers=headers)
    json_data = response.json()
    data_json = json_data['conversations']
    total_msg = int(data_json['meta']['total'])
    total_pages = (total_msg // 13) + 2
    offset = 0
    data_and_time_json = []
    should_stop = False  # Флаг для контроля выполнения цикла
    for i in range(total_pages):
        if i == 1:
            params = {
                'mvtoken': '65ba81c2be5d2888504754',
                'typeMessage': 'private',
                'action': 'clc',
                'isMobile': '0',
            }
            response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                                   headers=headers,proxies=proxi)
            json_data = response.json()
            data_json = json_data['conversations']
            for dj in data_json['list']:
                msg_last_id = dj['msg_last_id'] # id чата
                sender_id = dj['sender_id'] #id  модели
                user_id = dj['user_id']#id  клиента
                msg_date= dj['msg_date']#дата  чата
                msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                print(f'в Чате {msg_date} последняя дата {latest_date}')

                if msg_date == latest_date:
                    should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
                    print('Стоп')
                    break  # Прерываем внутренний цикл
                date_part, time_part = msg_date.split(' ')
                json_data_chat = (msg_last_id, msg_date)
                values = [msg_last_id, user_id, sender_id, date_part, time_part]

                if not json_data_chat in sql_data:
                    # SQL-запрос для вставки данных
                    insert_query = f"""
                    INSERT IGNORE INTO {use_table_chat} (msg_last_id, user_id, sender_id, date_part, time_part)
                                                           VALUES (%s, %s, %s, %s, %s)
                                                           """
                    cursor.execute(insert_query, values)

                    cnx.commit()  # Подтверждение изменений
                else:
                    break
        time.sleep(15)
        if should_stop:  # Повторная проверка флага после обработки каждой страницы
            break  # Прерываем внешний цикл, если флаг установлен

        elif i > 1:
            if should_stop:  # Проверяем флаг перед выполнением запроса на следующие страницы
                break  # Прерываем внешний цикл, если флаг установлен

            offset += 13
            params = {
                'mvtoken': '65ba81c2be5d2888504754',
                'typeMessage': 'private',
                'action': 'cl',
                'offset': offset,
                'type': 'all',
                'isMobile': '0',
            }
            response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
                                   headers=headers, proxies=proxi)
            json_data = response.json()
            data_json = json_data['conversations']
            for dj in data_json['list']:
                msg_last_id = dj['msg_last_id']  # id чата
                sender_id = dj['sender_id']  # id  модели
                user_id = dj['user_id']  # id  клиента
                msg_date = dj['msg_date']  # дата  чата
                msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                print(f'в Чате {msg_date} последняя дата {latest_date}')
                if msg_date == latest_date:
                    should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
                    print('Стоп')
                    break  # Прерываем внутренний цикл
                date_part, time_part = msg_date.split(' ')
                json_data_chat = (msg_last_id, msg_date)
                values = [msg_last_id, user_id, sender_id, date_part, time_part]

                if not json_data_chat in sql_data:
                    # SQL-запрос для вставки данных
                    insert_query = f"""
                                    INSERT IGNORE INTO {use_table_chat} (msg_last_id, user_id, sender_id, date_part, time_part)
                                                                           VALUES (%s, %s, %s, %s, %s)
                                                                           """
                    cursor.execute(insert_query, values)

                    cnx.commit()  # Подтверждение изменений
                else:
                    break
        # """Открыть когда пущу автомат"""
        # if i == 5:
        #     should_stop = True
        #     break
        if should_stop:  # Повторная проверка флага после обработки каждой страницы
            break  # Прерываем внешний цикл, если флаг установлен

    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()


def unique_users_to_sql():
    # # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)  # Замените db_config на ваш конфигурационный словарь
    cursor = cnx.cursor()
    # # # Выполнение SQL запроса
    # # cursor.execute("""
    # #     SELECT user_id, sender_id,
    # #            EXTRACT(YEAR FROM date_part) AS year,
    # #            EXTRACT(MONTH FROM date_part) AS month
    # #     FROM chat
    # #     ORDER BY EXTRACT(YEAR FROM date_part), EXTRACT(MONTH FROM date_part);
    # # """)
    # #
    # # # Получение результатов
    # # data = cursor.fetchall()
    # #
    # # # Создание DataFrame
    # # df = pd.DataFrame(data, columns=['user_id', 'sender_id', 'year', 'month'])
    # # print(df)
    # # # Закрытие соединения
    # # cursor.close()
    # # cnx.close()
    #
    """Тестировать"""
    #
    # # SQL запрос для получения списка user_id и даты (год и месяц)


    # Предполагается, что у вас уже есть подключение к базе данных


    # Выполнение SQL запроса для получения данных
    query = """
    SELECT sender_id, EXTRACT(MONTH FROM date_part) AS month, user_id
    FROM chat
    ORDER BY sender_id, month;
    """
    cursor.execute(query)

    # Считывание данных в DataFrame
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['sender_id', 'month', 'user_id'])

    # Группировка по sender_id и месяцу, подсчет уникальных user_id
    grouped = df.groupby(['sender_id', 'month'])['user_id'].apply(lambda x: set(x)).reset_index(name='unique_users')

    # Подготовка структуры для хранения результатов
    sender_monthly_new_users = defaultdict(dict)

    # Вычисление новых уникальных user_id для каждого sender_id по месяцам
    for sender_id, group in grouped.groupby('sender_id'):
        all_previous_users = set()
        for _, row in group.iterrows():
            month, unique_users = row['month'], row['unique_users']
            new_users = unique_users - all_previous_users
            sender_monthly_new_users[sender_id][month] = len(new_users)
            all_previous_users.update(new_users)
    #
    # # Преобразование результатов в DataFrame для удобного отображения
    results = []
    for sender_id, months in sender_monthly_new_users.items():
        for month, new_users_count in months.items():
            # Добавляем префикс к названию месяца
            month_prefixed = f'sales_month_{month}'
            results.append({'sender_id': sender_id, month_prefixed: new_users_count})

    # Создание DataFrame из списка результатов
    results_df = pd.DataFrame(results)

    # Поскольку каждая строка теперь представляет отдельный месяц, необходимо агрегировать данные по sender_id
    pivot_df = pd.pivot_table(results_df, index='sender_id', aggfunc='sum').fillna(0)

    # Сохранение в CSV
    pivot_df.to_csv('monthly_new_unique_users.csv', index=True)


    cursor.close()
    cnx.close()


    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    df = pd.read_csv('monthly_new_unique_users.csv')

    # Загрузка словаря id_models
    id_models = get_id_models_csv()  # {'FM05': '1007686262', ...}

    df['sender_id'] = df['sender_id'].astype(str)  # Убедимся, что sender_id в строковом формате
    df['model_id'] = df['sender_id'].apply(
        lambda x: [k for k, v in id_models.items() if v == x][0] if x in id_models.values() else None)
    df['model_id'].fillna(0, inplace=True)

    # Удаление колонки sender_id
    df.drop(columns=['sender_id'], inplace=True)

    # Проверяем DataFrame после изменений
    df_long = df.melt(id_vars=['model_id'], var_name='month', value_name='chat_users')

    # Удаление строк, где model_id равно 0 (если это необходимо)
    df_long = df_long[df_long['model_id'] != 0]

    # Преобразование длинного DataFrame обратно в широкий формат с model_id в качестве строк, месяцев в качестве колонок и chat_users в качестве значений
    df_pivot = df_long.pivot(index='model_id', columns='month', values='chat_users')

    # Заполнение NaN нулями, если это необходимо
    df_pivot.fillna(0, inplace=True)
    # print(df_pivot)
    # Проверяем результат преобразования
    for index, row in df_long.iterrows():
        model_id = row['model_id']
        sales_month = int(row['month'].replace('sales_month_', ''))  # Преобразование в int
        chat_users = row['chat_users']


        # Формирование и выполнение SQL-запроса на обновление # UPDATE monthly_sales
        # Формирование и выполнение SQL-запроса на вставку с условием обновления при дубликате
        upsert_query = """
            INSERT INTO unique_users (model_id, sales_month, chat_user)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE chat_user = VALUES(chat_user);
        """
        cursor.execute(upsert_query, (model_id, sales_month, chat_users))



    # # Подтверждение изменений и закрытие подключения
    cnx.commit()
    update_query = """
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)
    cnx.commit()
    cursor.close()
    cnx.close()

    # # Обход каждой строки в DataFrame
    # for index, row in df.iterrows():
    #     model_id = row['model_id']
    #     if model_id != 0:  # Проверяем, что model_id не равно 0
    #         for month in range(1, 13):  # Предполагаем, что данные за месяцы с 1 по 12
    #             if month in df.columns:
    #                 chat_users = row[month] if not pd.isna(row[month]) else 0
    #                 print(chat_users)
    #             # Обновление данных в таблице
    #             update_query = f"""
    #             UPDATE monthly_sales
    #             SET chat_user = %s
    #             WHERE model_id = %s AND sales_month = %s
    #             """
    #             cursor.execute(update_query, (chat_users, model_id, month))
    #
    # # Фиксация изменений и закрытие соединения
    # cnx.commit()
    # Переименование столбцов в DataFrame для соответствия таблице в БД
    # df.rename(columns={
    #     'model_fm': 'model_id',
    #     'year': 'sales_year',
    #     'month': 'sales_month',  # Убедитесь, что названия столбцов соответствуют вашему CSV файлу
    #     'total_seller_commission': 'total_sum'
    # }, inplace=True)

def get_pending_to_google():
    spreadsheet_id = '145mee2ZsApZXiTnASng4lTzbocYCJWM5EDksTx_FVYY'
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\scrap_tutorial-master\\manyvids\\access.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute("""
                  SELECT model_fm,
                EXTRACT(YEAR FROM sales_date) AS year,
                EXTRACT(MONTH FROM sales_date) AS month,
                ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
            FROM
                manyvids.daily_sales
            GROUP BY
                model_fm, year, month
            ORDER BY
                model_fm ASC, year ASC, month ASC;




                """)
    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv('monthly_sales.csv', index=False)


    # Чтение CSV файла
    df = pd.read_csv('monthly_sales.csv')

    # Переименование столбцов в DataFrame для соответствия таблице в БД
    df.rename(columns={
        'model_fm': 'model_id',
        'year': 'sales_year',
        'month': 'sales_month',  # Убедитесь, что названия столбцов соответствуют вашему CSV файлу
        'total_seller_commission': 'total_sum'
    }, inplace=True)

    # # Создание строки подключения
    # connection_string = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}'

    # Создание движка SQLAlchemy

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()


    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_monthly_sales}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()

    # Запись DataFrame в таблицу MySQL
    df.to_sql(name='monthly_sales', con=engine, if_exists='append', index=False)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    """Загрузка в месячную таблицу уникальных клиентов"""

    clear_pending_query = """
            UPDATE manyvids.monthly_sales
            SET pending_custom = NULL
            WHERE sales_month != %s;
        """
    cursor.execute(clear_pending_query, (month,))
    cnx.commit()
    id_models = get_id_models()
    folder = os.path.join(pending_custom_path, '*.html')
    cnx.commit()
    update_query = """
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)
    files_html = glob.glob(folder)
    for item in files_html:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[0]
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        custom_vids_body = soup.find_all('div', id="customVidsBody")
        for c in custom_vids_body:
            # Извлекаем все строки таблицы внутри найденного div
            rows = c.find_all('tr')

            # Проходимся по каждой строке и извлекаем содержимое шестой ячейки с элементом strong
            for row in rows:
                # Предполагая, что каждая строка содержит как минимум 6 ячеек
                if len(row.find_all('td')) >= 6:
                    strong_tag = row.find_all('td')[5].find(
                        'strong')  # Индексация начинается с 0, поэтому шестая ячейка это индекс 5
                    if strong_tag:
                        pending = strong_tag.get_text(strip=True).replace('$', '')
                        values = [model_id, month, pending]
                        # Убедитесь, что 'pending' преобразуется в числовой формат, если колонка 'pending_custom' ожидает число
                        try:
                            pending_value = float(pending)
                            # Подготовка и выполнение SQL запроса на обновление
                            update_query = """
                                                    UPDATE manyvids.monthly_sales
                                                    SET pending_custom = %s
                                                    WHERE model_id = %s AND sales_month = %s;
                                                """
                            cursor.execute(update_query, (pending_value, model_id, month))
                            cnx.commit()
                        except ValueError:
                            print(
                                f"Невозможно преобразовать '{pending}' в число для model_id {model_id} и месяца {month}.")
                    else:
                        print("Strong tag not found in the 6th cell")
    # # Подтверждение изменений и закрытие подключения


    """Запись в Google Таблицу"""
    # Подключение к базе данных и выполнение запроса
    # cnx = mysql.connector.connect(**db_config)
    # database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"



    # Выполнение запроса и чтение данных в DataFrame
    #Рабочий вариант
    # query = """
    #     SELECT model_id, sales_month, total_sum, pending_custom FROM manyvids.monthly_sales;
    # """

    query = """
        SELECT model_id, sales_month, total_sum, pending_custom, chat_user FROM manyvids.monthly_sales;

    """
    df = pd.read_sql_query(query, engine)

    # Преобразование DataFrame
    df_pivot = df.pivot_table(index='model_id',
                              columns='sales_month',
                              values=['total_sum', 'pending_custom', 'chat_user'],
                              aggfunc='first').reset_index()

    df_pivot.columns = ['_'.join(str(i) for i in col).strip() for col in df_pivot.columns.values]

    # Замена None на 0
    df_pivot.fillna(0, inplace=True)
    # Вывод преобразованного DataFrame для проверки
    # Запись в CSV
    csv_file_path = 'pending_custom.csv'
    df_pivot.to_csv(csv_file_path, index=False)
    #

    df = pd.read_csv('pending_custom.csv')
    months = range(1, 13)  # От 1 до 12

    for month in months:
        sheet_name = f'{month:02}_monthly_sales'

        # Подготовка данных для записи
        columns = ['model_id_']  # Основной столбец
        data_columns = []  # Столбцы данных для текущего месяца

        # Добавляем колонки в список, если они существуют в DataFrame
        pending_custom_col = f'pending_custom_{month}'
        total_sum_col = f'total_sum_{month}'
        chat_user_col = f'chat_user_{month}'  # Предполагаем, что столбец chat_user существует для каждого месяца

        # Проверяем наличие столбцов в DataFrame
        if pending_custom_col in df.columns:
            columns.append(pending_custom_col)
            data_columns.append(pending_custom_col)
        if total_sum_col in df.columns:
            columns.append(total_sum_col)
            data_columns.append(total_sum_col)
        if chat_user_col in df.columns:
            columns.append(chat_user_col)  # Добавляем chat_user в список столбцов для выборки
        else:
            # Если столбец chat_user отсутствует, предполагаем, что это ошибка в данных или логике
            # print(f"Warning: Column {chat_user_col} not found in DataFrame. Adding it with default value 0.")
            df[chat_user_col] = 0  # Добавляем столбец с 0, чтобы сохранить структуру данных
            columns.append(chat_user_col)

        # Если нет ни одной из специфичных колонок для месяца, кроме chat_user, пропускаем итерацию
        if not data_columns and chat_user_col not in df.columns:
            continue

        # Создаем подмножество DataFrame с нужными столбцами
        df_subset = df[columns].copy()
        df_subset.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

        # Получаем или создаем лист для текущего месяца
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

        # Формируем данные для обновления листа
        values = [df_subset.columns.tolist()] + df_subset.values.tolist()

        # Очистка и обновление листа
        worksheet.clear()
        worksheet.update(values, 'A1')

    # """ТЕСТОВЫЙ типа рабочий"""
    # """Запись в Google Таблицу"""
    # # client, spreadsheet = get_google()
    # df = pd.read_csv('pending_custom.csv')
    # # Список месяцев для проверки
    # # Предполагается, что spreadsheet уже определен
    # months = range(1, 13)  # От 1 до 12
    #
    # for month in months:
    #     sheet_name = f"{month}_monthly_sales"
    #     try:
    #         worksheet = spreadsheet.worksheet(sheet_name)
    #     except gspread.WorksheetNotFound:
    #         worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
    #
    #     # Формируем данные для обновления
    #     values = [["model_id", "total_sum", "pending_custom", "chat_user"]]  # Заголовки столбцов
    #
    #     for index, row in df.iterrows():
    #         # Ищем значения для текущего месяца
    #         total_sum_col = f"total_sum_{month}"
    #         pending_custom_col = f"pending_custom_{month}"
    #         chat_user_col = f"chat_user_{month}"
    #         # Проверяем, есть ли данные для текущего месяца
    #         # Обратите внимание: для chat_user мы берем значение из столбца, специфичного для месяца, если ваш случай другой - адаптируйте логику
    #         chat_user_value = row.get(chat_user_col, 0) if chat_user_col in df.columns else 0
    #
    #
    #         # Добавляем строку данных: model_id, total_sum, pending_custom, chat_user
    #         row_data = [
    #             row['model_id_'],
    #             row.get(total_sum_col, 0),  # Используем 0 в качестве значения по умолчанию
    #             row.get(pending_custom_col, 0),  # Используем 0 в качестве значения по умолчанию
    #             chat_user_value  # Уже обработали выше
    #         ]
    #         values.append(row_data)
    #     # print(values)
    #     # # Очистка и обновление листа
    #     worksheet.clear()
    #     worksheet.update(values, 'A1')


    """Рабочий код"""
    # for month in months:
    #     sheet_name = f'{month:02}_monthly_sales'
    #
    #     # Подготовка данных для записи
    #     columns = ['model_id_']
    #     data_columns = []
    #
    #     # Добавляем колонки в список, если они существуют в DataFrame
    #     pending_custom_col = f'pending_custom_{month}'
    #     total_sum_col = f'total_sum_{month}'
    #     if pending_custom_col in df.columns:
    #         columns.append(pending_custom_col)
    #         data_columns.append(pending_custom_col)
    #     if total_sum_col in df.columns:
    #         columns.append(total_sum_col)
    #         data_columns.append(total_sum_col)
    #
    #     # Если нет ни одной из специфичных колонок для месяца, пропускаем итерацию
    #     if not data_columns:
    #         continue
    #
    #     df_subset = df[columns].copy()
    #     df_subset.replace([np.inf, -np.inf, np.nan], 0, inplace=True)
    #
    #     # Получаем или создаем лист для текущего месяца
    #     try:
    #         worksheet = spreadsheet.worksheet(sheet_name)
    #     except gspread.WorksheetNotFound:
    #         worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
    #
    #     values = [df_subset.columns.tolist()] + df_subset.values.tolist()
    #
    #     worksheet.clear()
    #     worksheet.update(values,'A1')
    engine.dispose()

if __name__ == '__main__':
    # pen()
    # pend_proba()


    message_check()
    # update_chat()
    unique_users_to_sql()



    # delete_old_data()

    # get_requests_daily_sales()
    # get_requests_monthly_sales()
    # get_requests_payout_history()
    # get_login_pass_to_sql()
    # parsing_daily_sales()
    # parsing_monthly_sales()
    # parsing_monthly_sales_in_daily()
    # parsing_payout_history()
    # get_sql_payout_history()
    # pending_custom()
    # parsing_pending()
    # get_id_models()
    #     login_pass()
    # get_table_01_to_google()
    # get_table_02_to_google()
    get_table_03_to_google()
    # get_table_04_to_google()
    # get_to_google()
