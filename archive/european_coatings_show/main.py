# import pickle
# import zipfile
import csv
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import date

import pandas as pd
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
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
    driver.get(url=url)
    # time.sleep(1)
    time.sleep(5)


    isNextDisable = False
    while not isNextDisable:
        try:
            next_button = driver.find_elements(By.XPATH, '//div[contains(text(), "Show more")]')[1]
            # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
            if next_button:
                next_button.click()
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            else:
                isNextDisable = True
        except:
            isNextDisable = True
    with open(f'C:\\scrap_tutorial-master\\european_coatings_show\\data.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    driver.close()
    driver.quit()

def parsing_product():
    file_html = r"C:\scrap_tutorial-master\european_coatings_show\data.html"
    with open(file_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    links = soup.select('div.listContentContainer a')

    # получаем все URL и фильтруем только те, которые содержат "detail"
    all_urls = [link.get('href') for link in links if 'detail' in link.get('href')]

    # записываем URL в CSV-файл
    with open(f'C:\\scrap_tutorial-master\\european_coatings_show\\url.csv', 'w', newline='',
              encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
        writer.writerow(all_urls)





if __name__ == '__main__':
    # #Сайт на который переходим
    # url = "https://www.european-coatings-show.com/for-exhibitors/exhibitor-directory/#/search/f=h-entity_orga;v_sg=0;v_fg=0;v_fpa=FUTURE"
    # Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product(url)
    parsing_product()
    # csv_to_xlsx()
    # uploadGoogleDrive()
