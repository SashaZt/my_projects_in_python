import glob
import zipfile
import json
import time
import csv
import re
import datetime
import pandas as pd

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


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def get_url_category(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}

    urls_card = []
    for u in range(8):
        driver = get_chromedriver(use_proxy=False,
                                  user_agent=f"{useragent.random}")
        if u == 1:
            driver.get(url)
            time.sleep(1)
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            # with open(f"C:\\scrap_tutorial-master\\flagma.ua\\data.html", "w", encoding='utf-8') as file:
            #     file.write(driver.page_source)
            url_card = driver.find_elements(By.XPATH,
                                            '//div[@id="message-list"]//div[contains(@class,"page-list-item ")]/a')

            for i in url_card:
                url_product = i.get_attribute("href")
                urls_card.append(
                    {
                        'url_name': url_product
                    }
                )

        if u > 1:
            driver = get_chromedriver(use_proxy=False,
                                      user_agent=f"{useragent.random}")
            driver.get(f"{url}page-{u}/")
            time.sleep(1)
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            url_card = driver.find_elements(By.XPATH,
                                            '//div[@id="message-list"]//div[contains(@class,"page-list-item ")]/a')

            for i in url_card:
                url_product = i.get_attribute("href")
                urls_card.append(
                    {
                        'url_name': url_product
                    }
                )

    with open("urls_card.json", 'w') as file:
        json.dump(urls_card, file, indent=4, ensure_ascii=False)
    print('Файл car_url.json с сылками записан')


def parsing_product():
    # Получаем список файлов с сылками на товары
    targetPattern = r"C:\scrap_tutorial-master\flagma.ua\*.json"
    files_json = glob.glob(targetPattern)
    with open(f"C:\\scrap_tutorial-master\\flagma.ua\\urls_card_01.json") as file:
        all_site = json.load(file)
    #
    # for item in files_json:
    #     files_csv = item.replace(".json", "").strip('\\')[-12:]
    #     with open(f"{item}") as file:
    #         all_site = json.load(file)
    for href_card in all_site[1516:]:
        driver = get_chromedriver(use_proxy=True,
                                  user_agent=f"{useragent.random}")
        driver.get(href_card['url_name'])

        start_time = datetime.datetime.now()
        driver.maximize_window()
        time.sleep(1)
        try:
            name_card = driver.find_element(By.XPATH, '//div[@class="photos-block has-photos"]//h1').text
        except:
            name_card = ""
        try:
            company_name = driver.find_elements(By.XPATH, '//div[@class="company-info"]//span[@itemprop="name"]')
        except:
            company_name = ""
        try:
            region_name = driver.find_elements(By.XPATH, '//div[@class="company-info"]//span[@class="terr"]')
        except:
            region_name = ""
        try:
            com_name = company_name[0].text
        except:
            com_name = ""
        try:
            region = region_name[0].text
        except:
            region = ""
        try:
            price_old = driver.find_element(By.XPATH,
                                            '//div[@itemprop="priceSpecification"]//div[@class="retail-price"]').text
        except:
            price_old = ""
        try:
            contact_name = driver.find_elements(By.XPATH,
                                                '//div[@class="contacts"]//div[@class="user-name"]//span[@itemprop="name"]')
        except:
            contact_name = ""
        try:
            contc_name = contact_name[0].text
        except:
            contc_name = ""
        try:
            dest_name = driver.find_element(By.XPATH, '//div[@itemprop="description"]//p').text.replace("\n", "")
        except:
            dest_name = ""
        try:
            buttons_phone = driver.find_elements(By.XPATH,
                                                 '//div[@class="send-button-container"]//a[@class="phone"]')
        except:
            buttons_phone = ""
        try:
            but_phone = buttons_phone[0].click()
        except:
            print('-')
        phone_name = driver.find_elements(By.XPATH, '//div[@class="reveal-content"]//div[@class="phones"]//a')
        try:
            phone_name_01 = phone_name[0].text
        except:
            phone_name_01 = ""
        try:
            phone_name_02 = phone_name[1].text
        except:
            phone_name_02 = ""

        # print(href_card['url_name'], name_card, com_name, region, price_old, dest_name, phone_name_01,
        #       phone_name_02)
        with open(f"C:\\scrap_tutorial-master\\flagma.ua\\urls_card_01_.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    href_card['url_name'], name_card, com_name, region, price_old, dest_name, phone_name_01,
                    phone_name_02

                )
            )


def parse_content():
    # url = "https://flagma.ua/products/derevyannye-pallety-poddony/q=%D0%BF%D0%B0%D0%BB%D0%BB%D0%B5%D1%82%D0%BD%D0%B0%D1%8F+%D0%B7%D0%B0%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BA%D0%B0/type:sell/"
    # get_url_category(url)
    # get_url_product()
    parsing_product()


if __name__ == '__main__':
    parse_content()
