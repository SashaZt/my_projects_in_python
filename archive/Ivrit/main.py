import datetime
import json
import csv
import os
import pickle
import lxml
import time
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from random import randint
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import csv
from selenium import webdriver
import random
from fake_useragent import UserAgent
# Библиотеки для Асинхронного парсинга
import asyncio
import aiohttp
# Библиотеки для Асинхронного парсинга

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

useragent = UserAgent()
options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)
# # Работа в фоновом режиме
# options.headless = True
options.add_argument(
    # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
    f"user-agent={useragent.random}"
)
driver_service = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
driver = webdriver.Chrome(
    service=driver_service,
    options=options
)


# # Окно браузера на весь экран
# driver.maximize_window()


# Для работы webdriver____________________________________________________


# Для работы undetected_chromedriver ---------------------------------------

# import undetected_chromedriver as uc
# driver = uc.Chrome()


# Для работы undetected_chromedriver ---------------------------------------


# "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"

def get_content(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"

    }
    start_time = datetime.datetime.now()
    try:
        #Название группы берем из ссылки, сделаем срез
        # group = url.split("/")[-2]
        # with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.csv", "w", errors='ignore') as file:
        #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
        #     writer.writerow(
        #         (
        #             'Название',
        #             'Каталожный номер',
        #             'Название группы',
        #             'Цена',
        #             'Ссылка на изображение'
        #         )
        #     )
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

        # Читание json
        with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.json") as file:
            all_site = json.load(file)
        # С json вытягиваем только 'url_name' - это и есть ссылка
        product_sum = 0
        for item in all_site:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Обезательно ждем
            driver.implicitly_wait(5)
            driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
            soup = BeautifulSoup(driver.page_source, 'lxml')
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
            data.append(
                {
                     'char_prod_all': char_prod_all

                }
            )
            #     char_prod_01 = 'No characteristics'
            #     char_prod_02 = 'No characteristics'
            #     char_prod_03 = 'No characteristics'
            #     char_prod_04 = 'No characteristics'
            #     char_prod_05 = 'No characteristics'
            #     char_prod_06 = 'No characteristics'
            #     char_prod_07 = 'No characteristics'
            #     char_prod_08 = 'No characteristics'
            #     char_prod_09 = 'No characteristics'
            #     char_prod_10 = 'No characteristics'
            #     char_prod_11 = 'No characteristics'
            #     char_prod_12 = 'No characteristics'
            #     char_prod_13 = 'No characteristics'
            #     char_prod_14 = 'No characteristics'
            #     char_prod_15 = 'No characteristics'
            #
            # data = [name_product,
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
            #         ]

            # with open(f"C:\\scrap_tutorial-master\\Ivrit\\01.csv", "a", encoding = "cp862", errors='ignore') as file:
            #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
            #     writer.writerow(
            #         (
            #             data
            #         )
            #     )
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

    except Exception as ex:
        print(ex)

    finally:
        print("Обработка завершена, закрываем Браузер")
        # print(diff_time)
        driver.close()
        driver.quit()


def parse_content():
    url = "https://www.cms.co.il/catalog/search.aspx?groupid=1"
    get_content(url)


if __name__ == '__main__':
    parse_content()
