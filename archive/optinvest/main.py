import zipfile
import pickle

import requests
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
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = undetected_chromedriver.Chrome()
    # s = Service(
    #     executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    # )
    # driver = webdriver.Chrome(
    #     service=s,
    #     options=chrome_options
    # )

    return driver


def save_link_all_product(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }
    url_categors = []
    resp = requests.get(url, headers=header)
    soup = BeautifulSoup(resp.text, 'lxml')
    table_category = soup.find('ul', attrs={'class': 'cs-product-groups-gallery__list'}).find_all('li', attrs={
        'class': 'cs-product-groups-gallery__item cs-product-groups-gallery__item_page_main cs-online-edit'})

    for href_category in table_category:
        url_categor = 'https://optinvest.com.ua/' + href_category.find('div').find('a').get("href")
        url_categors.append(
            {
                'url_name': url_categor
            }
        )
    url_products = []
    for href_product in url_categors[0:1]:
        resp = requests.get(href_product['url_name'], headers=header)
        soup = BeautifulSoup(resp.text, 'lxml')
        table_product = soup.find('ul', attrs={'class': 'cs-product-gallery__list'}).find_all('li', attrs={
            'cs-online-edit cs-product-gallery__item js-productad'})
        for i in table_product:
            url_product = 'https://optinvest.com.ua/' + i.find('div',
                                                               attrs={'class': 'cs-product-gallery__order-bar'}).find(
                'a').get('href')
            url_product = 'https://optinvest.com.ua/' + i.find('div',
                                                               attrs={'class': 'cs-product-gallery__order-bar'}).find(
                'a').get('href')
            url_products.append(
                {
                    'url_name': url_product
                }
            )
    produkt_list = []
    for j in url_products[0:1]:
        resp = requests.get(j['url_name'], headers=header)
        soup = BeautifulSoup(resp.text, 'lxml')

        product_avaibel = soup.find('ul', attrs={'class': 'b-product-data'}).find('li').text
        product_sku = soup.find('li', attrs={'class': 'b-product-data__item b-product-data__item_type_sku'}).text
        product_name = soup.find('h1', attrs={'class': 'cs-product__name cs-online-edit'}).find('span').text
        product_price = soup.find('p', attrs={'class': 'b-product-cost__price'}).find('span').text
        table_product_info = soup.find('table', attrs={'class': 'b-product-info'}).find_all('tr')
        for o in table_product_info[1:]:
            print(o.text)
        print("*" * 50)


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


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    url = "https://optinvest.com.ua/ua/"
    save_link_all_product(url)
    # Парсим все товары из файлов с
    # parsing_product()
