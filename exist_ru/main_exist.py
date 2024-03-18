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

lock = Lock()
proxy = random.choice(proxies)


class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)


# def get_chromedriver():
# def get_chromedriver():
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
    # proxy_extension = ProxyExtension(*proxy)
    # chrome_options.add_argument(f"--load-extension={proxy_extension.directory}")
    s = Service(executable_path="./chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver
def extract_data_from_csv():
    csv_filename = 'exist_data.csv'
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


def process_data(part_data):
    # создаем экземпляр драйвера для каждого процесса
    driver = get_chromedriver()
    site = 'E'
    now = datetime.now().date()
    heandler = ['brand', 'part_number', 'description', 'quantity', 'price_new', 'price_old', 'now','site']
    with lock:  # межпроцессная блокировка
        with open('output_exist.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=";")

            quantity = 50
            for item in part_data[:5]:  # используем part_data
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
                    # values = [brend, sku, '-', quantity, '-', price_old, now]
                    # writer.writerow(values)
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

                    time.sleep(1)
                    scripts = driver.find_elements(By.TAG_NAME, 'script')

                    for script in scripts:
                        script_content = script.get_attribute("outerHTML")  # Изменение на outerHTML
                        if "//<![CDATA[" in script_content:
                            match = re.search(r'var _data = (.*); var _favs',
                                              script_content)  # Изменение регулярного выражения

                            if match:
                                json_str = match.group(1)
                                json_str = json_str.replace("\\u0027", "'").replace("\\u003e", ">").replace("\\u003c",
                                                                                                            "<")
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

                                values = [brand, part_number, description, quantity, price_new, price_old, now,site]
                                # print(values)
                                writer.writerow(values)  #


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


if __name__ == "__main__":
    main()