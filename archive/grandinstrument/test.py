import glob
import re
import os
import json
import pandas as pd
from random import randint
import time
import psutil
import requests
import undetected_chromedriver
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver

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


# def get_chromedriver(use_proxy=True, user_agent=None):
#     chrome_options = webdriver.ChromeOptions()
#
#     if use_proxy:
#         plugin_file = 'proxy_auth_plugin.zip'
#
#         with zipfile.ZipFile(plugin_file, 'w') as zp:
#             zp.writestr('manifest.json', manifest_json)
#             zp.writestr('background.js', background_js)
#
#         chrome_options.add_extension(plugin_file)
#
#     if user_agent:
#         chrome_options.add_argument(f'--user-agent={user_agent}')
#
#     s = Service(
#         executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
#     )
#     driver = webdriver.Chrome(
#         service=s,
#         options=chrome_options
#     )
#
#     return driver
def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--proxy-server=37.233.3.100:9999')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

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
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for row in csv_reader:
            counter += 1
            print(counter)
            url_ua = row[0]
            url_ru = url_ua.replace("https://grandinstrument.ua/ua/", "https://grandinstrument.ua/")
            art = url_ua.split("/")[-2]
            for lang in ['ua', 'ru']:
                url = url_ua if lang == 'ua' else url_ru
                file_name = f"{art}.html"
                driver.get(url=url)
                # time.sleep(1)
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                        (By.XPATH, '//ul[@class="product-info-ul"]')))
                except:
                    continue
                if driver.find_element(By.XPATH, '//ul[@class="product-info-ul"]'):
                    time.sleep(1)
                    # ожидаем появления элементов на странице
                    try:
                        element1 = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                            (By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                    except:
                        print("")
                    try:
                        element2 = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                            (By.XPATH, "//div[@class='sets-show btn btn-showmore my-4 pe-4']")))
                    except:
                        print("")
                    try:
                        element3 = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                            (By.XPATH, "//div[@class='product-info-collapse-header collapsed']")))
                    except:
                        print("")

                    try:
                        element1 = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='chars-show btn btn-showmore my-4 pe-4']")))
                        print("Первый элемент виден")
                        element1.click()
                        time.sleep(1)
                    except:
                        print("Первый элемент не виден")

                    try:
                        element2 = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='sets-show btn btn-showmore my-4 pe-4']")))
                        print("Второй элемент виден")
                        element2.click()
                        time.sleep(1)
                    except:
                        print("Второй элемент не виден")

                    try:
                        element3 = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='product-info-collapse-header collapsed']")))
                        print("Третий элемент виден")
                        element3.click()
                        time.sleep(1)
                    except:
                        print("Третий элемент не виден")

                    # сохраняем страницу в файл
                    with open(f"data_{lang}/{file_name}", "w", encoding='utf-8') as file:
                        file.write(driver.page_source)

            time.sleep(10)
def parsing_product():
    # ru_files = glob.glob("C:/scrap_tutorial-master/grandinstrument/data_ru/*")
    # ua_files = glob.glob("C:/scrap_tutorial-master/grandinstrument/data_ua/*")
    # data_list_ru = []
    # data_list_ua = []
    #
    # # Для данных на русском языке
    # for ru_item in ru_files:
    #     with open(ru_item, encoding="utf-8") as file:
    #         src_ru = file.read()
    #     soup_ru = BeautifulSoup(src_ru, 'lxml')
    #     script_ru = soup_ru.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))
    #     data_ru = script_ru.text
    #     item_ru = re.search(
    #         r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
    #         data_ru, re.DOTALL)
    #     item_name_ru = item_ru.group(1)
    #     item_id = item_ru.group(2)
    #     price = item_ru.group(3)
    #     item_brand = item_ru.group(4)
    #     item_category_ru = item_ru.group(5)
    #     description_ru = soup_ru.find('div', attrs={
    #         'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip()
    #     values_ru = [prop.text.strip() for prop in soup_ru.find_all('div', class_='property-value')]
    #     data_list_ru.append(item_name_ru)
    #     data_list_ru.append(item_id)
    #     data_list_ru.append(price)
    #     data_list_ru.append(item_brand)
    #     data_list_ru.append(item_category_ru)
    #     data_list_ru.append(description_ru)
    # data_dict = {}
    # # Для данных на украинском языке
    # for ua_item in ua_files:
    #     with open(ua_item, encoding="utf-8") as file:
    #         src_ua = file.read()
    #
    #     soup_ua = BeautifulSoup(src_ua, 'lxml')
    #     script_ua = soup_ua.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))
    #     data_ua = script_ua.text
    #     item_ua = re.search(
    #         r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
    #         data_ua, re.DOTALL)
    #     item_name_ua = item_ua.group(1)
    #     item_category_ua = item_ua.group(5)
    #     description_ua = soup_ua.find('div', attrs={
    #         'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip()
    #     values_ua = [prop.text.strip() for prop in soup_ua.find_all('div', class_='property-value')]
    #     data_list_ua.append(item_name_ua)
    #     data_list_ua.append(item_category_ua)
    #     data_list_ua.append(description_ua)
    #     # Создание словаря с данными
    #     data_dict[item_id] = {
    #         "item_name_ru": item_name_ru,
    #         "item_name_ua": item_name_ua,
    #         "item_id": item_id,
    #         "price": price,
    #         "item_brand": item_brand,
    #         "item_category_ru": item_category_ru,
    #         "item_category_ua": item_category_ua,
    #         "description_ru": description_ru,
    #         "description_ua": description_ua
    #     }
    # # Запись словаря в JSON-файл
    # import json
    #
    # with open('text.json', 'a', encoding='utf-8') as f:
    #     json.dump(data_dict, f, ensure_ascii=False, indent=4)

    """Рабочая версия"""

    # Путь к файлам с данными
    ru_files = glob.glob("c:/grandinstrument/data_ru/*")

    # Открыть файл для записи данных
    with open("output_ua.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        # Записать заголовки столбцов
        # writer.writerow(
        #     ['item_name_ru', 'item_id', 'price', 'item_brand', 'item_category_ru', 'description_ru'] + ['name_ru',
        #                                                                                                 'values_ru'])
        writer.writerow(
            ['item_name_ru', 'item_id', 'img_name_1', 'img_name_2', 'item_brand', 'item_category_ru',
             'description_ru'] + ['name_ru', 'values_ru'])
        # Для данных на русском языке
        for ru_item in ru_files:
            # pri/nt(ru_item)
            try:
                with open(ru_item, encoding="utf-8") as file:
                    src_ru = file.read()
                soup_ru = BeautifulSoup(src_ru, 'lxml')
                script_ru = soup_ru.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))
                data_ru = script_ru.text
                item_ru = re.search(
                    r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
                    data_ru, re.DOTALL)
                item_name_ru = item_ru.group(1)
                item_id = item_ru.group(2)
                price = item_ru.group(3)
                item_brand = item_ru.group(4)
                item_category_ru = item_ru.group(5)
                description_ru = soup_ru.find('div', attrs={
                    'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip().replace("\n", "")
                values_ru = [prop.text.strip() for prop in soup_ru.find_all('div', class_='property-value')]
                name_ru = [prop.text.strip() for prop in soup_ru.find_all('div', class_='property-name')]

                # link_tag = soup_ru.find('link', {'itemprop': 'image'})
                # href_value = link_tag['href']
                #
                # print(href_value)
                all_link_img = []
                for link in soup_ru.find_all("a"):
                    href = link.get("href")
                    if href and href.endswith(".jpg"):
                        all_link_img.append(href)

                #Рабочий
                # all_name_img = []
                # for i, link in enumerate(all_link_img):
                #     filename = f"{item_brand}_{item_id}_{i + 1}.jpg"
                #     all_name_img.append(f'tools/{filename}')
                #     filepath = os.path.join("c:/grandinstrument/data_ru/img/", filename)
                #     if not os.path.exists(filepath):  # проверяем, существует ли файл с заданным именем
                #         # теперь можно скачать файл по ссылке и сохранить его с заданным именем
                #         # например, используя библиотеку requests:
                #         response = requests.get(link)
                #         with open(filepath, "wb") as f:
                #             f.write(response.content)

                img_name_1 = ''
                img_name_2 = ''
                all_name_img = []
                for i, link in enumerate(all_link_img):
                    filename = f"{item_id}_{item_brand}_{i + 1}.jpg"
                    all_name_img.append(f'tools/{filename}')
                    print(filename)
                    filepath = os.path.join("c:\\grandinstrument\\data_ua\\img\\", filename)
                    if not os.path.exists(filepath):  # проверяем, существует ли файл с заданным именем
                        # теперь можно скачать файл по ссылке и сохранить его с заданным именем
                        # например, используя библиотеку requests:
                        response = requests.get(link)
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                    if i == 0:
                        img_name_1 = all_name_img[0]
                    elif i == 1:
                        img_name_2 = all_name_img[1]

                img_name = ",".join(all_name_img)
                # print(img_name)
                # # Создать новую строку
                # row = [item_name_ru, item_id, img_name, item_brand, item_category_ru, description_ru]
                # Создать новую строку
                row = [item_name_ru, item_id, img_name_1, img_name_2, item_brand, item_category_ru, description_ru]




                # Добавить значения values_ru[i] и name_ru[i] к строке
                for i in range(len(values_ru)):
                    # Если значения values_ru и name_ru отсутствуют
                    if i >= len(name_ru):
                        row.append('')
                        row.append(values_ru[i].replace("\n", ""))
                    # Если значения values_ru и name_ru присутствуют
                    else:
                        row.append(name_ru[i].replace("\n", ""))
                        row.append(values_ru[i].replace("\n", ""))

                # Записать строку в файл
                writer.writerow(row)
            except:
                print("*"*100)
                print(ru_item)
                continue






        # with open(f"test.csv", "a", errors='ignore', newline='') as file:
        #     writer = csv.writer(file, delimiter=";")
        #     writer.writerow(result)
        # data_list_ru.append(item_name_ru)
        # data_list_ru.append(item_id)
        # data_list_ru.append(price)
        # data_list_ru.append(item_brand)
        # data_list_ru.append(item_category_ru)
        # data_list_ru.append(description_ru)
    #
    # # Для данных на украинском языке
    # for ua_item in ua_files[:2]:
    #     with open(ua_item, encoding="utf-8") as file:
    #         src_ua = file.read()
    #
    #     soup_ua = BeautifulSoup(src_ua, 'lxml')
    #     script_ua = soup_ua.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))
    #     data_ua = script_ua.text
    #     item_ua = re.search(
    #         r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
    #         data_ua, re.DOTALL)
    #     item_name_ua = item_ua.group(1)
    #     item_category_ua = item_ua.group(5)
    #     description_ua = soup_ua.find('div', attrs={
    #         'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip()
    #     values_ua = [prop.text.strip() for prop in soup_ua.find_all('div', class_='property-value')]
    #     data_list_ua.append(item_name_ua)
    #     data_list_ua.append(item_category_ua)
    #     data_list_ua.append(description_ua)
    #

    # print(result)
    # result = data_list_ru[0], data_list_ua[0], data_list_ru[1], data_list_ru[2], data_list_ru[3], data_list_ru[4], data_list_ua[1], data_list_ru[5], data_list_ua[2]
    # print(data_list_ru)
    # print(data_list_ua)
    # with open(f"test.csv", "w", newline=" ", errors='ignore') as file:
    #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
    #     writer.writerow(result)




    # lang = ['ua', 'ru']
    # for i in lang:
    #     targetPattern = f"C:\\scrap_tutorial-master\\grandinstrument\\data_{i}\*.html"
    #     files_html = glob.glob(targetPattern)
    #     data = []
    #     for item in files_html[:1]:
    #         with open(f"{item}", encoding="utf-8") as file:
    #             src = file.read()
    #         soup = BeautifulSoup(src, 'lxml')
    #         script = soup.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))
    #
    #         data = script.text
    #         item = re.search(
    #             r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
    #             data, re.DOTALL)
    #         item_name = item.group(1)
    #         item_id = item.group(2)
    #         price = item.group(3)
    #         item_brand = item.group(4)
    #         item_category = item.group(5)
    # #         description = soup.find('div', attrs={
    #             'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip()
    #
    #         result = [item_name, item_id, price, item_brand, item_category, description]
    #         values = [prop.text.strip() for prop in soup.find_all('div', class_='property-value')]
    #
    #         print(values)
    #         print(result)
            # for div in soup.find_all('div', {'class': 'row mx-0'}):
            #     name = div.find('div', {'class': 'property-name'})
            #     value = div.find('div', {'class': 'property-value'})
            #     if name and value:  # проверяем, что элементы существуют
            #         result.append(name.text.strip())
            #         result.append(value.text.strip())
            #
            # with open(f"test.csv", "w", errors='ignore') as file:
            #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
            #     writer.writerow(result)

if __name__ == '__main__':
    # save_link_all_product()
    parsing_product()
