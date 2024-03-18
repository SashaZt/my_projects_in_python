from bs4 import BeautifulSoup
import random
import glob
import re
import requests
import json
import cloudscraper
import os
from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import time
import shutil
import tempfile
# import undetected_chromedriver as webdriver


from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
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
    'aws_lang': 'ru',
    'regStatus': 'pre-register',
    'aws-target-data': '%7B%22support%22%3A%221%22%7D',
    'AMCVS_7742037254C95E840A4C98A6%40AdobeOrg': '1',
    'AMCV_7742037254C95E840A4C98A6%40AdobeOrg': '1585540135%7CMCIDTS%7C19290%7CMCMID%7C91470991820856245777785966266006797918%7CMCAID%7CNONE%7CMCOPTOUT-1666653584s%7CNONE%7CvVersion%7C4.4.0',
    'session-id': '138-4380662-1523443',
    'ubid-main': '135-2594634-2322355',
    'ld': 'SCUSWPDirect',
    '__Host-mselc': 'H4sIAAAAAAAA/6tWSs5MUbJSSsytyjPUS0xOzi/NK9HLT85M0XM0dLcMM7UIcbd0CbMIUNJRykVSmZtalJyRCFKKRV02ssICkJKQsAAXb0/vCAMX1yClWgD6C4hIdQAAAA==',
    'JSESSIONID': '909085EE1D2F929A294972B8D650AE78',
    's_pers': '%20s_fid%3D46C1851F3C2C01F1-3538D67D7297AD09%7C1843574215573%3B%20s_dl%3D1%7C1685723215574%3B%20s_ev15%3D%255B%255B%2527SCUSWPDirect%2527%252C%25271685721415576%2527%255D%255D%7C1843574215576%3B',
    's_sess': '%20c_m%3DTyped%252FBookmarkedTyped%252FBookmarkedundefined%3B%20s_cc%3Dtrue%3B%20s_ppvl%3DSC%25253AUS%25253AWP-Welcome%252C74%252C74%252C929%252C1920%252C929%252C1920%252C1080%252C1%252CL%3B%20s_sq%3D%3B%20s_ppv%3DSC%25253AUS%25253AWP-Welcome%252C74%252C74%252C929%252C1920%252C929%252C1920%252C1080%252C1%252CL%3B',
    'csm-hit': 'tb:D5Q32N8SGX7AAA26F0MF+s-799MGFMS0WZ9TJ05245H|1685721617132&t:1685721617132&adb:adblk_no',
    'session-id-time': '2316441816l',
    'session-token': 'lgjaCtsdKVTOI8XNB7A4O1xHf6JfCO2ftQ+ScsIaMW0O/kS7eLuc8jTvJ0fSfKCe4ebUw3EMlTTyhcf4NTRboODau/qpKxa3vLvp4nCG0jKMQ31+hUqoU876zwylmLHvRhJDYhT/5xluH4n4mJV7L0LFz3o6inXy4IAs16NyLeHLOxtG5Nm2mUjJN/mGiYb5WSQRQNFUOdMHzs5bXB3XsGl/LKBegzri1zNc7OFt3T9Vy84W7mk1EL87KNg+M1fx',
    'x-main': '"oC68pbU5T65gulZAXnurMCc5nC3qgI?HQBBJPaIJl2J7hI1HPekVRRonZ4?b5GK?"',
    'at-main': 'Atza|IwEBICDpuHUN-aT_1Px3Ko7M9CI-F6JsViQsIDdePVd3JOVxtlgSVx4XUSshk0EEu6Q_NqMg2jhg-0TNlSrC_c62J0zNS4PiVKAn15njkdBZsaS9I3Jlor3ZOmPMOIChLdWGVpWsd0A5-k4LAPWJ5nqn-mlKrLZOHzlrp6DaiN0aLdxylzEk_CX_ZMLiy3wZzgkMvTxCfLOvJQC8OGfFSn0nhgs3KE-pDdoxtpzeKTEqjFUFlY2n8CTVigoYnDZMH6BStJw',
    'sess-at-main': '"D2MHczT9LRuGn+SnjOpusvdnH6v5rTVJuvJYtT/kP9s="',
    'sst-main': 'Sst1|PQHySIRfiE_GzoilFbqcjxsWCWX8VhyDGAO5bZ3t-xqIyFJXVpdbA8q58yZKtH75RKZ_5aOYf1DvhggJqTj2QwfIPQ69XRZLIlDekeNZuToKUr7xka83ancW0VJxH2Wvq1gjjtp_WkIb6Vyo_3t1AcvBqnXMp5v5R3ooCWR-BpMhyjniVBh4XFQSR9U85Zle6-r2g3m53HVyFAelPQEnyBOXete7qQ_KrlISsg2I3FYLAXLIDL3NlDZBedXJsxCqi-nsrEUsQfEkIWUIkLkyUmB1QpEsN5WGN_KfTPaWL22Tgqs',
    'stck': 'NA',
}

headers = {
    'authority': 'sellercentral.amazon.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'aws_lang=ru; regStatus=pre-register; aws-target-data=%7B%22support%22%3A%221%22%7D; AMCVS_7742037254C95E840A4C98A6%40AdobeOrg=1; AMCV_7742037254C95E840A4C98A6%40AdobeOrg=1585540135%7CMCIDTS%7C19290%7CMCMID%7C91470991820856245777785966266006797918%7CMCAID%7CNONE%7CMCOPTOUT-1666653584s%7CNONE%7CvVersion%7C4.4.0; session-id=138-4380662-1523443; ubid-main=135-2594634-2322355; ld=SCUSWPDirect; __Host-mselc=H4sIAAAAAAAA/6tWSs5MUbJSSsytyjPUS0xOzi/NK9HLT85M0XM0dLcMM7UIcbd0CbMIUNJRykVSmZtalJyRCFKKRV02ssICkJKQsAAXb0/vCAMX1yClWgD6C4hIdQAAAA==; JSESSIONID=909085EE1D2F929A294972B8D650AE78; s_pers=%20s_fid%3D46C1851F3C2C01F1-3538D67D7297AD09%7C1843574215573%3B%20s_dl%3D1%7C1685723215574%3B%20s_ev15%3D%255B%255B%2527SCUSWPDirect%2527%252C%25271685721415576%2527%255D%255D%7C1843574215576%3B; s_sess=%20c_m%3DTyped%252FBookmarkedTyped%252FBookmarkedundefined%3B%20s_cc%3Dtrue%3B%20s_ppvl%3DSC%25253AUS%25253AWP-Welcome%252C74%252C74%252C929%252C1920%252C929%252C1920%252C1080%252C1%252CL%3B%20s_sq%3D%3B%20s_ppv%3DSC%25253AUS%25253AWP-Welcome%252C74%252C74%252C929%252C1920%252C929%252C1920%252C1080%252C1%252CL%3B; csm-hit=tb:D5Q32N8SGX7AAA26F0MF+s-799MGFMS0WZ9TJ05245H|1685721617132&t:1685721617132&adb:adblk_no; session-id-time=2316441816l; session-token=lgjaCtsdKVTOI8XNB7A4O1xHf6JfCO2ftQ+ScsIaMW0O/kS7eLuc8jTvJ0fSfKCe4ebUw3EMlTTyhcf4NTRboODau/qpKxa3vLvp4nCG0jKMQ31+hUqoU876zwylmLHvRhJDYhT/5xluH4n4mJV7L0LFz3o6inXy4IAs16NyLeHLOxtG5Nm2mUjJN/mGiYb5WSQRQNFUOdMHzs5bXB3XsGl/LKBegzri1zNc7OFt3T9Vy84W7mk1EL87KNg+M1fx; x-main="oC68pbU5T65gulZAXnurMCc5nC3qgI?HQBBJPaIJl2J7hI1HPekVRRonZ4?b5GK?"; at-main=Atza|IwEBICDpuHUN-aT_1Px3Ko7M9CI-F6JsViQsIDdePVd3JOVxtlgSVx4XUSshk0EEu6Q_NqMg2jhg-0TNlSrC_c62J0zNS4PiVKAn15njkdBZsaS9I3Jlor3ZOmPMOIChLdWGVpWsd0A5-k4LAPWJ5nqn-mlKrLZOHzlrp6DaiN0aLdxylzEk_CX_ZMLiy3wZzgkMvTxCfLOvJQC8OGfFSn0nhgs3KE-pDdoxtpzeKTEqjFUFlY2n8CTVigoYnDZMH6BStJw; sess-at-main="D2MHczT9LRuGn+SnjOpusvdnH6v5rTVJuvJYtT/kP9s="; sst-main=Sst1|PQHySIRfiE_GzoilFbqcjxsWCWX8VhyDGAO5bZ3t-xqIyFJXVpdbA8q58yZKtH75RKZ_5aOYf1DvhggJqTj2QwfIPQ69XRZLIlDekeNZuToKUr7xka83ancW0VJxH2Wvq1gjjtp_WkIb6Vyo_3t1AcvBqnXMp5v5R3ooCWR-BpMhyjniVBh4XFQSR9U85Zle6-r2g3m53HVyFAelPQEnyBOXete7qQ_KrlISsg2I3FYLAXLIDL3NlDZBedXJsxCqi-nsrEUsQfEkIWUIkLkyUmB1QpEsN5WGN_KfTPaWL22Tgqs; stck=NA',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://sellercentral.amazon.com/inventory/ref=xx_invmgr_dnav_xx?tbla_myitable=sort:%7B%22sortOrder%22%3A%22DESCENDING%22%2C%22sortedColumnId%22%3A%22date%22%7D;search:;pagination:1;',
    'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
}

params = {
    'mSku': 'AV-QNMH-TN28',
    'ref': 'myi_skuc',
}
url = 'https://www.g2g.com/categories/diablo-4-boosting-service?seller=AMELIBOOST'


class ProxyExtension:
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
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
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
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)


def get_chromedriver(proxy):
    options = webdriver.ChromeOptions()

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-gpu")
    # options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    options.add_argument("--start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # options.add_argument('--disable-extensions') # Отключает использование расширений
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-setuid-sandbox')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    proxy_extension = ProxyExtension(*proxy)
    options.add_argument(f"--load-extension={proxy_extension.directory}")
    service = ChromeService(executable_path='C:\\scrap_tutorial-master\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver


def get_requests():
    import requests

    cookies = {
        'XSRF-TOKEN': 'eyJpdiI6Ing1UU10UFBRclBpaU5sbm1OSXc5eVE9PSIsInZhbHVlIjoiV1RxTlRBV3I3UUR1TU4xVHZsYTRtOVVLTnJcLzJPamxiT3BGajRBUVpFMGo5cUNEQ29ubFVJQXJCVTJMOFFwSnkiLCJtYWMiOiJmYTcwMGMyYzNiMzgxYWVlMDU1MjBkNTg3ZWU2OTQ0NTY5MzYwN2JlZjRlZDcxZDgwMDY1MGQ4YzY0Y2ViZTEzIn0%3D',
        'reima_session': 'eyJpdiI6InhZXC9Wdk91TDZ0d0QrNDZFenJiZVRnPT0iLCJ2YWx1ZSI6Im1CRTZjSXljczc2SmNYS1Bna3dKdFpxZ3JMY0w1STRUbjBkdUZiUXp4M2ZcL3U1bEQzSzBhczhqNThnWDJLaVVqIiwibWFjIjoiODk5MjlkMTZmZTQ2NGFkNmU5NzdhMDZmZWJkNjY0NGVkMmI4NmNjNmNiODMwODEzYTYwOGM0MzVhNzU0NjE4YiJ9',
        '_ga': 'GA1.1.288234887.1690127533',
        '_ga_9DM28L3K72': 'GS1.1.1690127532.1.1.1690127532.60.0.0',
        '_fbp': 'fb.1.1690127532932.1660194362',
    }

    headers = {
        'authority': 'reima.ua',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'XSRF-TOKEN=eyJpdiI6Ing1UU10UFBRclBpaU5sbm1OSXc5eVE9PSIsInZhbHVlIjoiV1RxTlRBV3I3UUR1TU4xVHZsYTRtOVVLTnJcLzJPamxiT3BGajRBUVpFMGo5cUNEQ29ubFVJQXJCVTJMOFFwSnkiLCJtYWMiOiJmYTcwMGMyYzNiMzgxYWVlMDU1MjBkNTg3ZWU2OTQ0NTY5MzYwN2JlZjRlZDcxZDgwMDY1MGQ4YzY0Y2ViZTEzIn0%3D; reima_session=eyJpdiI6InhZXC9Wdk91TDZ0d0QrNDZFenJiZVRnPT0iLCJ2YWx1ZSI6Im1CRTZjSXljczc2SmNYS1Bna3dKdFpxZ3JMY0w1STRUbjBkdUZiUXp4M2ZcL3U1bEQzSzBhczhqNThnWDJLaVVqIiwibWFjIjoiODk5MjlkMTZmZTQ2NGFkNmU5NzdhMDZmZWJkNjY0NGVkMmI4NmNjNmNiODMwODEzYTYwOGM0MzVhNzU0NjE4YiJ9; _ga=GA1.1.288234887.1690127533; _ga_9DM28L3K72=GS1.1.1690127532.1.1.1690127532.60.0.0; _fbp=fb.1.1690127532932.1660194362',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    response = requests.get('https://reima.ua/products/5100012A-2680_104', cookies=cookies, headers=headers)

    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    filename = f"data.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


def parsing():
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        file = f"data.html"
        with open(file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        # Найдите тег <script> с типом 'application/ld+json'
        script_tag = soup.find('script', {'type': 'application/ld+json'})

        # Извлеките текст из тега и удалите ненужные строки
        json_text = script_tag.string.replace('/*<![CDATA[*/', '').replace('/*]]>*/', '')

        # Загрузите текст в JSON
        data = json.loads(json_text)
        name_product = soup.find('h1', class_='h2 pdp-header').text
        discount_price = soup.find('span', class_='original-price discount-price').text.replace(' ₴', '').strip().replace(' ', '')
        discount_price = int(discount_price)
        old_price = soup.find('span', class_='original-price old').text.replace(' ₴', '').strip().replace(
            ' ', '')
        old_price = int(old_price)
        sizes = soup.find_all('a', class_=['btn btn-secondary btn-selector btn-selector-md border-radius-none size-option',
                                           'btn btn-secondary btn-selector btn-selector-md border-radius-none size-option selected'])

        size_values = [size.find('span', class_='size-value').text for size in sizes]

        all_image = soup.find_all('div', class_='thumbnail-item text-center')
        all_image_dict = []
        for i in all_image:
            url_ing = i.find('a').get('href')
            all_image_dict.append(url_ing)
        description_product = soup.find('div', class_='col-xs-12 col-sm-6 content-col-left margin-bottom-base description-product').text.replace('\n', ' ').strip()
        # margin_bottom_lg = soup.find('div', class_='col-xs-12 col-sm-6 content-col-left margin-bottom-base description-product').text.replace('\n', ' ').strip()
        border_left = soup.find('div', class_='margin-bottom-lg').text.replace('\n', ' ').replace("                                        Детальніше            Згорнути", '').strip()
        # border_right = soup.find_all('div', class_='col-xs-12 col-sm-6 content-col-right')[1].text.replace('\n', '').strip()
        sku_product = soup.find('div', class_='text-regular text-sm text-muted').text.replace('(', '').replace(')', '').strip()
        values = [name_product,sku_product, discount_price, old_price, size_values, all_image_dict,description_product, border_left]
        # print(values)

        writer.writerow(values)  # Дописываем значения из values
        # print(size_values)







'//li[@class=""]'
if __name__ == '__main__':
    get_requests()
    # parsing()
