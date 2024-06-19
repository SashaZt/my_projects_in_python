import glob
import requests
import os
import json
import sys
import time
import datetime
import pandas as pd
import shutil

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
list_products = os.path.join(temp_path, "list_products")
product = os.path.join(temp_path, "product")


# Читаем список sku
def read_sku_file():
    file_path = "sku.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            return [line.strip() for line in lines]
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return []


# Читаем файл config для получения cookies и headers
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


def get_list_products_json(time_sleep):
    # Создание директории, если она не существует
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(list_products, exist_ok=True)
    os.makedirs(product, exist_ok=True)
    config = load_config_headers()
    headers = config["headers"]
    all_skus = read_sku_file()
    for one_sku in all_skus:
        params = {
            "filter[keyword]": one_sku,
            "page[number]": "1",
            "page[size]": "100",
            "_session_key": "products",
        }
        filename = os.path.join(list_products, f"{one_sku}.json")
        if not os.path.exists(filename):
            response = requests.get(
                "https://app1.shippingeasy.com/jsapi/coalesced_products",
                params=params,
                headers=headers,
            )
            # Сохранить json
            json_data = response.json()
            json_data = json_data["data"][0]
            id_sku = json_data["id"]
            sku = json_data["attributes"]["sku"]
            datas = {"id": id_sku, "sku": sku}

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(datas, f, ensure_ascii=False, indent=4)  # Записываем в файл
            print(f"Сохранил файл {filename}")
            time.sleep(time_sleep)


def get_product(time_sleep):
    config = load_config_headers()
    headers = config["headers"]
    folder = os.path.join(list_products, "*.json")
    files_json = glob.glob(folder)
    for item in files_json:
        # Открыть json
        with open(item, encoding="utf-8") as f:
            data = json.load(f)
        id_sku = data["id"]
        sku = data["sku"]
        filename = os.path.join(product, f"{sku}.json")
        if not os.path.exists(filename):
            response = requests.get(
                f"https://app1.shippingeasy.com/jsapi/products/{id_sku}/transfers",
                headers=headers,
            )
            json_data = response.json()

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
            print(f"Сохранил файл {filename}")
            time.sleep(time_sleep)


# Парсим json
def parsing_product():
    folder = os.path.join(product, "*.json")
    files_json = glob.glob(folder)
    all_datas = []

    for item in files_json:
        file_name = os.path.basename(item)

        # Извлечение числа из имени файла (без расширения)
        sku = os.path.splitext(file_name)[0]
        # Открыть json
        with open(item, encoding="utf-8") as f:
            data = json.load(f)
        json_data = data["data"]

        for data in json_data:
            quantity = data["quantity"]
            source = data["source"]
            destination = data["destination"]
            headline = data["headline"]
            detail = data["detail"]
            is_incoming = data["is_incoming"]
            created_at = data["created_at"]
            dt_object = datetime.datetime.fromtimestamp(created_at)

            # Форматирование в нужный формат
            formatted_date = dt_object.strftime("%d.%m.%Y, %H:%M:%S")
            sign = "+" if is_incoming else "-"

            datas = {
                "sku": sku,
                "+ | −": f"{sign}{quantity}",
                "Change Activity": f"{destination} (from {source})",
                "Change Description": f"{headline} {detail}",
                "Timestamp": formatted_date,
            }
            all_datas.append(datas)

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Запись DataFrame в Excel
    output_file = "output.xlsx"
    df.to_excel(output_file, index=False)

    print(f"Данные успешно записаны в {output_file}")


# Удаление временных файлов
def delete_old_data():
    filename_csv_to_xlsx = os.path.join(current_directory, "output.xlsx")

    if os.path.exists(filename_csv_to_xlsx):
        # Удалите папку temp_path и её содержимое
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            print(f"Папка {temp_path} успешно удалена.")


while True:
    time_sleep = int(input("Введите количество сек для паузы: "))
    # Запрос ввода от пользователя
    while True:
        print(
            "Введите 1 для получения Id и SKU товаров"
            "\nВведите 2 для загрузки всех товаров"
            "\nВведите 3 после скачивания всех товаров, получаем отчет"
            "\nВведите 4 если у Вас есть файл с отчетом, можно удалить старые данные!!!!"
            "\nВведите 0 Закрытия программы"
        )
        try:
            user_input = int(
                input("Выберите действие: ")
            )  # Сначала получаем ввод как строку
        except ValueError:  # Если введенные данные нельзя преобразовать в число
            print("Неверный ввод, пожалуйста, введите корректный номер действия.")
            continue  # Пропускаем оставшуюся часть цикла и начинаем с новой итерации
        if user_input == 1:
            print("получаем Id и SKU товаров")
            get_list_products_json(time_sleep)
            print("Переходим к пункту 2")
        elif user_input == 2:
            get_product(time_sleep)
            print("Переходим к пункту 3")
        elif user_input == 3:
            parsing_product()
            print("Переходим к пункту 0")
        elif user_input == 4:
            delete_old_data()
            print("Старые файлы удалены, переходим к пункту 1")
        elif user_input == 0:
            print("Программа завершена.")
            time.sleep(2)
            sys.exit(1)

        else:
            print("Неверный ввод, пожалуйста, введите корректный номер действия.")
