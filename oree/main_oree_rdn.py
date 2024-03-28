import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import glob
import html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mysql.connector
import time
from datetime import datetime, timedelta
import os
import sys
import re
import pandas as pd
from datetime import datetime


current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
json_path = os.path.join(temp_path, "json")
html_path = os.path.join(temp_path, "html")


def creative_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, json_path, html_path]:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception as e:
            print(f"Ошибка при создании {folder}: {e}")


def load_config_headers():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config_oree.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    headers = config["headers"]

    # Генерация строки кукисов из конфигурации
    if "cookies" in config:
        cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
        headers["Cookie"] = cookies_str
    return config


def load_connection_to_sql():
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


def get_requests():
    config = load_connection_to_sql()
    db_config = config["db_config"]
    use_table = config["other_config"]["use_table"]
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    date_str = datetime.now()

    delivery_date_str = date_str + timedelta(days=1)
    delivery_date = delivery_date_str.strftime("%d.%m.%Y")
    config = load_config_headers()
    headers = config["headers"]

    url = f"https://www.oree.com.ua/index.php/PXS/get_pxs_hdata/{delivery_date}/DAM/2"
    print(url)
    while True:
        response = requests.post(url, headers=headers)

        src = response.text
        # Получаем текущую рабочую директорию
        current_directory = os.getcwd()
        name_html = "rdn.html"

        # Создаём полный путь к файлу
        filename = os.path.join(current_directory, name_html)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(src)
        with open(filename, encoding="utf-8") as file:
            src = file.read()
        decoded_html = html.unescape(src)
        decoded_html = decoded_html.replace(r"\"", '"').replace(r"\/", "/")
        soup = BeautifulSoup(decoded_html, "lxml")
        # Находим все строки с классом 'ranges-info'.
        rows = soup.find_all("tr", class_="ranges-info")
        if rows:
            # Если список не пустой, прерываем цикл и продолжаем выполнение программы
            break
        else:
            # Если список пустой, ждем 1 минуту и повторяем запрос
            print("Список пуст. Ожидание 1 минуты перед повторным запросом...")
            time.sleep(60)

    data_list = []

    for row in rows:
        # Извлекаем текст из всех 'td' текущей строки 'tr'.
        # Список comprehensions здесь может быть не нужен, если 'text.strip()' удаляет все ненужные символы.
        tds = [td.get_text(strip=True) for td in row.find_all("td")]

        # Убедитесь, что у вас правильное количество элементов в 'tds' перед добавлением в список.
        if len(tds) >= 6:  # Проверяем, есть ли минимум 6 значений в 'tds'.
            hour_data = {
                "hour": tds[0].replace("\\n", "").strip(),
                "delivery_date": delivery_date,
                "price": tds[2].replace("\\n", "").strip(),
                "sales_volume": tds[3].replace("\\n", "").strip(),
                "purchase_volume": tds[4].replace("\\n", "").strip(),
                "declared_sales_volume": tds[5].replace("\\n", "").strip(),
                "declared_volume_of_purchase": tds[6].replace("\\n", "").strip(),
            }
            data_list.append(hour_data)
    with open("filename_key_info.json", "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    for dd in data_list:
        hour = dd["hour"]
        delivery_date = datetime.strptime(dd["delivery_date"], "%d.%m.%Y").strftime(
            "%Y-%m-%d"
        )
        price = dd["price"]
        sales_volume = dd["sales_volume"]
        purchase_volume = dd["purchase_volume"]
        declared_sales_volume = dd["declared_sales_volume"]
        declared_volume_of_purchase = dd["declared_volume_of_purchase"]
        insert_query = f"""
                INSERT INTO {use_table} (hour, delivery_date, price, sales_volume, purchase_volume, declared_sales_volume, declared_volume_of_purchase)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
        cursor.execute(
            insert_query,
            (
                hour,
                delivery_date,
                price,
                sales_volume,
                purchase_volume,
                declared_sales_volume,
                declared_volume_of_purchase,
            ),
        )

    cnx.commit()


def run_at_specific_time(target_hour, target_minute, target_second):
    while True:
        now = datetime.now()
        # Задаем целевое время на сегодняшний день
        target_time = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)

        # Если текущее время уже после целевого времени, планируем на следующий день
        if target_time < now:
            target_time += timedelta(days=1)

        print(f"Скрипт запланирован на {target_time}")

        # Ожидаем до целевого времени
        while datetime.now() < target_time:
            time.sleep(1)

        # Ваша функция, которую нужно запустить
        get_requests()

        # Пауза перед следующей итерацией, чтобы избежать повторного немедленного запуска
        time.sleep(1)

if __name__ == "__main__":
    run_at_specific_time(12, 41, 0)


if __name__ == "__main__":
    get_requests()
#     get_data()
#     json_to_sql()
#     # run_at_specific_time("13:59:50")
