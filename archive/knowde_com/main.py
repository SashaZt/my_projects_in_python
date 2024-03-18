from bs4 import BeautifulSoup
import csv
import glob
import re
import requests
import json
import cloudscraper
import os
import time
import undetected_chromedriver as webdriver
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv

PROXY_HOST = '37.233.3.100'
PROXY_PORT = 9999
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'
# proxies = {
#     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
#     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
# }
proxies = {"http": f"http://{PROXY_HOST}:{PROXY_PORT}", f"https": f"http://{PROXY_HOST}:{PROXY_PORT}"}
cookies = {
    'search_id': '478c99b5-1f9e-4ae8-a07b-6f23672917da',
    'OptanonAlertBoxClosed': '2023-06-09T05:51:59.368Z',
    'auto_pop_sign_up_seen': 'true',
    'hub_page_origin': '',
    'builderSessionId': '5ad3175ac0c0433b97e28ada6c3d9f9e',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Fri+Jun+09+2023+09%3A03%3A10+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202211.2.0&isIABGlobal=false&hosts=&consentId=f5289940-fc11-4b48-b2cc-8fbb21eb9cab&interactionCount=1&landingPath=NotLandingPage&groups=C0004%3A1%2CC0003%3A1%2CC0002%3A1%2CC0001%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
    'ajs_anonymous_id': 'cea9ab59-5b51-44f5-ad3e-115d3151151f',
    'knowde_uuid': 'cea9ab59-5b51-44f5-ad3e-115d3151151f',
    '_dd_s': 'rum=2&id=2fcf2abf-9c76-4152-a02c-6a305be80f0d&created=1686289915690&expire=1686291590035&logs=1',
}

headers = {
    'authority': 'www.knowde.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'search_id=478c99b5-1f9e-4ae8-a07b-6f23672917da; OptanonAlertBoxClosed=2023-06-09T05:51:59.368Z; auto_pop_sign_up_seen=true; hub_page_origin=; builderSessionId=5ad3175ac0c0433b97e28ada6c3d9f9e; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Jun+09+2023+09%3A03%3A10+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202211.2.0&isIABGlobal=false&hosts=&consentId=f5289940-fc11-4b48-b2cc-8fbb21eb9cab&interactionCount=1&landingPath=NotLandingPage&groups=C0004%3A1%2CC0003%3A1%2CC0002%3A1%2CC0001%3A1&geolocation=UA%3B18&AwaitingReconsent=false; ajs_anonymous_id=cea9ab59-5b51-44f5-ad3e-115d3151151f; knowde_uuid=cea9ab59-5b51-44f5-ad3e-115d3151151f; _dd_s=rum=2&id=2fcf2abf-9c76-4152-a02c-6a305be80f0d&created=1686289915690&expire=1686291590035&logs=1',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

url = 'https://www.g2g.com/categories/diablo-4-boosting-service?seller=AMELIBOOST'
def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    return driver
def get_requests():
    response = requests.get('https://www.knowde.com/b/markets-personal-care/products', cookies=cookies, headers=headers)
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    filename = f"data.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(response.text)
    # script_json = soup.find('script', type="application/json")
    # data_json = json.loads(script_json.string)
    # companis = data_json['props']['pageProps']['browsePage']['records']
    # for i in companis[:1]:
    #     name = i['name']
    #     print(name)


def parsing():
    file = f"data.html"
    with open(file, encoding="utf-8") as file:
         src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    script_json = soup.find('script', type="application/json")
    data_json = json.loads(script_json.string)
    companis = data_json['props']['pageProps']['browsePage']['records']
    inci_values = ''
    summary_Function = ''
    # Открыть (или создать, если его не существует) CSV-файл для записи
    with open('output.csv', 'w', newline='') as csvfile:
        # Создать объект writer, который будет записывать данные в CSV
        writer = csv.writer(csvfile)

        # Записать заголовки CSV
        writer.writerow(["Name", "Company Name", "INCI Values", "Function", "Description"])
        for i in companis[:20]:
            name = i['name']
            companyName = i['companyName']
            for characteristic in i["characteristics"]:
                if characteristic["name"] == "INCI Name":
                    inci_values = characteristic["values"]
            for summary in i["summary"]:
                if summary["name"] == "Function":
                    summary_Function = summary["values"]
            description = i['description']
            writer.writerow([name, companyName, inci_values, summary_Function, description])



def get_cloudscraper():
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False

    })
    r = scraper.get(
        'https://sellercentral.amazon.com/skucentral?mSku=AV-QNMH-TN28&ref=myi_skuc', cookies=cookies, headers=headers
    )  # , proxies=proxies
    html = r.content
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html.decode('utf-8'))

def get_selenium():

    driver = get_undetected_chromedriver()
    driver.maximize_window()
    driver.get(url)
    time.sleep(10)

    file_name = f"AMELIBOOST.html"
    with open(os.path.join('data', file_name), "w", encoding='utf-8') as fl:
        fl.write(driver.page_source)

if __name__ == '__main__':
    # get_requests()
    # get_cloudscraper()
    # get_selenium()
    parsing()
