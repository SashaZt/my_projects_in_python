from bs4 import BeautifulSoup
import random
import glob
import re
import requests
import json
import cloudscraper
import os
from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import time
import shutil
import tempfile
# import undetected_chromedriver as webdriver


from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


def get_chromedriver():
    options = webdriver.ChromeOptions()

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-gpu")
    # options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    options.add_argument("--start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # options.add_argument('--disable-extensions') # Отключает использование расширений
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-setuid-sandbox')
    options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    service = ChromeService(executable_path='C:\\scrap_tutorial-master\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver
delta = '''
avtomobilnaya-aptechka
avtomobilnye-kliuchi
buksirovochnyy-tros
distillirovannaya-voda
fm-modulyatory
gruzovye-boksy
gubki-mochalki
kamery-zadnego-vida
klemmi_akkumuliatora
kompressory_avtomobilnye
kreplenie_dlya_velosipeda_na_avto
krepleniya-dlya-lyzh-i-snoubordov
motornoe-maslo-dlya-mototekhniki
nabor-avtomobilista
nabor-instrumentov
nozhi-montazhnye
nozhnicy-po-metallu
ochistiteli_dvigatelya_naruzhnye
ochistiteli_kondicionera
ochistiteli_ruk
ochistiteli_tormoznoy_sistemy
ochistiteli-karbiuratora
ochistiteli-salona
ochki-zashchitnye
perekhodnye-ramki-dlya-magnitol
poliroli-dlya-salona
polirol-dlya-avto
provoda-prikurivaniya
pusko-zaryadnye-ustroystva
restavracionnye-karandashi
schetki-skrebki-vodosgony
siemniki-izolyatsii
signalizatsii-na-avto
sredstva-dlya-ochistki-kuzova-avto
styazhki-dlya-gruza
tormoznaya-zhidkost
tortsevye-golovki
transmissionnoe-maslo
usb-kabeli
videoregistrator-zerkalo
yashchiki-dlya-instrumentov
zhilety-signalnyye
znaki_avarijnoj_ostanovki

'''
delta_list = delta.strip().split("\n")
def get_selenium():
    driver = get_chromedriver()
    driver.maximize_window()
    for folders in delta_list:
        url = f'https://dok.ua/ua/catalog/{folders}'
        name_files_ua = url.split('/')[-1].replace('-', '_')
        name_files_rus = url.split('/')[-1].replace('-', '_') + '_rus'

        driver.get(url)
        time.sleep(2)

        file_name_ua = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_ua}.html"
        with open(file_name_ua, "w", encoding='utf-8') as fl:
            fl.write(driver.page_source)
        driver.find_element(By.XPATH, '//div[@class="header__top-block"]//a[@data-language="ru"]').click()
        time.sleep(2)
        file_name_rus = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_rus}.html"
        with open(file_name_rus, "w", encoding='utf-8') as fl:
            fl.write(driver.page_source)
def parsing():
    for folders in delta_list:
    # folder = 'kreplenie_dlya_velosipeda_na_avto'
        name_files_ua = folders
        try:
            file_name_ua = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_ua}.html"
        except:
            file_name_ua = None
            print(folders)

        name_files_rus = folders + '_rus'
        file_name_rus = f"C:\\scrap_tutorial-master\\archive\\dok.ua\\heandler\\{name_files_rus}.html"
        try:
            with open(file_name_ua, encoding="utf-8") as file:
                 src = file.read()
        except:
            continue
        soup = BeautifulSoup(src, 'lxml')
        row_id = 1
        hedler_ua = []
        while True:
            element = soup.find('span', {'data-row-id': str(row_id)})
            if element:
                hedler_ua.append(element.text.strip())
                row_id += 1
            else:
                break
        with open(file_name_rus, encoding="utf-8") as file:
             src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        row_id = 1
        hedler_rus = []
        while True:
            element = soup.find('span', {'data-row-id': str(row_id)})
            if element:
                hedler_rus.append(element.text.strip())
                row_id += 1
            else:
                break
        # Элементы для добавления в начало каждого списка
        art_ua = 'Артикул'
        ser_ua = 'Серія'
        art_rus = 'Артикул'
        ser_rus = 'Серия'

        # Добавляем элементы в начало списков
        hedler_ua.insert(0, ser_ua)
        hedler_ua.insert(0, art_ua)

        hedler_rus.insert(0, ser_rus)
        hedler_rus.insert(0, art_rus)

        # Объединяем списки
        hedler = []
        hedler.extend(hedler_ua)
        hedler.extend(hedler_rus)
        add = ['link_product', 'name_product_ua', 'name_product_rus', 'link_img', 'price_product', 'delivery_product']
        hedler = add + hedler

        # Выводим исходные и объединенные списки для проверки
        # print("hedler_ua:", hedler_ua)
        # print("hedler_rus:", hedler_rus)
        print(folders)
        print('_'*100)
        print(hedler)


if __name__ == '__main__':
    get_selenium()
    # parsing()
