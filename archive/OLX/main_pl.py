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

import undetected_chromedriver as UC

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




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
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = UC.Chrome(service=s, options=chrome_options)
    driver.delete_all_cookies()


    return driver


def save_link_all_product(url):
    products_all_url = []
    driver = get_undetected_chromedriver()
    driver.get(url)
    try:
        button_coc = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]').click()
    except:
        print("нет кнопки")
    isNextDisable = False
    while not isNextDisable:
        try:
            card_product_url = driver.find_elements(By.XPATH, '//div[@data-cy="l-card"]//a')
            for hrefs in card_product_url:
                products_all_url.append(
                    hrefs.get_attribute("href")
                )
            driver.execute_script("window.scrollBy(0,2500)", "")
            # обезательно дождаться появление элемента, например кнопки следующая страница
            button_find = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@data-testid="pagination-forward"]')))
            next_button = driver.find_element(By.XPATH, '//a[@data-testid="pagination-forward"]')
            # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
            if next_button:
                next_button.click()
                time.sleep(1)
            else:
                print('Нет кнопки дальше')
                isNextDisable = True
        except:
            isNextDisable = True
    # Листать по страницам ---------------------------------------------------------------------------
    # Запись csv файла  по строчно
    with open('file.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
        writer.writerow(products_all_url)


def parsing_product():

    urls = []
    # Читаем CSV файл по строчко, обезательно проверять по строчно, бывают казусы!!!!
    with open('file.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in csv_reader:
            urls.append(row[0])
    for item in urls[0:3]:
        driver = get_undetected_chromedriver()


        driver.get(item)  # 'url_name' - это и есть ссылка
        driver.maximize_window()
        driver.execute_script("window.scrollBy(0,500)", "")
        time.sleep(1)
        try:
            button_wait_coc = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')))
            button_coc = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]').click()
            time.sleep(1)
        except:
            print("нет кнопки")
        time.sleep(1)
        try:
            button_wait_telef = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@class="css-1hrtz3t"]')))
            button_telef = driver.find_element(By.XPATH, '//button[@class="css-1hrtz3t"]').click()
            time.sleep(1)
        except:
            print("Нет кнопки телефон")
            continue
        time.sleep(1)
        try:
            telef = driver.find_element(By.XPATH, '//a[@data-testid="contact-phone"]').text
        except:
            continue
        driver.execute_script("window.scrollBy(0,500)", "")
        time.sleep(1)
        try:
            button_wait_firma = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="trader-about"]//button[@class="css-4h6vq2"]')))
            button_firma = driver.find_element(By.XPATH, '//div[@data-testid="trader-about"]//button[@class="css-4h6vq2"]').click()
            time.sleep(1)
        except:
            print("нет кнопки Фирма")
            continue
        time.sleep(1)
        try:
            data_firm = driver.find_element(By.XPATH, '//div[@data-testid="trader-about"]').text.replace("\n", " ").strip()
        except:
            continue
        with open(f"C:\\scrap_tutorial-master\\archive\\OLX\\olx_pl.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    telef, data_firm

                )
            )
        driver.close()
        driver.quit()





if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    # url = "https://www.olx.pl/d/oferty/q-Pellet/"
    # save_link_all_product(url)
    # Парсим все товары из файлов с
    parsing_product()
