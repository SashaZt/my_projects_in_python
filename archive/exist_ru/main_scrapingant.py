from concurrent.futures import ProcessPoolExecutor
from threading import Lock
import csv
from selenium.webdriver.chrome.service import Service
import os
import json
import re
from pathlib import Path
import html
from datetime import datetime
import random
import shutil
import tempfile
import os
from bs4 import BeautifulSoup
from proxi import proxies
import concurrent.futures
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import zipfile
import time
# import undetected_chromedriver as webdriver
from selenium import webdriver
import undetected_chromedriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv




def extract_data_from_csv():
    csv_filename = 'exist_data.csv'
    columns_to_extract = ['price', 'Numer katalogowy części', 'Producent części']

    data = []  # Создаем пустой список для хранения данных

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')  # Указываем разделитель точку с запятой

        for row in reader:
            item = {}  # Создаем пустой словарь для текущей строки
            for column in columns_to_extract:
                item[column] = row[column]  # Извлекаем значения только для указанных столбцов
            data.append(item)  # Добавляем словарь в список
    return data


def main():
    data_csv = extract_data_from_csv()
    # Разбиваем data_csv на части (например, на 4 части)
    num_parts = 5
    size_per_part = len(data_csv) // num_parts
    parts = [data_csv[i:i + size_per_part] for i in range(0, len(data_csv), size_per_part)]

    # Создаём output.csv и записываем заголовок
    header = ['brand', 'part_number', 'description', 'quantity', 'price_new', 'price_old', 'now','site']
    with open('output_exist.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(header)

    # Запускаем обработку данных в нескольких потоках
    with ProcessPoolExecutor(max_workers=num_parts) as executor:
        executor.map(process_data, parts)



def process_data(part_data):
    now = datetime.now().date()
    data_csv = extract_data_from_csv()  # Вызываем функцию extract_data_from_csv
    heandler = ['brand', 'part_number', 'description', 'quantity', 'price_new', 'price_old', 'data_parsing']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        quantity = 50
        for item in data_csv:
            driver.get('https://exist.ru/')
            price_old = item['price']
            sku = item['Numer katalogowy części']
            brend = item['Producent części'].capitalize()

            try:
                element_to_click = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@id="pcode"]')))
            except:
                continue
            element_to_click.send_keys(sku)
            element_to_click.send_keys(Keys.RETURN)
            try:
                find_catalogs = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//ul[@class="catalogs"]/li/a')))
            except:
                values = [brend, sku, '-', quantity, '-', price_old, now]
                writer.writerow(values)
                continue
            elements_catalogs = driver.find_elements(By.XPATH, '//ul[@class="catalogs"]/li/a')

            base_url = "https://exist.ru"
            brands_links = {}

            for elem in elements_catalogs:
                link = elem.get_attribute('href')
                if not link.startswith("https://exist.ru"):
                    link = base_url + link
                brand_name = elem.find_element(By.XPATH, './/span/b').text
                brands_links[brand_name] = link
            if brend in brands_links:
                # Забираем значение ссылки для этого brend
                link = brands_links[brend]
                # Переходим по ссылке
                driver.get(link)
                time.sleep(1)
                try:
                    find_prices = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@id="price-wrapper"]')))
                except:
                    print('Не загрузилась')
                    continue

                time.sleep(2)
                scripts = driver.find_elements(By.TAG_NAME, 'script')

                for script in scripts:
                    script_content = script.get_attribute("outerHTML")  # Изменение на outerHTML
                    if "//<![CDATA[" in script_content:
                        match = re.search(r'var _data = (.*); var _favs',
                                          script_content)  # Изменение регулярного выражения

                        if match:
                            json_str = match.group(1)
                            json_str = json_str.replace("\\u0027", "'").replace("\\u003e", ">").replace("\\u003c", "<")
                            try:
                                json_data = json.loads(json_str)
                            except json.JSONDecodeError as e:
                                print("Ошибка при попытке декодирования JSON:", e)

                            # Извлекаем необходимую информацию
                            brand = json_data[0].get('CatalogName', None)
                            part_number = json_data[0].get('PartNumber', None)

                            description = json_data[0].get('Description', None)
                            date = None

                            aggregated_parts = json_data[0].get('AggregatedParts', [])
                            if aggregated_parts:
                                statistic_html = aggregated_parts[0].get('StatisticHTML', None)
                                # Если значение есть, примените к нему регулярное выражение
                                if statistic_html:
                                    match = re.search(r'(\d+\.\d+\.\d+)', statistic_html)
                                    date = match.group(1) if match else None

                            aggregated_parts = json_data[0].get('AggregatedParts', [])
                            if aggregated_parts:
                                price_new = aggregated_parts[0].get('priceString', None)
                            else:
                                price_new = None

                            values = [brand, part_number, description, quantity, price_new, price_old, now]
                            # print(values)
                            writer.writerow(values)  #
