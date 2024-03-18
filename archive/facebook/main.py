import random
import glob
import zipfile
import json
import pickle
import time
import csv
import re
import requests
import datetime
import pandas as pd
from selenium.webdriver import ActionChains
import undetected_chromedriver
from fake_useragent import UserAgent
from selenium import webdriver
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
# Нажатие клавиш
from selenium.webdriver.common.by import By

# Библиотеки для Асинхронного парсинга
# Библиотеки для Асинхронного парсинга

useragent = UserAgent()
# options = webdriver.ChromeOptions()
# # Отключение режима WebDriver
# options.add_experimental_option('useAutomationExtension', False)
# # # Работа в фоновом режиме
# # options.headless = True
# options.add_argument(
#     # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
#     f"user-agent={useragent.random}"
# )
# driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
# driver = webdriver.Chrome(
#     service=driver_service,
#     options=options
# )
#
# # # Окно браузера на весь экран
# driver.maximize_window()

# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"


# Данные для прокси
PROXY_HOST = '141.145.205.4'
PROXY_PORT = 31281
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'

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


#
def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

    if user_agent:
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )
    # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #     'source': '''
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    #                 delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    #           '''
    # })

    return driver


# def get_undetected_chromedriver(use_proxy=False, user_agent=None):
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument(
#         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
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


def get_url_category(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}

    urls_card = []
    driver = get_chromedriver(use_proxy=True,
                              user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    driver.get(url)
    time.sleep(5)
    # # Блок работы с куками-----------------------------------------
    # # Создание куки
    # time.sleep(30)
    # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
    # # Читание куки
    for cookie in pickle.load(open("cookies", "rb")):
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(5)
    # with open("data.html", "w", encoding='utf-8') as file:
    #     file.write(driver.page_source)
    for i in range(34):
        url_img = driver.find_element(By.XPATH,
                                       '//img[@data-visualcompletion="media-vc-image"]').get_attribute("src")
        img_data = requests.get(url_img)
        with open(f"0{i}.jpg", 'wb') as file_img:
            file_img.write(img_data.content)
        driver.find_element(By.XPATH, '//div[@aria-label="Следующее фото"]').click()
        time.sleep(2)



def parse_content():
    url = "https://www.facebook.com/photo/?fbid=244845037973621&set=pcb.1427247788035088"
    get_url_category(url)


if __name__ == '__main__':
    parse_content()
