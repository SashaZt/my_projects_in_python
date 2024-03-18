import os
import glob
import urllib3.exceptions
import re
import json
import traceback
from random import randint
import time
import psutil
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait

import csv


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--proxy-server=37.233.3.100:9999')
    chrome_options.add_argument('--disable-gpu')
    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver

def save_link_all_product():
    driver = get_chromedriver()
    for i in range(89, 1158):

        url = f"https://latifundist.com/birzha?rid=0&page={i}"

        driver.get(url=url)
        driver.maximize_window()
        time.sleep(10)
        try:
            wait = WebDriverWait(driver, 60)
            button_art_wait = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="add_form"]')))
            with open(f"c:\\data_latifundist\\data_{i}.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
        except requests.exceptions.ConnectionError:
            print(f"Connection error occurred while saving data for {i}")
        with open(f'bad_client.csv', 'a', newline='',
                  encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=";", lineterminator="\r")
            writer.writerow(url)
        traceback.print_exc()
    driver.close()
    driver.quit()




def parsing_url_in_html():
    targetPattern = r"c:\data_latifundist\*.html"
    files_html = glob.glob(targetPattern)
    data_url = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            links = soup.find_all('a', {'class': 'material_item__link'})
            for link in links:
                url = "https://latifundist.com/birzha" + link['href']
                data_url.append(url)
    with open('urls.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL'])
        for url in data_url:
            writer.writerow([url])

def save_html_page_clients():
    driver = get_chromedriver()
    with open(f'urls.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        coun = 0
        for url in urls:
            driver.get(url=url[0])
            driver.maximize_window()
            coun += 1
            time.sleep(10)
            try:
                # wait = WebDriverWait(driver, 60)
                # button_art_wait = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="add_form"]')))
                with open(f"c:\\data_latifundist\\data_{coun}.html", "w", encoding='utf-8') as file:
                    file.write(driver.page_source)
            except requests.exceptions.ConnectionError:
                print(f"Connection error occurred while saving data for {i}")
            with open(f'bad_client.csv', 'a', newline='',
                      encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=";", lineterminator="\r")
                writer.writerow(url)
            traceback.print_exc()
        driver.close()
        driver.quit()

def find_bad_html_files():
    # задаем путь к папке
    folder_path = r'c:\\data_latifundist\\'
    bad_urls = []
    # перебираем все файлы в папке
    for filename in os.listdir(folder_path):

        # создаем полный путь к файлу
        file_path = os.path.join(folder_path, filename)

        # проверяем размер файла
        if os.path.isfile(file_path) and os.path.getsize(file_path) == 252:
            bad_urls.append(int(filename.replace("data_", "").replace(".html", "")))
    print(bad_urls)

def bad_url():
    driver = get_chromedriver()
    # задаем номера строк, по которым нужно получить URL
    row_numbers = [693,343, 694, 695, 696, 697, 698, 699, 700, 702, 703, 711, 715, 733, 737, 745, 749, 759, 776, 778, 783, 788, 797, 799, 831, 832, 833, 835, 836, 838, 855, 866, 871, 878, 879]

    # открываем файл urls.csv
    with open('urls.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        coun = 2000
        # перебираем номера строк и получаем соответствующие URL
        for row_number in row_numbers:
            url = urls[row_number][0]
            driver.get(url=url)
            driver.maximize_window()
            coun += 1
            time.sleep(10)
            try:
                # wait = WebDriverWait(driver, 60)
                # button_art_wait = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="add_form"]')))
                with open(f"c:\\data_latifundist\\data_{[row_number][0]}.html", "w", encoding='utf-8') as file:
                    file.write(driver.page_source)
            except requests.exceptions.ConnectionError:
                print(f"Connection error occurred while saving data for {[row_number][0]}")
            with open(f'bad_client.csv', 'a', newline='',
                      encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=";", lineterminator="\r")
                writer.writerow(url)
            traceback.print_exc()
        driver.close()
        driver.quit()
def parsing_product():
    targetPattern = r"c:\data_latifundist\*.html"
    files_html = glob.glob(targetPattern)
    data_url = []
    with open('data.csv', "w",
              errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                "", "", "", "", "", "", ""
            )
        )
    for item in files_html:
        # print(item)
        codes = []
        with open(item, encoding="utf-8") as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            # try:
            script = soup.find_all('script', {'type': 'application/ld+json'})[1].string
            # except:
            #     script = soup.find_all('script', {'type': 'application/ld+json'})[1].string.replace(',\n', '')
            # Десериализация JSON-строки
            try:
                json_object = json.loads(script)
            except:
                print(f'Ошибка {item}')
                continue
            # Обращение к нужным полям объекта
            name = json_object[0]['name']
            # author = json_object[0]['author']
            keywords = json_object[0]['keywords']
            date_published = json_object[0]['datePublished']
            description = json_object[0]['description']
            # Находим элемент <article class="wrapper">
            article = soup.find('article', {'class': 'wrapper'})

            # Находим все элементы <p style="padding-left: 30px;"> внутри элемента <article class="wrapper">
            paragraphs = article.find_all('p', {'style': 'padding-left: 30px;'})
            try:
                tel = paragraphs[0].text
            except:
                tel = None
            try:
                emaail_firma = paragraphs[1].text
            except:
                emaail_firma = None
            # Находим элемент <article class="wrapper">
            article = soup.find('article', {'class': 'wrapper'})

            # Находим элемент <strong>Цена:</strong> внутри элемента <article class="wrapper">
            price_element = article.find('strong', string='Цена:')

            price_value_element = price_element.next_sibling
            price_value = price_value_element.strip()
            codes.append(name)
            codes.append(keywords)
            codes.append(date_published)
            codes.append(description)
            codes.append(tel)
            codes.append(emaail_firma)
            codes.append(price_value)
            with open(f"data.csv", "a",
                      errors='ignore', encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow((codes))



if __name__ == '__main__':
    # save_link_all_product()
    # parsing_url_in_html()
    # save_html_page_clients()
    # find_bad_html_files()
    # bad_url()
    parsing_product()
