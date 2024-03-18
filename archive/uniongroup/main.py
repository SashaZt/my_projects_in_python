import zipfile
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import csv
import time
import glob

# Нажатие клавиш

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver

from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

useragent = UserAgent()

# Данные для прокси
PROXY_HOST = 'IP'
PROXY_PORT = 'PORT' #Без кавычек
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
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.get(url=url)

    driver.maximize_window()
    driver.execute_script("window.scrollBy(0,1000)", "")
    categoriy_product_urls = []


    categoriy_product_url = driver.find_elements(By.XPATH, '//div[@class="catalog-categories"]//div[@class="catalog-categories-box"]//a')
    for item_categoriy in categoriy_product_url:
        category = item_categoriy.get_attribute("textContent").strip().replace("/", "_")
        categoriy_product_urls.append(
            {'url_name': item_categoriy.get_attribute("href"),
             'title_group': category}
        )
        # with open(f"C:\\scrap_tutorial-master\\uniongroup\\link\\{category}.json", 'w') as file:
        #     json.dump(card_product_url_all, file, indent=4, ensure_ascii=False)


    for item_pod_categ in categoriy_product_urls:
        driver.get(item_pod_categ['url_name'])
        card_product_url_all = []

        # Листать по страницам ---------------------------------------------------------------------------
        isNextDisable = False
        while not isNextDisable:

            try:
                product_urls = driver.find_elements(By.XPATH,
                                                    '//div[@class="categories-wrap"]//div[@class="categories-box"]//a[@class="card-of-item"]')
                group_product = driver.find_element(By.XPATH, '//ul[@class="breadcrumb breadcrumb-card"]//li[2]').text.replace("» ", "").replace("/", "_")
                for h in product_urls:
                        card_product_url_all.append(
                            {'url_name': h.get_attribute("href")}
                        )
                # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                pagan_next = driver.find_element(By.XPATH, '//div[@class="nav-links"]//a[@class="next page-numbers"]')
                if pagan_next:
                    pagan_next.click()
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------
        print(group_product)
        with open(f"C:\\scrap_tutorial-master\\uniongroup\\link\\{group_product}.json", 'w') as file:
            json.dump(card_product_url_all, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()



def parsing_product():
    # Получаем список файлов с сылками на товары
    targetPattern = r"c:\scrap_tutorial-master\uniongroup\link\*.json"
    files_json = glob.glob(targetPattern)

    for item in files_json:
        with open(f"{item}") as file:
            all_site = json.load(file)

        driver = get_chromedriver(use_proxy=False,
                                  user_agent=f"{useragent.random}")

        group = item.replace(".json", "").split("\\")[-1].replace(" ", "_")
        with open(f"C:\\scrap_tutorial-master\\uniongroup\\data\\{group}.csv", "w", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    'name_product', 'card_code', 'art_product', 'cart_product', 'cart_list', 'desc_product', 'Общая информация', 'Размер и вес товара', 'Размер и вес товара в упаковке', 'link_img'
                )
            )
        # Переходим по каждой ссылке товара и получаем данные
        for href_card in all_site:
            driver.get(href_card['url_name'])  # 'url_name' - это и есть ссылка
            driver.maximize_window()
            try:
                name_product = driver.find_element(By.XPATH, '//div[@class="card-title-box"]/h2').text
            except:
                name_product = 'Not name_product'
            try:
                card_code = driver.find_element(By.XPATH, '//div[@class="card-title-box"]/span').text.replace("код ", "")
            except:
                card_code = "Not card_code"
            try:
                art_product = driver.find_element(By.XPATH, '//div[@class="card-desc"]//p[@class="card-article"]').get_attribute("textContent").replace("Артикул: ", "")
            except:
                art_product = 'Not art_product'
            try:
                cart_product = driver.find_element(By.XPATH, '//div[@class="card-desc"]//div[@class="card-text"]').text
            except:
                cart_product = 'Not cart_product'
            try:
                cart_list = driver.find_element(By.XPATH, '//ul[@class="card-list"]').get_attribute('textContent').replace("\n", "").replace("\t", "")
            except:
                cart_list = 'Not cart_list'
            try:
                desc_product = driver.find_element(By.XPATH, '//div[@class="card-tabs-change card-tabs-desc is-active"]').get_attribute('outerText').replace("\n", "").replace("\t", "")
            except:
                desc_product = 'Not desc_product'
            all_link_img = []
            imgs_product = driver.find_elements(By.XPATH, '//div[@class="fotorama__nav__shaft fotorama__grab"]//div//img')
            imgs_product_02 = driver.find_elements(By.XPATH, '//div[@class="fotorama__nav__shaft"]//div//img')
            if imgs_product:
                imgs_product = driver.find_elements(By.XPATH,
                                                    '//div[@class="fotorama__nav__shaft fotorama__grab"]//div//img')
                for h in imgs_product:
                    all_link_img.append(h.get_attribute("src"))
                    # Обьеденяим их в одну сроку, разделитель указываем в начале
                link_img = " ; ".join(all_link_img)
            elif imgs_product_02:
                imgs_product = driver.find_elements(By.XPATH, '//div[@class="fotorama__nav__shaft"]//div//img')
                for h in imgs_product:
                    all_link_img.append(h.get_attribute("src"))
                    # Обьеденяим их в одну сроку, разделитель указываем в начале
                link_img = ", ".join(all_link_img) #Для Prom.ua только такой разделитель

            values = driver.find_elements(By.XPATH, '//ul[@class="card-tabs-spec-list"]//p[@class="card-tabs-spec-subtitle"]')
            try:
                ch_01 = values[0].get_attribute("outerText").replace("\n", "").replace("\t", "")
            except:
                ch_01 = "Not ch_01"
            try:
                ch_02 = values[1].get_attribute("outerText").replace("\n", "").replace("\t", "")
            except:
                ch_02 = "Not ch_02"
            try:
                ch_03 = values[2].get_attribute("outerText").replace("\n", "").replace("\t", "")
            except:
                ch_03 = "Not ch_03"


            with open(f"C:\\scrap_tutorial-master\\uniongroup\\data\\{group}.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow(
                    (
                        name_product, card_code, art_product, cart_product, cart_list, desc_product, ch_01, ch_02, ch_03,link_img

                    )
                )
        print(group)

        driver.close()
        driver.quit()


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    # url = "https://uniongroup.com.ua/catalog/"
    # save_link_all_product(url)
    #Парсим все товары из файлов с
    parsing_product()