import zipfile
import pickle
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
from selenium.webdriver.common.keys import Keys
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
import undetected_chromedriver

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
def get_undetected_chromedriver(use_proxy=False, user_agent=None):
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
    # driver = get_undetected_chromedriver(use_proxy=True, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    driver = get_undetected_chromedriver()
    driver.get(url=url)
    time.sleep(10)
    # Блок работы с куками-----------------------------------------
    # Создание куки
    # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
    # Читание куки

    # Блок работы с куками-----------------------------------------
    for i in range(1, 50):
        # for cookie in pickle.load(open("cookies", "rb")):
        #     driver.add_cookie(cookie)
        driver.get(url + f'&page={i}')

        driver.maximize_window()
        time.sleep(20)
        # try:
        #     appy_botton = driver.find_element(By.XPATH,
        #                                       '//button[@class="MuiButtonBase-root MuiButton-root MuiButton-text MuiButton-textPrimary MuiButton-sizeMedium MuiButton-textSizeMedium css-15hdkn7"]').click()
        # except:
        #     appy_botton = print('!')
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(5)
        with open(f"data_{i}.html", "w", encoding='utf-8') as file:
            file.write(driver.page_source)
    exit()

    products_all_url = []
    categoriy_product_urls = []
    pod_categoriy_product_urls = []
    card_product_url_all = []
    categoriy_product_url = driver.find_elements(By.XPATH, '//ul[@class="menu-list"]//li[@id="menu-id"]/a')
    for item_categoriy in categoriy_product_url:
        time.sleep(1)

        categoriy_product_urls.append(
            {'url_name': item_categoriy.get_attribute("href")}
        )

    for item_pod_categ in categoriy_product_urls:
        time.sleep(1)

        driver.get(item_pod_categ['url_name'])
        pod_categ_product_url = driver.find_elements(By.XPATH, '//div[@class="rubric"]//ul[@class="rubric-list"]//a')
        for item_card in pod_categ_product_url:
            pod_categoriy_product_urls.append(
                {'url_name': item_card.get_attribute("href")}
            )

    for item_prod in pod_categoriy_product_urls:
        # time.sleep(1)

        driver.get(item_prod['url_name'])
        print(item_prod['url_name'])
        time.sleep(5)
        # group_product = item_prod['url_name'].split("/")[-1]
        # pagan = int(driver.find_element(By.XPATH,
        #                                 '//div[@class="pager add-more-pages"]//ul[@class="pager__list"]//li[@class="last"]').text)
        # # Листание по страницам
        # for page in range(1, pagan + 1):
        #     products_all_url = []
        #     if page == 1:
        #         driver.get(item_prod['url_name'])
        #     if page > 1:
        #         driver.get(item_prod['url_name'] + f"?page={page}")
        #     time.sleep(1)
        #     products_01 = driver.find_elements(By.XPATH,'//div[@class="catalog__product-list-row"]//div[@class="product-card__layout-inside"]//div[@class="product-card__layout-inside-link"]//div[@class="advanced-tile-on"]//a')
        #     products_02 = driver.find_elements(By.XPATH,'//div[@class="catalog__product-list-row"]//div[@class="product-card__layout-inside"]//div[@class="product-card__layout-inside-link"]//div[@class="advanced-tile-off"]//a')
        #     if products_01:
        #         products = products_01
        #     elif products_02:
        #         products = products_02
        #
        #     for href in products:
        #         products_all_url.append(
        #             {'url_name': href.get_attribute("href"),
        #              'title_group': f'{group_product}'
        #              }
        #         )
        #     with open(f"C:\\scrap_tutorial-master\\dok.ua\\link\\{group_product}.json", 'a') as file:
        #         json.dump(products_all_url, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()

    # # Листать по страницам ---------------------------------------------------------------------------
    # isNextDisable = False
    # while not isNextDisable:
    #     try:
    #         # driver.execute_script("window.scrollBy(0,500)", "")
    #         next_button = driver.find_element(By.XPATH, '//div[@class="pager add-more-pages"]//button')
    #         next_button = driver.find_element(By.XPATH, '//div[@class="pager add-more-pages"]//button[@id="add-more"]')
    #         next_button = driver.find_element(By.XPATH, '//ul[@class="pager__list"]//li[@class="next"]')
    #         # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
    #         if next_button:
    #             next_button.click()
    #             # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #             time.sleep(2)
    #         else:
    #             isNextDisable = True
    #     except:
    #         isNextDisable = True
    # # Листать по страницам ---------------------------------------------------------------------------


def parsing_product():
    targetPattern = r"c:\scrap_tutorial-master\dubai\data\*.html"
    files_html = glob.glob(targetPattern)
    data = []
    for item in files_html[26:27]:
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        print(item)
        soup = BeautifulSoup(src, 'lxml')
        card_all = soup.find_all('div', attrs={'class': 'sc-cmkc2d-0 dhbOk'})
        for cards in card_all:
            try:
                img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('img').get('src')
            except:
                img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('span').find('img').get('src')
            # На странице 33 и 34 установить два условия
            # img_card = cards.find('div', attrs={'data-testid': 'image-gallery'}).find('img').get('src')
        print(img_card)

    #
    #         km_avto = cards.find('div', attrs={'data-testid': 'listing-kms'}).text
    #         try:
    #             color_avto = cards.find('div', attrs={'data-testid': 'listing-color'}).text
    #         except:
    #             color_avto = "Not color"
    #         try:
    #             price_avto = cards.find('div', attrs={'class': 'sc-11jo8dj-1 cpHdIU'}).text
    #         except:
    #             price_avto = "Not color"
    #         data.append({
    #             'Пробег' : km_avto,
    #             'Цвет' : color_avto,
    #             'Цена': price_avto,
    #             'Фото': img_card
    #         })
    # with open('data.json', 'w', encoding="utf-8") as file:
    #     json.dump(data, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # # Собираем все ссылки на категории товаров
    # url = "https://dubai.dubizzle.com/motors/used-cars/toyota/?kilometers__lte=100000&ads_posted=1673567999"
    # save_link_all_product(url)
    # Парсим все товары из файлов с
    parsing_product()
