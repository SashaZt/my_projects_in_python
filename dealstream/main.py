# -*- coding: utf-8 -*-
import csv
import glob
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from config import api_key
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')
img_path = os.path.join(temp_path, 'img')



def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path, img_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path, img_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


def get_total_company():
    url = 'https://dealstream.com/search/financialassets?q='
    response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}')
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    text = soup.find('div', class_='text-muted text-center').em.string

    # Используем регулярное выражение для извлечения числа
    match = re.search(r'of ([\d,]+) results', text)
    if match:
        number_str = match.group(1).replace(',', '')  # Удалить запятые
        number = int(number_str)  # Преобразовать строку в число
        return number





def parsing_online():
    productid_list = get_csv_productid()
    heandler = ['name', 'description', 'url', 'productid', 'image', 'logo', 'price', 'priceCurrency', 'addressCountry',
                'addressLocality', 'addressRegion', 'industry', 'category','location']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)
        all_product = get_total_company()
        coun = 0
        pages = (all_product // 20) + 2
        stop_processing = False
        for i in range(1, pages):
            filename = os.path.join(product_path, f'data_{coun}.html')
            coun += 1
            print(f'Страница {coun}')
            if stop_processing:  # Если флаг установлен, прекращаем обработку следующих страниц
                break
            filename = os.path.join(product_path, f'0{coun}.html')
            urls = f'https://dealstream.com/search/financialassets?page={i}&q='
            if not os.path.exists(filename):
                while True:
                    response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={urls}')
                    src = response.text
                    soup = BeautifulSoup(src, 'lxml')
                    scripts = soup.find_all('script', type="application/ld+json")
                    if scripts:
                        script = scripts[0]
                        data_json = json.loads(script.string)
                        with open(filename, "w", encoding='utf-8') as f:
                            f.write(src)
                        break
                    else:
                        print(f'Пауза 10сек, делаем повтор')
                        time.sleep(10)
                table = soup.find('div', attrs={"class": "panel panel-default"})
                rows = table.find_all('div', attrs={"class": "list-group-item post"})

                stop_processing = False  # Переменная для прекращения обработки

                for j, r in zip(data_json['about'], rows):
                    productid = j.get('item', {}).get('productid', None)

                    name = j.get('item', {}).get('name', None)
                    description = j.get('item', {}).get('description', None)
                    url = j.get('item', {}).get('url', None)
                    image = j.get('item', {}).get('image', None)
                    logo = j.get('item', {}).get('logo', None)
                    price = j.get('item', {}).get('offers', {}).get('price', None)
                    priceCurrency = j.get('item', {}).get('offers', {}).get('priceCurrency', None)
                    addressCountry = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                          {}).get(
                        'addressCountry', None)
                    addressLocality = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                           {}).get(
                        'addressLocality', None)
                    addressRegion = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                         {}).get(
                        'addressRegion', None)
                    try:
                        industry = r.find('span', attrs={"title": "Industry"}).text
                    except:
                        industry = None
                    try:
                        category = r.find('span', attrs={"title": "Category"}).text
                    except:
                        category = None
                    try:
                        location = r.find('span', attrs={"title": "Location"}).text
                    except:
                        location = None

                    values = [name, description, url, productid, image, logo, price, priceCurrency, addressCountry,
                              addressLocality, addressRegion, industry, category, location]

                    writer.writerow(values)
                    if productid in productid_list:
                        stop_processing = True  # Устанавливаем флаг остановки обработки
                        break  # Прекращаем выполнение текущего цикла for

                if stop_processing:  # Если флаг установлен, прекращаем обработку страниц
                    break



def get_csv_productid():
    csv_filename = 'output.csv'
    productid_list = []

    try:
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")

            for row in reader:
                productid = row.get('productid')
                if productid:
                    productid_list.append(productid)

    except FileNotFoundError:
        # Если файла не существует, функция вернёт пустой список
        pass

    return productid_list


def save_xslx():
    # Определите регулярное выражение для фильтрации недопустимых символов
    pattern = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')

    # Открываем CSV файл для чтения
    with open('output_12k.csv', 'r', newline='', encoding='utf-8') as csvfile:
    # with open('output.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        # next(reader)  # Пропускаем первую строку с заголовками

        # Создаем новую книгу Excel и выбираем активный лист
        workbook = Workbook()
        sheet = workbook.active

        # Заполняем лист данными из CSV файла, фильтруя недопустимые символы
        for row in reader:
            filtered_row = [re.sub(pattern, '', cell) if cell else cell for cell in row]
            sheet.append(filtered_row)

        # Сохраняем книгу в файле XLSX
        workbook.save('output_12k.xlsx')
        # workbook.save('output.xlsx')

def parsing_offline():
    folder = os.path.join('C:\\scrap_tutorial-master\\dealstream\\temp\\product 700', '*.html')

    files_html = glob.glob(folder)
    heandler = ['name', 'description', 'url', 'productid', 'image', 'logo', 'price', 'priceCurrency', 'addressCountry',
                'addressLocality', 'addressRegion', 'industry', 'category', 'location']
    with open('output_12k.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            scripts = soup.find_all('script', type="application/ld+json")[0]
            data_json = json.loads(scripts.string)
            table = soup.find('div', attrs={"class": "panel panel-default"})
            rows = table.find_all('div', attrs={"class": "list-group-item post"})

            for j, r in zip(data_json['about'], rows):
                productid = j.get('item', {}).get('productid', None)

                name = j.get('item', {}).get('name', None)
                description = j.get('item', {}).get('description', None)
                url = j.get('item', {}).get('url', None)
                image = j.get('item', {}).get('image', None)
                logo = j.get('item', {}).get('logo', None)
                price = j.get('item', {}).get('offers', {}).get('price', None)
                priceCurrency = j.get('item', {}).get('offers', {}).get('priceCurrency', None)
                addressCountry = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                      {}).get(
                    'addressCountry', None)
                addressLocality = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                       {}).get(
                    'addressLocality', None)
                addressRegion = j.get('item', {}).get('offers', {}).get('availableAtOrFrom', {}).get('address',
                                                                                                     {}).get(
                    'addressRegion', None)
                try:
                    industry = r.find('span', attrs={"title": "Industry"}).text
                except:
                    industry = None
                try:
                    category = r.find('span', attrs={"title": "Category"}).text
                except:
                    category = None
                try:
                    location = r.find('span', attrs={"title": "Location"}).text
                except:
                    location = None

                values = [name, description, url, productid, image, logo, price, priceCurrency, addressCountry,
                          addressLocality, addressRegion, industry, category, location]

                writer.writerow(values)

if __name__ == '__main__':
    # delete_old_data()
    # parsing_online()
    save_xslx()
    # parsing_offline()

