import requests
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
import json
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
        if not os.path.exists(folder):
            os.makedirs(folder)

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

    filename_config = os.path.join(application_path, "config.json")
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

    filename_config = os.path.join(application_path, "connection_to_sql.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


def get_requests():
    config = load_config_headers()
    headers = config["headers"]

    params = {
        "boid": "1d46cedfa548472098a17510ba2f023e",
        "_dc": "1710932831658",
    }

    response = requests.get(
        "https://scmo.oree.com.ua/portal/Plugins/PXS/Pages/Intraday/Lightboard/Default.aspx",
        params=params,
        headers=headers,
        verify=False,
    )

    src = response.text
    # soup = BeautifulSoup(src, "lxml")
    # json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
    # # # Декодирование HTML-сущностей
    # decoded_json = html.unescape(json_str)

    # # # Преобразование декодированной строки в объект Python с помощью json.loads()
    # data_json = json.loads(decoded_json)

    # # for item in data_json:
    # #     print(f"Date: {item['Date']}, Price: {item['Price']}, Quantity: {item['Quantity']}")
    # formatted_data = [
    #     {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
    #     for item in data_json
    # ]
    #  # Получение текущего времени
    # now = datetime.now()

    # # Извлечение текущего часа
    # current_hour = now.hour
    # name_csv = f"{current_hour + 2}-{current_hour + 3}"
    # filename = os.path.join(json_path, f'{name_csv}.json')
    # # Сохраняем в файл
    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(formatted_data, f, ensure_ascii=False, indent=4)

    # Получение текущего времени
    now = datetime.now()

    # Извлечение текущего часа
    current_hour = now.hour
    name_html = f"{current_hour + 2}-{current_hour + 3}"
    filename_html = os.path.join(html_path, f"{name_html}.html")
    with open(filename_html, "w", encoding="utf-8") as file:
        file.write(src)


def get_data():
    now = datetime.now()
    current_hour = now.hour
    name_html = f"{current_hour + 2}-{current_hour + 3}"
    filename_html = os.path.join(html_path, f"{name_html}.html")
    with open(filename_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    json_str = soup.find("input", attrs={"id": "lastTradeChartPoints"}).get("value")
    decoded_json = html.unescape(json_str)

    data_json = json.loads(decoded_json)

    formatted_data = [
        {"Date": item["Date"], "Price": item["Price"], "Quantity": item["Quantity"]}
        for item in data_json
    ]
    name_json = f"{current_hour + 2}-{current_hour + 3}.json"
    filename = os.path.join(json_path, name_json)
    # Сохраняем в файл
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)


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
                delivery_date_str = sales_date_str + timedelta(days=1)
                delivery_date = delivery_date_str.strftime("%Y-%m-%d")
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

                if result[0] == 0:  # Если записи не найдено, вставляем данные
                    insert_query = f"""
                        INSERT INTO {use_table} (sales_date, sales_time, amount_time, price_time, delivery_date, delivery_time)
                        VALUES (%s, %s, %s, %s, %s, %s);
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


# def jsons_to_csv():
#     folder = os.path.join(json_path, "*.json")

#     files_json = glob.glob(folder)
#     # Открываем файл CSV для записи
#     with open("data.csv", "w", newline="", encoding="utf-8") as csvfile:
#         # Задаём названия колонок для CSV файла
#         fieldnames = ["Дата", "Година", "Обсяги", "Ціна"]

#         # Создаём объект DictWriter, указываем файл, заголовки и разделитель (если нужен другой, кроме запятой)
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",")

#         # Записываем заголовки в файл
#         writer.writeheader()
#         # Собираем все данные в один список
#         all_data = []
#         for item in files_json:
#             with open(item, "r", encoding="utf-8") as file:
#                 data = json.load(file)
#                 all_data.extend(
#                     data
#                 )  # Добавляем данные из текущего файла в общий список

#         # Сортируем список по дате
#         all_data_sorted = sorted(
#             all_data, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%dT%H:%M:%S")
#         )

#         # Теперь у вас есть отсортированный список all_data_sorted, и вы можете записать его в CSV
#         with open("sorted_data.csv", "w", encoding="utf-8", newline="") as f:
#             fieldnames = ["Дата", "Година", "Обсяги", "Ціна"]
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()

#             for item in all_data_sorted:
#                 dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
#                 date = dt_object.strftime("%Y-%m-%d")
#                 time = dt_object.strftime("%H:%M:%S")

#                 writer.writerow(
#                     {
#                         "Дата": date,
#                         "Година": time,
#                         "Обсяги": item["Quantity"],
#                         "Ціна": item["Price"],
#                     }
#                 )
#         # for item in files_json:
#         #     # Читаем данные из JSON файла
#         #     with open(item, "r", encoding="utf-8") as file:
#         #         data = json.load(file)

#         #         # Проходим по каждому элементу в списке
#         #         for item in data:
#         #             # Разделяем дату и время
#         #             dt_object = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
#         #             date = dt_object.strftime("%Y-%m-%d")
#         #             time = dt_object.strftime("%H:%M:%S")

#         #             # Записываем данные в строку файла
#         #             writer.writerow(
#         #                 {
#         #                     "Дата": date,
#         #                     "Година": time,
#         #                     "Обсяги": item["Quantity"],
#         #                     "Ціна": item["Price"],
#         #                 }
#         #             )
#     # Загрузка данных из файла CSV
#     data = pd.read_csv("sorted_data.csv", encoding="utf-8")

#     # Сохранение данных в файл XLSX
#     data.to_excel(f"sorted_data.xlsx", index=False, engine="openpyxl")


# if __name__ == "__main__":
#     run_at_specific_time(59, 30)


def run_at_specific_time(target_time_str):
    # Преобразование строки времени в объект datetime сегодняшнего дня
    now = datetime.now()
    target_time = datetime.strptime(target_time_str, "%H:%M:%S").replace(
        year=now.year, month=now.month, day=now.day
    )

    # Если целевое время уже прошло сегодня, устанавливаем его на следующий день
    if target_time < now:
        target_time += timedelta(days=1)

    print(f"Скрипт запланирован на {target_time}")

    # Ожидание до целевого времени
    while datetime.now() < target_time:
        time.sleep(
            1
        )  # Спим по 1 секунде, чтобы избежать чрезмерной загрузки процессора

    # Вызов функции после достижения целевого времени
    get_requests()
    get_data()


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
        get_data()
        json_to_sql()
        time.sleep(10)  # Короткая пауза перед планированием следующего запуска


if __name__ == "__main__":
    # run_at_specific_time("15:50:50")
    run_at_specific_timee_ach_hour(59, 58)


# if __name__ == "__main__":
#     # creative_folders()
#     # get_requests()
#     get_data()
#     json_to_sql()
#     # run_at_specific_time("13:59:50")
