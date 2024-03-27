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


creative_folders()
# # Удалите файлы из папок list и product
# for folder in [list_path, product_path, img_path]:
#     files = glob.glob(os.path.join(folder, '*'))
#     for f in files:
#         if os.path.isfile(f):
#             os.remove(f)


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
    # headers = config["headers"]

    # url = f"https://www.oree.com.ua/index.php/PXS/get_pxs_hdata/{delivery_date}/DAM/2"
    # response = requests.post(
    #     url,
    #     headers=headers,
    # )

    # src = response.text
    # with open("fdf.html", "w", encoding='utf-8') as file:
    #     file.write(src)
    with open("fdf.html", encoding="utf-8") as file:
        src = file.read()
    decoded_html = html.unescape(src)
    decoded_html = decoded_html.replace(r'\"', '"').replace(r'\/', '/')
    soup = BeautifulSoup(decoded_html, "lxml")
    # Находим все строки с классом 'ranges-info'.
    rows = soup.find_all("tr", class_="ranges-info")

    data_list = []

    for row in rows:
        # Извлекаем текст из всех 'td' текущей строки 'tr'.
        # Список comprehensions здесь может быть не нужен, если 'text.strip()' удаляет все ненужные символы.
        tds = [td.get_text(strip=True) for td in row.find_all("td")]
        
        # Убедитесь, что у вас правильное количество элементов в 'tds' перед добавлением в список.
        if len(tds) >= 6:  # Проверяем, есть ли минимум 6 значений в 'tds'.
            hour_data = {
                "hour": tds[0].replace('\\n', '').strip(),
                "delivery_date": delivery_date,
                "price": tds[2].replace('\\n', '').strip(),
                "sales_volume": tds[3].replace('\\n', '').strip(),
                "purchase_volume": tds[4].replace('\\n', '').strip(),
                "declared_sales_volume": tds[5].replace('\\n', '').strip(),
                "declared_volume_of_purchase": tds[6].replace('\\n', '').strip()
            }
            data_list.append(hour_data)
    with open("filename_key_info.json", "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    for dd in data_list:
        hour = dd["hour"]
        delivery_date = datetime.strptime(dd["delivery_date"], '%d.%m.%Y').strftime('%Y-%m-%d')
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
                declared_volume_of_purchase

            ),
        )

    cnx.commit()
        
    
    
    # data = []

    # # Находим все строки с классом 'ranges-info'
    # rows = soup.find_all("tr", class_="ranges-info")

    # for row in rows:
    #     # Для каждой строки находим все элементы 'td'
    #     tds = row.find_all("td")
    #     # Извлекаем текст из каждого 'td', удаляя пробельные символы на концах
    #     data = [td.get_text(strip=True) for td in tds]
    #     data.append(data)
    # print(soup)



    # cleaned_data = []
    # for item in data:
    #     cleaned_item = item.replace('<\\ /td>', '').replace('\\n', '').replace('\\t', '').strip()
    #     if cleaned_item and '<' not in cleaned_item and '/' not in cleaned_item:
    #         cleaned_data.append(cleaned_item)
    # final_cleaned_data = []
    # for i, item in enumerate(cleaned_data):
    #     if i == 0 or (item.isdigit() and item != cleaned_data[i - 1]):
    #         final_cleaned_data.append(item)
    #     elif not item.isdigit():
    #         final_cleaned_data.append(item)
    # result = []
    # for i in range(0, len(final_cleaned_data), 6):
    #     hour_data = {
    #         "hour": final_cleaned_data[i],
    #         "price": final_cleaned_data[i + 1],
    #         "sales_volume": final_cleaned_data[i + 2],
    #         "purchase_volume": final_cleaned_data[i + 3],
    #         "declared_sales_volume": final_cleaned_data[i + 4],
    #         "declared_volume_of_purchase": final_cleaned_data[i + 5]
    #     }
    #     result.append(hour_data)
    # with open("filename_key_info.json", "w", encoding="utf-8") as f:
    #     json.dump(result, f, ensure_ascii=False, indent=4)
    # Вывод результата
    # print(result)
    
    
    
    
    
    
    
    
    
    # # """JSON"""
    # start_index = src.find('html')
    # end_index = src.rfind('}')  # Находим закрывающую скобку последнего объекта JSON

    # if start_index != -1 and end_index != -1:
    #     valid_json_str = '{' + src[start_index:end_index + 1]  # Обрезаем строку для корректного JSON

    #     try:
    #         # Десериализация обрезанной строки JSON
    #         data = json.loads(valid_json_str)
    #         print(data)
            # # Извлекаем необходимые данные
            # prices_data = data.get('pricesData', [])
            # amounts_data = data.get('amountsData', [])
            # labels = data.get('labels', [])

            # # Выводим данные
            # print("Prices data:", prices_data)
            # print("Amounts data:", amounts_data)
            # print("Labels:", labels)
        # except json.JSONDecodeError as e:
        #     print(f"Ошибка декодирования JSON: {e}")

    # current_hour = int(datetime.now().hour)
    # if current_hour == 22:
    #     name_files = "23-24"
    # elif current_hour == 23:
    #     name_files = "0-1"  # Предположим, что после 23 часа вы хотите видеть "0-1"
    # else:
    #     name_files = f"{current_hour + 2}-{current_hour + 3}"
    # soup = BeautifulSoup(src, "lxml")
    # json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
    # decoded_json = html.unescape(json_str)

    # data_json = json.loads(decoded_json)

    # formatted_data = [
    #     {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
    #     for item in data_json
    # ]
    # name_json = f"{name_files}.json"
    # filename = os.path.join(json_path, name_json)
    # # Сохраняем в файл
    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    # filename_html = os.path.join(html_path, f"{name_files}.html")
    # with open(filename_html, "w", encoding="utf-8") as file:
    #     file.write(src)
   


# def get_data():
#     now = datetime.now()
#     current_hour = now.hour
#     if current_hour == 22:
#         name_html = "0-1"
#     elif current_hour == 23:
#         name_html = "1-2"
#     else:
#         name_html = f"{current_hour + 2}-{current_hour + 3}"
#     filename_html = os.path.join(html_path, f"{name_html}.html")
#     with open(filename_html, encoding="utf-8") as file:
#         src = file.read()
#     soup = BeautifulSoup(src, "lxml")
#     json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
#     decoded_json = html.unescape(json_str)

#     data_json = json.loads(decoded_json)

#     formatted_data = [
#         {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
#         for item in data_json
#     ]
#     name_json = f"{current_hour + 2}-{current_hour + 3}.json"
#     filename = os.path.join(json_path, name_json)
#     # Сохраняем в файл
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(formatted_data, f, ensure_ascii=False, indent=4)


def json_to_sql():
    config = load_connection_to_sql()
    db_config = config["db_config"]
    use_table = config["other_config"]["use_table"]
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        folder_json = os.path.join(json_path, "*.json")

        files_json = glob.glob(folder_json)
        for item_json in files_json:
            delivery_time = os.path.splitext(os.path.basename(item_json))[0]
            with open(item_json, "r", encoding="utf-8") as file:
                data = json.load(file)

            for item in data:
                dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
                sales_date = dt_object.strftime("%Y-%m-%d")
                sales_time = dt_object.strftime("%H:%M:%S")
                sales_date_str = datetime.now()
                # delivery_date_str = sales_date_str + timedelta(days=1)
                # delivery_date = delivery_date_str.strftime("%Y-%m-%d")
                delivery_date = sales_date_str.strftime("%Y-%m-%d")
                price_time = item["Price"]
                amount_time = item["Quantity"]

                # Проверка наличия записи в базе данных
                check_query = f"""
                    SELECT COUNT(*) FROM {use_table}
                    WHERE sales_date = %s AND sales_time = %s AND amount_time = %s AND price_time = %s;
                """
                cursor.execute(
                    check_query, (sales_date, sales_time, amount_time, price_time)
                )
                result = cursor.fetchone()
                data_and_time_data_download = datetime.now().strftime(
                    "%d.%m.%Y_%H:%M:%S"
                )
                if result[0] == 0:  # Если записи не найдено, вставляем данные
                    insert_query = f"""
                        INSERT INTO {use_table} (sales_date, sales_time, amount_time, price_time, delivery_date, delivery_time,data_and_time_data_download)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """
                    cursor.execute(
                        insert_query,
                        (
                            sales_date,
                            sales_time,
                            amount_time,
                            price_time,
                            delivery_date,
                            delivery_time,
                            data_and_time_data_download,
                        ),
                    )

        cnx.commit()
        os.remove(item_json)

    except mysql.connector.Error as err:
        print(f"Ошибка при работе с MySQL: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


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
        get_requests()
        # get_data()
        json_to_sql()
        time.sleep(1)  # Короткая пауза перед планированием следующего запуска


# if __name__ == "__main__":
#     run_at_specific_timee_ach_hour(59, 58)


if __name__ == "__main__":
    get_requests()
#     get_data()
#     json_to_sql()
#     # run_at_specific_time("13:59:50")
