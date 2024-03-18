import zipfile
import pickle
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
from selenium.webdriver.common.keys import Keys
import csv
import time
import glob

# Нажатие клавиш

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver

from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver

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


# def get_chromedriver(use_proxy=True, user_agent=None):
#     chrome_options = webdriver.ChromeOptions()
#
#     if use_proxy:
#         plugin_file = 'proxy_auth_plugin.zip'
#
#         with zipfile.ZipFile(plugin_file, 'w') as zp:
#             zp.writestr('manifest.json', manifest_json)
#             zp.writestr('background.js', background_js)
#
#         chrome_options.add_extension(plugin_file)
#
#     if user_agent:
#         chrome_options.add_argument(f'--user-agent={user_agent}')
#
#     s = Service(
#         executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
#     )
#     driver = webdriver.Chrome(
#         service=s,
#         options=chrome_options
#     )
#
#     return driver
def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    driver = undetected_chromedriver.Chrome()
    # s = Service(
    #     executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    # )
    # driver = webdriver.Chrome(
    #     service=s,
    #     options=chrome_options
    # )

    return driver


def save_link_all_product():
    # driver = get_undetected_chromedriver(use_proxy=True, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    urls = [

    ]

    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        count_url = 0
        for row in csv_reader[176561:180000]:
            urls.append(row[0])
    driver = get_undetected_chromedriver()
    counter = 176561
    for i in urls:
        counter += 1
        driver.get(i)
        try:
            next_button = WebDriverWait(driver, 200).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@id="global-search"]')))
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            time.sleep(1)
            with open(f"C:\\scrap_tutorial-master\\webstaurantstore\\data\\{counter}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
        except:
            continue


def parsing_product():
    targetPattern = r"c:\scrap_tutorial-master\dubai\data\*.html"
    files_html = glob.glob(targetPattern)
    data = []
    for item in files_html[26:27]:
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        print(item)
        soup = BeautifulSoup(src, 'lxml')
        card_all = soup.find_all('div', attrs={'class': 'sc-cmkc2d-0 dhbOk'})
        for cards in card_all:
            try:
                img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('img').get('src')
            except:
                img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('span').find('img').get('src')
            # На странице 33 и 34 установить два условия
            # img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('img').get('src')
        print(img_card)

    #
    #         km_avto = cards.find('div', attrs={'data-testid': 'listing-kms'}).text
    #         try:
    #             color_avto = cards.find('div', attrs={'data-testid': 'listing-color'}).text
    #         except:
    #             color_avto = "Not color"
    #         try:
    #             price_avto = cards.find('div', attrs={'class': 'sc-11jo8dj-1 cpHdIU'}).text
    #         except:
    #             price_avto = "Not color"
    #         data.append({
    #             'Пробег' : km_avto,
    #             'Цвет' : color_avto,
    #             'Цена': price_avto,
    #             'Фото': img_card
    #         })
    # with open('data.json', 'w', encoding="utf-8") as file:
    #     json.dump(data, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    # url = "https://dubai.dubizzle.com/motors/used-cars/toyota/?kilometers__lte=100000&ads_posted=1673567999"
    save_link_all_product()
    # Парсим все товары из файлов с
    # parsing_product()
