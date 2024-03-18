# import pickle
# import zipfile
import csv
import json
import os
import time
from datetime import date

import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
# import requests
# Нажатие клавиш
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import Select

from selenium import webdriver
# import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

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
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.get(url=url)
    # time.sleep(1)

    button_cookies = driver.find_element(By.XPATH,
                                         '//div[@class="cookie-alert-extended-controls"]//button[@class="cookie-alert-extended-button"]').click()
    # time.sleep(1)
    product_url = []
    card_url = []

    card_product_url = driver.find_elements(By.XPATH,
                                            '//ul[@class="items am-filter-items-attr_category_ids am-labels-folding -am-singleselect"]/li/a')
    for item in card_product_url[1:2]:
        product_url.append(
            {
                'url_name': item.get_attribute("href"),
                'title_group': item.get_attribute("title")  # Добавляем еще одно необходимое поле
            }
            # Добавляем в словарь два параметра для дальнейшего записи в json
        )
    for i in product_url:
        driver.get(i['url_name'])  # 'url_name' - это и есть ссылка
        for k in range(20):
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        cards = driver.find_elements(By.XPATH, '//div[@class="product details product-item-details"]/a')
        for j in cards:
            card_url.append(
                {
                    'url_name': j.get_attribute("href"),
                    'title_group': i['title_group']
                }
                # Добавляем в словарь два параметра для дальнейшего записи в json
            )
    with open(f"C:\\scrap_tutorial-master\\lidl\\card_url.json", 'w', encoding="utf-8") as file:
        json.dump(card_url, file, indent=4, ensure_ascii=False)
    print('Собрали все ссылки')
    driver.close()
    driver.quit()


def parsing_product():
    current_date = date.today()
    with open(f"card_url.json") as file:
        all_site = json.load(file)
    product_url = []
    data = []
    char_prod_all = {}
    files_result = f"{current_date}_product.csv"
    with open(files_result, "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Title',
                'Brand_product',
                'title_group',
                'Artikelnr',
                'Weight product',
                'Price',
                'Link to img'
            )
        )
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    for item in all_site[:10]:
        Title_group = item['title_group']
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            button_cookies = driver.find_element(By.XPATH,
                                                 '//div[@class="cookie-alert-extended-controls"]//button[@class="cookie-alert-extended-button"]').click()
        except:
            pass
        time.sleep(1)
        # Обезательно ждем
        # driver.implicitly_wait(5)
        try:
            name_product = driver.find_element(By.XPATH, '//div[@class="page-title-wrapper product"]/h1/span').text
        except:
            name_product = 'Not title'
        try:
            # sku_product = driver.find_element(By.XPATH, '///*[@id="tab-description"]/div/div/p').text.replace('Artikelnr.: ', '')
            sku_product = driver.find_element(By.XPATH, '//div[@class="col-left"]/p').text.replace('Artikelnr.: ', '')
        except:
            sku_product = "Not SKU"
        try:
            weight_product = driver.find_element(By.XPATH,
                                                 '//*[@id="maincontent"]/div[3]/div/div[1]/div[1]/div[1]/div[3]/div[3]/span/span[2]').text.replace(
                '\n', '')
        except:
            weight_product = "Not weight_product"

        try:
            brand_product = driver.find_element(By.XPATH,
                                                '//div[@class="product-info-extrahint hidden-small"]//div[@class="brand-details"]//p[1]').text
        except:
            brand_product = "Not weight_product"

        try:
            img = driver.find_element(By.XPATH,
                                      '//div[@class="fotorama__stage__frame fotorama__active fotorama_horizontal_ratio fotorama__loaded fotorama__loaded--img"]').get_attribute(
                "href")
        except:
            img = 'no img'

        try:
            price = driver.find_element(By.XPATH, '//div[@class="product-info-price"]//strong').text.replace('*CHF',
                                                                                                             '').replace(
                '.', ',')
        except:
            price = 'No price'
        #
        with open(files_result, "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product,
                    brand_product,
                    Title_group,
                    sku_product,
                    weight_product,
                    price,
                    f'=IMAGE("{img}")'
                )
            )

    print('Сохранил результат в CSV файл')
    driver.close()
    driver.quit()


def csv_to_xlsx():
    current_date = date.today()
    files_csv = f"{current_date}_product.csv"
    files_xlsx = f"data/{current_date}_product.xlsx"
    csv_files = pd.read_csv(f'{files_csv}', sep=';')
    excel_files = pd.ExcelWriter(f'{files_xlsx}')
    csv_files.to_excel(excel_files)
    excel_files.save()
    print('Сохранили резултат в XLSX файл')


def uploadGoogleDrive(dir_path='data/'):
    try:
        drive = GoogleDrive(gauth)

        for file_name in os.listdir(dir_path):
            my_file = drive.CreateFile({'title': f'{file_name}'})
            my_file.SetContentFile(os.path.join(dir_path, file_name))
            my_file.Upload()

            print(f'Файл {file_name} загружен!')

        return 'Success!Have a good day!'
    except Exception as _ex:
        return 'Got some trouble, check your code please!'


if __name__ == '__main__':
    # #Сайт на который переходим
    # url = "https://sortiment.lidl.ch/de/alle-kategorien.html"
    # Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product(url)
    # parsing_product()
    # csv_to_xlsx()
    uploadGoogleDrive()
