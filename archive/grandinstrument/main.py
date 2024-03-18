import glob
import re
import pandas as pd
from random import randint
import time
import psutil
import requests
import undetected_chromedriver
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait

import csv

# Нажатие клавиш

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = 'IP'
PROXY_PORT = 'PORT'  # Без кавычек
PROXY_USER = 'LOGIN'
PROXY_PASS = 'PASS'

# Настройка для requests чтобы использовать прокси
proxies = {'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}/'}

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
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"76.0.0"
}
"""

background_js = """
let config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
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
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver
# def get_undetected_chromedriver(use_proxy=False, user_agent=None):
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument(
#         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
#     chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#
#     driver = undetected_chromedriver.Chrome()
#     # s = Service(
#     #     executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
#     # )
#     # driver = webdriver.Chrome(
#     #     service=s,
#     #     options=chrome_options
#     # )
#
#     return driver


def save_link_all_product():
    with open('url.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        count_url = 0
        bad_product = []
        counter = 0
        for row in csv_reader[:5]:
            url_ua = row[0]
            counter += 1
            art = url_ua.split("/")[-2]
            print(art)
            driver = get_chromedriver()
            driver.get(url_ua.rstrip(';'))
            driver.maximize_window()
            wait = WebDriverWait(driver, 2)
            # time.sleep(1)
            try:
                product_info_ul_wait = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//ul[@class="product-info-ul"]')))
                if driver.find_element(By.XPATH, '//ul[@class="product-info-ul"]'):
                    element1_wait = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                    # time.sleep(1)
                    # ожидаем появления элементов на странице
                    try:
                        element1 = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                        driver.execute_script("arguments[0].click();", element1)
                    except:
                        print("Нет Характеристик наборов")

                    try:
                        element2 = wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//div[@class='sets-show btn btn-showmore my-4 pe-4']")))
                        driver.execute_script("arguments[0].click();", element2) #Принудительное нажатие кнопки мышки
                    except:
                        print("Нет Комплектаций наборов")

                    try:
                        element3 = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-controls='productInfoCollapseDesc']")))
                        driver.execute_script("arguments[0].click();", element3)
                    except:
                        print("Нет Описания товаров")

                    # сохраняем страницу в файл
                    with open(f"data/ua_{art}.html", "w", encoding='utf-8') as file:
                        file.write(driver.page_source)
                if url_ua not in "https://grandinstrument.ua/ua/":
                    url_rus = url_ua.replace("https://grandinstrument.ua/ua/", "https://grandinstrument.ua/").rstrip(';')
                    driver.get(url_rus)
                    wait = WebDriverWait(driver, 2)
                    # time.sleep(1)
                    product_info_ul_wait = wait.until(
                        EC.presence_of_element_located((By.XPATH, '//ul[@class="product-info-ul"]')))
                    if driver.find_element(By.XPATH, '//ul[@class="product-info-ul"]'):
                        element1_wait = wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                        # time.sleep(1)
                        # ожидаем появления элементов на странице
                        try:
                            element1 = wait.until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                            driver.execute_script("arguments[0].click();", element1)
                        except:
                            print("Нет Характеристик наборов")

                        try:
                            element2 = wait.until(EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='sets-show btn btn-showmore my-4 pe-4']")))
                            driver.execute_script("arguments[0].click();", element2)  # Принудительное нажатие кнопки мышки
                        except:
                            print("Нет Комплектаций наборов")

                        try:
                            element3 = wait.until(EC.presence_of_element_located(
                                (By.XPATH, "//div[@aria-controls='productInfoCollapseDesc']")))
                            driver.execute_script("arguments[0].click();", element3)
                        except:
                            print("Нет Описания товаров")

                        # сохраняем страницу в файл
                        with open(f"data/ru_{art}.html", "w", encoding='utf-8') as file:
                            file.write(driver.page_source)
            except:
                driver.close()
                driver.quit()

            driver.close()
            driver.quit()

def parsing_product():
    targetPattern = r"data/*.html"
    files_html = glob.glob(targetPattern)
    # data = []
    for item in files_html[:1]:
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        script = soup.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))

        data = script.text
        item = re.search(
            r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
            data, re.DOTALL)
        item_name = item.group(1)
        item_id = item.group(2)
        price = item.group(3)
        item_brand = item.group(4)
        item_category = item.group(5)
        description = soup.find('div', attrs={
            'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip()

        result = [item_name, item_id, price, item_brand, item_category, description]
        for div in soup.find_all('div', {'class': 'row mx-0'}):
            name = div.find('div', {'class': 'property-name'})
            value = div.find('div', {'class': 'property-value'})
            if name and value:  # проверяем, что элементы существуют
                result.append(name.text.strip())
                result.append(value.text.strip())

        with open(f"test.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(result)

if __name__ == '__main__':
    save_link_all_product()
    # parsing_product()
