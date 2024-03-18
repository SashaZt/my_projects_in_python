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
    url = "https://panoramafirm.pl/fryzjerzy_i_salony_fryzjerskie"
    coun = 0
    time.sleep(1)
    driver = get_chromedriver(use_proxy=False,
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    for i in range(10,201):
        if i == 1:
            driver.get(url=url)
            driver.maximize_window()
            try:
                button_wait_cookies = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]')))
                button_cookies = driver.find_element(By.XPATH,
                                                     '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]').click()
            except:
                print("")
            driver.execute_script("window.scrollBy(0,5000)", "")
            time.sleep(1)

            with open(f"c:\\Data_panoramafirm.pl\\0_{i}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
        if i > 1:
            driver.get(url=f'{url}/firmy,{i}.html')
            driver.maximize_window()
            time.sleep(1)
            try:
                button_wait_cookies = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]')))
                button_cookies = driver.find_element(By.XPATH,
                                                     '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]').click()
            except:
                print("")
            driver.execute_script("window.scrollBy(0,5000)", "")
            time.sleep(1)
            with open(f"c:\\Data_panoramafirm.pl\\0_{i}.html", "w",
                      encoding='utf-8') as file:
                file.write(driver.page_source)
    driver.close()
    driver.quit()



# Сохраняем товар в html файл
def parser_url_html():
    targetPattern = r"c:\Data_panoramafirm.pl\*.html"
    files_html = glob.glob(targetPattern)

    coun = 0
    data = []
    for item in files_html:
        coun += 1
        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        regex_cart = re.compile(r'.*mb-0.*')
        urls_firma = soup.find_all('h2', attrs={'class': regex_cart})
        for i in urls_firma:
            data.append(i.find('a').get("href"))
    with open(f'c:\\scrap_tutorial-master\\panoramafirm.pl\\urls_firma.csv', 'w', newline='',
              encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
        writer.writerow(data)
        # print(item)
        # print("*"*50)
        # print(len(data))

        # with open(f'c:\\scrap_tutorial-master\\panoramafirm.pl\\urls_firma.csv', 'w', newline='', encoding='utf-8') as csvfile:
        #     writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
        #     writer.writerow(data)




# Парсим html файл
def save_html_firma():
    urls = [

    ]
    with open(f'C:\\scrap_tutorial-master\\panoramafirm.pl\\urls_firma.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in csv_reader:
            urls.append(row[0])
    count = 0
    for item in urls[:20]:
        count += 1
        driver = get_chromedriver(use_proxy=False,
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        driver.get(item)  # 'url_name' - это и есть ссылка

        driver.maximize_window()
        try:
            button_wait_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]')))
            button_cookies = driver.find_element(By.XPATH,
                                                 '//a[@class="cookies-eu-message-button cookies-eu-message-button-accept action-accept-cookies-eu"]').click()
        except:
            print("")
        driver.execute_script("window.scrollBy(0,5000)", "")
        with open(f"c:\\firma_panoramafirm.pl\\_data_{count}.html", "w", encoding='utf-8') as file:
            file.write(driver.page_source)
        time.sleep(1)

def parsing_html():
    targetPattern = r"c:\firma_panoramafirm.pl\*.html"
    files_html = glob.glob(targetPattern)
    urls = []
    with open(f"C:\\scrap_tutorial-master\\panoramafirm.pl\\firma.csv", "w",
              errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                "name_company", "uslugi_firma", "adr_firma", "email", "telephone", "keyword_firma", "face_firma", "ins_firma", "nip"
            )
        )
    for item in files_html:

        with open(f"{item}", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            name_company = soup.find('h1', attrs={'class': 'pt-3 font-weight-bold'}).text
        except:
            name_company = ""
        try:
            uslugi_firma = soup.find('h2', attrs={'class': 'font-weight-bold'}).text.strip().replace("\n", "")
        except:
            uslugi_firma = ""

        try:
            adr_firma = soup.find('div', attrs={'class': 'col-10 pl-1'}).find('strong').text.strip().replace("\n", "")

        except:
            adr_firma = ""

        script_1 = soup.find_all('script', type="application/ld+json")[0]
        script_2 = soup.find_all('script', type="application/ld+json")[1]
        try:
            data_json_1 = json.loads(script_1.string)
        except:
            data_json_1 = ""
        try:
            data_json_2 = json.loads(script_2.string)
        except:
            data_json_2 = ""
        try:
            email = data_json_1['email']
        except:
            email = ""
        try:
            telephone = data_json_1['telephone']
        except:
            telephone = ""
        try:
            www = data_json_1['sameAs']
        except:
            www = ""
        try:
            face_firma = soup.find('a', attrs={'class': 'addax addax-cs_ip_facebook_prv addax addax-cs_ip_facebook'})['href']
        except:
            face_firma = ""
        try:
            ins_firma = soup.find('a', attrs={'class': 'addax addax-cs_ip_instagram'})['href']
        except:
            ins_firma = ""

        keywords_firma = soup.find_all('div', attrs={'class': 'pr-2 d-inline'})
        text_list = [div.text.strip().replace("\n", "") for div in keywords_firma]
        keyword_firma = ''.join(text_list)
        try:
            nip = soup.find_all('div', attrs={'class': 'row contact-item py-2'})[1].find('div', attrs={'class': 'col-lg-8 col-sm-7 align-self-center'}).text.strip().replace("\n", "")
        except:
            nip = ""


        with open(f"C:\\scrap_tutorial-master\\panoramafirm.pl\\firma.csv", "a",
                  errors='ignore', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_company, uslugi_firma, adr_firma, email, telephone, keyword_firma, face_firma, ins_firma, nip
                )
            )





if __name__ == '__main__':
    # save_html()
    # parser_url_html()
    # save_html_firma()
    parsing_html()

