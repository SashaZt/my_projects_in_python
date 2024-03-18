import zipfile
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import requests
import csv
import undetected_chromedriver as UC
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

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = 'IP'
PROXY_PORT = 'PORT' #Без кавычек
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
def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = UC.Chrome(service=s, options=chrome_options)
    # driver.delete_all_cookies()

    return driver

# def get_chromedriver(use_proxy=False, user_agent=None):
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


def save_link_all_product():
    with open(f'C:\\scrap_tutorial-master\\archive\\dok.ua\\url_no_ads.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        coun = 0
        driver = get_undetected_chromedriver(use_proxy=False,
                                             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
        for f in csv_reader:
            coun += 1
            driver.get(f[0])
            driver.maximize_window()
            time.sleep(2)
            with open(f'./data/data_0{coun}.html', 'w', encoding='utf-8') as file:
                file.write(driver.page_source)
            print(coun)

def parsing_img():
    folders = [r"c:\111111111111\*.html",
               r"c:\nbsklep_pl\html_product\damskie\*.html",
               r"c:\nbsklep_pl\html_product\dzieciece\*.html"]

    for folder in folders[:1]:
        files_html = glob.glob(folder)
        coun = 0
        for item in files_html:

                with open(item, encoding="utf-8") as file:
                    src = file.read()
                coun += 1
                soup = BeautifulSoup(src, 'lxml')
                divs = soup.find_all('div', {'class': 'slick-list draggable'})
                try:
                    name_product = soup.find('div', {'class': 'card-title-box'}).find('h1').text
                except:
                    name_product = ""
                try:
                    url_product = soup.find('link', {'hreflang': 'ru'}).get('href')
                except:
                    url_product = ""

                # Проходим по всем найденным div-элементам
                for div in divs:
                    # Находим все теги img внутри текущего div-элемента
                    imgs = div.find_all('img')
                    # Проходим по всем найденным тегам img
                    for img in imgs:
                        # Извлекаем URL из атрибута src, проверяем расширение и выводим на экран
                        if img['src'].endswith('.jpg'):
                            with open(f"C:\\scrap_tutorial-master\\archive\\dok.ua\\no_ads.csv", "a",
                                      errors='ignore', encoding="utf-8") as file:
                                writer = csv.writer(file, delimiter=",", lineterminator="\r")
                                writer.writerow((url_product, name_product, img['src']))
                            # print(f"{name_product} | {img['src']}")


                print(coun)



if __name__ == '__main__':
    # save_link_all_product()
    parsing_img()
