from bs4 import BeautifulSoup
import csv
import glob
import re
import requests
import json
import cloudscraper
import os
import time
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor

headers = {
    'authority': 'ukrparts.com.ua',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded',
    'dnt': '1',
    'origin': 'https://ukrparts.com.ua',
    'pragma': 'no-cache',
    'referer': 'https://ukrparts.com.ua/part/oc90/knecht_mahle/?__cf_chl_tk=4ipsHFy6a_kf9R0_5MGbX26oZQacugzgocTNY_Yzqk0-1706097921-0-gaNycGzNCyU',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"121.0.6167.86"',
    'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.86", "Chromium";v="121.0.6167.86"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
}


def get_requests():
    import requests

    response = requests.post('https://ukrparts.com.ua/part/oc90/knecht_mahle/', headers=headers)
    response.encoding = 'utf-8'

    src = response.text
    filename = f"planeta.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


#
def parsing():
    with open('MAHLE.csv', 'w', newline='', encoding='utf-16') as file:
        writer = csv.writer(file, delimiter="\t")
        file = "planeta.html"
        with open(file, encoding="utf-8") as file:
            src = file.read()

        # Используйте BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(src, 'lxml')
        full_product = soup.find('div', attrs={'class': 'container-fluid product_page'})
        title = full_product.find('h1', attrs={'itemprop': 'name'}).get_text(strip=True)
        part_brand = full_product.find('div', attrs={'class': 'part_brand'}).get_text(strip=True)
        part_article_id = full_product.find('div', attrs={'class': 'part_article_id'}).get_text(strip=True)
        part_img = full_product.find('a', attrs={'class': 'fancybox pointer'}).get('href')
        # price_min = full_product.find('span', attrs={'class': 'price_min'}).get_text(strip=True)
        part_detail = full_product.find('ul', attrs={'class': '_part_detail'}).find('ul').find_all('li')

        part_details = [p.get_text(strip=True) for p in part_detail]

        # Начальные значения, которые будут в первых столбцах
        values = [title, part_brand, part_article_id, part_img]

        # Добавляем детали как отдельные столбцы в список values
        values.extend(part_details)


        container_fluid = full_product.find_all('div', attrs={'class': 'container-fluid'})[1]
        pointer_showTypes_all = container_fluid.find_all('tr', attrs={'class': 'pointer showTypes'})
        for i in pointer_showTypes_all:
            data_id = i.get('data-id')
            data_manuf = i.get('data-manuf')
            data_model = i.get('data-model')
            params = {
                'act': 'getCompatibilityCars',
            }
            data = {
                'ID': data_id,
                'manuf': data_manuf,
                'model': data_model,
            }

            response = requests.post('https://ukrparts.com.ua/ajax.php', params=params,
                                     headers=headers, data=data)
            response.encoding = 'utf-8'
            src_01 = response.text
            soup_01 = BeautifulSoup(src_01, 'lxml')

            rows = soup_01.find_all('tr')
            # Для каждой строки извлекаем данные из каждого <td> и сохраняем в список
            first_row_data = [td.get_text(strip=True) for td in rows[1].find_all('td')]
            for row in rows[2:]:  # Начинаем со второй строки данных, так как первая уже сохранена
                # Создаём временный список для хранения данных текущей строки
                temp_values = [title, part_brand, part_article_id, part_img,
                               ]  # Переопределите эти переменные соответствующим образом
                temp_values.extend(part_details)  # Добавляем детали как отдельные столбцы

                # Извлекаем текст из каждого <td> внутри текущей строки, кроме первого элемента
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                # Соединяем сохранённые данные первой строки с данными текущей строки
                combined_row = first_row_data + cols
                temp_values.extend(combined_row)

                row_analogs = full_product.find('div', attrs={'style': 'margin-top:15px;'}).find_all('div', attrs={
                    'class': 'col-xs-12 col-md-4'})
                # Собираем тексты из row_analogs в одной строке, разделяя их запятыми
                analogs_texts = [r.get_text(strip=True) for r in row_analogs]
                analogs_column = ",".join(analogs_texts)
                temp_values.append(analogs_column)
                # for r in row_analogs:
                #     temp_values.append(r.get_text(strip=True))

                # Записываем собранные данные текущей строки в CSV файл
                writer.writerow(temp_values)

            # # Для каждой строки извлекаем данные из каждого <td> и сохраняем в список
            # first_row_data = [td.get_text(strip=True) for td in rows[1].find_all('td')]
            # for row in rows[2:]:  # Начинаем со второй строки данных, так как первая уже сохранена
            #     # Извлекаем текст из каждого <td> внутри текущей строки, кроме первого элемента
            #     cols = [td.get_text(strip=True) for td in row.find_all('td')]
            #     # Соединяем сохранённые данные первой строки с данными текущей строки
            #     combined_row = first_row_data + cols
            #     values.extend(combined_row)
        # row_analogs = full_product.find('div', attrs={'style': 'margin-top:15px;'}).find_all('div', attrs={'class': 'col-xs-12 col-md-4'})
        # for r in row_analogs:
        #     values.append(r.get_text(strip=True))
        # writer.writerow(values)


def parsing_analog():
    file = "pointer_showTypes_all.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()

    # Используйте BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(src, 'lxml')

    # data = []
    # for row in rows[1:]:
    #     # Извлекаем текст из каждого <td> внутри строки
    #     first_cols = [td.get_text(strip=True) for td in row.find_all('td')[0:1]]
    #     cols = [td.get_text(strip=True) for td in row.find_all('td')[1:]]
    #     print(first_cols, cols)
    #     # data.append(cols)
    # # print(data)
    # # Выводим результат
    # for item in data:
    #     print(item)


if __name__ == '__main__':
    # get_requests()
    parsing()
