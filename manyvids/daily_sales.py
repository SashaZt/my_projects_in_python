# -*- coding: utf-8 -*-
import glob
import json
import os
import random
import time
from collections import defaultdict
from datetime import datetime, timedelta

import gspread
import mysql.connector
import numpy as np
import pandas as pd
import requests
import schedule
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine

from config import (
    db_config,
    use_table_daily_sales,
    headers,
    host,
    user,
    password,
    database,
    use_table_payout_history,
    use_table_monthly_sales,
    spreadsheet_id,
    time_a,
    time_b,
    use_table_chat,
)
from proxi import proxies

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, "cookies")
login_pass_path = os.path.join(temp_path, "login_pass")
daily_sales_path = os.path.join(temp_path, "daily_sales")
monthly_sales_path = os.path.join(temp_path, "monthly_sales")
payout_history_path = os.path.join(temp_path, "payout_history")
pending_custom_path = os.path.join(temp_path, "pending_custom")
chat_path = os.path.join(temp_path, "chat")
max_attempts = 3
attempts = 0


def log_message(message, log_filename="log.txt"):
    """
    Функция для логирования сообщений в файл.

    :param message: Сообщение для логирования.
    :param log_filename: Имя файла лога.
    """
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")


def proxy_random():
    """
    Функция для случайного прокси
    """
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # Возвращаем словарь с прокси
    return {"http": formatted_proxy, "https": formatted_proxy}


def delete_all_files():
    """
    Функция для удаления временных файлов по всем папкам
    """
    all_path = [chat_path, daily_sales_path, payout_history_path, pending_custom_path]

    for path in all_path:
        # Получаем список всех файлов в директории
        files = glob.glob(os.path.join(path, "*"))
        for f in files:
            # Проверяем, является ли путь файлом
            if os.path.isfile(f):
                os.remove(f)  # Удаляем файл
            elif os.path.isdir(f):
                # Если нужно удалить и поддиректории, раскомментируйте следующие строки
                # for subfile in glob.glob(os.path.join(f, '*')):
                #     os.remove(subfile)  # Удаляем файлы в поддиректории
                # os.rmdir(f)  # Удаляем саму поддиректорию
                print(f"Directory {f} skipped.")


def get_google():
    """
    Функция для подключения к Google sheets
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_file = os.path.join(current_directory, "access.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


def get_id_models_from_sql():
    """
    Функция для получения данных с Mysql
    """
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Выполнение запроса для получения уникальных значений
    cursor.execute(f"SELECT DISTINCT model_fm, model_id FROM {database}.daily_sales")

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


def get_latest_chat_date():
    """
    Функция для получения последней даты чата с Mysql
    """
    sql_data = check_chat()
    if sql_data:
        latest_date_tuple = max(
            sql_data, key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")
        )
        latest_date = latest_date_tuple[1]  # Извлекаем дату из кортежа
    else:
        # Если sql_data пуст, устанавливаем latest_date в None или другое значение по умолчанию
        # Это значение можно использовать для проверки необходимости выполнения следующих шагов
        latest_date = None
        log_message("Нет данных для обработки. Продолжаем выполнение скрипта.")
    log_message(f"Последняя дата в БД {latest_date}")
    return latest_date


def get_cookies():
    """
    Функция для работы с cookies
    """
    filename_cookies = os.path.join(current_directory, "cookies.json")
    with open(filename_cookies, "r", encoding="utf-8") as f:
        data_json = json.load(f)
    questionnaires_json = data_json["questionnaires"]
    models_cookies = []

    for s in questionnaires_json:
        # Собираем информацию о каждом магазине
        model_info = {
            "model": s["model"],
            "mvtoken": s["mvtoken"],
            "cookies": s["cookies"],
        }
        # Добавляем информацию о магазине в список
        models_cookies.append(model_info)

    # Возвращаем список с информацией о всех магазинах и их cookies
    return models_cookies


def get_requests(month, filterYear):
    """
    Функция получения данных о дневной продажи, истории и т.д.
    """
    filename_cookies = os.path.join(cookies_path, "*.json")
    files_json = glob.glob(filename_cookies)
    for item in files_json:
        with open(item, "r") as f:
            cookies_list = json.load(f)
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies_list}
        session = requests.Session()
        session.cookies.update(cookies_dict)
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken = parts[1].replace(".json", "")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message(f"{current_datetime} Модель {mvtoken}")
        """Получаем дневные продажи"""
        data_day = {
            "mvtoken": mvtoken,
            "day": "",
            "month": month,
            "filterYear": filterYear,
        }
        get_requests_day(session, data_day)
        """Получаем историю"""
        data_payout_history = {"mvtoken": mvtoken, "year": filterYear}
        get_requests_history(session, data_payout_history)
        """Получаем pending"""
        mvtoken_value = data_day["mvtoken"]
        filterYear_value = data_day["filterYear"]
        get_requests_pending(session, mvtoken_value, filterYear_value)
        """Получаем чат"""
        param_chat = {
            "mvtoken": mvtoken,
            "typeMessage": "private",
            "action": "clc",
            "isMobile": "0",
        }
        get_requests_chat(param_chat, session)


def get_requests_day(session, data_day):
    """
    Функция для сохранения json файлов дневных продаж
    """
    attempts = 0
    mvtoken_value = data_day["mvtoken"]
    month_value = data_day["month"]
    filterYear_value = data_day["filterYear"]
    need_delay = False  # Добавляем переменную для контроля задержки
    """День"""
    filename = os.path.join(
        daily_sales_path, f"{mvtoken_value}_{month_value}_{filterYear_value}.json"
    )
    if not os.path.exists(filename):
        while attempts < max_attempts:
            try:

                proxi = proxy_random()
                response = session.post(
                    "https://www.manyvids.com/includes/get_earnings.php",
                    headers=headers,
                    proxies=proxi,
                    data=data_day,
                )
                if response.status_code == 200:
                    data_json = response.json()
                    if "error" not in data_json:
                        # Если ключ "error" отсутствует, записываем данные в файл
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(
                                data_json, f, ensure_ascii=False, indent=4
                            )  # Записываем в файл
                        break  # Если запрос успешен, выходим из цикла
                    else:
                        log_message(
                            f"Ошибка: в получение дневных продаж {mvtoken_value}",
                            data_json["error"],
                        )
                        break
                else:
                    log_message(
                        f"Ответ сервера с кодом {response.status_code} для {mvtoken_value}"
                    )
                    need_delay = True  # Устанавливаем флаг задержки
            except requests.exceptions.RequestException as e:
                log_message(f"Попытка {attempts + 1} не удалась: {e}")
                need_delay = True  # Устанавливаем флаг задержки
            finally:
                attempts += 1
                if attempts >= max_attempts:
                    log_message(
                        f"Достигнуто максимальное количество попыток. {mvtoken_value}"
                    )
                    break
                if need_delay:  # Проверяем, нужна ли задержка
                    time.sleep(30)
                need_delay = False  # Сбрасываем флаг задержки


def get_requests_history(session, data_payout_history):
    """
    Функция для сохранения json файлов истории
    """
    attempts = 0
    need_delay = False  # Добавляем переменную для контроля задержки
    mvtoken = data_payout_history["mvtoken"]
    filterYear = data_payout_history["year"]
    """История"""
    filename = os.path.join(payout_history_path, f"{mvtoken}_{filterYear}.json")

    sleep_time = random.randint(time_a, time_b)
    time.sleep(sleep_time)
    if not os.path.exists(filename):
        while attempts < max_attempts:
            try:
                proxi = proxy_random()
                response = session.post(
                    "https://www.manyvids.com/includes/get_payperiod_earnings.php",
                    headers=headers,
                    data=data_payout_history,
                    proxies=proxi,
                )
                if response.status_code == 200:
                    data_json = response.json()  # Декодирование JSON
                    if "error" not in data_json:
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(
                                data_json, f, ensure_ascii=False, indent=4
                            )  # Записываем в файл
                        break  # Если запрос успешен, выходим из цикла
                    else:
                        log_message(f"Ошибка: при получении дневных чата {mvtoken}")
                        break
                else:
                    log_message(
                        f"Ответ сервера с кодом {response.status_code} для {mvtoken}"
                    )
                    need_delay = True  # Устанавливаем флаг задержки
            except requests.exceptions.RequestException as e:
                log_message(f"Попытка {attempts + 1} не удалась: {e}")
                need_delay = True  # Устанавливаем флаг задержки
            finally:
                attempts += 1
                if attempts >= max_attempts:
                    log_message(
                        f"Достигнуто максимальное количество попыток. {mvtoken}"
                    )
                    break
                if need_delay:  # Проверяем, нужна ли задержка
                    time.sleep(30)
                need_delay = False  # Сбрасываем флаг задержки


def get_requests_pending(session, mvtoken_value, filterYear_value):
    """
    Функция для сохранения json файлов pending
    """
    attempts = 0
    need_delay = False  # Добавляем переменную для контроля задержки
    """pending"""
    filename = os.path.join(
        pending_custom_path, f"{mvtoken_value}_{filterYear_value}.html"
    )
    sleep_time = random.randint(time_a, time_b)
    time.sleep(sleep_time)
    if not os.path.exists(filename):
        while attempts < max_attempts:
            try:
                proxi = proxy_random()
                response = session.get(
                    "https://www.manyvids.com/View-my-earnings/",
                    headers=headers,
                    proxies=proxi,
                )
                src = response.text
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(src)
                break  # Если запрос успешен, выходим из цикла
            except requests.exceptions.RequestException as e:
                log_message(f"Попытка {attempts + 1} не удалась: {e}")
                need_delay = True  # Устанавливаем флаг задержки
            finally:
                attempts += 1
                if attempts >= max_attempts:
                    log_message(
                        f"Достигнуто максимальное количество попыток. {mvtoken_value}"
                    )
                    break
                if need_delay:  # Проверяем, нужна ли задержка
                    time.sleep(30)
                need_delay = False  # Сбрасываем флаг задержки


def get_requests_chat(param_chat, session):
    """Качаем по одной странице для получения total_msg"""
    sql_data = check_chat()
    # files = glob.glob(os.path.join(chat_path, '*'))
    # # Удаляем каждый файл
    # for f in files:
    #     if os.path.isfile(f):
    #         os.remove(f)
    need_delay = False  # Добавляем переменную для контроля задержки
    mvtoken = param_chat["mvtoken"]
    attempts = 0

    filename = os.path.join(chat_path, f"{mvtoken}.json")
    if not os.path.exists(filename):
        while attempts < max_attempts:
            try:
                proxi = proxy_random()
                response = session.get(
                    "https://www.manyvids.com/includes/user_messages.php",
                    params=param_chat,
                    headers=headers,
                    proxies=proxi,
                )
                if response.status_code == 200:
                    data_json = response.json()  # Декодирование JSON
                    if "error" not in data_json:
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data_json, f, ensure_ascii=False, indent=4)
                        time.sleep(2)
                        break
                    else:
                        log_message(f"Ошибка: при получении дневных чата {mvtoken}")
                        break
                else:
                    log_message(
                        f"Ответ сервера с кодом {response.status_code} для {mvtoken}"
                    )
                    need_delay = True  # Устанавливаем флаг задержки
            except requests.exceptions.RequestException as e:
                log_message(f"Попытка {attempts + 1} не удалась: {e}")
                need_delay = True  # Устанавливаем флаг задержки
            finally:
                attempts += 1
                if attempts >= max_attempts:
                    log_message(
                        f"Достигнуто максимальное количество попыток. {mvtoken}"
                    )
                    break
                if need_delay:  # Проверяем, нужна ли задержка
                    time.sleep(30)
                need_delay = False  # Сбрасываем флаг задержки
    latest_date = get_latest_chat_date()
    folder = os.path.join(chat_path, "*.json")
    files_json = glob.glob(folder)
    models_fms = get_id_models_from_sql()

    """Получаем остальные страницы чатов"""
    for item in files_json:
        filename = os.path.basename(item)
        parts = filename.split("_")
        mvtoken_coockies = parts[0]
        need_delay = False
        with open(item, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        try:
            data_json = json_data["conversations"]
        except:
            log_message(f"Обнови файлы куки для {mvtoken_coockies}!!!!!!!!!!!!!")
            continue
        total_msg = int(data_json["meta"]["total"])
        total_pages = (total_msg // 13) + 2
        offset = 0
        should_stop = False  # Флаг для контроля выполнения цикла
        for i in range(total_pages):
            filename = os.path.join(chat_path, f"{mvtoken}_0{i}.json")
            if not os.path.exists(filename):
                if i == 1:
                    while attempts < max_attempts:
                        try:
                            proxi = proxy_random()
                            response = session.get(
                                "https://www.manyvids.com/includes/user_messages.php",
                                params=param_chat,
                                headers=headers,
                                proxies=proxi,
                            )
                            if response.status_code == 200:
                                data_json = response.json()  # Декодирование JSON
                                if "error" not in data_json:
                                    with open(filename, "w", encoding="utf-8") as f:
                                        json.dump(
                                            data_json, f, ensure_ascii=False, indent=4
                                        )
                                    time.sleep(2)
                                    break
                                else:
                                    log_message(
                                        f"Ошибка: при получении дневных чата {mvtoken}"
                                    )
                                    need_delay = True  # Устанавливаем флаг задержки
                            else:
                                log_message(
                                    f"Ответ сервера с кодом {response.status_code}"
                                )
                                need_delay = True  # Устанавливаем флаг задержки
                        except requests.exceptions.RequestException as e:
                            log_message(f"Попытка {attempts + 1} не удалась: {e}")
                            need_delay = True  # Устанавливаем флаг задержки
                        finally:
                            attempts += 1
                            if attempts >= max_attempts:
                                log_message(
                                    f"Достигнуто максимальное количество попыток.{mvtoken}"
                                )
                                break
                            if need_delay:  # Проверяем, нужна ли задержка
                                time.sleep(30)
                            need_delay = False  # Сбрасываем флаг задержки

                elif i > 1:
                    if (
                        should_stop
                    ):  # Проверяем флаг перед выполнением запроса на следующие страницы
                        break  # Прерываем внешний цикл, если флаг установлен
                    while attempts < max_attempts:
                        offset += 13
                        params_offset = {
                            "mvtoken": mvtoken,
                            "typeMessage": "private",
                            "action": "cl",
                            "offset": offset,
                            "type": "all",
                            "isMobile": "0",
                        }
                        try:
                            proxi = proxy_random()
                            response = session.get(
                                "https://www.manyvids.com/includes/user_messages.php",
                                params=params_offset,
                                headers=headers,
                                proxies=proxi,
                            )
                            if response.status_code == 200:
                                data_json = response.json()  # Декодирование JSON
                                if "error" not in data_json:
                                    with open(filename, "w", encoding="utf-8") as f:
                                        json.dump(
                                            data_json, f, ensure_ascii=False, indent=4
                                        )
                                        time.sleep(2)
                                    break
                                else:
                                    log_message(
                                        f"Ошибка: при получении дневных чата {mvtoken}"
                                    )
                                    need_delay = True  # Устанавливаем флаг задержки
                            else:
                                log_message(
                                    f"Ответ сервера с кодом {response.status_code} для {mvtoken}"
                                )
                                need_delay = True  # Устанавливаем флаг задержки
                        except requests.exceptions.RequestException as e:
                            log_message(f"Попытка {attempts + 1} не удалась: {e}")
                            need_delay = True  # Устанавливаем флаг задержки
                        finally:
                            attempts += 1
                            if attempts >= max_attempts:
                                log_message(
                                    f"Достигнуто максимальное количество попыток для {mvtoken}"
                                )
                                break
                            if need_delay:  # Проверяем, нужна ли задержка
                                time.sleep(30)
                            need_delay = False  # Сбрасываем флаг задержки

                if i == 5:
                    should_stop = True
                    break
                if (
                    should_stop
                ):  # Повторная проверка флага после обработки каждой страницы
                    break  # Прерываем внешний цикл, если флаг установлен
    # if not should_stop and filename_chat:
    #     with open(filename_chat, 'r', encoding="utf-8") as f:
    #         data_json = json.load(f)
    #     os.remove(filename_chat)
    #     try:
    #         total_msg = int(data_json['conversations']['meta']['total'])
    #         total_pages = (total_msg // 13) + 2
    #         offset = 0
    #         data_and_time_json = []
    #         for i in range(total_pages):
    #             filename_chat_all = os.path.join(daily_sales_path, f'{mvtoken}_0{i}.json')
    #             if i == 1:
    #                 params = {'mvtoken': mvtoken, 'typeMessage': 'private', 'action': 'clc', 'isMobile': '0'}
    #                 while attempts < max_attempts:
    #                     try:
    #                         proxi = proxy_random()
    #                         response = session.get('https://www.manyvids.com/includes/user_messages.php',
    #                                                params=params, headers=headers, proxies=proxi)
    #                         if "error" in data_json:
    #                             log_message(f"Ошибка: в получение дневных продаж {mvtoken}", data_json["error"])
    #                         else:
    #                             # Если ключ "error" отсутствует, записываем данные в файл
    #                             with open(filename_chat_all, 'w', encoding='utf-8') as f:
    #                                 json.dump(data_json, f, ensure_ascii=False, indent=4)  # Записываем в файл
    #                         break  # Если запрос успешен, выходим из цикла
    #                     except requests.exceptions.ConnectionError as e:
    #                         log_message(f"Попытка {attempts + 1} не удалась из-за проблемы соединения: {e}")
    #                     except requests.exceptions.RequestException as e:
    #                         log_message(f"Попытка {attempts + 1} не удалась: {e}")
    #                     finally:
    #                         attempts += 1
    #                         if attempts < max_attempts:
    #                             time.sleep(30)  # Задержка перед следующей попыткой
    #                         else:
    #                             log_message("Достигнуто максимальное количество попыток.")
    #                 # json_data = response.json()
    #                 # data_json = json_data['conversations']
    #                 # for dj in data_json['list']:
    #                 #     msg_last_id = dj['msg_last_id']  # id чата
    #                 #     sender_id = dj['sender_id']  # id  модели
    #                 #     user_id = dj['user_id']  # id  клиента
    #                 #     msg_date = dj['msg_date']  # дата  чата
    #                 #     msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    #                 #     # log_message(f'в Чате {msg_date} последняя дата {latest_date}')
    #                 #
    #                 #     if msg_date == latest_date:
    #                 #         should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
    #                 #         log_message('Стоп')
    #                 #         break  # Прерываем внутренний цикл
    #                 #     date_part, time_part = msg_date.split(' ')
    #                 #     json_data_chat = (msg_last_id, msg_date)
    #                 #     values = [msg_last_id, user_id, sender_id, date_part, time_part]
    #                 #
    #                 #     if not json_data_chat in sql_data:
    #                 #         # SQL-запрос для вставки данных
    #                 #         insert_query = f"""
    #                 #                     INSERT IGNORE INTO {use_table_chat}
    #                 #                     (msg_last_id, user_id, sender_id, date_part, time_part)
    #                 #                     VALUES (%s, %s, %s, %s, %s)
    #                 #                     """
    #                 #         cursor.execute(insert_query, values)
    #                 #
    #                 #         cnx.commit()  # Подтверждение изменений
    #                 #     else:
    #                 #         break
    #
    #             sleep_time = random.randint(time_a, time_b)
    #             log_message(f'Пауза {sleep_time}сек')
    #             time.sleep(sleep_time)
    #             if should_stop:  # Повторная проверка флага после обработки каждой страницы
    #                 break  # Прерываем внешний цикл, если флаг установлен
    #
    #             elif i > 1:
    #                 if should_stop:  # Проверяем флаг перед выполнением запроса на следующие страницы
    #                     break  # Прерываем внешний цикл, если флаг установлен
    #
    #                 offset += 13
    #                 params = {'mvtoken': mvtoken, 'typeMessage': 'private', 'action': 'cl', 'offset': offset,
    #                           'type': 'all', 'isMobile': '0'}
    #                 while attempts < max_attempts:
    #                     try:
    #                         proxi = proxy_random()
    #                         response = session.get('https://www.manyvids.com/includes/user_messages.php',
    #                                                params=params, headers=headers, proxies=proxi)
    #                         if "error" in data_json:
    #                             log_message(f"Ошибка: в получение дневных продаж {mvtoken}", data_json["error"])
    #                         else:
    #                             # Если ключ "error" отсутствует, записываем данные в файл
    #                             with open(filename_chat_all, 'w', encoding='utf-8') as f:
    #                                 json.dump(data_json, f, ensure_ascii=False, indent=4)  # Записываем в файл
    #                         break  # Если запрос успешен, выходим из цикла
    #                     except requests.exceptions.ConnectionError as e:
    #                         log_message(f"Попытка {attempts + 1} не удалась из-за проблемы соединения: {e}")
    #                     except requests.exceptions.RequestException as e:
    #                         log_message(f"Попытка {attempts + 1} не удалась: {e}")
    #                     finally:
    #                         attempts += 1
    #                         if attempts < max_attempts:
    #                             time.sleep(30)  # Задержка перед следующей попыткой
    #                         else:
    #                             log_message("Достигнуто максимальное количество попыток.")
    #                 # try:
    #                 #     json_data = response.json()
    #                 # except:
    #                 #     log_message(f'что-то не то с {mvtoken}')
    #                 #     continue
    #                 # data_json = json_data['conversations']
    #                 # for dj in data_json['list']:
    #                 #     msg_last_id = dj['msg_last_id']  # id чата
    #                 #     sender_id = dj['sender_id']  # id  модели
    #                 #     user_id = dj['user_id']  # id  клиента
    #                 #     msg_date = dj['msg_date']  # дата  чата
    #                 #     msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    #                 #     # log_message(f'в Чате {msg_date} последняя дата {latest_date}')
    #                 #     if msg_date == latest_date:
    #                 #         should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
    #                 #         log_message('Стоп')
    #                 #         break  # Прерываем внутренний цикл
    #                 #     date_part, time_part = msg_date.split(' ')
    #                 #     json_data_chat = (msg_last_id, msg_date)
    #                 #     values = [msg_last_id, user_id, sender_id, date_part, time_part]
    #                 #
    #                 #     if not json_data_chat in sql_data:
    #                 #         # SQL-запрос для вставки данных
    #                 #         insert_query = f"""
    #                 #         INSERT IGNORE INTO {use_table_chat}
    #                 #             (msg_last_id, user_id, sender_id, date_part, time_part)
    #                 #         VALUES (%s, %s, %s, %s, %s)
    #                 #         """
    #                 #         cursor.execute(insert_query, values)
    #                 #
    #                 #         cnx.commit()  # Подтверждение изменений
    #                 #     else:
    #                 #         break
    #             """Открыть когда пущу автомат"""
    #             if i == 20:
    #                 should_stop = True
    #                 break
    #             if should_stop:  # Повторная проверка флага после обработки каждой страницы
    #                 break  # Прерываем внешний цикл, если флаг установлен
    #
    #         # Здесь ваш код для обработки страниц
    #     except KeyError as e:
    #         log_message(f"В ответе отсутствуют необходимые данные: {e}")
    # else:
    #     log_message("Пропускаем итерацию или выполняем альтернативные действия")
    #
    # # Дополнительная логика, если была ошибка
    # if should_stop:
    #     log_message("Обработка остановлена из-за ошибки")
    #
    # # Закрытие соединения с базой данных
    # cursor.close()
    # cnx.close()


def unique_users_to_sql():
    """
    Функция для загрузки данных об уникальных клиентах
    """
    # # Подключение к базе данных
    cnx = mysql.connector.connect(
        **db_config
    )  # Замените db_config на ваш конфигурационный словарь
    cursor = cnx.cursor()

    # Выполнение SQL запроса для получения данных
    query = f"""
            SELECT sender_id, EXTRACT(MONTH FROM date_part) AS month, user_id
            FROM chat
            ORDER BY sender_id, month;
            """
    cursor.execute(query)

    # Считывание данных в DataFrame
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["sender_id", "month", "user_id"])

    # Группировка по sender_id и месяцу, подсчет уникальных user_id
    grouped = (
        df.groupby(["sender_id", "month"])["user_id"]
        .apply(lambda x: set(x))
        .reset_index(name="unique_users")
    )

    # Подготовка структуры для хранения результатов
    sender_monthly_new_users = defaultdict(dict)

    # Вычисление новых уникальных user_id для каждого sender_id по месяцам
    for sender_id, group in grouped.groupby("sender_id"):
        all_previous_users = set()
        for _, row in group.iterrows():
            month, unique_users = row["month"], row["unique_users"]
            new_users = unique_users - all_previous_users
            sender_monthly_new_users[sender_id][month] = len(new_users)
            all_previous_users.update(new_users)
    #
    # # Преобразование результатов в DataFrame для удобного отображения
    results = []
    for sender_id, months in sender_monthly_new_users.items():
        for month, new_users_count in months.items():
            # Добавляем префикс к названию месяца
            month_prefixed = f"sales_month_{month}"
            results.append({"sender_id": sender_id, month_prefixed: new_users_count})

    # Создание DataFrame из списка результатов
    results_df = pd.DataFrame(results)

    # Поскольку каждая строка теперь представляет отдельный месяц, необходимо агрегировать данные по sender_id
    pivot_df = pd.pivot_table(results_df, index="sender_id", aggfunc="sum").fillna(0)

    # Сохранение в CSV
    pivot_df.to_csv("monthly_new_unique_users.csv", index=True)

    cursor.close()
    cnx.close()

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    df = pd.read_csv("monthly_new_unique_users.csv")

    # Загрузка словаря id_models
    id_models = get_id_models_from_sql()  # {'FM05': '1007686262', ...}

    df["sender_id"] = df["sender_id"].astype(
        str
    )  # Убедимся, что sender_id в строковом формате
    df["model_id"] = df["sender_id"].apply(
        lambda x: (
            [k for k, v in id_models.items() if v == x][0]
            if x in id_models.values()
            else None
        )
    )
    df["model_id"].fillna(0, inplace=True)

    # Удаление колонки sender_id
    df.drop(columns=["sender_id"], inplace=True)

    # Проверяем DataFrame после изменений
    df_long = df.melt(id_vars=["model_id"], var_name="month", value_name="chat_users")

    # Удаление строк, где model_id равно 0 (если это необходимо)
    df_long = df_long[df_long["model_id"] != 0]

    # Преобразование длинного DataFrame обратно в широкий формат с model_id в качестве строк, месяцев в качестве колонок и chat_users в качестве значений
    df_pivot = df_long.pivot(index="model_id", columns="month", values="chat_users")

    # Заполнение NaN нулями, если это необходимо
    df_pivot.fillna(0, inplace=True)
    # log_message(df_pivot)
    # Проверяем результат преобразования
    for index, row in df_long.iterrows():
        model_id = row["model_id"]
        sales_month = int(
            row["month"].replace("sales_month_", "")
        )  # Преобразование в int
        chat_users = row["chat_users"]

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
    update_query = f"""
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)
    cnx.commit()
    cursor.close()
    cnx.close()


def check_data_day():
    """
    Функция для получение из БД дневных продажах
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT buyer_user_id, sales_date, sales_time, seller_commission_price FROM {database}.daily_sales;
    """
    )
    data = {(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


def check_payout_history():
    """
    Функция для получение из БД истории
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT model_id,payment_date,paid  FROM {database}.payout_history;
    """
    )
    data = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


def check_chat():
    """
    Функция для получение из БД чатов
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT msg_last_id, CONCAT(date_part, ' ', time_part) AS datetime FROM {database}.chat;
    """
    )
    data = {(row[0], row[1]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data


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

            log_message(f"dayItems пустой в файле {item}.")
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
                    mvtoken,
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
                              seller_commission_price, model_id, mvtoken,model_fm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, values)
                    cnx.commit()  # Подтверждение изменений

            except mysql.connector.Error as err:
                log_message("Ошибка при добавлении данных:", err)
                break  # Прерываем цикл в случае ошибки

    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()


def get_sql_payout_history():
    """
    Функция для отправки данных об истории в в Mysql
    """
    # cnx = mysql.connector.connect(**db_config)
    # cursor = cnx.cursor()
    #
    # # # Очистка таблицы перед вставкой новых данных
    # truncate_query = f"TRUNCATE TABLE {use_table_payout_history}"
    # cursor.execute(truncate_query)
    # cnx.commit()  # Подтверждение изменений
    #
    # folder = os.path.join(payout_history_path, '*.json')
    # files_json = glob.glob(folder)
    # id_models = get_id_models()
    #
    # for item in files_json:
    #     filename = os.path.basename(item)
    #     parts = filename.split("_")
    #     mvtoken = parts[0]
    #
    #     # Ищем, какому ключу соответствует mvtoken
    #     models_id = [key for key, value in id_models.items() if value == mvtoken]
    #     try:
    #         model_id = models_id[0]
    #         log_message(models_id)
    #
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
    #         # log_message(values)
    #
    #         # SQL-запрос для вставки данных
    #         insert_query = f"""
    #         INSERT INTO {use_table_payout_history} (model_id, payment_date, paid)
    #         VALUES (%s, %s, %s)"""
    #         cursor.execute(insert_query, values)
    #     cnx.commit()  # Подтверждение изменений
    # cursor.close()
    # cnx.close()

    sql_data = check_payout_history()

    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    folder = os.path.join(payout_history_path, "*.json")
    files_json = glob.glob(folder)
    id_models = get_id_models_from_sql()
    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            raw_json_str = f.read()
            data_json = json.loads(raw_json_str)
            data_json = json.loads(data_json)
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
            data_json = json.loads(raw_json_str)
            data_json = json.loads(data_json)
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
                log_message("Стоп")
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


#             # Закрытие соединения с базой данных
#             cursor.close()
#             cnx.close()
#     # # Проверяем, были ли
# #                   json_data = response.json()
#                     data_json = json_data['conversations']
#                     for dj in data_json['list']:
#                         msg_last_id = dj['msg_last_id']  # id чата
#                         sender_id = dj['sender_id']  # id  модели
#                         user_id = dj['user_id']  # id  клиента
#                         msg_date = dj['msg_date']  # дата  чата
#                         msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
#                         # print(f'в Чате {msg_date} последняя дата {latest_date}')
#
#                         if msg_date == latest_date:
#                             should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
#                             print('Стоп')
#                             break  # Прерываем внутренний цикл
#                         date_part, time_part = msg_date.split(' ')
#                         json_data_chat = (msg_last_id, msg_date)
#                         values = [msg_last_id, user_id, sender_id, date_part, time_part]
#
#                         if not json_data_chat in sql_data:
#                             # SQL-запрос для вставки данных
#                             insert_query = f"""
#                                         INSERT IGNORE INTO {use_table_chat} (msg_last_id, user_id, sender_id, date_part, time_part)
#                                                                                VALUES (%s, %s, %s, %s, %s)
#                                                                                """
#                             cursor.execute(insert_query, values)
#
#                             cnx.commit()  # Подтверждение изменений
#                         else:
#                             break
#                 print(f'Пауза {sleep_time}сек')
#                 sleep_time = random.randint(time_a, time_b)
#                 time.sleep(sleep_time)
#                 if should_stop:  # Повторная проверка флага после обработки каждой страницы
#                     break  # Прерываем внешний цикл, если флаг установлен
#
# while attempts < max_attempts:
#     try:
#         response = session.get('https://www.manyvids.com/includes/user_messages.php', params=params,
#                                headers=headers, proxies=proxi)
#         break  # Если запрос успешен, выходим из цикла
#     except requests.exceptions.ConnectionError as e:
#         print(f"Попытка {attempts + 1} не удалась: {e}")
#         attempts += 1
#         time.sleep(sleep_time)  # Задержка перед следующей попыткой
# json_data = response.json()
# data_json = json_data['conversations']
# for dj in data_json['list']:
#     msg_last_id = dj['msg_last_id']  # id чата
#     sender_id = dj['sender_id']  # id  модели
#     user_id = dj['user_id']  # id  клиента
#     msg_date = dj['msg_date']  # дата  чата
#     msg_date = datetime.strptime(msg_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
#     # print(f'в Чате {msg_date} последняя дата {latest_date}')
#     if msg_date == latest_date:
#         should_stop = True  # Устанавливаем флаг в True, когда нашли совпадение
#         print('Стоп')
#         break  # Прерываем внутренний цикл
#     date_part, time_part = msg_date.split(' ')
#     json_data_chat = (msg_last_id, msg_date)
#     values = [msg_last_id, user_id, sender_id, date_part, time_part]
#
#     if not json_data_chat in sql_data:
#         # SQL-запрос для вставки данных
#         insert_query = f"""
#                                     INSERT IGNORE INTO {use_table_chat} (msg_last_id, user_id, sender_id, date_part, time_part)
#                                                                            VALUES (%s, %s, %s, %s, %s)
#                                                                            """
#         cursor.execute(insert_query, values)
#
#         cnx.commit()  # Подтверждение изменений
#     else:
#         break


def get_table_01_to_google():
    """
    Функция для отправки данных об дневных в Google sheets
    """
    filename = "daily_sales.csv"
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(
            f"""
            SELECT model_fm, sales_date, 
            ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
            FROM {database}.daily_sales 
            WHERE YEAR(sales_date) = YEAR(CURDATE()) AND MONTH(sales_date) = MONTH(CURDATE())
            GROUP BY model_fm, sales_date
            ORDER BY model_fm ASC, sales_date ASC;
        """
        )
        results = cursor.fetchall()
        # Обработка результатов запроса здесь
        # Например, вывод результатов:
        # for row in results:
        #     print(row)
    except mysql.connector.Error as e:
        log_message(f"Произошла ошибка при выполнении запроса к базе данных: {e}")
    finally:
        if "cnx" in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

    # Получение результатов в DataFrame
    df = pd.DataFrame(results, columns=[x[0] for x in cursor.description])

    # Преобразование DataFrame в сводную таблицу
    pivot_df = df.pivot_table(
        index="model_fm",
        columns="sales_date",
        values="total_seller_commission",
        fill_value=0,
    )

    # Добавляем строку 'Итого' в конец сводной таблицы
    total_row = pivot_df.sum().rename("Итого").to_frame().T
    # Обратите внимание: мы преобразуем Series total_row в DataFrame и используем .T для транспонирования

    # Используем pd.concat для добавления итоговой строки к pivot_df
    pivot_df_with_total = pd.concat([pivot_df, total_row], axis=0)

    # Сохранение в CSV
    pivot_df_with_total.to_csv(filename, index=True)

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()

    """Запись в Google Таблицу"""
    client, spreadsheet_id = get_google()
    sheet_daily_sales = client.open_by_key(spreadsheet_id).worksheet("daily_sales")
    # Читаем CSV файл
    df = pd.read_csv(filename)

    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())
    try:
        # Очистка всего листа
        sheet_daily_sales.clear()
    except gspread.exceptions.APIError as e:
        log_message(f"Произошла ошибка при обновлении Google Sheets: {e}")
    except Exception as e:
        log_message(f"Произошла неожиданная ошибка: {e}")
    try:
        # Обновляем данные в Google Sheets
        sheet_daily_sales.update(values, "A1")
    except gspread.exceptions.APIError as e:
        log_message(f"Произошла ошибка при обновлении Google Sheets: {e}")
    except Exception as e:
        log_message(f"Произошла неожиданная ошибка: {e}")

    # Форматирование текущей даты и времени
    try:
        # Предполагается, что sheet_daily_sales уже определен и настроен
        current_datetime_get_table_01 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Обновляем ячейку A1 с текущей датой и временем
        sheet_daily_sales.update(
            [[current_datetime_get_table_01]], "A1", value_input_option="USER_ENTERED"
        )
    except gspread.exceptions.APIError as e:
        log_message(f"Произошла ошибка при обновлении Google Sheets: {e}")
    except Exception as e:
        log_message(f"Произошла неожиданная ошибка: {e}")
    if os.path.exists(filename):
        os.remove(filename)


def get_pending_to_google():
    """
    Функция для отправки данных об pending в Google sheets
    """
    # scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
    #          'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    # creds_file = os.path.join(current_directory, 'access.json')
    # creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    # client = gspread.authorize(creds)
    client, spreadsheet_id = get_google()
    filename_monthly_sales = "monthly_sales.csv"
    spreadsheet = client.open_by_key(spreadsheet_id)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                  SELECT
                        model_fm,
                        EXTRACT(YEAR FROM sales_date) AS year,
                        EXTRACT(MONTH FROM sales_date) AS month,
                        ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
                        FROM {database}.daily_sales 
                        GROUP BY model_fm , year , month
                        ORDER BY model_fm ASC , year ASC , month ASC;
                """
    )
    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv(filename_monthly_sales, index=False)

    # Чтение CSV файла
    df = pd.read_csv(filename_monthly_sales)

    # Переименование столбцов в DataFrame для соответствия таблице в БД
    df.rename(
        columns={
            "model_fm": "model_id",
            "year": "sales_year",
            "month": "sales_month",  # Убедитесь, что названия столбцов соответствуют вашему CSV файлу
            "total_seller_commission": "total_sum",
        },
        inplace=True,
    )

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
    df.to_sql(name="monthly_sales", con=engine, if_exists="append", index=False)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    """Загрузка в месячную таблицу уникальных клиентов"""

    clear_pending_query = f"""
            UPDATE {database}.monthly_sales
            SET pending_custom = NULL
            WHERE sales_month != %s;
        """
    cursor.execute(clear_pending_query, (month,))
    cnx.commit()

    cnx.commit()
    update_query = f"""
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)

    folder = os.path.join(pending_custom_path, "*.html")
    files_html = glob.glob(folder)
    id_models = get_id_models_from_sql()
    for item in files_html:

        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        custom_vids_body = soup.find_all("div", id="customVidsBody")
        try:
            mvtoken = soup.find("a", id="hiddenPremiumTrigger").get("data-model-id")
        except:
            continue
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        total_pending_custom = 0
        for c in custom_vids_body:
            rows = c.find_all("tr")
            for row in rows:
                if len(row.find_all("td")) >= 6:
                    strong_tag = row.find_all("td")[5].find("strong")
                    if strong_tag:
                        pending = strong_tag.get_text(strip=True).replace("$", "")
                        try:
                            pending_value = float(pending)
                            total_pending_custom += pending_value
                        except ValueError:
                            # Обрабатываем случай, когда pending не может быть преобразовано в число
                            continue

        # После накопления суммы выполняем обновление базы данных одной строкой
        update_query = f"""
                        UPDATE {database}.monthly_sales
                        SET pending_custom = %s
                        WHERE model_id = %s AND sales_month = %s;
                        """
        cursor.execute(update_query, (total_pending_custom, model_id, month))
        cnx.commit()
    if os.path.exists(filename_monthly_sales):
        os.remove(filename_monthly_sales)
    cursor.close()
    cnx.close()

    """Запись в Google Таблицу"""

    query = f"""
        SELECT model_id,  sales_month, total_sum, pending_custom, chat_user 
        FROM {database}.monthly_sales
        WHERE sales_year = YEAR(CURDATE());

    """
    df = pd.read_sql_query(query, engine)
    filename_pending_custom = "pending_custom.csv"
    # Преобразование DataFrame
    # Предполагается, что df уже загружен и содержит необходимые данные.
    # Создаем pivot_table.
    df_pivot = df.pivot_table(
        index="model_id",
        columns="sales_month",
        values=["total_sum", "pending_custom", "chat_user"],
        aggfunc="first",
    ).reset_index()

    # Обновляем названия столбцов, чтобы они были более читаемыми.
    df_pivot.columns = [
        "_".join(str(i) for i in col).strip() for col in df_pivot.columns.values
    ]

    # Заменяем NaN на 0.
    df_pivot.fillna(0, inplace=True)

    # Убедимся, что столбцы, содержащие числовые значения, имеют числовой тип данных.
    for col in df_pivot.columns:
        if "total_sum" in col or "chat_user" in col or "pending_custom" in col:
            df_pivot[col] = pd.to_numeric(df_pivot[col], errors="coerce")

    # Сохраняем результат в CSV. Индекс не сохраняем, если он не несет важной информации.
    df_pivot.to_csv(filename_pending_custom, index=False)
    #
    df = pd.read_csv(filename_pending_custom)
    months = range(1, 13)  # От 1 до 12

    for month in months:
        sheet_name = f"{month:02}_monthly_sales"

        # Подготовка данных для записи
        columns = ["model_id_"]  # Основной столбец
        data_columns = []  # Столбцы данных для текущего месяца

        # Добавляем колонки в список, если они существуют в DataFrame
        pending_custom_col = f"pending_custom_{month}"
        total_sum_col = f"total_sum_{month}"
        chat_user_col = f"chat_user_{month}"  # Предполагаем, что столбец chat_user существует для каждого месяца

        if total_sum_col in df.columns:
            columns.append(total_sum_col)
            data_columns.append(total_sum_col)
        # Проверяем наличие столбцов в DataFrame
        if pending_custom_col in df.columns:
            columns.append(pending_custom_col)
            data_columns.append(pending_custom_col)
        if chat_user_col in df.columns:
            columns.append(
                chat_user_col
            )  # Добавляем chat_user в список столбцов для выборки
        else:
            # Если столбец chat_user отсутствует, предполагаем, что это ошибка в данных или логике
            # log_message(f"Warning: Column {chat_user_col} not found in DataFrame. Adding it with default value 0.")
            df[chat_user_col] = (
                0  # Добавляем столбец с 0, чтобы сохранить структуру данных
            )
            columns.append(chat_user_col)

        # Если нет ни одной из специфичных колонок для месяца, кроме chat_user, пропускаем итерацию
        if not data_columns and chat_user_col not in df.columns:
            continue

        # Создаем подмножество DataFrame с нужными столбцами и заменяем плохие значения
        df_subset = df[columns].copy()
        df_subset.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

        # Проверяем, есть ли данные для total_sum_col и только тогда работаем с листом
        if total_sum_col in data_columns and df[total_sum_col].any():
            # Пытаемся получить лист, если он существует, иначе создаем новый
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, rows="100", cols="20"
                )

            # Добавляем строку "Итого" с подсчетом сумм по колонкам
            totals = (
                df_subset.select_dtypes(include=["number"]).sum().tolist()
            )  # Считаем суммы только для числовых колонок
            # Создаем итоговую строку
            totals_row = ["Итого"] + totals

            # Убедимся, что итоговая строка правильно выровнена с заголовками
            # Отнимаем 1, так как 'Итого' уже добавлено в totals_row
            non_numeric_columns_count = len(df_subset.columns) - len(totals) - 1
            totals_row = [""] * non_numeric_columns_count + totals_row

            # Формируем данные для обновления листа, добавляя totals_row
            values = (
                [df_subset.columns.tolist()] + df_subset.values.tolist() + [totals_row]
            )

            # Очистка и обновление листа
            worksheet.clear()
            worksheet.update(values, "A1")

            # Форматирование текущей даты и времени
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Обновление ячейки A1 с текущей датой и временем
            worksheet.update([[current_datetime]], "A1")
        else:
            # Если нет данных для total_sum_col, лист не создается и пропускаем обновление
            log_message(
                f"Skipping sheet creation and update for {sheet_name} due to no data in {total_sum_col}."
            )

    engine.dispose()
    if os.path.exists(filename_pending_custom):
        os.remove(filename_pending_custom)


def get_table_03_to_google():
    """
    Функция для отправки данных об истории в Google sheets
    """
    filename = "payout_history.csv"
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                    SELECT model_id,  payment_date, paid FROM {database}.payout_history
                    ORDER BY model_id, payment_date;
                    """
    )

    # Получение результатов в DataFrame

    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    df = df.drop_duplicates(subset=["model_id", "payment_date"], keep="first")

    pivot_df = df.pivot(index="model_id", columns="payment_date", values="paid")

    for column in pivot_df.columns:
        pivot_df[column] = pd.to_numeric(pivot_df[column], errors="coerce").fillna(0)

    total_row = pivot_df.sum().rename("Итого").to_frame().T
    pivot_df_with_total = pd.concat([pivot_df, total_row], axis=0)
    pivot_df_with_total = pivot_df_with_total.round(2)
    # pivot_df.to_csv('payout_history.csv')

    pivot_df_with_total.to_csv(filename)

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet(
        "payout_history"
    )

    # Читаем CSV файл
    df = pd.read_csv(filename)
    df.fillna(0, inplace=True)

    # Поскольку мы уже округлили числа до сохранения в CSV,
    # заменяем точку на запятую уже после чтения из файла, если это необходимо
    df = df.astype(str).applymap(lambda x: x.replace(".", ","))

    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    # Очистка всего листа
    sheet_payout_history.clear()
    # Обновляем данные в Google Sheets
    sheet_payout_history.update(values, "A1")

    # Форматирование текущей даты и времени
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Обновление ячейки A1 с текущей датой и временем
    sheet_payout_history.update([[current_datetime]], "A1")
    if os.path.exists(filename):
        os.remove(filename)


def get_table_04_to_google():
    """
    Функция для отправки данных об клиентах в Google sheets
    """
    filename = "withdrawals.csv"
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                   SELECT 
            buyer_stage_name,
            buyer_user_id,
            ROUND(SUM(seller_commission_price), 2) AS total_commission,
            COUNT(*) AS total_count,
            ROUND(AVG(seller_commission_price), 2) AS average_commission,
            GROUP_CONCAT(DISTINCT model_fm
                SEPARATOR ', ') AS all_buyer_usernames
        FROM
            {database}.daily_sales
        GROUP BY buyer_stage_name , buyer_user_id
        ORDER BY total_commission DESC;
        """
    )

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv(filename, index=False)
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet("clients")

    # Читаем CSV файл
    df = pd.read_csv(filename)
    df.fillna(0, inplace=True)
    df = df.astype(str)
    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    # Очистка всего листа
    sheet_payout_history.clear()
    # Обновляем данные в Google Sheets
    sheet_payout_history.update(values, "A1")

    # Форматирование текущей даты и времени
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Обновление ячейки A1 с текущей датой и временем
    sheet_payout_history.update([[current_datetime]], "A1")
    if os.path.exists(filename):
        os.remove(filename)


def get_asio():
    import glob
    import asyncio
    import json
    import os
    import random
    from datetime import datetime

    import aiofiles
    import aiohttp
    import aiomysql
    from aiohttp import BasicAuth
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    from config import db_config_asio, headers, use_bd
    from proxi import proxies

    current_directory = os.getcwd()
    temp_directory = "temp"
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, temp_directory)
    cookies_path = os.path.join(temp_path, "cookies")
    daily_sales_path = os.path.join(temp_path, "daily_sales")
    payout_history_path = os.path.join(temp_path, "payout_history")
    pending_custom_path = os.path.join(temp_path, "pending_custom")
    chat_path = os.path.join(temp_path, "chat")

    async def proxy_random():
        proxy = random.choice(proxies)
        proxy_host = proxy[0]
        proxy_port = proxy[1]
        proxy_user = proxy[2]
        proxy_pass = proxy[3]

        # Возвращаем словарь, соответствующий ожидаемому формату для Playwright
        return {
            "server": f"http://{proxy_host}:{proxy_port}",
            "username": proxy_user,
            "password": proxy_pass,
        }

    async def login_pass():
        # Список для хранения данных
        data_list = []

        # Устанавливаем соединение с базой данных
        conn = await aiomysql.connect(**db_config_asio)
        cursor = await conn.cursor()

        await cursor.execute("SELECT identifier, login, pass FROM login_pass;")

        # Получение всех записей
        records = await cursor.fetchall()

        for record in records:
            # Создание словаря для каждой строки и добавление его в список
            data_dict = {
                "identifier": record[0],
                "login": record[1],
                "password": record[2],
            }
            data_list.append(data_dict)

        await cursor.close()
        conn.close()
        return data_list

    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def save_cookies(page, identifier, mvtoken):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(cookies_path, f"{identifier}_{mvtoken}.json")
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def load_cookies_and_update_session(session, filename):
        async with aiofiles.open(filename, "r") as f:
            cookies_list = json.loads(await f.read())
        for cookie in cookies_list:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def get_requests_day(
        session, proxy, headers, mvtoken, month, filterYear, filename
    ):
        data = {"mvtoken": mvtoken, "day": "", "month": month, "filterYear": filterYear}
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/get_earnings.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json
            # if response.headers.get('Content-Type') == 'application/json':
            #     data_json = await response.json()
            #     return data_json
            # else:
            #     content = await response.text()
            #     print(f'Unexpected response: {content}')
            #     return None

    async def save_day_json(data_json, mvtoken, month, filterYear):
        filename = os.path.join(
            daily_sales_path, f"{mvtoken}_{month}_{filterYear}.json"
        )
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def get_requests_history(
        session, proxy, headers, mvtoken, filterYear, filename
    ):
        data = {"mvtoken": mvtoken, "year": filterYear}
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/get_payperiod_earnings.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json
            # if response.headers.get('Content-Type') == 'application/json':
            #     data_json = await response.json()
            #     return data_json
            # else:
            #     content = await response.text()
            #     print(f'Unexpected response: {content}')
            #     return None

    async def save_history_json(data_json, mvtoken, filterYear):
        filename = os.path.join(payout_history_path, f"{mvtoken}_{filterYear}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def save_page_content(page, mvtoken, filterYear):
        filename = os.path.join(pending_custom_path, f"{mvtoken}_{filterYear}.html")
        content = await page.content()
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(content)

    async def get_requests_chat(session, proxy, headers, mvtoken, filename):
        data = {
            "mvtoken": mvtoken,
            "typeMessage": "private",
            "action": "clc",
            "isMobile": "0",
        }
        """Получаем дневные продажи"""
        # Загрузка кук из файла и обновление сессии
        await load_cookies_and_update_session(session, filename)

        roxy_auth = None
        if proxy["username"] and proxy["password"]:
            proxy_auth = BasicAuth(login=proxy["username"], password=proxy["password"])

        async with session.post(
            "https://www.manyvids.com/includes/user_messages.php",
            headers=headers,
            proxy=proxy["server"],
            proxy_auth=proxy_auth,
            data=data,
        ) as response:
            data_json = await response.text()
            return data_json

    async def save_chat_json(data_json, mvtoken):
        filename = os.path.join(chat_path, f"{mvtoken}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def get_total_msg():
        folder = os.path.join(chat_path, "*.json")
        files_json = glob.glob(folder)
        total_pages = 0

        for item in files_json:
            filename = os.path.basename(item)
            parts = filename.split("_")
            mvtoken_cookies = parts[0]

            async with aiofiles.open(item, "r", encoding="utf-8") as f:
                json_data = await f.read()
                json_string_unescaped = json.loads(json_data)

                # Второе преобразование: из строки JSON в объект Python (в данном случае, в словарь)
                json_data = json.loads(json_string_unescaped)
                # json_data = json.loads(json_data)

                data_json = json_data["conversations"]
                total_msg = int(data_json["meta"]["total"])
                total_pages += (total_msg // 13) + 2

        return total_pages

    async def get_requests_all_chat(
        session, proxy, headers, mvtoken, filename, total_msg
    ):
        offset = 0
        results = []  # Собираем результаты здесь

        for i in range(1, total_msg):  # Исправлено на range
            await load_cookies_and_update_session(session, filename)

            proxy_auth = None
            if proxy["username"] and proxy["password"]:
                proxy_auth = BasicAuth(
                    login=proxy["username"], password=proxy["password"]
                )

            # Подготовка данных запроса
            data = {
                "mvtoken": mvtoken,
                "typeMessage": "private",
                "action": "clc" if i == 1 else "cl",
                "isMobile": "0",
            }
            if i > 1:
                offset += 13
                data.update({"offset": offset, "type": "all"})

            # Выполнение запроса
            async with session.post(
                "https://www.manyvids.com/includes/user_messages.php",
                headers=headers,
                proxy=proxy["server"],
                proxy_auth=proxy_auth,
                data=data,
            ) as response:
                data_json = await response.text()
                results.append((data_json, i))  # Добавляем результат в список
                # Добавляем случайную задержку от 0 до 5 секунд
            await asyncio.sleep(random.uniform(0, 5))
            if i == 5:  # Прерываем цикл после обработки пяти итераций
                break

        return results  # Возвращаем собранные результаты после завершения цикла

    async def save_all_chat_json(data_json, mvtoken, i):
        filename = os.path.join(chat_path, f"{mvtoken}_{i}.json")
        async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def run(playwright):
        # Попытка входа и повтор в случае необходимости
        max_attempts = 5  # Максимальное количество попыток
        attempts = 0  # Счетчик попыток
        now = datetime.now()
        month = str(now.month)
        filterYear = str(now.year)

        data_login_pass = await login_pass()
        timeout_ancet = 100000
        async with aiohttp.ClientSession() as session:
            for item in data_login_pass:
                successful_login = False
                attempts = 0
                while attempts < max_attempts and not successful_login:
                    proxy = (
                        await proxy_random()
                    )  # Получение нового прокси при каждой попытке
                    browser = await playwright.chromium.launch(
                        headless=False, proxy=proxy
                    )
                    context = await browser.new_context()
                    page = await context.new_page()

                    try:
                        await page.goto(
                            "https://www.manyvids.com/Login/",
                            wait_until="networkidle",
                            timeout=timeout_ancet,
                        )
                        await page.wait_for_selector(
                            'h1:text("Login to ManyVids")', timeout=timeout_ancet
                        )
                        await page.fill("input#triggerUsername", item["login"])
                        await page.fill("input#triggerPassword", item["password"])
                        await page.press("input#triggerPassword", "Enter")

                        # Проверяем исчезновение элемента login
                        await page.wait_for_selector(
                            '//a[@data-recaptcha-action="login"]',
                            state="hidden",
                            timeout=30000,
                        )
                        print(f"Успешный вход для {item['login']}")
                        successful_login = True
                    except Exception as e:
                        print(
                            f"Ошибка при попытке входа для {item['login']} на попытке {attempts + 1}: {str(e)}"
                        )
                        attempts += 1
                        await browser.close()  # Закрыть браузер при ошибке

                if successful_login:
                    # Продолжаем использовать текущий браузер и прокси
                    try:
                        await page.goto(
                            "https://www.manyvids.com/View-my-earnings/",
                            wait_until="networkidle",
                            timeout=timeout_ancet,
                        )
                        try:
                            await page.wait_for_selector(
                                '//div[@class="text-left"]', timeout=timeout_ancet
                            )
                        except:
                            print(f"Страница не загрузилась для {item['login']} 60 секунд.")
                            await browser.close()

                        await page.wait_for_selector("[data-mvtoken]", timeout=timeout_ancet)
                        mvtoken = await page.get_attribute("[data-mvtoken]", "data-mvtoken")
                        filename = await save_cookies(page, item["identifier"], mvtoken)

                        await load_cookies_and_update_session(session, filename)

                        """Дневные продажи"""
                        data_json_day = await get_requests_day(
                            session, proxy, headers, mvtoken, month, filterYear, filename
                        )
                        await save_day_json(data_json_day, mvtoken, month, filterYear)

                        """История"""
                        data_json_history = await get_requests_history(
                            session, proxy, headers, mvtoken, filterYear, filename
                        )
                        await save_history_json(data_json_history, mvtoken, filterYear)

                        """Pending"""
                        await save_page_content(page, mvtoken, filterYear)
                        #

                        """Загрузка чатов"""
                        data_json_first_chat = await get_requests_chat(
                            session, proxy, headers, mvtoken, filename
                        )
                        #
                        await save_chat_json(data_json_first_chat, mvtoken)

                        total_msg = await get_total_msg()

                        results = await get_requests_all_chat(
                            session, proxy, headers, mvtoken, filename, total_msg
                        )
                        for data_json, i in results:
                            await save_all_chat_json(data_json, mvtoken, i)
                        
                    except Exception as e:
                        print(
                            f"Не удалось загрузить страницу заработков для {item['login']}: {str(e)}"
                        )
                    finally:
                        await browser.close()
                else:
                    print(
                        f"Не удалось войти для {item['login']} после {max_attempts} попыток."
                    )

                

                """Закрываем"""
            await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())


def job():
    log_filename = "log.txt"
    if os.path.exists(log_filename):
        os.remove(log_filename)

    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    filterYear = str(now.year)
    currentTime = now.strftime("%H:%M:%S")  # Форматирование текущего времени

    log_message(
        f"[{currentTime}] Запуск задачи для месяца {month} и года {filterYear}."
    )
    # Ваши функции здесь
    # get_requests(month, filterYear)

    get_asio()

    get_sql_data_day()

    get_sql_payout_history()
    get_sql_chat()
    # #
    get_table_01_to_google()

    """payout_history"""
    get_table_03_to_google()

    # get_table_04_to_google()
    get_pending_to_google()
    unique_users_to_sql()

    log_message(f"Все выполнено, ждем 30мин")
    delete_all_files()


# Вызов функции для немедленного выполнения задачи при запуске скрипта
job()

# Настройка расписания
# schedule.every().hour.at(":25").do(job)  # Запуск каждый час в 00 минут
# Настройка расписания на выполнение каждые 30 минут
schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

# if __name__ == '__main__':
#     log_message("Какой месяц парсим от 1 до 12?")
#     month = input()
#     log_message("Какой год парсим? в формате 2024")
#     filterYear = input()
#     get_requests(month, filterYear)
#     get_sql_data_day()
#     get_table_01_to_google()
