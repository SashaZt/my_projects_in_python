import os
import glob
import urllib3.exceptions
import re
import traceback
from random import randint
import time
import psutil
import requests
import undetected_chromedriver
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait

import csv

# Нажатие клавиш

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = 'IP'
PROXY_PORT = 'PORT'  # Без кавычек
PROXY_USER = 'LOGIN'
PROXY_PASS = 'PASS'

# Настройка для requests чтобы использовать прокси
proxies = {'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}/'}

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"76.0.0"
}
"""

background_js = """
let config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver
# def get_undetected_chromedriver(use_proxy=False, user_agent=None):
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument(
#         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
#     chrome_options.add_argument('--disable-blink-features=AutomationControlled')
#
#     driver = undetected_chromedriver.Chrome()
#     # s = Service(
#     #     executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
#     # )
#     # driver = webdriver.Chrome(
#     #     service=s,
#     #     options=chrome_options
#     # )
#
#     return driver


def save_link_all_product():
    with open('member.csv', 'r') as f:
        nums = f.read().splitlines()
    for i in nums:
        print(i)
        url = "https://bi.prozorro.sale/#/participantsCard"
        driver = get_chromedriver()
        driver.get(url=url)
        driver.maximize_window()
        try:
            wait = WebDriverWait(driver, 60)
            button_art_wait = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@class="title ng-binding"]')))
            button_art = driver.find_element(By.XPATH, '//span[@class="title ng-binding"]')
            driver.execute_script("arguments[0].click();", button_art)
            find_button_wait = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Пошук у списку"]')))
            find_button = driver.find_element(By.XPATH, '//input[@placeholder="Пошук у списку"]')
            find_button.send_keys(i)
            find_button.send_keys(Keys.RETURN)
            button_prosto_wait = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@x-dir-text="Пропозиції"]')))
            button_prosto = driver.find_element(By.XPATH, '//div[@x-dir-text="Пропозиції"]').click()
            time.sleep(2)
            with open(f"c:\\data_bi_prozorro_sale\\data_{i}.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
            driver.close()
            driver.quit()
        except requests.exceptions.ConnectionError:
            print(f"Connection error occurred while saving data for {i}")
            with open(f'bad_client.csv', 'a', newline='',
                      encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=";", lineterminator="\r")
                writer.writerow(i)
            traceback.print_exc()
            driver.close()
            driver.quit()
            continue
        except Exception as e:
            traceback.print_exc()
            driver.close()
            driver.quit()
            continue
        # except Exception as e:
        #     print(f"Connection error occurred while saving data for {i}")
        #     with open(f'bad_client.csv', 'a', newline='',
        #               encoding='utf-8') as csvfile:
        #         writer = csv.writer(csvfile, delimiter=";", lineterminator="\r")
        #         writer.writerow(i)
        #     traceback.print_exc()
        #     driver.close()
        #     driver.quit()



def parsing_product():
    targetPattern = r"E:\data_bi_prozorro_sale\*.html"
    files_html = glob.glob(targetPattern)
    # data = []

    with open('data.csv', "w",
              errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                "Назва", "Код", "Регіон", "Місто", "Представник", "Телефон", "Електронна пошта", "Дата пропозиції",
                "Організатор", "Ідентифікатор аукціону", "Аукціон", "Статус аукціону", "Переможність пропозиції",
                "Фінальна сума пропозиції", "URL (Майданчик пропозиції)"
            )
        )
    for item in files_html:
        codes = []

        with open(item, encoding="utf-8") as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            spans = soup.find_all('span', {'ng-switch-when': 'text'})
            try:
                lot = spans[29].text
            except:
                lot = None
            try:
                name = spans[1].text.replace("\n", "").replace("\t", "")
            except:
                name = None
            try:
                edrpou = spans[4].text.replace("\n", "").replace("\t", "")
            except:
                edrpou = None

            try:
                tel = spans[10].text.replace("\n", "").replace("\t", "")
            except:
                tel = None

            try:
                email = spans[13].text.replace("\n", "").replace("\t", "")
            except:
                email = None

            try:
                add_19 = spans[19].text.replace("\n", "").replace("\t", "")
            except:
                add_19 = None

            try:
                add_22 = spans[22].text.replace("\n", "").replace("\t", "")
            except:
                add_22 = None
            try:
                fio = spans[7].text.replace("\n", "").replace("\t", "")
            except:
                fio = None

            try:
                datas = spans[27].text.replace("\n", "").replace("\t", "")
            except:
                datas = None
            try:
                organiz = spans[28].text.replace("\n", "").replace("\t", "")
            except:
                organiz = None

            try:
                aukchion = spans[30].text.replace("\n", "").replace("\t", "")
            except:
                aukchion = None

            try:
                status = spans[31].text.replace("\n", "").replace("\t", "")
            except:
                status = None

            try:
                pobiditel = spans[32].text.replace("\n", "").replace("\t", "")
            except:
                pobiditel = None
            try:
                final_summa =spans[35].text.replace("\n", "").replace("\t", "")
            except:
                final_summa = None
            codes.append(name)
            codes.append(edrpou)
            codes.append(add_19)
            codes.append(add_22)
            codes.append(fio)
            codes.append(tel)
            codes.append(email)
            codes.append(datas)
            codes.append(organiz)
            codes.append(lot)
            codes.append(aukchion)
            codes.append(status)
            codes.append(pobiditel)
            codes.append(final_summa)
            with open(f"data.csv", "a",
                      errors='ignore', encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow((codes))
            # print(f'{item} - {codes}')



if __name__ == '__main__':
    # save_link_all_product()
    parsing_product()
