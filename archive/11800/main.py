import pickle
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
    with open('info.txt', 'r') as f:
        nums = f.read().splitlines()
    for i in nums:
        if os.path.exists(f"1.json"):
            print(f"C:\\scrap_tutorial-master\\11800\\{i}.json" + " уже существует")
    else:
        driver = get_chromedriver(use_proxy=True,
                                  user_agent=f"{useragent.random}")

        # Блок работы с куками-----------------------------------------

        product_url = []
        # Читаем с файла слова которые необходимо прозводить поиск построчно!
        with open('info.txt', 'r') as f:
            nums = f.read().splitlines()
        for i in nums:
            driver.get(url)
            driver.implicitly_wait(5)

            # Блок работы с куками-----------------------------------------
            # Создание куки
            # pickle.dump(driver.get_cookies(), open("cookies", "wb"))
            # Читание куки
            for cookie in pickle.load(open("cookies", "rb")):
                driver.add_cookie(cookie)
            driver.refresh()
            field_find = driver.find_element(By.XPATH, '//*[@id="form-search-and-find"]/div/search-part[1]/div/input')
            field_find
            field_button = driver.find_element(By.XPATH, '//*[@id="form-search-and-find"]/div/div[1]/button')
            field_button.click()

            isNextDisable = False
            while not isNextDisable:
                try:
                    # ----------------------------------------------------------
                    # Если необходимо сначала прогрузить все товары тогда открываем все и только потом получаем ссылки
                    # Сначала что то ищем на первой странице, а только потом ищем на остальных
                    card_product_url = driver.find_elements(By.XPATH,
                                                            '//div[@class="result-list-entry-wrapper mb-3 mb-md-3"]/a')
                    for item in card_product_url[0:16]:
                        product_url.append(
                            {'url_name': item.get_attribute("href")}
                            # Добавляем в словарь два параметра для дальнейшего записи в json
                        )
                    # Если необходимо подождать елемент тогда WebDriverWait
                    # next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//i[@class="fa fa-chevron-right"]')))
                    # driver.implicitly_wait(5)
                    # Опускаемя в самый низ страницы
                    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    next_button = driver.find_element(By.XPATH, '//button[@class="link icon-right"]')
                    driver.execute_script("window.scrollBy(0,1200)", "")
                    # Прокручиваем пока не найдем элемент
                    # driver.execute_script("arguments[0].scrollIntoView();",next_button)
                    # # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    if next_button:
                        next_button.click()
                    else:
                        isNextDisable = True
                except:
                    isNextDisable = True
            # Листать по страницам ---------------------------------------------------------------------------
            with open(f"C:\\scrap_tutorial-master\\11800\\{i}.json", 'w') as file:
                json.dump(product_url, file, indent=4, ensure_ascii=False)
            driver.close()
            driver.quit()
        # Попробовать не возвращать список
        # return product_url


def parsing_product():
    driver = get_chromedriver(use_proxy=True,
                              user_agent=f"{useragent.random}")
    with open(f"C:\\scrap_tutorial-master\\11800\\Alfa-Romeo.json") as file:
        all_site = json.load(file)
    with open(f"C:\\scrap_tutorial-master\\11800\\Alfa-Romeo.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_company',
                'adr_company',
                'tel_company',
                'tel_company_02',
                'email_company',
                'www_company',
                'link_company',
                'social_company'

            )
        )
    # С json вытягиваем только 'url_name' - это и есть ссылка
    product_sum = 0
    for item in all_site:
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        try:
            tel_company = driver.find_element(By.XPATH, '//*[@id="entry"]/div[4]/div[1]/div/div[1]/a/div[2]').text
            # .replace('"', '').replace('/ №', '').replace('*', '_')  # удаляем из названия следующие символы
        except:
            tel_company = 'No phone'
        try:
            tel_company_02 = driver.find_element(By.XPATH, '//*[@id="kontakt"]').text.replace("\n", ", ")
            # .replace('"', '').replace('/ №', '').replace('*', '_')  # удаляем из названия следующие символы
        except:
            tel_company_02 = 'No phone additionally'
        try:
            name_company = driver.find_element(By.XPATH, '//*[@id="entry"]/div[1]/div[1]/h1').text
        except:
            name_company = driver.find_element(By.XPATH, '//*[@id="entry"]/div[2]/div[1]/h1').text
        try:
            email_company = driver.find_element(By.XPATH, '//*[@id="box-email-link"]/div[2]').text
            # .replace("\n", "")  # Убираем перенос с описания
        except:
            email_company = "No email"
        try:
            www_company = driver.find_element(By.XPATH, '//*[@id="entry"]/div[4]/div[2]/div/div[2]/a/div[2]').text

        except:
            www_company = driver.find_element(By.XPATH, '//*[@id="entry"]/div[5]/div[2]/div/div[2]/a/div[2]').text

        try:
            adr_company = driver.find_element(By.XPATH,
                                              '//*[@id="entry"]/div[4]/div[1]/div/div[3]/div/div[2]/span').text.replace(
                "\n", "")
        except:
            adr_company = driver.find_element(By.XPATH,
                                              '//*[@id="entry"]/div[5]/div[1]/div/div[3]/div/div[2]/span').text.replace(
                "\n", "")

        try:
            social_company = driver.find_element(By.XPATH,
                                                 '//*[@id="entry"]/div[5]/div[2]/div/div[3]/a').get_attribute("href")
        except:
            social_company = 'No social'

        with open(f"C:\\scrap_tutorial-master\\11800\\Alfa-Romeo.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_company,
                    adr_company,
                    tel_company,
                    tel_company_02,
                    email_company,
                    www_company,
                    item['url_name'],
                    social_company

                )
            )

    driver.close()
    driver.quit()


if __name__ == '__main__':
    ##Сайт на который переходим
    # url = "https://www.11880.com/"
    ## Запускаем первую функцию для сбора всех url на всех страницах
    # save_link_all_product(url)
    parsing_product()
