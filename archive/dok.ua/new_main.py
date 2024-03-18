import re
import os
from bs4 import BeautifulSoup
import random
import glob
import re
from pathlib import Path
import requests
import json
import cloudscraper
import os
from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import time
import shutil
import tempfile
# import undetected_chromedriver as webdriver


from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


def get_chromedriver():
    options = webdriver.ChromeOptions()

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    service = ChromeService(executable_path='C:\\scrap_tutorial-master\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver


def get_creation_folders():
    name_files = Path('C:/scrap_tutorial-master/archive/dok.ua') / 'url.csv'
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in urls:
            url = row[0]
            # Создание папки, если её нет
            folder_path_list = f"c:/DATA/dok_ua/list/{url.split('/')[-1].replace('-', '_')}/"
            folder_path_products = f"c:/DATA/dok_ua/products/{url.split('/')[-1].replace('-', '_')}/"
            folder_path_products_ua = f"c:/DATA/dok_ua/products/{url.split('/')[-1].replace('-', '_')}/ua/"
            folder_path_products_rus = f"c:/DATA/dok_ua/products/{url.split('/')[-1].replace('-', '_')}/rus/"

            os.makedirs(folder_path_list, exist_ok=True)
            os.makedirs(folder_path_products, exist_ok=True)
            os.makedirs(folder_path_products_ua, exist_ok=True)
            os.makedirs(folder_path_products_rus, exist_ok=True)




def get_selenium_list():
    driver = get_chromedriver()
    name_files = Path('C:/scrap_tutorial-master/archive/dok.ua') / 'url.csv'
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in urls:
            url = row[0]
            folder_path_list = f"c:/DATA/dok_ua/list/{url.split('/')[-1].replace('-', '_')}/"
            driver.get(url)
            time.sleep(1)
            last_page = None
            try:
                last_page = int(driver.find_element(By.XPATH, '//li[@class="last"]').text)
            except:
                div = driver.find_element(By.XPATH, '//div[@class="add-more-info"]').text
                match = re.search(r'з (\d+) товарів', div)
                if match:
                    last_page = int(match.group(1)) // 12
            count = 0
            for p in range(1, last_page + 2):
                count +=1
                new_url = f'{url}?page={p}'
                driver.get(new_url)
                time.sleep(1)
                file_name = f"{folder_path_list}data_0{count}.html"
                with open(file_name, "w", encoding='utf-8') as fl:
                    fl.write(driver.page_source)
    driver.close()
    driver.quit()


def get_url_ua():
    # Указываем путь до папки
    folder_path = "c:/DATA/dok_ua/list/"

    # Получаем список всех подпапок
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]

    # Проходимся по каждой подпапке
    for subfolder in subfolders:
        full_path = os.path.join(folder_path, subfolder)
        # Используем glob для выбора всех HTML-файлов в подпапке
        files_html = glob.glob(f"{full_path}/*.html")
        if not os.path.exists(f'c:\\scrap_tutorial-master\\archive\\dok.ua\\link\\{subfolder}.csv'):
            with open(f'c:\\scrap_tutorial-master\\archive\\dok.ua\\link\\{subfolder}.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=";")
                # Открываем каждый HTML-файл и читаем его содержимое
                for item in files_html:
                    with open(item, encoding="utf-8") as file:
                        src = file.read()
                    soup = BeautifulSoup(src, 'lxml')
                    # urls = soup.find_all('div', attrs={'class': 'product-card-packaging__item'})
                    urls = soup.find_all('a', attrs={'class': 'product-card__layout-name'})
                    for u in urls:
                        # url = u.get("data-link")
                        url = u.get("href")
                        url = f'https://dok.ua{url}'
                        writer.writerow([url])
            print(subfolder)

def get_url_rus():
    # Указываем путь до папки
    folder_path = "c:/scrap_tutorial-master/archive/dok.ua/link/"
    file_list = []

    # Пройдемся по всем файлам в директории
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):  # Проверяем, что это файл, а не папка
            file_list.append(filename)
            print(filename.replace('.csv', ''))

    # Перебираем все файлы в списке
    for filename in file_list:
        full_file_path = os.path.join(folder_path, filename)

        # Читаем содержимое файла
        with open(full_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Заменяем все вхождения "https://dok.ua/ua/" на "https://dok.ua/"
        lines = [line.replace('https://dok.ua/ua/', 'https://dok.ua/') for line in lines]

        # Составляем новое имя для файла
        new_filename = filename.split('.')[0] + '_rus.csv'
        new_file_path = os.path.join(folder_path, new_filename)

        # Записываем обратно в новый файл
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"Обработан файл {filename}, сохранён как {new_filename}")

if __name__ == '__main__':
    # get_creation_folders()
    # get_selenium_list()
    # get_url_ua()
    get_url_rus()
