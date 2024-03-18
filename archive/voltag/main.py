import csv
import glob
import json
import os
import re
import time
import csv
import openpyxl
import re

import requests
from bs4 import BeautifulSoup

current_directory = os.getcwd()
temp_directory = 'temp'
csv_directory = 'csv'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')
csv_path = os.path.join(current_directory, csv_directory)
img_path = os.path.join(temp_path, 'img')
cookies = {
    'PHPSESSID': 'y46XRseJa01FdwxsfBTBxIs6IFpyXhFc',
    '_ym_uid': '16977015098771791',
    '_ym_d': '1697701509',
    '__utma': '197302824.1165919871.1697701509.1697701509.1697701509.1',
    '__utmc': '197302824',
    '__utmz': '197302824.1697701509.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
    '__utmt': '1',
    '__utmb': '197302824.1.10.1697701509',
    '_ym_isad': '2',
    'BX_USER_ID': '3304339f1fce1f8b8863297ab0e125ea',
    '_ym_visorc': 'w',
}

headers = {
    'authority': 'voltag.ru',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'max-age=0',
    # 'cookie': 'PHPSESSID=y46XRseJa01FdwxsfBTBxIs6IFpyXhFc; _ym_uid=16977015098771791; _ym_d=1697701509; __utma=197302824.1165919871.1697701509.1697701509.1697701509.1; __utmc=197302824; __utmz=197302824.1697701509.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmb=197302824.1.10.1697701509; _ym_isad=2; BX_USER_ID=3304339f1fce1f8b8863297ab0e125ea; _ym_visorc=w',
    'dnt': '1',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
}


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


names = 'f2-166'


def total_pages():
    urls = [
        'https://voltag.ru/catalog/list/f2-39/',
        'https://voltag.ru/catalog/list/f2-547/',
        'https://voltag.ru/catalog/list/f2-153/',
        'https://voltag.ru/catalog/list/f2-159/',
        'https://voltag.ru/catalog/list/f2-158/',
        'https://voltag.ru/catalog/list/f2-179/',
        'https://voltag.ru/catalog/list/f2-506/',
        'https://voltag.ru/catalog/list/f2-167/',
        'https://voltag.ru/catalog/list/f2-165/',
        'https://voltag.ru/catalog/list/f2-166/',
        'https://voltag.ru/catalog/list/f2-41/',
        'https://voltag.ru/catalog/list/f2-280/',
        'https://voltag.ru/catalog/list/f2-292/',
        'https://voltag.ru/catalog/list/f2-428/',
        'https://voltag.ru/catalog/list/f2-267/',
        'https://voltag.ru/catalog/list/f2-359/',
        'https://voltag.ru/catalog/list/f2-396/',
        'https://voltag.ru/catalog/list/f2-339/',
        'https://voltag.ru/catalog/list/f2-350/',
        'https://voltag.ru/catalog/list/f2-225/',
        'https://voltag.ru/catalog/list/f2-318/',
        'https://voltag.ru/catalog/list/f2-119/'
    ]
    data = []

    for url in urls:
        response = requests.get(url, cookies=cookies, headers=headers)
        src = response.text
        soup = BeautifulSoup(src, 'lxml')

        total_pages = int(soup.find_all('div', attrs={'class': 'page_number'})[-1].text)
        category = url.split('/')[-2]

        data.append({'name': category, 'total_pages': total_pages})
        time.sleep(5)

    # Запись данных в файл
    with open('categories_info.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_request_list():
    # Открытие и чтение файла
    with open('categories_info.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data[5:]:
        name = item.get('name')
        total_pages = item.get('total_pages')
        for i in range(1, total_pages + 1):
            """
            product_path: Путь к папке, где будут сохраняться все файлы.
            f'{name}': Имя подпапки, которое соответствует имени категории. Сюда подставляется значение переменной name.
            f'{i:02d}.html': Имя файла. Здесь i — это номер страницы, который форматируется как двузначное число с ведущими
            нулями (например, 01, 02, ..., 10, 11, ...). Это обеспечивается форматом :02d. Расширение файла — .html."""
            filename = os.path.join(list_path, name, f'{i:02d}.html')

            if not os.path.exists(filename):
                if i == 1:
                    url = f'https://voltag.ru/catalog/list/{name}/'
                else:
                    url = f'https://voltag.ru/catalog/list/{name}/p-{i}/'

                response = requests.get(url, cookies=cookies, headers=headers)
                src = response.text

                # Создаем папку если она не существует
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))

                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src)

                print(f'Страница {i} категории {name} сохранена.')
                time.sleep(5)
            else:
                print(f'Страница {i} категории {name} уже существует.')


def get_urls_products():
    # Открытие и чтение файла
    with open('categories_info.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data[5:]:
        name = item.get('name')
        filename_hml = os.path.join(list_path, name, '*.html')
        files_glob = glob.glob(filename_hml)
        filename_csv = os.path.join(temp_path, f'{name}.csv')
        # Создаем папку, если она не существует
        if not os.path.exists(os.path.dirname(filename_csv)):
            os.makedirs(os.path.dirname(filename_csv))

        with open(filename_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=";")
            for h in files_glob:  # срез на файлы
                with open(h, encoding="utf-8") as file:
                    src = file.read()
                soup = BeautifulSoup(src, 'lxml')
                urls = soup.find_all('div', attrs={'class': 'catalog_item_title'})
                for u in urls:
                    a_tag = u.find('a')
                    if a_tag:
                        ur = f"https://voltag.ru{a_tag.get('href', '')}"
                        values = [ur]
                        writer.writerow(values)


def get_request_product():
    # Открытие и чтение файла
    with open('categories_info.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data[5:]:
        name = item.get('name')
        filename_csv = os.path.join(temp_path, f'{name}.csv')

        if not os.path.exists(os.path.join(product_path, name)):
            os.makedirs(os.path.join(product_path, name))

        with open(filename_csv, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=";")
            for index, row in enumerate(reader, start=1):
                filename_html = os.path.join(product_path, name, f'{index:02d}.html')
                if not os.path.exists(filename_html):
                    response = requests.get(row[0], cookies=cookies, headers=headers)
                    src = response.text
                    with open(filename_html, "w", encoding='utf-8') as file:
                        file.write(src)
                    print(f'Страница {filename_html}  сохранена.')
                    time.sleep(1)


def parsing():
    # Открытие и чтение файла
    with open('categories_info.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data[5:]:
        name = item.get('name')
        filename_hml = os.path.join(product_path, name, '*.html')
        files_glob = glob.glob(filename_hml)
        all_data_dicts = []  # Список словарей для хранения всех данных
        handler_set = {"title", "crosslist", "application"}  # Инициализация сета с специальными ключами
        for g in files_glob:  # срез на файлы
            with open(g, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            catalog_item_params = soup.find('div', attrs={'class': 'catalog_group_params'})

            data_dict = {}  # Словарь для хранения данных из текущего файла
            crosslist_div = soup.find('div', attrs={'class': 'catalog_group_crosslist_info'})
            if crosslist_div:
                crosslist = re.sub(r'\s+', ' ', crosslist_div.get_text()).strip()
                data_dict['crosslist'] = crosslist

            application_div = soup.find('div', attrs={'class': 'catalog_group_application_info'})
            if application_div:
                application = re.sub(r'\s+', ' ', application_div.get_text()).strip()
                data_dict['application'] = application
            title_div = soup.find('div', attrs={'class': 'catalog_group_title'})
            if title_div:
                title = re.sub(r'\s+', ' ', title_div.get_text()).strip()
                data_dict['title'] = title
            if catalog_item_params:
                # Извлекаем все строки таблицы
                rows = catalog_item_params.select("tbody")
                for tbody in rows:
                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')
                        if cells:
                            key_text = cells[0].text.strip()
                            if key_text:  # Проверяем, что ключ не пустой
                                key = key_text[:-1] if key_text.endswith(':') else key_text
                                values = [cell.text.strip() for cell in
                                          cells[2:]]  # Извлекаем значения начиная со второй ячейки
                                data_dict[key] = ', '.join(values)
                                handler_set.add(key)

            all_data_dicts.append(data_dict)  # Добавляем словарь в список

        special_keys = ["title", "crosslist", "application"]
        other_keys = list(handler_set - set(special_keys))
        fieldnames = special_keys + other_keys

        with open(f'{name}.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()  # записываем заголовки
            for data_dict in all_data_dicts:
                writer.writerow(data_dict)




def csv_to_xlsx():
    filename_csv = os.path.join(csv_path, '*.csv')
    files_glob = glob.glob(filename_csv)

    for g in files_glob:
        name_xlsx = g.split("\\")[-1].replace(".csv", "")

        if os.path.exists(g):  # Проверка на существование файла
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            with open(g, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=";")
                for row_index, row in enumerate(reader, start=1):
                    for col_index, cell_value in enumerate(row, start=1):
                        worksheet.cell(row=row_index, column=col_index, value=cell_value)

            workbook.save(f'{name_xlsx}.xlsx')
        else:
            print(f"Файл {g} не существует.")

if __name__ == '__main__':
    # delete_old_data()
    # extract_data_from_csv()
    # get_request_list()
    # get_urls_products()
    # get_request_product()
    # parsing()
    csv_to_xlsx()

    # total_pages()
