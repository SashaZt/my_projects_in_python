# import pickle
# import zipfile
from datetime import date
import pandas as pd
import os
import json
import csv
import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

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
        executable_path="C:\\lidl\\chromedriver.exe"
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
    driver.implicitly_wait(5)
    driver.maximize_window()

    button_cookies = driver.find_element(By.XPATH,
                                         '//div[@class="cookie-alert-extended-controls"]//button[@class="cookie-alert-extended-button"]')
    if button_cookies:
        button_cookies.click()
    time.sleep(1)
    product_url = []
    card_url = []
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.implicitly_wait(10)
    card_product_url = driver.find_elements(By.XPATH,
                                            '//div[@class="nuc-a-flex-item nuc-a-flex-item--width-6 nuc-a-flex-item--width-4@sm"]//article[@class="ret-o-card"]//a')
    product = 0
    for item in card_product_url:
        product_url.append(
            {
                'url_name': item.get_attribute("href"),
                # 'title_group': item.get_attribute("title")  # Добавляем еще одно необходимое поле
            }
            # Добавляем в словарь два параметра для дальнейшего записи в json
        )
        product += 1
    print(f'Всего товаров {product}')
    with open(f"C:\\lidl\\product_sale.json", 'w', encoding="utf-8") as file:
        json.dump(product_url, file, indent=4, ensure_ascii=False)
    # for i in product_url:
    #     driver.get(i['url_name'])  # 'url_name' - это и есть ссылка
    #     for k in range(20):
    #         time.sleep(1)
    #         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     cards = driver.find_elements(By.XPATH, '//div[@class="product details product-item-details"]/a')
    #     for j in cards:
    #         card_url.append(
    #             {
    #                 'url_name': j.get_attribute("href"),
    #                 'title_group': i['title_group']
    #             }
    #             # Добавляем в словарь два параметра для дальнейшего записи в json
    #         )
    # with open(f"C:\\lidl\\card_url_sale.json", 'w', encoding="utf-8") as file:
    #     json.dump(card_url, file, indent=4, ensure_ascii=False)

    driver.close()
    driver.quit()


def parsing_product():
    with open(f"C:\\lidl\\product_sale.json") as file:
        all_site = json.load(file)

    with open(f"C:\\lidl\\product_sale.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_product',
                'ad',
                'article_texbody_01',
                'article_texbody_02',
                'article_texbody_03',
                'Price',
                'Link to img'
            )
        )
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    product = 0
    for item in all_site:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            button_cookies = driver.find_element(By.XPATH,
                                                 '//div[@class="cookie-alert-extended-controls"]//button[@class="cookie-alert-extended-button"]').click()
        except:
            pass
        # Обезательно ждем
        try:
            name_product = driver.find_element(By.XPATH,
                                               '//h1[@class="attributebox__headline attributebox__headline--h1"]').text
        except:
            name_product = 'Not title'
        try:
            ad = driver.find_element(By.XPATH,
                                     '//div[@class="ribbon ribbon--primary ribbon--single"]//div[@class="ribbon__text"]').text
        except:
            ad = "Not AD"
        try:
            article_texbody_01 = driver.find_element(By.XPATH,
                                                     '//div[@class="attributebox__long-description"]//li[1]').text

        except:
            article_texbody_01 = 'No article_texbody'
        try:
            article_texbody_02 = driver.find_element(By.XPATH,
                                                     '//div[@class="attributebox__long-description"]//li[2]').text

        except:
            article_texbody_02 = 'No article_texbody'

        try:
            article_texbody_03 = driver.find_element(By.XPATH,
                                                     '//div[@class="attributebox__long-description"]//li[3]').text
        except:
            article_texbody_03 = 'No article_texbody'

        try:
            img = driver.find_element(By.XPATH,
                                      '//div[@class="multimediabox__preview"]//a').get_attribute("href")
        except:
            img = 'no img'
        try:
            price = driver.find_element(By.XPATH,
                                        '//*[@id="productbox"]/div[2]/div/div[1]/div/div[2]/div[2]/span').text.replace(
                '*CHF',
                '').replace(
                '.', ',')
        except:
            price = 'No price'
        with open(f"C:\\lidl\\product_sale.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product,
                    ad,
                    article_texbody_01,
                    article_texbody_02,
                    article_texbody_03,
                    price,
                    f'=IMAGE("{img}")'
                )
            )
    print('Сохранил результат в CSV файл')
    driver.close()
    driver.quit()


def csv_to_xlsx():
    current_date = date.today()
    files_csv = f"{current_date}_product_sale.csv"
    files_xlsx = f"data/{current_date}_product_sale.xlsx"
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
    print('Вставьте ссылку на акцию')
    url = input('')
    # # # Запускаем первую функцию для сбора всех url на всех страницах
    save_link_all_product(url)
    parsing_product()
