from pathlib import Path
from bs4 import BeautifulSoup
import random
import glob
import natsort
import pandas as pd
import re
import requests
import json
import cloudscraper
import os
from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import time
import shutil
import tempfile
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

file_path = "all_proxy.txt"


def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)


def get_chromedriver():
    options = webdriver.ChromeOptions()

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-gpu")
    # options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # options.add_argument('--disable-infobars')
    options.add_argument("--start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # options.add_argument('--disable-extensions') # Отключает использование расширений
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-setuid-sandbox')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
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

def all_page():
    driver = get_chromedriver()
    driver.maximize_window()
    driver.get('https://www.rootdata.com/Projects')
    time.sleep(2)
    el_pagination_total = driver.find_element(By.XPATH, '//span[@class="el-pagination__total"]').text.replace('Total ',
                                                                                                              '')
    el_pagination_total = int(el_pagination_total)
    return el_pagination_total


def get_page():
    # Указываем путь до папки, которую хотим создать
    folder_path_company = "c:/DATA/rootdata/company/"
    folder_path_page = "c:/DATA/rootdata/page/"

    # Создаем директорию, если она еще не существует
    os.makedirs(folder_path_company, exist_ok=True)
    os.makedirs(folder_path_page, exist_ok=True)

    driver = get_chromedriver()
    driver.maximize_window()
    driver.get('https://www.rootdata.com/Projects')
    time.sleep(2)
    el_pagination_total = driver.find_element(By.XPATH, '//span[@class="el-pagination__total"]').text.replace('Total ',
                                                                                                              '')
    el_pagination_total = int(el_pagination_total)
    el_pagination_total = el_pagination_total // 30
    for p in range(1, el_pagination_total + 2):
        file_name = f"c:\\DATA\\rootdata\\page\\rootdata_{p}.html"
        with open(file_name, "w", encoding='utf-8') as fl:
            fl.write(driver.page_source)
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        next_button = driver.find_element(By.XPATH, '//button[@class="btn-next"]').click()
        time.sleep(5)


def get_url_company():
    folder = r'c:\DATA\rootdata\page\*.html'
    files_html = glob.glob(folder)
    with open('url_company.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            table_row = soup.find('tbody', attrs={'role': 'rowgroup'})
            rows = table_row.find_all('tr', attrs={'role': 'row'})
            for r in rows:
                url = 'https://www.rootdata.com' + r.find('a', attrs={'class': 'list_name animation_underline'}).get(
                    'href')
                writer.writerow([url])


def get_page_company():
    cookies = {
        'auth.strategy': 'local1',
        'i18n_redirected': 'en',
        '_ga_TXPS04VGH2': 'GS1.1.1690034358.1.0.1690034358.0.0.0',
        '_ga': 'GA1.1.1249396543.1690034359',
    }

    headers = {
        'authority': 'www.rootdata.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'auth.strategy=local1; i18n_redirected=en; _ga_TXPS04VGH2=GS1.1.1690034358.1.0.1690034358.0.0.0; _ga=GA1.1.1249396543.1690034359',
        'dnt': '1',
        'pragma': 'no-cache',
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
    name_files = Path(f'C:/scrap_tutorial-master/rootdata/') / 'url_company.csv'
    coun = 0
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in urls:
            coun += 1
            name_files = Path('c:/DATA/rootdata/company/') / f'data_{coun}.html'
            if not os.path.exists(name_files):
                proxies = load_proxies(file_path)
                proxy = get_random_proxy(proxies)
                login_password, ip_port = proxy.split('@')
                login, password = login_password.split(':')
                ip, port = ip_port.split(':')
                proxy_dict = {
                    "http": f"http://{login}:{password}@{ip}:{port}",
                    "https": f"https://{login}:{password}@{ip}:{port}"
                }
                try:
                    response = requests.get(row[0], headers=headers, cookies=cookies)  # , proxies=proxy_dict
                except:
                    continue
                src = response.text
                with open(name_files, "w", encoding='utf-8') as file:
                    file.write(src)

                pause_time = random.randint(1, 3)
                time.sleep(pause_time)

                print(f'{len(urls) - coun}')


def get_data():
    folder = r'c:\DATA\rootdata\company\*.html'
    files_html = glob.glob(folder)
    files_html = natsort.natsorted(files_html)
    coun = 0
    # pages = all_page()
    pages = 8495
    total_files = pages  # Замените эту строку на количество файлов в вашем списке

    with open('datas.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        for item in files_html:
            data = [total_files, '', '', '', '']  # Создаем список с пятью пустыми значениями
            total_files -= 1  # Уменьшаем счетчик
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            try:
                name_company = soup.find('div', attrs={'class': 'd-flex flex-row align-center mb-1'}).text
                data[1] = name_company
            except:
                # print(item)
                continue

            table_urls = soup.find('div', attrs={'class': 'links d-flex flex-row flex-wrap mt-6'}).find_all('a')
            for index, i in enumerate(table_urls):
                urls = i.get('href')
                if index == 0:  # Первое значение добавляется всегда
                    if 'https://twitter.com' in urls:
                        data[3] = urls  # Записываем ссылку в столбец 4
                    else:
                        data[2] = urls
                else:
                    if 'https://twitter.com' in urls:
                        data[3] = urls  # Записываем ссылку в столбец 4
                    elif 'https://www.linkedin.com' in urls:
                        data[4] = urls  # Записываем ссылку в столбец 5


            writer.writerow(data)



if __name__ == '__main__':
    # get_page()
    # get_url_company()
    # get_page_company()
    get_data()
