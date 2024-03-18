import csv
import re
import glob
import requests
import json
import time
import zipfile
import pandas
import undetected_chromedriver
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium import webdriver

from fake_useragent import UserAgent

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")

    driver = undetected_chromedriver.Chrome()

    return driver


# Получаем все ссылки на необходимый товар
def save_link_all_product(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

    }
    product_url = []
    resp = requests.get(url, headers=header)
    soup = BeautifulSoup(resp.text, 'lxml')
    regex_table = re.compile('slick-slide*')
    urls = soup.find_all('div', attrs={'class': 'col col-9 text-truncate'})
    for i in urls:
        product_url.append(
            {'url_name': f'https://uk.tgstat.com/{i.find("a").get("href")}'}
        )
        with open(f"url_category.json", 'w') as file:
            json.dump(product_url, file, indent=4, ensure_ascii=False)


# Сохраняем товар в html файл
def save_category_html():
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

    }
    with open(f"url_category.json") as file:
        all_site = json.load(file)
    driver = get_chromedriver(use_proxy=False,
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    for item in all_site:

        driver.maximize_window()
        driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        category = driver.find_element(By.XPATH, '//h1[@class="text-dark mt-2 text-center"]').text
        # Листать по страницам ---------------------------------------------------------------------------
        isNextDisable = False
        while not isNextDisable:
            try:
                driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                driver.implicitly_wait(2)
                next_button = driver.find_element(By.XPATH,
                                                  '//button[@class="btn btn-light border lm-button py-1 min-width-220px"]')
                # Проверка на наличие кнопки следующая страница, если есть, тогда листаем!
                if next_button:
                    next_button.click()
                    driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                    driver.implicitly_wait(2)
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        # Листать по страницам ---------------------------------------------------------------------------
        with open(f"data_{category}.html", "w", encoding='utf-8') as fl:
            fl.write(driver.page_source)
    driver.close()
    driver.quit()


def pasing_html():
    datas = []
    targetPattern = r"C:\\scrap_tutorial-master\\tgstat.ru\\*.html"
    files_html = glob.glob(targetPattern)
    url_category = []
    for item in files_html:

        group = item.split("\\")[-1].replace('.html', '')
        driver = get_chromedriver(use_proxy=False,
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
        # driver.maximize_window()
        driver.get(item)  # 'url_name' - это и есть ссылка
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        urls = driver.find_elements(By.XPATH, '//div[@class="col-12 col-sm-6 col-md-4"]//a')
        for i in urls:
            url_category.append(
                {'url_name': i.get_attribute("href")}
            )
    df = pandas.DataFrame(url_category)
    df.to_csv(f"url_all.csv", sep=',', index=False)
    # with open(f"url_all.json", 'a') as file:
    #     json.dump(url_category, file, indent=4, ensure_ascii=False)


def pars_group_url():
    # Получаем список файлов с сылками на товары
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

    }
    targetPattern = r"C:\\scrap_tutorial-master\\tgstat.ru\\*.json"
    files_json = glob.glob(targetPattern)
    # По очереди json файл открывает
    # driver = get_chromedriver(use_proxy=False,
    #                           user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    for item in files_json[18:]:
        group = item.split("\\")[-1].replace('.json', '')

        data = []
        with open(f"{item}") as file:
            all_site = json.load(file)

        # Внутри json файла открывает ссылки
        for href_card in all_site:
            resp = requests.get(href_card['url_name'], headers=header)
            soup = BeautifulSoup(resp.text, 'lxml')
            try:
                href_soup = soup.find('div', attrs={'class': 'text-center text-sm-left'}).find('a').get("href")
            except:
                href_soup = href_card['url_name']

            # driver.get(href_card['url_name'])  # 'url_name' - это и есть ссылка
            # driver.maximize_window()
            # href = driver.find_element(By.XPATH, '//div[@class="text-center text-sm-left"]//a').get_attribute("href")
            with open(f"tg_.csv", "a", errors='ignore') as file:
                writer = csv.writer(file, delimiter=";", lineterminator="\r")
                writer.writerow((
                    href_soup, group
                ))

    # driver.close()
    # driver.quit()


def parsing():
    """Парсим уже из готовых html страничек"""
    targetPattern = fr"c:\\DATA_TG\\*.html"
    files_html = glob.glob(targetPattern)

    for item in files_html:

        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            href_soup = soup.find('div', attrs={'class': 'text-center text-sm-left'}).find('a').get("href")
        except:
            href_soup = item
        try:
            categ = soup.find('div', attrs={'class': 'text-left text-sm-right'}).find('div', attrs={
                'class': 'mt-2'}).find('a').text
        except:
            categ = item
        # print(categ)
        with open(f"C:\\scrap_tutorial-master\\tgstat.ru\\tg_.csv", "a",
                  errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    href_soup, categ
                )
            )


if __name__ == '__main__':
    # url = "https://uk.tgstat.com/"
    # save_link_all_product(url)
    # save_category_html()
    # ######################save_html(url)
    # pasing_html()
    # pars_group_url()
    parsing()
