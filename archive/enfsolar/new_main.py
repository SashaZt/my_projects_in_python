import zipfile
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
from bs4 import BeautifulSoup

from selenium import webdriver
import random
from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = '141.145.205.4'
PROXY_PORT = 31281
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'

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


def get_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

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
    proxies = {
        'http': 'socks5://37.233.3.100:30808',
        'https': 'socks5://37.233.3.100:30808'
    }
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}
    # resp = requests.get(url, headers=header)
    # soup = BeautifulSoup(resp.text, 'lxml')
    # category_drop = soup.find('div', attrs={'class': 'dropdown-menu dropdown-menu-cd'})
    # category_url = category_drop.find_all('a')
    # url_category = []
    # for url_categorys in category_url:
    #     href_category = 'https://www.enfsolar.com' + url_categorys.get("href")
    #     url_category.append({'url_name': href_category})
    #
    # groups = []
    # for url_group in url_category:
    #     resp = requests.get(url_group['url_name'], headers=header)
    #     soup = BeautifulSoup(resp.text, 'lxml')
    #     table_grop = soup.find_all('div', attrs={'class': 'mk-section-body clearfix'})
    #
    #
    #     for url_groups in table_grop[:-1]:
    #         hrefs_group = url_groups.find_all('li', attrs={'class': 'pull-left'})
    #         for url_group in hrefs_group:
    #             href_group = url_group.find('a')
    #             url_grop = 'https://www.enfsolar.com' + href_group.get("href")
    #             groups.append({'url_name': url_grop})
    #
    # with open(f"groups.json", 'w') as file:
    #     json.dump(groups, file, indent=4, ensure_ascii=False)
    # Читание json
    with open(f"groups.json") as file:
        all_groups = json.load(file)
    # С json вытягиваем только 'url_name' - это и есть ссылка

    for item in all_groups:
        resp = requests.get(item['url_name'], headers=header, proxies=proxies)
        soup = BeautifulSoup(resp.text, 'lxml')
        # получение количевства страниц, т.е. сколько страниц на данной категории
        try:
            pagination = int(
                soup.find('ul', attrs={'class': 'pagination enf-pagination'}).find_all('a')[-2].text.strip())
        except:
            continue
        print(f"item['url_name'].split('/')[-1]")
        url_firma = []
        for list_group in range(1, pagination + 1):
            time.sleep(5)
            if list_group > 1:
                url_list_group = item['url_name'] + f"?page={list_group}"
            else:
                url_list_group = item['url_name']
            resp = requests.get(url_list_group, headers=header, proxies=proxies)
            print(resp)
            print(url_list_group)
            soup = BeautifulSoup(resp.text, 'lxml')
            table_firma = soup.find('table', attrs={'class': 'enf-list-table'})
            # Получаем таблицу всех фирм на странице
            firma_url = table_firma.find('tbody').find_all('tr')
            # Получаем ссылку на каждую фирму
            for i in firma_url:
                url = i.find_next('td').find('a').get("href")
                # Добавляем ссылки на фирмы в список
                url_firma.append({'url_name': url})
            print(f"Страница {list_group}")
        with open(f"{item['url_name'].split('/')[-1]}.json", 'w') as file:
            json.dump(url_firma, file, indent=4, ensure_ascii=False)

    # url_firma = []
    # for href in range(1, 18):
    #     if href > 1:
    #         url = f"https://www.enfsolar.com/directory/installer/other_europe?page={href}"
    #     else:
    #         url = "https://www.enfsolar.com/directory/installer/other_europe"
    #     # driver = get_chromedriver(use_proxy=True,
    #     #                           user_agent=f"{useragent.random}")
    #     header = {
    #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #         "user-agent": f"{useragent.random}"
    #
    #     }
    #     # print(url)
    #     url_country = []
    #
    #
    #     resp = requests.get(url, headers=header)
    #     soup = BeautifulSoup(resp.text, 'lxml')
    #     # soup = BeautifulSoup(driver.page_source, 'lxml')
    #     table_firma = soup.find('table', attrs={'class': 'enf-list-table'})
    #     # Получаем таблицу всех фирм на странице
    #     firma_url = table_firma.find('tbody').find_all('tr')
    #     # Получаем ссылку на каждую фирму
    #
    #     for i in firma_url:
    #         url = i.find_next('td').find('a').get("href")
    #         # Добавляем ссылки на фирмы в список
    #         url_firma.append({'url_name': url})
    #
    #
    # with open(f"url_firma.json", 'w') as file:
    #     json.dump(url_firma, file, indent=4, ensure_ascii=False)

    # table = soup.find('div', class_='mk-body')
    # table_continent = table.find_all('div', class_='clearfix mk-section')
    # for i in table_continent:
    #     driver.implicitly_wait(5)
    #     country_list = i.find_all('li', class_='pull-left')
    #     for j in country_list:
    #         href = 'https://www.enfsolar.com' + j.find_next('a').get("href")
    #         url_country.append({'url_name':href})
    #     with open(f"country_list.json", 'w') as file:
    #         json.dump(url_country, file, indent=4, ensure_ascii=False)
    #
    # for item in url_country[0:1]:
    #     with open(f"country_list.json") as file:
    #         all_site = json.load(file)
    #     driver.implicitly_wait(5)
    #     driver.get(item['url_name'])
    #     print(item)
    #     exit()
    #
    #     country = item['url_name'].strip("/")[-1]
    #     # Листать по страницам ---------------------------------------------------------------------------
    #     isNextDisable = False
    #     while not isNextDisable:
    # #         try:
    #             soup = BeautifulSoup(driver.page_source, 'lxml')
    #             table_firma = soup.find('table', attrs={'class': 'enf-list-table'})
    #             # Получаем таблицу всех фирм на странице
    #             firma_url = table_firma.find('tbody').find_all('tr')
    #             # Получаем ссылку на каждую фирму
    #             for href in firma_url:
    #                 url = href.find_next('td').find('a').get("href")
    #                 # Добавляем ссылки на фирмы в список
    #                 url_firma.append({'url_name': url})
    #             time.sleep(5)
    #             # Если необходимо подождать елемент тогда WebDriverWait
    #             # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
    #             next_button = driver.find_element(By.XPATH, '//i[@class="fa fa-chevron-right"]')
    #             # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
    #             with open(f"url_firma.json", 'a') as file:
    #                 json.dump(url_firma, file, indent=4, ensure_ascii=False)
    #             if next_button:
    #                 next_button.click()
    #                 time.sleep(2)
    #             else:
    #                 isNextDisable = True
    #         except:
    #             isNextDisable = True

    # driver.close()
    # driver.quit()


def parsing_product():
    pass
    # for href_url in url_firma:
    #     driver = get_chromedriver(use_proxy=True,
    #                               user_agent=f"{useragent.random}")
    #     driver.get(f"{href_url}")
    #     try:
    #         name_firma = driver.find_element(By.XPATH, '//h1[@itemprop="name"]').text
    #     except:
    #         name_firma = 'Нет названия фирмы'
    #     try:
    #         adress_firma = driver.find_element(By.XPATH, '//td[@itemprop="address"]').text
    #     except:
    #         adress_firma = 'Нет адресса фирмы'
    #     try:
    #         # Получение информации с атрибута, атрибут можно найти на вкладке Properties
    #         tel_firma_ = driver.find_element(By.XPATH, '//td[@itemprop="telephone"]').click()
    #         time.sleep(1)
    #         tel_firma = driver.find_element(By.XPATH, '//td[@itemprop="telephone"]').get_attribute('outerText')
    #     except:
    #         tel_firma = 'Нет телефона фирмы'
    #     try:
    #         email_firma_ = driver.find_element(By.XPATH, '//td[@itemprop="email"]').click()
    #         time.sleep(1)
    #         email_firma = driver.find_element(By.XPATH, '//td[@itemprop="email"]').get_attribute('outerText')
    #     except:
    #         email_firma = 'Нет email фирмы'
    #     try:
    #         www_firma = driver.find_element(By.XPATH, '//a[@itemprop="url"]').get_attribute('outerText')
    #     except:
    #         www_firma = 'Нет сайта фирмы'
    #     try:
    #         countrys_firma = driver.find_elements(By.XPATH, '//span[@itemprop="name"]')
    #         country_firma = countrys_firma[1].text
    #     except:
    #         countrys_firma = 'Нет страны фирмы'
    #     with open("countrys_firma.csv", "a", errors='ignore') as file:
    #         writer = csv.writer(file, delimiter=";", lineterminator="\r")
    #         writer.writerow(
    #             (
    #                 name_firma,
    #                 adress_firma,
    #                 tel_firma,
    #                 email_firma,
    #                 www_firma,
    #                 country
    #             )
    #         )


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    url = "https://www.enfsolar.com/directory/installer/other_europe"
    save_link_all_product(url)
    # Парсим все товары из файлов с
    # parsing_product()
