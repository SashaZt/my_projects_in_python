import csv
import datetime
import glob
import os
import pandas as pd
import re
from datetime import datetime
from io import StringIO
import sys
import time
import json
import numpy as np
import random
import requests
from bs4 import BeautifulSoup

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')
from config_lal import name_files

def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        # print(f'Очистил папку {os.path.basename(folder)}')


def extract_data_from_csv():
    csv_filename = 'data.csv'
    columns_to_extract = ['price', 'Numer katalogowy części', 'Producent części']

    data = []  # Создаем пустой список для хранения данных

    with open(csv_filename, 'r', newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')  # Указываем разделитель точку с запятой

        for row in reader:
            item = {}  # Создаем пустой словарь для текущей строки
            for column in columns_to_extract:
                item[column] = row[column]  # Извлекаем значения только для указанных столбцов
            data.append(item)  # Добавляем словарь в список
    return data
def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")

    with open(filename_config, "r") as config_file:
        config = json.load(config_file)

    return config

def get_requests():
    import aiohttp
    import asyncio
    import csv
    import os

    current_directory = os.getcwd()
    temp_directory = 'temp'
    temp_path = os.path.join(current_directory, temp_directory)
    list_path = os.path.join(temp_path, 'list')
    product_path = os.path.join(temp_path, 'product')
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")

    async def fetch(session, sku, brend,price_old, filename, headers):
        params = {
            'action': 'catalog_price_view',
            'code': sku,
            'id_currency': '1',
            'cross_advance': ['0', '1'],
        }
        url = 'https://lal-auto.ru/'
        try:
            async with session.get(url, params=params, headers=headers) as response:
                src = await response.text()
                soup = BeautifulSoup(src, 'lxml')
                table_manufacturers = soup.find('div', {'class': 'hrey_hd'})
                # Извлечение всего текста из элемента и его очистка
                text = " ".join(table_manufacturers.stripped_strings).lower()
                text = text.replace('\n', ' ').replace('\r', '')  # Удаление переносов строк, если они есть
                text_find = 'aртикул найден в следующих вариантах:'
                if text_find not in text:
                    with open(filename, "w", encoding='utf-8') as file:
                        file.write(src)
                else:
                    # sku = re.sub(r"[^\w\d]|_", "", sku)
                    rows = soup.select('form#table_form tr')
                    url_to_fetch = None
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 2 and tds[1].text.strip() == sku:
                            brand_text = tds[0].text.strip()
                            
                            if brand_text.upper() == brend.upper():
                                href = tds[0].get('href') if 'href' in tds[0].attrs else None
                                if href.startswith("./"):
                                    href = href[2:]  # Удаляем первые два символа
                                url_to_fetch = f'https://lal-auto.ru/{href}'
                                break
                    if url_to_fetch is not None:
                        async with session.get(url_to_fetch, headers=headers) as response:
                            src = await response.text()
                            with open(filename, "w", encoding='utf-8') as file:
                                file.write(src)
        except Exception as e:
            print(f"Произошла ошибка: {e}")

            values = [price_old, sku, brend]
            with open('exist_data.csv', 'a', newline='', encoding='utf-16') as exist_file:
                exist_writer = csv.writer(exist_file, delimiter='\t')
                exist_writer.writerow(values)  # Записываем в exist.csv

    def extract_data_from_csv():
        csv_filename = 'data.csv'
        columns_to_extract = ['price', 'Numer katalogowy części', 'Producent części']

        data = []  # Создаем пустой список для хранения данных

        with open(csv_filename, 'r', newline='', encoding='utf-16') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')  # Указываем разделитель точку с запятой

            for row in reader:
                item = {}  # Создаем пустой словарь для текущей строки
                for column in columns_to_extract:
                    item[column] = row[column]  # Извлекаем значения только для указанных столбцов
                data.append(item)  # Добавляем словарь в список
        return data

    async def main():
        file_path = 'exist_data.csv'

        if os.path.exists(file_path):
            os.remove(file_path)

        data_csv = extract_data_from_csv()
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(data_csv), 1000):
                tasks = []
                for item in data_csv[i:i + 1000]:
                    sku = item['Numer katalogowy części'].replace(" ", "").replace("/", "")
                    brend = item['Producent części'].capitalize()
                    price_old = item['price']
                    sku = re.sub(r"[^\w\d]|_", "", sku)
                    filename = os.path.join(product_path, sku + '.html')
                    if not os.path.exists(filename):
                        tasks.append(fetch(session, sku, brend,price_old, filename, headers))
                if tasks:
                    await asyncio.gather(*tasks)
                    if i + 1000 < len(data_csv):
                        sleep_time = random.randint(time_a, time_b)
                        # print(f'Сторінка {p}')

                        time.sleep(sleep_time)
                               


    asyncio.run(main())


def parsing():
    now = datetime.now().date()
    data_csv = extract_data_from_csv()  # Вызываем функцию extract_data_from_csv
    # print(data_csv)
    # exit()
    quantity = 50
    site = 'L'
    heandler = ['brand', 'part_number', 'description', 'quantity', 'lowest_price', 'price_old', 'data_transport',
                              'price_update', 'site', 'now']
    with open(f'{name_files}_lal.csv', 'w', newline='', encoding='utf-16') as file, open('exist_data.csv', 'a', newline='', encoding='utf-16') as exist_file:
        writer = csv.writer(file, delimiter='\t')
        exist_writer = csv.writer(exist_file, delimiter='\t')  # Создаем writer для exist.csv
        # exist_writer.writerow(['brand', 'sku', 'price'])  # Записываем заголовок для exist.csv
        exist_writer.writerow(['price', 'Numer katalogowy części', 'Producent części'])  # Записываем заголовок для exist.csv

        writer.writerow(heandler)  # Записываем заголовки только один раз для output.csv

        for item in data_csv:
            price_old = item['price']
            sku = item['Numer katalogowy części']
            # sku = item['Numer katalogowy części'].replace(" ", "")
            sku = re.sub(r"[^\w\d]|_", "", sku)
            # sku = sku.replace("/", "")
            brend = item['Producent części'].capitalize()
            folders_html = os.path.join(product_path, f"{sku}.html")
            try:
                with open(folders_html, encoding="utf-8") as file:
                    src = file.read()
            except:
                continue
            soup = BeautifulSoup(src, 'lxml')
            table = soup.find('table', class_='datatable')
            html_string_io = StringIO(str(table))
            df = pd.read_html(html_string_io)[0]
            try:
                selected_columns = df.iloc[:, [0, 1, 2, 6, 7, 8]]
            except:
                values = [price_old, sku, brend]
                exist_writer.writerow(values)  # Записываем в exist.csv
                continue  # заменил continue на pass, потому что в вашем коде не было цикла
            # Удаляем первую строку
            selected_columns = selected_columns.iloc[1:, :]

            # Удаляем символ "Р." без изменения типа данных
            selected_columns['Цена'] = selected_columns['Цена'].str.replace(' Р.', '', regex=False)

            # Заменяем "---" на np.nan без предупреждения о изменении типа данных
            selected_columns['Цена'] = selected_columns['Цена'].replace('---', np.nan)

            # Явное преобразование столбца "Цена" в числовой формат
            selected_columns['Цена'] = pd.to_numeric(selected_columns['Цена'], errors='coerce')


            filtered_rows = selected_columns[selected_columns.iloc[:, 1] == sku]

            # Если есть строки с данным SKU
            if not filtered_rows.empty:
                # Проверяем, есть ли в 'Цена' значения, отличные от NaN
                if not filtered_rows['Цена'].isna().all():
                    # Находим индекс строки с минимальной ценой
                    min_price_index = filtered_rows['Цена'].idxmin()

                    # Извлекаем эту строку
                    min_price_row = filtered_rows.loc[min_price_index]

                    # Выводим значения каждой колонки
                    brand = min_price_row.iloc[0]
                    part_number = min_price_row.iloc[1]
                    description = min_price_row.iloc[2]
                    if isinstance(description, str):  # проверка, что description является строкой
                        description = "".join(re.findall(r'[а-яА-ЯёЁ\s]+', description)).strip()
                        description = " ".join(description.split())
                    else:
                        description = ""  # или любое другое действие в случае, если description не является строкой

                    try:
                        data_transport = min_price_row.iloc[3].replace(' - ', ' _ ')
                    except:
                        data_transport = min_price_row.iloc[3]
                    price_update = min_price_row.iloc[4]
                    lowest_price = min_price_row.iloc[5]

                    values = [brand, part_number, description, quantity, lowest_price, price_old, data_transport,
                              price_update, site, now]
                    writer.writerow(values)
                    # print(values)
                else:
                    values = [price_old, sku, brend]
                    exist_writer.writerow(values)  # Записываем в exist.csv
                    continue
            else:
                values = [price_old, sku, brend]
                exist_writer.writerow(values)  # Записываем в exist.csv
                continue

def sort_csv():
    # Читаем CSV файл
    df = pd.read_csv(f'{name_files}_lal.csv', sep='\t', encoding='utf-16')
    # Преобразовываем столбец 'price_update' в формат даты
    df['price_update'] = pd.to_datetime(df['price_update'], format='%d.%m.%y')

    df = df.sort_values(by='price_update', ascending=False)
    df.to_csv(f'{name_files}_lal.csv', sep='\t', encoding='utf-16', index=False)


if __name__ == '__main__':
    # delete_old_data()
    # get_requests()
    parsing()
    # sort_csv()
