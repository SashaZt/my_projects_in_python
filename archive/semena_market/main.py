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

# Работа в фоновом режиме
options.headless = True

options.add_argument(
    # "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
    f"user-agent={useragent.random}"
)
driver_service = Service(executable_path="/chromedriver.exe")
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

    try:
        start_time = datetime.datetime.now()
        driver.get(url=url)
        groups_url = []
        with open(f"/archive/semena_market/group.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    'Название',
                    'Описание товара',
                    'Артикул товара',
                    'Бренд товара',
                    'Характеристика товара',
                    "Ссылка на изображение",
                    "Наличие товара",
                    "Цена",
                    "Каталог товара"
                )
            )
        # Блок работы с куками-----------------------------------------
        # Создание куки
        # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        # Читание куки
        # for cookie in pickle.load(open("cookies", "rb")):
        #     driver.add_cookie(cookie)
        # Блок работы с куками-----------------------------------------

        group_link = 0
        try:
            # Сначала что то ищем на первой странице, а только потом ищем на остальных
            card_products = driver.find_element(By.XPATH, '//ul[@class="catalog-tree"]')
            card_product = card_products.find_elements(By.XPATH, '//li[@role="treeitem"]/a')
            list_product = 0
            for item in card_product[8:56]:
                groups_url.append(
                    {'url_name': item.get_attribute("href")} # Добавляем в словарь два параметра для дальнейшего записи в json
                )
                list_product += 1
                print('-' * 50)
                print(f"Обработано {list_product} страниц")
                print('-' * 50)
            # Проверяем на существование файла, если нету тогда записываем в json
            if os.path.exists("group.json"):
                print(f"C:\\scrap_tutorial-master\\semena_market\\group.json" + " уже существует")
            else:
                with open(f"/archive/semena_market/group.json", 'w') as file:
                    json.dump(groups_url, file, indent=4, ensure_ascii=False)

            # Читание json
            with open(f"/archive/semena_market/group.json") as file:
                all_site = json.load(file)
            # С json вытягиваем только 'url_name' - это и есть ссылка
            product_sum = 0
            url_products = []
            for item in all_site:
                driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
                next_button = driver.find_element(By.XPATH, '//div[@id="filter-limit"]').click()
                driver.implicitly_wait(5)
                # Нажимаем кнопку все позиции на странице
                all_product_list = driver.find_element(By.XPATH, '//a[@data-value="all"]').click()
                driver.implicitly_wait(5)
                table_product_in_list = driver.find_elements(By.XPATH, '//div[@class="goods goods-items s2 view-tiles clearfix"]//article//div[@class="name-wrap"]/a')
                for product in table_product_in_list:
                    url_products.append(product.get_attribute("href"))
                    product_sum += 1
                    print('-' * 50)
                    print(f"Обработано {product_sum} продуктов")
                    print('-' * 50)
            product_url = 0
            for href in url_products:
                driver.get(href)
                try:
                    name_product = driver.find_element(By.XPATH, '//h1[@itemprop="name"]').text
                except:
                    name_product = "Нет названия"
                try:
                    discrip_product = driver.find_element(By.XPATH, '//p[@style="text-align: justify;"]//span[@style="font-size: 14px;"]').text
                except:
                    discrip_product = "Нет описания"
                try:
                    art_product = driver.find_element(By.XPATH, '//div[@class="artno-wrap"]//div[2]').text
                except:
                    art_product = "Нет артикула"
                try:
                    brand_product = driver.find_element(By.XPATH, '//div[@class="main-col"]//span[@class="brand"]').text
                except:
                    brand_product = "Нет бренда"
                try:
                    character_product = driver.find_elements(By.XPATH , '//table[@class="table table-characteristic"]//tbody')
                    for i in character_product:
                        character_product = i.text.replace('\n', '; ')
                except:
                    character_product = 'Нет характеристик'
                try:
                    avaib_product = driver.find_element(By.XPATH, '//div[@class="main-col"]//div[@class="balance"]').text
                except:
                    avaib_product = "Нет информации"
                try:
                    img_product = driver.find_element(By.XPATH , '//div[@id="bigimg"]//img').get_attribute("src")
                except:
                    img_product = "Нет фото товара"
                try:
                    price_product = driver.find_element(By.XPATH, '//div[@class="price-current"]//span[@id="calc-good-total"]').text.replace('.', ',')
                except:
                    price_product = "Нет цены"

                try:
                    catalog_product = driver.find_element(By.XPATH, '//div[@class="producer active"]//div//a').text
                except:
                    catalog_product = "Нет каталога"
                with open(f"/archive/semena_market/group.csv", "a", errors='ignore') as file:
                    writer = csv.writer(file, delimiter=";", lineterminator="\r")
                    writer.writerow(
                        (
                            name_product,
                            discrip_product,
                            art_product,
                            brand_product,
                            character_product,
                            img_product,
                            avaib_product,
                            price_product,
                            catalog_product
                        )
                    )
                product_url += 1
                print('-' * 50)
                print(f"Обработано {product_url} найменования")
                print('-' * 50)
        except Exception as ex:
            print(ex)

        diff_time = datetime.datetime.now() - start_time

    except Exception as ex:
        print(ex)

    finally:
        print('-' * 50)
        print("Обработка завершена, закрываем Браузер")
        print('-' * 50)
        print(diff_time)
        driver.close()
        driver.quit()


def parse_content():
    url = "https://semena.market/semena"
    get_content(url)


if __name__ == '__main__':
    parse_content()
