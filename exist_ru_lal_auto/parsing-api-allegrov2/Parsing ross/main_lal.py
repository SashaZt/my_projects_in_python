import csv
import datetime
import glob
import os
import pandas as pd
import re
from datetime import datetime
from io import StringIO

import numpy as np
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

    async def fetch(session, sku, brend,price_old, filename, headers):
        params = {
            'action': 'catalog_price_view',
            'code': sku,
            'id_currency': '1',
            'cross_advance': ['0', '1'],
        }
        try:
            async with session.get('https://lal-auto.ru/', params=params, headers=headers) as response:
                src = await response.text()
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src)
        except Exception as e:
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
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            # 'Cookie': 'PHPSESSID=erp05a6c0d8a9kvdres8ilh1p0',
            'DNT': '1',
            'Pragma': 'no-cache',
            # 'Referer': 'https://lal-auto.ru/?action=catalog_price_view&code=602+0008+00&id_currency=1&cross_advance=0&cross_advance=1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        data_csv = extract_data_from_csv()
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(data_csv), 1000):
                tasks = []
                for item in data_csv[i:i + 1000]:
                    sku = item['Numer katalogowy części'].replace(" ", "").replace("/", "")
                    brend = item['Producent części'].capitalize()
                    price_old = item['price']
                    filename = os.path.join(product_path, sku + '.html')
                    if not os.path.exists(filename):
                        tasks.append(fetch(session, sku, brend,price_old, filename, headers))
                if tasks:
                    await asyncio.gather(*tasks)
                    if i + 1000 < len(data_csv):
                        await asyncio.sleep(10)

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
            sku = item['Numer katalogowy części'].replace(" ", "")
            sku = sku.replace("/", "")
            brend = item['Producent części'].capitalize()
            folders_html = os.path.join(product_path, f"{sku}.html")
            try:
                with open(folders_html, encoding="utf-8") as file:
                    src = file.read()
            except:
                continue
            soup = BeautifulSoup(src, 'html.parser')
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
            # Удаляем символ "Р." и заменяем "---" на NaN
            selected_columns['Цена'] = selected_columns['Цена'].str.replace(' Р.', '', regex=False).replace('---',
                                                                                                            np.nan)

            # Преобразуем столбец "Цена" в числовой формат
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
    delete_old_data()
    get_requests()
    parsing()
    sort_csv()
