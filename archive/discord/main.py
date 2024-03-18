import glob
import urllib.request
from urllib.request import urlretrieve
from PIL import Image
import PIL
import re
import zipfile
import os
import json
import csv
import time
import requests
from bs4 import BeautifulSoup
import lxml
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
    driver.maximize_window()
    time.sleep(2)
    for i in range(1, 201):
        time.sleep(2)
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(2)
        button_input = driver.find_element(By.XPATH, '//div[@class="countPage"]//input[@type="number"]')
        button_input.clear()
        button_input.send_keys(i)
        button_input.send_keys(Keys.ENTER)
        time.sleep(2)
        with open(f"C:\\scrap_tutorial-master\\discord\\data\\{i}.html", "w", encoding='utf-8') as file:
            file.write(driver.page_source)

    driver.close()
    driver.quit()


def get_items():
    with open(f"C:\\scrap_tutorial-master\\discord\\data.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Name', 'ID'

            )
        )
    targetPattern = "C:\\scrap_tutorial-master\\discord\\data\\*.html"
    files_html = glob.glob(targetPattern)
    for item in files_html:
        with open(item, encoding='utf-8') as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        table = soup.find('table', attrs={'class': 'table serversList'})
        table_tbody = table.find('tbody')
        cart_table = table_tbody.find_all('tr', attrs={'class': 'tr'})
        for i in cart_table:
            name_card = i.find('a', attrs={'class': 'serverName'}).text
            id_card = i.find('span', attrs={'class': 'members'}).text
            print(item, ";", name_card, ";", id_card)

            # with open(f"C:\\scrap_tutorial-master\\ranker.com\\data.csv", "a", errors='ignore') as file:
            #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
            #     writer.writerow(
            #         (
            #             name_card, id_card
            #
            #         )
            #     )


if __name__ == '__main__':
    # print("Вставьте ссылку")
    # url = input()
    # # # # # ##Сайт на который переходим
    # # # # # # url = "https://www.ranker.com/list/favorite-male-singers-of-all-time/music-lover?ref=browse_rerank&l=1"
    # # # # # # Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product('https://server-discord.com/')
    get_items()
    # parsing_product()
