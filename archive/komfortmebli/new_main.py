import pickle
#import zipfile
#from bs4 import BeautifulSoup

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



def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    s = Service(
        executable_path="//Users//vynohradnyk//Desktop//Комфорт-меблі//chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def save_link_all_product(url):
    driver = get_chromedriver(use_proxy=False,
                              user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    driver.get(url=url)
    driver.implicitly_wait(10)
    driver.maximize_window()

    categoriy_product_urls = []
    card_product_url_all = []
    categoriy_product_url = driver.find_elements(By.XPATH, '//div[@class="bx_catalog_tile"]//li/a')
    for item_categoriy in categoriy_product_url:
        categoriy_product_urls.append(
            {'url_name': item_categoriy.get_attribute("href")}
        )
    pod_categ_urls = []
    for item_pod_categ in categoriy_product_urls:
        driver.get(item_pod_categ['url_name'])
        pod_categ_product_url = driver.find_elements(By.XPATH, '//div[@class="bx_catalog_tile"]//li/a')
        for item_card in pod_categ_product_url:
            pod_categ_urls.append(
                {'url_name': item_card.get_attribute("href")}
            )
    for item_prod in pod_categ_urls:
        driver.get(item_prod['url_name'])

        for k in range(100):
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        cards = driver.find_elements(By.XPATH, '//div[@class="product-item"]//div[@class="product-item-title"]//a')
        for href in cards:

            card_product_url_all.append(
                {'url_name': href.get_attribute("href")}
            )
                                        # Добавляем в словарь два параметра для дальнейшего записи в json

    with open(f"//Users//vynohradnyk//Desktop//Комфорт-меблі//all_link.json", 'w') as file:
        json.dump(card_product_url_all, file, indent=4, ensure_ascii=False)

    print('Ссылки все получены')
    driver.close()
    driver.quit()


def parsing_product():
    with open(f"//Users//vynohradnyk//Desktop//Комфорт-меблі//all_link.json") as file:
        all_site = json.load(file)

    driver = get_chromedriver(use_proxy=False,
                              user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")


    # driver.maximize_window()

    with open(f"//Users//vynohradnyk//Desktop//Комфорт-меблі//data.csv", "w", errors='ignore', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_product','categ_product','price_new', 'price_old', 'Описание' ,'Артикул', 'Висота', 'Ширина', 'Глибина', 'Ціновий діапазон', 'Серія', 'Тип кухні', 'Можливість індивідуального замовлення', 'Гарантія', "Матеріал корпуса", 'Матеріал фасада', 'Упаковка','Наявність', 'Спосіб оплати',  'images'

            )
        )
    # Если необходимо продолжить с какой то позиции тогда for item in all_site[2502:] от 2502 до последней позиции
    for item in all_site[6253:]:
        data_table = []
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        driver.maximize_window()
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            char = driver.find_element(By.XPATH, '//div[@class="col-sm-8 col-md-9"]//li[@class="product-item-detail-tab"]').click()
        except:
            char = 'No button'
        #if char:
        #    char.click()
        #else:
        #    print('No button')
        try:
            des = driver.find_element(By.XPATH,'//div[@class="product-item-detail-tab-content active"]').get_attribute("outerText").replace("\n", " ")
        except:
            des = 'No des'
        

        try:
            name_product = driver.find_element(By.XPATH, '//div[@class="container-fluid"]//h1').text
        except:
            name_product = 'Not title'
        try:
            categ_product = driver.find_element(By.XPATH, '//div[@class="bx-breadcrumb-item"][last()]/span').text
        except:
            categ_product = "Not cat"
        try:
            price_old = driver.find_element(By.XPATH,
                                            '//div[@class="product-item-detail-pay-block"]//div[@class="product-item-detail-price-old"]').text
        except:
            price_old = 'no price_old'
        try:
            price_new = driver.find_element(By.XPATH,
                                            '//div[@class="product-item-detail-pay-block"]//div[@class="product-item-detail-price-current"]').text
        except:
            price_new = 'No price_new'
        try:
            images = driver.find_element(By.XPATH,'//div[@class="product-item-detail-slider-images-container"]//div//img').get_attribute("src")
        except:
            images = 'No images'
        try:
            n_01 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[1]').text
        except:
            n_01 = 'No n_01'
        try:
            n_02 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[2]').text
        except:
            n_02 = 'No n_02'
        try:
            n_03 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[3]').text
        except:
            n_03 = 'No n_03'
        try:
            n_04 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[4]').text
        except:
            n_04 = 'No n_04'
        try:
            n_05 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[5]').text
        except:
            n_05 = 'No n_05'
        try:
            n_06 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[6]').text
        except:
            n_06 = 'No n_06'
        try:
            n_07 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[7]').text
        except:
            n_07 = 'No n_07'
        try:
            n_08 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[8]').text
        except:
            n_08 = 'No n_08'
        try:
            n_09 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[9]').text
        except:
            n_09 = 'No n_09'
        try:
            n_10 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[10]').text
        except:
            n_10 = 'No n_10'
        try:
            n_11 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[11]').text
        except:
            n_11 = 'No n_11'
        try:
            n_12 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[12]').text
        except:
            n_12 = 'No n_12'
        try:
            n_13 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[13]').text
        except:
            n_13 = 'No n_13'
        try:
            n_14 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[14]').text
        except:
            n_14 = 'No n_14'
        try:
            n_15 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dt[15]').text
        except:
            n_15 = 'No n_15'
        try:
            v_01 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[1]').text
        except:
            v_01 = 'No n_01'
        try:
            v_02 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[2]').text
        except:
            v_02 = 'No n_02'
        try:
            v_03 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[3]').text
        except:
            v_03 = 'No n_03'
        try:
            v_04 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[4]').text
        except:
            v_04 = 'No n_04'
        try:
            v_05 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[5]').text
        except:
            v_05 = 'No n_05'
        try:
            v_06 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[6]').text
        except:
            v_06 = 'No n_06'
        try:
            v_07 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[7]').text
        except:
            v_07 = 'No n_07'
        try:
            v_08 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[8]').text
        except:
            v_08 = 'No n_08'
        try:
            v_09 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[9]').text
        except:
            v_09 = 'No n_09'
        try:
            v_10 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[10]').text
        except:
            v_10 = 'No n_10'
        try:
            v_11 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[11]').text
        except:
            v_11 = 'No n_11'
        try:
            v_12 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[12]').text
        except:
            v_12 = 'No n_12'
        try:
            v_13 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[13]').text
        except:
            v_13 = 'No n_13'
        try:
            v_14 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[14]').text
        except:
            v_14 = 'No n_14'
        try:
            v_15 = driver.find_element(By.XPATH, '//div[@class="col-xs-12"]//div[@class="product-item-detail-tab-content"]//dl//dd[15]').text
        except:
            v_15 = 'No n_15'
        

        # header_table.append(
        #     [
        #         'name_product','categ_product','price_new', 'price_old', des, n_01, n_02, n_03, n_04, n_05, n_06, n_07, n_08, n_09, n_10, n_11, n_12, n_13, n_14, n_15,'images'
        #     ]
        # )
        data_table.append(
            [
                name_product, categ_product, price_new, price_old,v_01, v_02, v_03, v_04, v_05, v_06,
                v_07, v_08, v_09, v_10, v_11, v_12, v_13, v_14, v_15, images
            ]
        )
        with open(f"//Users//vynohradnyk//Desktop//Комфорт-меблі//data.csv", "a", errors='ignore', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product, categ_product, price_new, price_old, des, v_01, v_02, v_03, v_04, v_05, v_06, v_07, v_08, v_09, v_10, v_11, v_12, v_13, v_14, v_15, images

                )
            )
        # # Дописываем данные из списка data в файл
        # writer.writerows(
        #     data_table
        # )








if __name__ == '__main__':
    # #Сайт на который переходим
    #url = "https://komfortmebli.com.ua/ua/"
    # Запускаем первую функцию для сбора всех url на всех страницах
    #save_link_all_product(url)
    parsing_product()
