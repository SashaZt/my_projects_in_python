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
    'session-id': '142-4156051-2826849',
    'ubid-main': '135-0200416-6965265',
    'at-main': 'Atza|IwEBIHLENpvSo6IYU2heB7riylOu6be5vQagD_ucLEFt2UfXHgiQHVZ7xRfVcAYadFi8ib8mt-fhd1yegmao8hSuX5vcEWP8gg3vLHxTzmg5uzXvxGSyEUmjGKPMaxpfVxS7lmPJiL-CS44B4NsqT3lDkNv6PSHdresvfJ2HRvm-T13KHKaJx7EG7_tIDqQQSQF_zUIUzVgqprv7DJYz47K6FNZ-YNdpZMXNnl5PJXOmHXuXBSQDNOCBi8-KIab0HR2n0mEpcJcICzFoEJouFusIupwKR7CXC3KtMWfF78u8schavw',
    'sess-at-main': '"IdhMzuGhPU5e0XmtHASAFlgyp5zJI6ZHWIaM0QVTITM="',
    'sst-main': 'Sst1|PQGEmNiYL84BFT_awTvcUbA4CQR9fQwYZi3ZP9Zj2zJ9OuZEEcAWcba5pfE9rwjuJf8cPTsosQ1pJDbvcLNoNOc8e6FNYtKBjuzLH0rlVIxNYnTsBR40DzEDWTPe8aCEmgEBOKkg-q4dys-q8YuJVZMSSd8p1xMFDqpKz9GDYngmqPY4ahBksaFRFYToIt1Opvj6OgEoJVG8m_WzcCxiIezIFTm5TOYtpYdnvCuStLOWwhmDI-aiUU6JKLIDsyQTMnuLUL91ciNgFFve9HyJL_nuD9iip3LdNdvOa6ZcOcUnE-w',
    'session-id-time': '2082787201l',
    'i18n-prefs': 'USD',
    'skin': 'noskin',
    'sp-cdn': '"L5Z9:UA"',
    'lc-main': 'en_US',
    'session-token': '"055TzHoT+uUJhMJxd/kR7PGDhkhW6CEFgHhJCQBFx5VubASmBtMoeKEE/HaJ/PaERrxeVX4fxw6sfyex1Z1kBPPY2PXJZAxdeVst+sQUU0tgk6wOb9+y72D0jR2xzO0NfBkqVjbcLnMwdJ+XhMhD8oG74qNhBQkH8H6jGk3xLquT+1+js/E6jCK166CFyrK+A6dBCSd0q2FA8XpByaXWOu6eLPGrZ4UEEbJrnNxOzy8="',
    'csm-hit': 'adb:adblk_no&t:1687247536508&tb:QCF6R5T7WFZ4R58FKXWX+sa-TZ7PKAZ4SSGZNHQ5QJ5X-7HB88RE8AF4W86G1Q5Y8|1687247536508',
}

headers = {
    'authority': 'www.amazon.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'max-age=0',
    # 'cookie': 'session-id=142-4156051-2826849; ubid-main=135-0200416-6965265; at-main=Atza|IwEBIHLENpvSo6IYU2heB7riylOu6be5vQagD_ucLEFt2UfXHgiQHVZ7xRfVcAYadFi8ib8mt-fhd1yegmao8hSuX5vcEWP8gg3vLHxTzmg5uzXvxGSyEUmjGKPMaxpfVxS7lmPJiL-CS44B4NsqT3lDkNv6PSHdresvfJ2HRvm-T13KHKaJx7EG7_tIDqQQSQF_zUIUzVgqprv7DJYz47K6FNZ-YNdpZMXNnl5PJXOmHXuXBSQDNOCBi8-KIab0HR2n0mEpcJcICzFoEJouFusIupwKR7CXC3KtMWfF78u8schavw; sess-at-main="IdhMzuGhPU5e0XmtHASAFlgyp5zJI6ZHWIaM0QVTITM="; sst-main=Sst1|PQGEmNiYL84BFT_awTvcUbA4CQR9fQwYZi3ZP9Zj2zJ9OuZEEcAWcba5pfE9rwjuJf8cPTsosQ1pJDbvcLNoNOc8e6FNYtKBjuzLH0rlVIxNYnTsBR40DzEDWTPe8aCEmgEBOKkg-q4dys-q8YuJVZMSSd8p1xMFDqpKz9GDYngmqPY4ahBksaFRFYToIt1Opvj6OgEoJVG8m_WzcCxiIezIFTm5TOYtpYdnvCuStLOWwhmDI-aiUU6JKLIDsyQTMnuLUL91ciNgFFve9HyJL_nuD9iip3LdNdvOa6ZcOcUnE-w; session-id-time=2082787201l; i18n-prefs=USD; skin=noskin; sp-cdn="L5Z9:UA"; lc-main=en_US; session-token="055TzHoT+uUJhMJxd/kR7PGDhkhW6CEFgHhJCQBFx5VubASmBtMoeKEE/HaJ/PaERrxeVX4fxw6sfyex1Z1kBPPY2PXJZAxdeVst+sQUU0tgk6wOb9+y72D0jR2xzO0NfBkqVjbcLnMwdJ+XhMhD8oG74qNhBQkH8H6jGk3xLquT+1+js/E6jCK166CFyrK+A6dBCSd0q2FA8XpByaXWOu6eLPGrZ4UEEbJrnNxOzy8="; csm-hit=adb:adblk_no&t:1687247536508&tb:QCF6R5T7WFZ4R58FKXWX+sa-TZ7PKAZ4SSGZNHQ5QJ5X-7HB88RE8AF4W86G1Q5Y8|1687247536508',
    'device-memory': '8',
    'dnt': '1',
    'downlink': '10',
    'dpr': '1',
    'ect': '4g',
    'referer': 'https://www.amazon.com/s?i=stripbooks&rh=n%3A283155&dc&fs=true&ds=v1%3AFW8FzwCBmo65EzoRsz1El3Z1rFWVVXAAYR6kFuYqSyk&qid=1687247019&ref=sr_ex_n_1',
    'rtt': '50',
    'sec-ch-device-memory': '8',
    'sec-ch-dpr': '1',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"10.0.0"',
    'sec-ch-viewport-width': '1100',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'viewport-width': '1100',
}

params = {
    'i': 'stripbooks',
    'rh': 'n%3A283155%2Cn%3A1',
    'dc': '',
    'fs': 'true',
    'page': 2,
    'qid': '1687247117',
    'rnid': '283155',
    'ref': 'sr_pg_2',
}


# url = 'https://www.g2g.com/categories/diablo-4-boosting-service?seller=AMELIBOOST'


def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
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
    import requests

    cookies = {
        'locale': 'ua',
        '__cf_bm': 'bpW6G9IMs2e.Nqlg2axi5OIGdfYsHR5iDtqNrJy9nAA-1689742731-0-AaT4syoOIZxDAxNKGrQGvfxabRgS0pR9K1NVDi7G5aHarGOwo9aAFY69rQ8nh4lg4zjLgjZTEvFj/zxiIeQ/JLU=',
    }

    headers = {
        'authority': 'bank.gov.ua',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'locale=ua; __cf_bm=bpW6G9IMs2e.Nqlg2axi5OIGdfYsHR5iDtqNrJy9nAA-1689742731-0-AaT4syoOIZxDAxNKGrQGvfxabRgS0pR9K1NVDi7G5aHarGOwo9aAFY69rQ8nh4lg4zjLgjZTEvFj/zxiIeQ/JLU=',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.google.com/',
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

    response = requests.get('https://bank.gov.ua/ua/markets/exchangerates', cookies=cookies, headers=headers)
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    scripts = soup.find_all('script')

    json_str = scripts[2].string.split('window.results = JSON.parse(', 1)[1].rsplit(')', 1)[0].strip("'")
    json_data = json.loads(json_str)  # Преобразовываем строку JSON в словарь Python
    course_dollars = json_data[7]['rate']
    print(course_dollars)
    # json_data = response.json()
    # with open(f'test.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    # filename = f"amazon.html"
    # with open(filename, "w", encoding='utf-8') as file:
    #     file.write(src)


def parsing():
    file = f"amazon.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    scripts = soup.find_all('script')

    json_str = scripts[2].string.split('window.results = JSON.parse(', 1)[1].rsplit(')', 1)[0].strip("'")
    json_data = json.loads(json_str)  # Преобразовываем строку JSON в словарь Python
    course_dollars = json_data[7]['rate']
        # if 'window.results = JSON.parse' in script.string:

    # json_data = json.loads(script_tag.string)
    # filename = f"c:\\DATA\\iaai\\product\\data_0.json"
    # with open(filename, 'w') as f:
    #     json.dump(json_data, f)
    # print(json_data)
    # json_data = None
    #
    # for tag in script_tags:
    #     content = tag.string
    #     if content and 'window.__HYDRATION_STATE__=' in content:
    #         # Разделяем строку на две части: все до 'window.__HYDRATION_STATE__=' и все после
    #         parts = content.split('window.__HYDRATION_STATE__=', 1)
    #         json_str = parts[1]  # Берем вторую часть
    #         json_data = json.loads(json_str)
    #         print(json_data)
    #         break



if __name__ == '__main__':
    get_requests()
    # parsing()
