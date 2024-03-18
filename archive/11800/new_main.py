import csv
import glob
import json
import time
import pandas
import undetected_chromedriver
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
    product_url = []
    driver = get_undetected_chromedriver()
    driver.get(url)
    group = url.split("/")[-2]
    isNextDisable = False
    while not isNextDisable:
        try:
            # Ждем пока появится элемент, как только появляется, выполняем следующие действия
            button_find = WebDriverWait(driver, 100).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-default-highlight btn-find"]')))
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            card_product_url = driver.find_elements(By.XPATH,
                                                    '//li[@class="result-list-entry result-list-entry--clickable result-list-entry--hoverable search-result-list-item search-result-entry-item"]//div[@class="result-list-entry-wrapper mb-3 mb-md-3"]//a')
            for item in card_product_url:
                product_url.append(
                    item.get_attribute("href")
                )

            next_button = driver.find_element(By.XPATH, '//button[@class="link icon-right"]')
            # driver.execute_script("window.scrollBy(0,1500)", "")
            if next_button:
                next_button.click()
                button_find = WebDriverWait(driver, 100).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-default-highlight btn-find"]')))
            else:
                isNextDisable = True
        except:
            isNextDisable = True
    # Запись CSV по строчно
    df = pandas.DataFrame(product_url)
    df.to_csv(f"C:\\scrap_tutorial-master\\archive\\11800\\url\\{group}\\url.csv", sep=',', index=False)
    # with open(f"C:\\scrap_tutorial-master\\archive\\11800\\url\\{group}\\url_firm.csv", "a", errors='ignore') as file:
    #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
    #     writer.writerow((product_url))

    driver.close()
    driver.quit()


# Сохраняем товар в html файл
def save_html(url):
    group = url.split("/")[-2]
    driver = get_undetected_chromedriver()

    # with open(f"C:\\scrap_tutorial-master\\archive\\11800\\url\\{group}\\url_firm.json") as file:
    #     all_site = json.load(file)

    with open(f'C:\\scrap_tutorial-master\\archive\\11800\\url\\{group}\\url.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
    counter = 1
    for row in csv_reader:
        counter += 1
        # driver.get(item['url_name'])  # 'url_name' - это и есть ссылка
        driver.get(row[0])  # 'url_name' - это и есть ссылка
        try:
            next_button = WebDriverWait(driver, 100).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-default-highlight btn-find"]')))
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            time.sleep(1)
            with open(f"C:\\scrap_tutorial-master\\archive\\11800\\data\\{group}\\data_{counter}.html", "w",
                      encoding='utf-8') as fl:
                fl.write(driver.page_source)
        except:
            continue

    # С json вытягиваем только 'url_name' - это и есть ссылка

    # for item in all_site:

    driver.close()
    driver.quit()


# Парсим html файл
def pasing_html(url):
    group = url.split("/")[-2]
    datas = []
    targetPattern = fr"c:\\Temp\\data\\{group}\\*.html"
    files_html = glob.glob(targetPattern)
    with open(f"c:\\Temp\\csv\\{group}.csv", "w",
              errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Brand', 'Firm', 'Address', 'Telephone', 'email', 'web', 'services'
            )
        )
    for item in files_html:
        data_csv = []
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            brand_firn = soup.find('span', attrs={'class': 'trades-list'}).text.strip()
        except:
            brand_firn = ""
        # href_firma = soup.find('ol', attrs={'class': 'bread-crumb'}).get_attribute('itemid')
        try:
            href_firma = soup.find('ol', attrs={'class': 'bread-crumb'}).find_all('li')[2].find('span')['itemid']
        except:
            href_firma = ""

        script = soup.find_all('script', type="application/ld+json")[0]
        # script = soup.find_all('script', type="application/json")[1].text.strip()[4:-3]
        data_json = json.loads(script.string)
        name_firm = data_json['name']
        try:
            telef_firm = data_json['telephone'][0]
        except:
            telef_firm = ""
        try:
            email_firm = data_json['email']
        except:
            email_firm = ""
        try:
            url_firm = data_json['url']
        except:
            url_firm = ""
        try:
            postalCode = data_json['address']['postalCode']
        except:
            postalCode = ""
        try:
            addressLocality = data_json['address']['addressLocality']
        except:
            addressLocality = ""
        try:
            addressRegion = data_json['address']['addressRegion']
        except:
            addressRegion = ""
        try:
            streetAddress = data_json['address']['streetAddress']
        except:
            streetAddress = ""
        adress_firma = f"{postalCode}, {addressLocality}, {addressRegion}, {streetAddress}"

        try:
            servises_firma_1 = soup.find_all('div', attrs={'class': 'term-box__panel-content'})[0].find('div', attrs={
                'class': 'row'}).find_all('div')
        except:
            servises_firma_1 = ""

        try:
            servises_firma_2 = soup.find_all('div', attrs={'class': 'term-box__panel-content'})[1].find('div', attrs={
                'class': 'row'}).find_all('div')
        except:
            servises_firma_2 = ""
        all_s1 = []
        for s1 in servises_firma_1:
            all_s1.append(s1.text)
        servises_firma_01 = ",".join(all_s1)
        all_s2 = []
        for s2 in servises_firma_2:
            all_s2.append(s2.text)
        servises_firma_02 = ",".join(all_s2)
        servise = f'{servises_firma_01}, {servises_firma_02}'
        with open(f"c:\\Temp\\csv\\{group}.csv", "a",
                  errors='ignore', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    group, name_firm, adress_firma, telef_firm, email_firm, url_firm, servise
                )
            )


if __name__ == '__main__':
    url = "https://www.11880.com/suche/Volvo/deutschland"
    # save_link_all_product(url)
    # ######################save_html(url)
    pasing_html(url)
