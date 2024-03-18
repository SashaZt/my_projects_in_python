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
options.headless = True
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
        group = url.split("/")[-2]
        with open(f"C:\\scrap_tutorial-master\\moderngroup\\{group}.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    'Название',
                    'Каталожный номер',
                    'Название группы',
                    'Цена',
                    'Ссылка на изображение'
                )
            )
        driver.get(url=url)
        product_url = []

        # Блок работы с куками-----------------------------------------
        # Создание куки
        # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        # Читание куки
        # for cookie in pickle.load(open("cookies", "rb")):
        #     driver.add_cookie(cookie)
        # Блок работы с куками-----------------------------------------

        # Листать по страницам ---------------------------------------------------------------------------
        page_product = 0
        isNextDisable = False
        while not isNextDisable:
            try:
                # Сначала что то ищем на первой странице, а только потом ищем на остальных
                card_product_url = driver.find_elements(By.XPATH, '//h4[@class="card-title"]/a')
                for item in card_product_url[0:21]:
                    product_url.append(
                        {'url_name': item.get_attribute("href")} # Добавляем в словарь два параметра для дальнейшего записи в json
                    )

                # Если необходимо подождать елемент тогда WebDriverWait
                # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
                driver.implicitly_wait(5)
                next_button = driver.find_elements(By.XPATH, '//li[@class="pagination-item pagination-item--next"]')[1]
                # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                if next_button:
                    next_button.click()
                    page_product += 1
                    print(f"Обработано {page_product} страниц")
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------

        # Проверяем на существование файла, если нету тогда записываем в json
        if os.path.exists(f"{group}.json"):
            print(f"C:\\scrap_tutorial-master\\moderngroup\\{group}.json" + " уже существует")
        else:
            with open(f"C:\\scrap_tutorial-master\\moderngroup\\{group}.json", 'w') as file:
                json.dump(product_url, file, indent=4, ensure_ascii=False)

        # Читание json
        with open(f"C:\\scrap_tutorial-master\\moderngroup\\{group}.json") as file:
            all_site = json.load(file)
        # С json вытягиваем только 'url_name' - это и есть ссылка
        product_sum = 0
        for item in all_site:
            driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
            try:
                name_product = driver.find_element(By.XPATH, '//h1[@class="productView-title"]').text
            except:
                name_product = 'Нет названия'
            try:
                sku_product = driver.find_element(By.XPATH, '//dd[@data-product-sku=""]').text
            except:
                sku_product = "Нет SKU"
            try:
                group_products = driver.find_elements(By.XPATH, '//a[@class="breadcrumb-label"]')[2]
                group_product = group_products.text
            except:
                group_products = "Нет группы"
                group_product = group_products
            try:
                price_products = driver.find_elements(By.XPATH, '//span[@class="price price--withoutTax"]')[0]
                price_product = price_products.text
            except:
                price_products = 'Нет цены'
                price_product = price_products
            try:
                img_product = driver.find_element(By.XPATH, '//figure[@data-fancybox="gallery"]').get_attribute("href")
            except:
                img_product = 'Нет фото'
            try:
                desc_01 = driver.find_element(By.XPATH, '//div[@id="tab-description"]//p[3]').text
                desc_02 = driver.find_element(By.XPATH, '//div[@id="tab-description"]//p[4]').text
            except:
                desc_01 = 'Нету описания'
                desc_02 = 'Нету описания'
            with open(f"C:\\scrap_tutorial-master\\moderngroup\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product,
                        sku_product,
                        group_product,
                        price_product,
                        img_product,
                        desc_01,
                        desc_02
                    )
                )
            product_sum += 1
            print(f"Обработано {product_sum} найменования")
        diff_time = datetime.datetime.now() - start_time

    except Exception as ex:
        print(ex)

    finally:
        print("Обработка завершена, закрываем Браузер")
        print(diff_time)
        driver.close()
        driver.quit()


def parse_content():
    url = "https://shop.moderngroup.com/fleetguard/"
    get_content(url)


if __name__ == '__main__':
    parse_content()
