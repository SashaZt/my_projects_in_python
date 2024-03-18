import zipfile
import csv
import re
import os
import glob
import json
import time
import pandas
import undetected_chromedriver as UC
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait

# Данные для прокси
PROXY_HOST = '141.145.205.4'
PROXY_PORT = 31281
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'
''

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
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )
    driver.delete_all_cookies()
    return driver

def get_undetected_chromedriver(use_proxy=False, user_agent=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = UC.Chrome(service=s, options=chrome_options)
    # driver.delete_all_cookies()

    return driver


# Получаем все ссылки на необходимый товар
def save_html():
    urls = [

    ]
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in csv_reader:

            urls.append(row[0])

    for item in urls[56:58]:

        driver = get_chromedriver(use_proxy=False,
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        driver.get(item)  # 'url_name' - это и есть ссылка
        group = item.split("/")[-2]
        driver.maximize_window()
        try:
            button_wait_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@id="cmpbntyestxt"]')))
            button_cookies = driver.find_element(By.XPATH, '//span[@id="cmpbntyestxt"]').click()
        except:
            print(f"{group}")
        time.sleep(1)
        isNextDisable = False
        while not isNextDisable:
            try:
                driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                next_button = driver.find_element(By.XPATH, '//a[@class="mod-LoadMore--button"]')
                driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                if next_button:
                    next_button.click()
                    time.sleep(1)
                    driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
                else:
                    isNextDisable = True
            except:
                isNextDisable = True
        with open(f"C:\\scrap_tutorial-master\\gelbeseiten.de\\html\\{group}.html", "w",
                  encoding='utf-8') as file:
            file.write(driver.page_source)

    driver.close()
    driver.quit()


# Сохраняем товар в html файл
def parser_url_html():
    targetPattern = r"C:\scrap_tutorial-master\gelbeseiten.de\html\*.html"
    files_html = glob.glob(targetPattern)

    for item in files_html:
        data = []
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
            print(item)
        group = item.replace(".html", "").split("\\")[-1]
        soup = BeautifulSoup(src, 'lxml')
        regex_cart = re.compile('mod mod-Treff.*')
        urls_firma = soup.find_all('article', attrs={'class': regex_cart})
        for i in urls_firma:
            try:
                data.append(i.find('a').get("href"))
                print(i.find('a').get("href"))
            except:
                continue
        # Запись csv файла  по строчно
        with open(f'C:\\scrap_tutorial-master\\gelbeseiten.de\\url\\{group}.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
            writer.writerow(data)



# Парсим html файл
def pasing_url():
    """
    autoSattlereien
    Autotuning
    Autowäsche
    Bentley
    BMW
    Cadillac
    Chevrolet
    Chrysler
    Citroen
    Dacia
    Daewoo
    Fahrzeugaufbereitung
    Fahrzeugbau
    Fahrzeugbeschriftungen
    Fahrzeugelektrik
    Fahrzeuginnenausstattungen
    Fahrzeuglackierereien
    Fahrzeugpflege
    Ferrari
    Fiat
    Ford
    Honda
    Hummer
    Hyundai
    Infiniti
    Isuzu
    Jaguar
    Jeep
    Kfz-Reparaturen
    Kfz-Sachverständige
    Kfz-Werkstätten
    Kia
    Lamborghini
    Lancia
    suche
    Lexus
    Maserati
    Maybach
    Mazda
    McLaren
    Mercedes
    Mini
    Mitsubishi
    Nissan
    Opel
    Peugeot
    PKW
    Porsche
    Reifenservice
    Renault
    Rolls-Royce
    Saab
    Seat
    Skoda
    Smart
    Ssangyong
    Subaru
    Suzuki
    Tesla
    Toyota
    Tuning
    Volkswagen
    Volvo
    """
    """
    Ручной парсинг
    """
    group = "Volvo"
    urls = [

    ]
    with open(f'C:\\scrap_tutorial-master\\gelbeseiten.de\\url\\{group}.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in csv_reader:
            urls.append(row[0])
    count = 0
    for item in urls:
        count += 1
        driver = get_chromedriver(use_proxy=False,
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        driver.get(item)  # 'url_name' - это и есть ссылка

        driver.maximize_window()
        try:
            button_wait_cookies = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@id="cmpbntyestxt"]')))
            button_cookies = driver.find_element(By.XPATH, '//span[@id="cmpbntyestxt"]').click()
        except:
            print("")
        try:
            button_wait = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//h1[@class="mod-TeilnehmerKopf__name"]')))
            with open(f"c:\\html_data\\{group}\\_data_{count}.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
        except:
            continue

def parsing_html():
    # urls = [
    #
    # ]
    # with open('url.csv', newline='', encoding='utf-8') as files:
    #     csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
    #     for row in csv_reader:
    #         urls.append(row[0])
    # for i in urls:
    #     t = i.split("/")[-2]
    #     # print(t)
    group = "Land Rover"
    datas = []
    targetPattern = fr"c:\\html_data\\{group}\\*.html"
    files_html = glob.glob(targetPattern)
    with open(f"c:\\scrap_tutorial-master\\gelbeseiten.de\\csv\\{group}.csv", "w",
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
            brand_firma = soup.find('span', attrs={'data-selenium': 'teilnehmerkopf__branche'}).text
        except:
            brand_firma = ""

        script_1 = soup.find_all('script', type="application/ld+json")[1]
        script_2 = soup.find_all('script', type="application/ld+json")[2]
        try:
            data_json_1 = json.loads(script_1.string)
        except:
            data_json_1 = ""
        """
        Собираем информацию прямо из json структуры
        """
        try:
            script_div = soup.find('div', attrs={'class': 'mod mod-Chat contains-icon-chatlight'})['data-parameters']
        except:
            script_1 = ''
        data_json_2 = json.loads(script_2.string)
        try:
            data_json_div = json.loads(script_div)
        except:
            data_json_div = ""
        try:
            email = data_json_div['inboxConfig']['organizationQuery']['generic']['email']
        except:
            email = ""
        try:
            telephone = data_json_2['telephone']
        except:
            telephone = ""
        try:
            faxNumber = data_json_2['faxNumber']
        except:
            faxNumber = ""
        try:
            name_firm = data_json_2['name']
        except:
            name_firm = ""
        try:
            address_postalCode = data_json_2['address']['postalCode']
        except:
            address_postalCode = ""
        try:
            address_addressLocality = data_json_2['address']['addressLocality']
        except:
            address_addressLocality = ""
        try:
            address_streetAddress = data_json_2['address']['streetAddress']
        except:
            address_streetAddress = ""
        Address = f'{address_streetAddress} {address_postalCode} {address_addressLocality}'
        try:
            web = data_json_2['sameAs']
        except:
            web = ""
        try:
            services = data_json_2['keywords']
        except:
            services = ""
        with open(f"C:\\scrap_tutorial-master\\gelbeseiten.de\\csv\\{group}.csv", "a",
                  errors='ignore', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    group, name_firm, Address, telephone, email, web, services
                )
            )




if __name__ == '__main__':
    # save_html()
    # parser_url_html()
    # pasing_url()
    # ######################save_html(url)
    parsing_html()
