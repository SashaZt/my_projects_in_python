import glob
import json
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import time
import pickle
from datetime import datetime
import zipfile
from bs4 import BeautifulSoup

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Нажатие клавиш

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

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


def get_chromedriver(use_proxy=True, user_agent=None):
    chrome_options = webdriver.ChromeOptions()

    # chrome_options.headless = True

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Включить режим инкогнито
        # chrome_options.add_argument("--incognito")

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


"""
Собираем все ссылки на товар
"""


def get_url_lot(url):
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.get(url)
    driver.maximize_window()

    time.sleep(5)
    try:
        button_coocies = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')
        if button_coocies:
            button_coocies.click()
    except:
        print("")

    time.sleep(5)
    lots_url = []
    # Листать по страницам ---------------------------------------------------------------------------
    isNextDisable = False
    while not isNextDisable:
        try:

            driver.execute_script("window.scrollBy(0,500)", "")
            time.sleep(5)
            lot_url = driver.find_elements(By.XPATH,
                                           '//div[@ng-repeat="sale in allSales"]//div[@class="listing ng-scope"]//h3//a')

            for i in lot_url:
                if i.get_attribute("href") != None:
                    lots_url.append(
                        {'url_name': i.get_attribute("href")}
                    )
            time.sleep(5)
            next_button = driver.find_element(By.XPATH, '//li[@ng-if="pagination.hasNextPage()"][1]')

            if next_button:
                print("Есть кнопка, нажимаем")
                next_button.click()
                time.sleep(5)
            else:
                print("Нет кнопки")
                isNextDisable = True
        except:
            isNextDisable = True
    # Листать по страницам ---------------------------------------------------------------------------

    with open("lot_url.json", 'w') as file:
        json.dump(lots_url, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()


def get_url_car():
    # Читание json
    with open(f"lot_url.json") as file:
        all_site = json.load(file)
    # С json вытягиваем только 'url_name' - это и есть ссылка
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.maximize_window()
    urls_car = []
    for item in all_site[:1]:

        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        time.sleep(5)
        try:
            button_coocies = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')
            if button_coocies:
                button_coocies.click()
                time.sleep(1)
        except:
            print("")

        # Листать по страницам ---------------------------------------------------------------------------
        isNextDisable = False
        while not isNextDisable:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                url_cars = driver.find_elements(By.XPATH,
                                                '//div[@class="layout__inner"]//div[@class="listing"]//div[@class="left listing__title"]//a')
                for i in url_cars:
                    urls_car.append(
                        {'url_name': i.get_attribute("href")}
                    )
                time.sleep(5)
                next_button = driver.find_element(By.XPATH,
                                                  '//nav[@class="nav nav--pagination right"]//ul//li//a[@id="nextPage"]')

                if next_button:
                    print("Есть кнопка, нажимаем")
                    next_button.click()
                    time.sleep(5)
                else:
                    print("Нет кнопки")
                    isNextDisable = True
            except:
                isNextDisable = True
            # Листать по страницам ---------------------------------------------------------------------------

    with open("car_url.json", 'w') as file:
        json.dump(urls_car, file, indent=4, ensure_ascii=False)
    driver.close()
    driver.quit()
    print('Все ссылки получены')


"""
Извлечение информации с каждой страницы html
"""


def save_html_page():
    # Читание json
    with open(f"car_url.json") as file:
        all_site = json.load(file)
    # С json вытягиваем только 'url_name' - это и есть ссылка
    driver = get_chromedriver(use_proxy=False,
                              user_agent=f"{useragent.random}")
    driver.maximize_window()
    urls_car = []
    for item in all_site[:1]:

        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        time.sleep(5)
        try:
            button_coocies = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')
            if button_coocies:
                button_coocies.click()
                time.sleep(1)
        except:
            print("")
        img_car = driver.find_elements(By.XPATH, '//div[@class="viewlot__gallery"]//li//a')
    driver.close()
    driver.quit()


if __name__ == '__main__':
    # # Собираем все ссылки на лоты
    # url = 'https://www.bcautoencheres.fr/buyer/facetedSearch/saleCalendar?cultureCode=en'
    # get_url_lot(url)
    # Парсим все товары из файлов с
    ## Собираем все ссылки на машины
    # get_url_car()
    ## Сохранить html страницу
    save_html_page()
