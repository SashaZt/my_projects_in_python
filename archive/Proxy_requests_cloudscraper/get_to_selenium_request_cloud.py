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
url = 'https://web.telegram.org/k/'
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
    response = requests.get('https://sellercentral.amazon.com/skucentral', params=params, cookies=cookies, headers=headers)
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


def parsing():
    file = f"amazon.html"
    with open(file, encoding="utf-8") as file:
         src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    print(soup)


def get_cloudscraper():
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False

    })
    r = scraper.get(
        'https://sellercentral.amazon.com/skucentral?mSku=AV-QNMH-TN28&ref=myi_skuc', params=params, cookies=cookies, headers=headers
    )  # , proxies=proxies
    html = r.content
    filename = f"amazon.html"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html.decode('utf-8'))

def get_selenium():

    driver = get_chromedriver()
    driver.maximize_window()
    driver.get(url)
    time.sleep(10)
    driver.find_element(By.XPATH, '//*[@id="auth-pages"]/div/div[2]/div[3]/div/div[2]/button[2]/span').click()

def get_coocies():
    """Получение куки из любого сайта и отправка их в reqest"""
    url = 'https://www.vaurioajoneuvo.fi/?model_year_min=1999'
    from playwright.sync_api import sync_playwright
    from cf_clearance import sync_cf_retry, sync_stealth
    import requests

    # not use cf_clearance, cf challenge is fail
    proxies = {
        "all": "socks5://localhost:7890"
    }
    res = requests.get(url)
    if '<title>Just a moment...</title>' in res.text:
        print("cf challenge fail")
    # get cf_clearance
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        sync_stealth(page, pure=True)
        page.goto(url)
        res = sync_cf_retry(page)
        if res:
            cookies = page.context.cookies()
            for cookie in cookies:
                if cookie.get('name') == 'cf_clearance':
                    cf_clearance_value = cookie.get('value')
                    print(cf_clearance_value)
            ua = page.evaluate('() => {return navigator.userAgent}')
            print(ua)
        else:
            print("cf challenge fail")
        browser.close()
    # use cf_clearance, must be same IP and UA
    headers = {"user-agent": ua}
    cookies = {"cf_clearance": cf_clearance_value}
    res = requests.get(url, headers=headers, cookies=cookies)
    html = res.content
    with open("avto_.html", "w", encoding='utf-8') as f:
        f.write(html.decode('utf-8'))
    if '<title>Just a moment...</title>' not in res.text:
        print("cf challenge success")

"""Все что ниже для ротации прокси"""

file_path = "all_proxy.txt" #Тут все прокси которые есть
def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)

"""Эту часть использовать внутри кода"""
proxies = load_proxies(file_path)
proxy = get_random_proxy(proxies)
login_password, ip_port = proxy.split('@')
login, password = login_password.split(':')
ip, port = ip_port.split(':')
proxy_dict = {
    "http": f"http://{login}:{password}@{ip}:{port}",
    "https": f"http://{login}:{password}@{ip}:{port}"
}
print(proxy_dict)






if __name__ == '__main__':
    # get_requests()
    # get_cloudscraper()
    get_selenium()
    # parsing()
