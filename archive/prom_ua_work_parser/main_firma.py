import glob
import zipfile
import os
import json
from bs4 import BeautifulSoup
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
PROXY_PORT = 31281  # Без кавычек
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

def save_html():
    url = "https://prom.ua/ua/Avto-moto"
    coun = 1
    driver = get_chromedriver(use_proxy=True,
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    for i in range(80,346):

        if i == 1:
            driver.get(url=url)
            driver.maximize_window()
            time.sleep(1)
            driver.execute_script("window.scrollBy(0,3500)", "")
            time.sleep(5)
            # button_wait_cookies = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, '//a[@data-qaid="next_page"]')))
            with open(f"C:\\scrap_tutorial-master\\prom_ua_work_parser\\{i}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
        if i > 1:
            driver.get(url=f'{url};{i}')
            driver.maximize_window()
            time.sleep(1)
            driver.execute_script("window.scrollBy(0,3500)", "")
            time.sleep(5)
            # button_wait_cookies = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, '//a[@data-qaid="next_page"]')))
            with open(f"C:\\scrap_tutorial-master\\prom_ua_work_parser\\{i}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
    driver.close()
    driver.quit()

def parsing_urls_is_html():
    targetPattern = r"c:\prom_firma_url\*.html"
    files_html = glob.glob(targetPattern)
    urls = []
    for item in files_html:
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        urls_firmas = soup.find_all('div', attrs={'class': 'M3v0L BXDW- qzGRQ aO9Co'})
        for j in urls_firmas:
            i = j.find('a').get('href')
            urls.append(i)
    with open(f'C:\\scrap_tutorial-master\\prom_ua_work_parser\\url_firma.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
        writer.writerow(urls)

def save_html_firma():
    urls = [

    ]
    with open('url_firma.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in csv_reader:
            urls.append(row[0])
    driver = get_chromedriver(use_proxy=True,
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    coun = 418
    for item in urls[418:]:
        coun += 1
        driver.get(item)  # 'url_name' - это и есть ссылка
        driver.maximize_window()
        button_wait_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-qaid="contacts_btn"]')))
        button_contact = driver.find_element(By.XPATH, '//button[@data-qaid="contacts_btn"]').click()
        time.sleep(5)
        with open(f"c:\\prom_fitma\\0_{coun}.html", "w",
                  encoding='utf-8') as file:
            file.write(driver.page_source)
    driver.close()
    driver.quit()

def parsin_contact():
    targetPattern = r"c:\prom_fitma\*.html"
    files_html = glob.glob(targetPattern)
    urls = []
    for item in files_html:
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            name_company = soup.find('a', attrs={'data-qaid': 'qa_company_title'}).text
        except:
            name_company = ""
        try:
            www_company_find = soup.find('a', attrs={'data-qaid': 'qa_company_title'}).get("href")
            www_company = f'prom.ua{www_company_find}'
        except:
            www_company = ""

        phones_all = []
        try:
            phones_company = soup.find_all('a', attrs={'data-qaid': 'phone'})
            for h in phones_company:
                phones_all.append(h.text)
            # Обьеденяим их в одну сроку, разделитель указываем в начале
            phone = " ; ".join(phones_all)
        except:
            phone = ""
        try:
            email_company = soup.find('a', attrs={'data-qaid': 'email_btn'}).text
        except:
            email_company = ""
        with open(f"C:\\scrap_tutorial-master\\prom_ua_work_parser\\datas.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_company, phone, email_company, www_company

                )
            )


if __name__ == '__main__':
    # save_html()
    # parsing_urls_is_html()
    # save_html_firma()
    parsin_contact()
