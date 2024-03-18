import pickle
import zipfile
import os
import json
import csv
import time
import requests
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver
import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()

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


def save_link_all_product(url):
    if os.path.exists(f"1.json"):
        print(f"C:\\scrap_tutorial-master\\Ivrit\\01.json" + " уже существует")
    else:
        driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
        driver.get(url=url)
        product_url = []
        data = []
        char_prod_all = {}

        # Блок работы с куками-----------------------------------------
        # Создание куки
        # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        # Читание куки
        # for cookie in pickle.load(open("cookies", "rb")):
        #     driver.add_cookie(cookie)
        # Блок работы с куками-----------------------------------------
        page_product = 0
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Обезательно ждем
        driver.implicitly_wait(5)

        card_product_url = driver.find_elements(By.XPATH, '//ul[@class="catalog_insert w-list-unstyled"]//a')
        for item in card_product_url:
            product_url.append(
                {'url_name': item.get_attribute("href")}
                # Добавляем в словарь два параметра для дальнейшего записи в json
            )

        with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.json", 'w') as file:
            json.dump(product_url, file, indent=4, ensure_ascii=False)

        driver.close()
        driver.quit()

def parsing_product():
    with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.json") as file:
        all_site = json.load(file)
    product_url = []
    data = []
    char_prod_all = {}
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    for item in all_site:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Обезательно ждем
        driver.implicitly_wait(5)
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            name_product = driver.find_element(By.XPATH, '//div[@class="list_title_group"]/h1').text
        except:
            name_product = 'Not title'
        try:
            sku_product = driver.find_element(By.XPATH, '//div[@class="item_code product"]').text
        except:
            sku_product = "Not SKU"

        try:

            char_prod = driver.find_elements(By.XPATH, '//div[@class="product_specific_group"]//div/div/div')
            char_prod_01 = char_prod[0].text
            char_prod_02 = char_prod[1].text
            char_prod_03 = char_prod[2].text
            char_prod_04 = char_prod[3].text
            char_prod_05 = char_prod[4].text
            char_prod_06 = char_prod[5].text
            char_prod_07 = char_prod[6].text
            char_prod_08 = char_prod[7].text
            char_prod_09 = char_prod[8].text
            char_prod_10 = char_prod[9].text
            char_prod_11 = char_prod[10].text
            char_prod_12 = char_prod[11].text
            char_prod_13 = char_prod[12].text
            char_prod_14 = char_prod[13].text
            char_prod_15 = char_prod[14].text

        except:
            pass
        # data.append(
        #     {
        #         'char_prod_all': char_prod_all
        #
        #     }
        # )
            char_prod_01 = 'No characteristics'
            char_prod_02 = 'No characteristics'
            char_prod_03 = 'No characteristics'
            char_prod_04 = 'No characteristics'
            char_prod_05 = 'No characteristics'
            char_prod_06 = 'No characteristics'
            char_prod_07 = 'No characteristics'
            char_prod_08 = 'No characteristics'
            char_prod_09 = 'No characteristics'
            char_prod_10 = 'No characteristics'
            char_prod_11 = 'No characteristics'
            char_prod_12 = 'No characteristics'
            char_prod_13 = 'No characteristics'
            char_prod_14 = 'No characteristics'
            char_prod_15 = 'No characteristics'

        data = [name_product,
                    sku_product,
                    char_prod_01,
                    char_prod_02,
                    char_prod_03,
                    char_prod_04,
                    char_prod_05,
                    char_prod_06,
                    char_prod_07,
                    char_prod_08,
                    char_prod_09,
                    char_prod_10,
                    char_prod_11,
                    char_prod_12,
                    char_prod_13,
                    char_prod_14,
                    char_prod_15
                ]

        with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.csv", "a", encoding = "cp1255", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    data
                )
            )
        # with open(f"C:\\scrap_tutorial-master\\Ivrit\\01_cp1255.csv", "a", encoding = "cp424", errors='ignore') as file:
        #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
        #     writer.writerow(
        #         (
        #             name_product,
        #             sku_product,
        #             char_prod_01,
        #             char_prod_02,
        #             char_prod_03,
        #             char_prod_04,
        #             char_prod_05,
        #             char_prod_06,
        #             char_prod_07,
        #             char_prod_08,
        #             char_prod_09,
        #             char_prod_10,
        #             char_prod_11,
        #             char_prod_12,
        #             char_prod_13,
        #             char_prod_14,
        #             char_prod_15
        #         )
        #     )
        # product_sum += 1
        # print(f"Обработано {product_sum} найменования")
        # diff_time = datetime.datetime.now() - start_time





if __name__ == '__main__':
    # #Сайт на который переходим
    # url = "https://www.cms.co.il/catalog/search.aspx?groupid=1"
    # # Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product(url)
    parsing_product()

