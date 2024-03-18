import csv
import glob
import os
import random
import time

import requests
from bs4 import BeautifulSoup

from proxi import proxies
import re
import glob
import json
import os
from bs4 import BeautifulSoup
import shutil
import pickle
import tempfile
import zipfile
import time
import random
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

# import undetected_chromedriver as webdriver
def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions') # Отключает использование расширений
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver

def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)


file_path = "proxies.txt"


def get_requests():
    cookies = {
        'LangId': '2',
        'MAXCOST': '0',
        'MINCOST': '0',
        'SIDS': '0',
        'avrsid': 'c2noes7uulnk00he5u1u96jcp5',
        'lst-cat': '',
        '_ga_HSTS5N7TNH': 'GS1.1.1692187785.1.0.1692187785.60.0.0',
        '_ga': 'GA1.1.1515260137.1692187785',
        '_gcl_au': '1.1.700059413.1692187785',
        '_fbp': 'fb.2.1692187785515.177623426',
    }

    headers = {
        'authority': 'www.avtoradosti.com.ua',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'LangId=2; MAXCOST=0; MINCOST=0; SIDS=0; avrsid=c2noes7uulnk00he5u1u96jcp5; lst-cat=; _ga_HSTS5N7TNH=GS1.1.1692187785.1.0.1692187785.60.0.0; _ga=GA1.1.1515260137.1692187785; _gcl_au=1.1.700059413.1692187785; _fbp=fb.2.1692187785515.177623426',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.avtoradosti.com.ua/ua/katalog-tovara/avtolampy/p_1.html',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }
    for i in range(1, 197):
        proxies = load_proxies(file_path)
        proxy = get_random_proxy(proxies)
        login_password, ip_port = proxy.split('@')
        login, password = login_password.split(':')
        ip, port = ip_port.split(':')
        proxy_dict = {
            "http": f"http://{login}:{password}@{ip}:{port}",
            "https": f"http://{login}:{password}@{ip}:{port}"
        }
        response = requests.get(f'https://www.avtoradosti.com.ua/katalog-tovara/avtolampy/p_{i}.html', cookies=cookies,
                                headers=headers)
        print(response.status_code)
        src = response.text
        soup = BeautifulSoup(src, 'lxml')
        filename = f"c:\\DATA\\avtoradosti\\pages\\data_0{i}.html"
        with open(filename, "w", encoding='utf-8') as file:
            file.write(src)
        time.sleep(1)


def parsing_url():
    folder = r'c:\DATA\avtoradosti\pages\ru\*.html'
    files_html = glob.glob(folder)
    url_all = []
    with open('url_ru.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            urls = soup.find_all('div', attrs={'class': 'p-imod'})
            for u in urls:
                url_product = u.find('a').get('href')
                url_all.append(url_product)
        for url in url_all:
            writer.writerow([url])


def get_selenium():
    name_files = r'C:\scrap_tutorial-master\avtoradosti\url_ru.csv'
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        con = 0
        driver = get_chromedriver()
        driver.maximize_window()
        for row in urls:
            con +=1
            filename = fr"c:\DATA\avtoradosti\pages\ru\data_0{con}.html"
            if os.path.exists(filename):
                continue
            url = row[0]

            driver.get(url)
            wait = WebDriverWait(driver, 60)
            time.sleep(1)
            url_ru = driver.find_element(By.XPATH, '//div[@class="ht-lang"]//a').click()
            # print()
            # driver.get(url_ru)
            time.sleep(1)
            with open(filename, "w", encoding='utf-8') as fl:
                fl.write(driver.page_source)
            # wait_email = wait.until(
            #     EC.presence_of_element_located((By.XPATH, '//input[@name="user[email]"]')))

def parsin_product():
    folder = r'c:\DATA\avtoradosti\pages\ua\*.html'
    files_html = glob.glob(folder)
    with open('data_ua.csv', 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for item in files_html:
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]
            proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            try:
                title = soup.find('h1').find('span', attrs={'itemprop': 'name'}).text
            except:
                title = None
            try:
                sku = soup.find('span', attrs={'itemprop': 'sku'}).text.replace('/', '_').strip()
            except:
                sku = None

            table_char = soup.find('table', attrs={'class': 'cc-tech'})
            try:
                rows = table_char.select("table.cc-tech tr:not(:first-child)")  # исключаем первую строку с заголовком
            except:
                rows = None
            desired_order = ["Бренд", "Тип ламп", "Цоколь", "Тип цоколя ЕСЕ", "Напряжение", "Цветовая температура",
                             "Световой поток, lm", "Серия", "Срок службы, часов", "Количество"]
            desired_order = ["Бренд", "Тип", "Цоколь", "Тип цоколя ЕСЕ", "Напруга", "Колірна температура",
                             "Світловий потік, lm", "Серія", "Термін служби, годин", "Кількість"]


            characteristics_dict = {}
            for row in rows:
                key_element = row.select_one("td.cc-pn")
                value_element = row.select_one("td:nth-child(2)")

                key = key_element.text if key_element else None
                value = value_element.text if value_element else None

                if key and value:
                    characteristics_dict[key] = value

            # Создаем список характеристик на основе желаемого порядка
            ordered_characteristics = []
            for key in desired_order:
                ordered_characteristics.append(key)
                ordered_characteristics.append(characteristics_dict.get(key, ''))

            brand_row = table_char.find('td', string='Бренд')
            brand_value = None
            if brand_row:
                brand_value = brand_row.find_next_sibling('td').text.replace('/', '_').strip()
            else:
                print("Бренд не найден")
            filenames = []
            img_dir = "c:\\DATA\\avtoradosti"
            try:
                all_img = soup.find('div', attrs={'class': 'slider-thumbs'}).find_all('a')
            except:
                all_img = None
                continue
            coun = 0
            unique_urls = set()

            for i in all_img:
                url_img = i.find('img').get('data-btnpic')
                unique_urls.add(url_img)

            downloaded_files_count = 0

            for url_img in unique_urls:
                coun += 1
                filename = f"{brand_value}_{sku}_{coun}.jpg"
                file_path = os.path.join(img_dir, filename)
                filenames.append(filename)

                if os.path.exists(file_path):
                    downloaded_files_count += 1
                    continue

                try:
                    img_data = requests.get(url_img)
                    with open(file_path, 'wb') as file_img:
                        file_img.write(img_data.content)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error when downloading {url_img}. Error: {e}")
                    exit()

            # if downloaded_files_count == len(unique_urls):
            #     print("All images are already downloaded.")
            writer.writerow([sku, title, filenames] + ordered_characteristics)

def write_metadata_in_jpg():
    """Запись метаданных в изображение"""
    import piexif
    image_path = "C:\\scrap_tutorial-master\\Temp\\036_BOSCH_02.jpg"
    output_image_path = "C:\\scrap_tutorial-master\\Temp\\036_BOSCH_02_new.jpg"

    # Загрузить EXIF данные из изображения
    exif_dict = piexif.load(image_path)

    # Добавить или изменить метаданные
    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = "intercars"
    exif_dict['Exif'][piexif.ExifIFD.UserComment] = b"ASCII\0\0\0intercars"

    # Конвертировать словарь обратно в байты
    exif_bytes = piexif.dump(exif_dict)

    # Записать обратно в изображение
    piexif.insert(exif_bytes, image_path, output_image_path)

if __name__ == '__main__':
    # get_requests()
    # parsing_url()
    # get_selenium()
    parsin_product()
