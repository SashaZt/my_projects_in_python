import os
import pickle
import json
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
import lxml
import undetected_chromedriver
# Нажатие клавиш
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

from selenium import webdriver
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = undetected_chromedriver.Chrome()
    # s = Service(
    #     executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    # )
    # driver = webdriver.Chrome(
    #     service=s,
    #     options=chrome_options
    # )

    return driver


def save_link_all_product(url):
    driver = undetected_chromedriver.Chrome(use_subprocess=True)
    # driver = get_chromedriver(use_proxy=False,
    #                           user_agent=f"{useragent.random}")

    e_mail = 'a.zinchyk83@gmail.com'
    pas_s = 'RqgP9jXkND!xTDP'
    driver.get(url=url)
    driver.maximize_window()
    time.sleep(5)
    try:
        log_in = driver.find_element(By.XPATH, '//span[text() = "Log In"]').click()
    except:
        log_in = print('No Log In')
    time.sleep(10)
    try:
        button_email = driver.find_element(By.XPATH, '//input[@autocomplete="email"]')
        button_email.send_keys(e_mail)
        time.sleep(5)
    except:
        button_email = print('Not email')
    try:
        button_pass = driver.find_element(By.XPATH, '//input[@autocomplete="current-password"]')
        button_pass.send_keys(pas_s)
        time.sleep(5)
    except:
        button_pass = print('Not pass')

    try:
        button_in = driver.find_element(By.XPATH,
                                        '//button[@class="mat-focus-indicator login mat-raised-button mat-button-base mat-primary mat-button-disabled"]').click()
    except:
        button_in = print('Not in')

    # Блок работы с куками-----------------------------------------
    # # Создание куки
    # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
    # time.sleep(5)
    # Читание куки
    # for cookie in pickle.load(open("cookies", "rb")):
    #     driver.add_cookie(cookie)
    # Блок работы с куками-----------------------------------------

    # driver.refresh()
    # time.sleep(5)
    # button_find = driver.find_element(By.XPATH, '//input[@aria-label="Search Crunchbase"]')
    # time.sleep(1)
    # button_find.send_keys('Roku')
    # time.sleep(5)
    # r = driver.find_elements(By.XPATH, '//div[@class="org-text-container"]//div[contains(text(), "Roku")]')
    # r[0].click()
    # time.sleep(1)

    # button_Technology = driver.find_element(By.XPATH, ' // span[text() = "Technology"]').click()
    # time.sleep(10)

    driver.close()
    driver.quit()


def get_items(file_path):
    pass


if __name__ == '__main__':
    # print("Вставьте ссылку")
    # url = input()
    # # # # # ##Сайт на который переходим
    # # # # # # url = "https://www.ranker.com/list/favorite-male-singers-of-all-time/music-lover?ref=browse_rerank&l=1"
    # # # # # # Запускаем первую функцию для сбора всех url на всех страницах
    save_link_all_product('https://www.crunchbase.com')
    # get_items('C:\\scrap_tutorial-master\\ranker.com\\data.html')
    # parsing_product()
