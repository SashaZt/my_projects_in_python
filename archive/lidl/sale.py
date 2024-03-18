#import pickle
#import zipfile
import os
import json
import csv
import time
#import requests
# Нажатие клавиш
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import Select

from selenium import webdriver
#import random
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
    with open(f"C:\\scrap_tutorial-master\\lidl\\product_sale.json", 'w', encoding="utf-8") as file:
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
    # with open(f"C:\\scrap_tutorial-master\\lidl\\card_url.json", 'w', encoding="utf-8") as file:
    #     json.dump(card_url, file, indent=4, ensure_ascii=False)

    driver.close()
    driver.quit()


def parsing_product():
    with open(f"C:\\scrap_tutorial-master\\lidl\\product_sale.json") as file:
        all_site = json.load(file)

    with open(f"C:\\scrap_tutorial-master\\lidl\\product_sale.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_product',
                'ad',
                'brand',
                'Price_New',
                'Price_Old',
                'article_texbody_01',
                'article_texbody_02',
                'article_texbody_03',
                'Link to img'
            )
        )
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    product = 0
    for item in all_site:
        driver.implicitly_wait(2)
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            button_cookies = driver.find_element(By.XPATH,'//div[@class="cookie-alert-extended-controls"]//button[@class="cookie-alert-extended-button"]').click()
        except:
            pass
        # Обезательно ждем
        try:
            name_product = driver.find_element(By.XPATH, '//h1[@class="attributebox__headline attributebox__headline--h1"]').text
        except:
            name_product = 'Not title'
        try:
            ad = driver.find_element(By.XPATH, '//div[@class="ribbon ribbon--primary ribbon--single"]//div[@class="ribbon__text"]').text
        except:
            ad = "Not AD"
        try:
            article_texbody_01 = driver.find_element(By.XPATH, '//div[@class="attributebox__long-description"]//li[1]').text.replace('.', ',')

        except:
            article_texbody_01 = 'No article_texbody'
        try:
            article_texbody_02 = driver.find_element(By.XPATH, '//div[@class="attributebox__long-description"]//li[2]').text.replace('.', ',')

        except:
            article_texbody_02 = 'No article_texbody'

        try:
            article_texbody_03 = driver.find_element(By.XPATH, '//div[@class="attributebox__long-description"]//li[3]').text.replace('.', ',')
        except:
            article_texbody_03 = 'No article_texbody'

        try:
            img = driver.find_element(By.XPATH,
                                      '//div[@class="multimediabox__preview"]//a').get_attribute("href")
        except:
            img = 'no img'
        try:
            price_new = driver.find_element(By.XPATH, '//*[@id="productbox"]/div[2]/div/div[1]/div/div[2]/div[2]/span').text.replace('*CHF',
                                                                                                             '').replace(
                '.', ',')
        except:
            price_new = 'No price'
        try:
            price_old = driver.find_element(By.XPATH, '//*[@id="productbox"]/div[2]/div/div[1]/div/div[2]/div[1]/span/span').get_attribute('outerText').replace('.', ',').replace('\n', ',')
        except:
            price_old = 'No price'
        try:
            brand = driver.find_element(By.XPATH, '//div[@class="pricebox pricebox--highlight-offer pricebox--negative pricebox--medium"]//span[@class="pricebox__recommended-retail-price"]').get_attribute("textContent")
        except:
            brand = 'No price'

        # print(name_product,
        #             ad,
        #             brand,
        #             article_texbody_01,
        #             article_texbody_02,
        #             article_texbody_03,
        #             price_new,
        #             price_old,
        #             img
        #       )
        with open(f"C:\\scrap_tutorial-master\\lidl\\product_sale.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product,
                    ad,
                    brand,
                    price_new,
                    price_old,
                    article_texbody_01,
                    article_texbody_02,
                    article_texbody_03,
                    img
                )
            )

    driver.close()
    driver.quit()


if __name__ == '__main__':
    # #Сайт на который переходим
    # print('Вставьте ссылку на акцию')
    # url =  input('')
    # # # Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product(url)
    parsing_product()
