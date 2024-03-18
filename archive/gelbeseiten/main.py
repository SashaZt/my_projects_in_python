import datetime
import json
import csv
import os
import pickle
import lxml
import time
#Настройка прокси
#from proxy_config import login, password, proxy
#Настройка прокси
from itertools import groupby

# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
# Нажатие клавиш
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
# proxies = {
#     'https': f'http://{login}:{password}@{proxy}'
# }
options = webdriver.ChromeOptions()
# Отключение режима WebDriver
options.add_experimental_option('useAutomationExtension', False)

# Работа в фоновом режиме
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
driver.maximize_window()
driver.set_window_size(1400, 3000)


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
        url_firma = []
        click_coocek = driver.find_element(By.XPATH, '//span[@id="cmpbntyestxt"]').click()
        driver.implicitly_wait(5)
        # find_company = driver.find_element(By.XPATH, '//span[@class="gc-btn__text"]').click()
        driver.implicitly_wait(5)
        # Листать по страницам ---------------------------------------------------------------------------
        page_product = 0

        isNextDisable = False
        while not isNextDisable:
            try:
                # Сначала что то ищем на первой странице, а только потом ищем на остальных
                next_button = driver.find_element(By.XPATH, '//a[@id="mod-LoadMore--button"]')
                driver.implicitly_wait(5)
                # Опускаемся на странице до
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!

                if next_button:
                    next_button.click()
                    driver.implicitly_wait(5)
                    page_product += 1
                    print(f"Обработано {page_product} страниц")
                else:
                    isNextDisable = True
                    table_firma = driver.find_elements(By.XPATH,
                                                       '//div[@id="gs_treffer"]//article[@class="mod mod-Treffer"]//a')
                    for firma in table_firma:
                        url_firma.append(
                            {'url_name': firma.get_attribute("href")}
                            # Добавляем в словарь два параметра для дальнейшего записи в json
                        )
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------

        with open(f"C:\\scrap_tutorial-master\\\gelbeseiten\\group.json", 'a') as file:
            json.dump(url_firma, file, indent=4, ensure_ascii=False)


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
    url = "https://www.gelbeseiten.de/suche/kfz-werkst%c3%a4tten/deutschland"
    get_content(url)


if __name__ == '__main__':
    parse_content()
