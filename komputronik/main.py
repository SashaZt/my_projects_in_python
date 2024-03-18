import csv
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from lxml import etree as ET

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


def get_category():
    url_base = 'https://www.komputronik.pl/category/7545/lodowki.html?showBuyActiveOnly=1'

    name_category = url_base.split('/')[-2]
    """Использование сессий requests:
    Это может улучшить производительность при 
    многократных запросах к одному и тому же серверу, 
    так как сессии могут повторно использовать подключения TCP."""
    with requests.Session() as session:
        session.params = {'api_key': api_key}

        # Получаем общее количество продуктов
        response = session.get('http://api.scraperapi.com', params={'url': url_base})
        soup = BeautifulSoup(response.content, 'lxml')
        product_list = soup.find('ktr-product-list')
        products_count = int(product_list['products-count']) if product_list else 0
        total_page = products_count // 20
        # Скачиваем страницы
        for p in range(1, total_page + 2):
            filename = os.path.join(list_path, f"0{p}_{name_category}.html")
            url = f'{url_base}&p={p}' if p > 1 else url_base
            if not os.path.exists(filename):
                response = session.get('http://api.scraperapi.com', params={'url': url})

                with open(filename, "w", encoding='utf-8') as file:
                    file.write(response.text)


def get_url_product():
    folder = os.path.join(list_path, '*.html')

    files_html = glob.glob(folder)
    with open('url.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            link_tags = soup.find_all('h2',
                                      class_='font-headline text-lg font-bold leading-6 line-clamp-3 md:text-xl md:leading-8')
            urls = [l.find('a')['href'] for l in link_tags if l.find('a') and l.find('a').has_attr('href')]
            for url in urls:
                writer.writerow([url])


"""Это позволит вам обрабатывать несколько URL одновременно, что может значительно ускорить процесс."""


def fetch_url(url, api_key, product_path):
    name_product = url.split('/')[-2]
    filename = os.path.join(product_path, f"{name_product}.html")
    if not os.path.exists(filename):
        with requests.Session() as session:
            session.params = {'api_key': api_key}
            response = session.get('http://api.scraperapi.com', params={'url': url})
            with open(filename, "w", encoding='utf-8') as file:
                file.write(response.text)


def get_product():
    name_files = 'url.csv'

    with open(name_files, newline='', encoding='utf-8') as files:
        urls = [row[0] for row in csv.reader(files, delimiter=' ', quotechar='|')]

    # Установите количество потоков (например, 5)
    threads = 5

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(fetch_url, url, api_key, product_path) for url in urls]
        for future in futures:
            future.result()  # Ждем завершения каждого потока


def parsing_proba():
    folder = os.path.join(product_path, '*.html')

    files_html = glob.glob(folder)
    # with open('product.csv', 'w', newline='', encoding='utf-8') as file:
    #     writer = csv.writer(file, delimiter=";")
    catalog = ET.Element('catalog')
    catalog.set('date', '2023-11-21 11:52')  # Пример даты, можно заменить актуальной
    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        script = soup.find_all('script', type="application/ld+json")[1]
        data_json = json.loads(script.string)
        url = data_json['offers']['url']
        name = data_json['name']
        price = data_json['offers']['price']
        system_code = data_json['sku']
        vendor = data_json['brand']['name']
        mpn_code = data_json['mpn']
        ean = data_json['gtin13']

        links = soup.find('div', class_='tests-breadcrumbs').find_all('a')
        category = None
        if len(links) == 5:
            # Извлечение текста из первых трех ссылок и объединение их в одну строку
            category = '/'.join(link.get_text().strip() for link in links[1:4])
        elif len(links) == 4:
            category = '/'.join(link.get_text().strip() for link in links[1:3])
        else:
            print(len(links))
            print("Количество ссылок не соответствует ожидаемому.")
        description = data_json['description']

        specifications = {}
        pairs = soup.select('.tests-full-specification .grid.grid-cols-2')
        # Перебор пар и добавление их в словарь
        for pair in pairs:
            key = pair.find('div', class_='relative flex space-x-2 p-1 xl:p-2').find('span').get_text(strip=True)
            value = pair.find('div', class_='p-1 font-semibold xl:p-2').get_text(strip=True)
            specifications[key] = value

        # Поиск div с классом "relative", который содержит ktr-gallery
        relative_divs = soup.find_all('div', class_='relative')

        # Перебор всех найденных div и поиск ktr-gallery
        for r in relative_divs:
            gallery_tag = r.find('ktr-gallery')
            if gallery_tag and 'items' in gallery_tag.attrs:
                try:
                    # Удаление кавычек и попытка преобразования JSON
                    items_json = gallery_tag['items'].strip("'")
                    items_data = json.loads(items_json)

                    # Проверка, что результат является списком словарей
                    if isinstance(items_data, list) and all(isinstance(item, dict) for item in items_data):
                        # print(items_data)
                        break  # Прерываем цикл, если найден и обработан нужный элемент
                    else:
                        print("Найденный JSON не является списком словарей.")
                except json.JSONDecodeError:
                    continue
            else:
                continue
        picture = []
        for item in items_data:
            if 'url' in item:
                picture.append(item['url'])
        # Создание элемента продукта
        product = ET.SubElement(catalog, 'product')

        # Добавление данных продукта
        ET.SubElement(product, 'url').text = url
        product.append(create_cdata_element('name', name))
        ET.SubElement(product, 'price').text = str(price)
        ET.SubElement(product, 'system_code').text = system_code
        product.append(create_cdata_element('vendor', vendor))
        ET.SubElement(product, 'mpn_code').text = mpn_code
        ET.SubElement(product, 'ean').text = ean
        product.append(create_cdata_element('category', category))
        product.append(create_cdata_element('description', description))

        # Добавление изображений
        for pic_url in picture:
            ET.SubElement(product, 'picture').text = pic_url

        # Добавление спецификаций
        for key, value in specifications.items():
            add_param_with_cdata(product, key, value)

            # Функция для красивого вывода XML
            # Сохранение итогового XML-файла
        with open('output.xml', 'w', encoding='utf-8') as file:
            file.write(prettify(catalog))


def add_param_with_cdata(parent, name, text):
    param = ET.SubElement(parent, 'param')
    param.set('name', name)
    param.text = ET.CDATA(text)


def create_cdata_element(tag, text):
    element = ET.Element(tag)
    element.text = ET.CDATA(text)
    return element


def prettify(element):
    rough_string = ET.tostring(element, pretty_print=True, encoding='UTF-8', xml_declaration=True)
    return rough_string.decode('utf-8')


if __name__ == "__main__":
    parsing_proba()
