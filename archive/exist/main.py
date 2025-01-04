import csv
import json
import math
from datetime import datetime
import os
import re
import pandas as pd
import mysql.connector
from concurrent.futures import ProcessPoolExecutor
import time
# from headers_cookies import cookies, headers
from urllib.parse import urlparse, parse_qs
import glob
import requests
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import random
from selenium.webdriver.common.by import By


"""Настройка browsermob-proxy"""
server_options = {
    'log_path': 'NUL'
}

server = Server(r"c:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy", options=server_options)
server.start()
proxy = server.create_proxy()


"""Настройка для Selenium"""
def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver


"""Получаем curl с помощью Selenium и browsermob-proxy"""
def selenium_get_curl(url):
    proxy.new_har("exist.ua", options={'captureHeaders': True, 'captureContent': True})
    """Ссылка куда переходим"""
    driver = get_chromedriver()
    driver.get(url)
    time.sleep(5)

    driver.execute_script('''
        var elements = document.querySelectorAll('[aria-label="Network panel"]');
        for (var i = 0; i < elements.length; i++) {
            var element = elements[i];
            if (element.offsetWidth > 0 && element.offsetHeight > 0) {
                element.click();
                break;
            }
        }
    ''')
    time.sleep(5)
    # получить все запросы из Network panel
    requests = driver.execute_script('''
        var performanceEntries = performance.getEntriesByType("resource");
        var fetchRequests = [];
        for (var i = 0; i < performanceEntries.length; i++) {
            var entry = performanceEntries[i];
            fetchRequests.push(entry);
        }
        return fetchRequests;
    ''')

    curl_command = "curl "
    entries = proxy.har['log']['entries']
    print(entries)
    for entry in entries:
        # print(entry)
        """Указываем тут url который нужно отслеживать"""
        if entry['request']['url'].startswith('https://exist.ua/api/v1/catalogue/product-index/'):
            # Method (GET, POST, etc.)
            curl_command += "-X {} ".format(entry['request']['method'])

            # URL
            curl_command += "'{}' \\\n".format(entry['request']['url'])

            # Headers
            for header in entry['request']['headers']:
                header_name = header['name']
                header_value = header['value']
                curl_command += "  -H '{}: {}' \\\n".format(header_name, header_value)

            if entry['request']['method'] == 'GET' and 'postData' in entry['request']:
                if 'text' in entry['request']['postData']:
                    curl_command += "  --data '{}'".format(entry['request']['postData']['text'])

            break

    # Extracting cookies
    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split('; ')
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies_list}

    # Extracting headers
    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(': ')[0]: header.split(': ')[1] for header in headers_match}
    print(curl_command)

    return curl_command

"""curl разбираем на cookies и headers"""
def get_cookie_header(curl_command):
    cookies = {}
    headers = {}
    params = {}
    method = "GET"  # по умолчанию

    url_match = re.search(r"'(.*?)'", curl_command)
    if url_match:
        url = url_match.group(1)
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

    method_match = re.search(r"-X (\w+)", curl_command)
    if method_match:
        method = method_match.group(1)

    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split("; ")
        cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies_list}

    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(": ")[0]: header.split(": ")[1] for header in headers_match}
    url_match = re.search(r"'(.*?)'", curl_command)
    url = None
    if url_match:
        url = url_match.group(1)

    return params, cookies, headers
# def save_to_file(url, params, cookies, headers):
#     with open("headers_cookies.py", "w") as f:
#         f.write("url = '{}'\n\n".format(url))
#
#         f.write("params = {\n")
#         for key, value in params.items():
#             f.write("    '{}': {},\n".format(key, value))
#         f.write("}\n\n")
#
#         f.write("cookies = {\n")
#         for key, value in cookies.items():
#             f.write("    '{}': '{}',\n".format(key, value))
#         f.write("}\n\n")
#
#         f.write("headers = {\n")
#         for key, value in headers.items():
#             f.write("    '{}': '{}',\n".format(key, value))
#         f.write("}\n")

"""Получаем общее количество объявлений"""
def get_totalElements():
    json_data = {
        'query': [
            '*',
        ],
        'filter': {
            'NLTS': [
                'expected_sale_assigned_ts_utc:[NOW/DAY-1DAY TO NOW/DAY]',
            ],
        },
        'sort': None,
        'page': 0,
        'size': 100,
        'start': 0,
        'watchListOnly': False,
        'freeFormSearch': False,
        'hideImages': False,
        'defaultSort': False,
        'specificRowProvided': False,
        'displayName': '',
        'searchName': '',
        'backUrl': '',
        'includeTagByField': {},
        'rawParams': {},
    }
    response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
                             headers=headers, json=json_data)

    data_json = response.json()
    totalElements = data_json['data']['results']['totalElements']
    print(f'Всего {totalElements}')
    return totalElements


"""Получаем все объявления"""
def get_request(totalElements):

    ad = totalElements
    page_ad = ad // 100
    start = 0
    page = 0
    # for i in range(0, 1):
    for i in range(page_ad + 1):
        filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
        if not os.path.exists(filename):
            # Создаем сессию
            json_data = {
                'query': [
                    '*',
                ],
                'filter': {
                    'NLTS': [
                        'expected_sale_assigned_ts_utc:[NOW/DAY-1DAY TO NOW/DAY]',
                    ],
                },
                'sort': None,
                'page': page,
                'size': 100,
                'start': start,
                'watchListOnly': False,
                'freeFormSearch': False,
                'hideImages': False,
                'defaultSort': False,
                'specificRowProvided': False,
                'displayName': '',
                'searchName': '',
                'backUrl': '',
                'includeTagByField': {},
                'rawParams': {},
            }

            try:
                response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
                                         headers=headers, json=json_data)
            except:
                continue
            data = response.json()
            print(f'Пауза 1 сек')
            time.sleep(1)

            with open(filename, 'w') as f:
                json.dump(data, f)
        page += 1
        start += 100
    now = datetime.now()
    print(f'Все {page_ad} страницы скачаны в {now}')

"""Собираем все ссылки"""
def get_id_ad_and_url():
    folders_html = r"c:\DATA\copart\list\*.json"
    files_html = glob.glob(folders_html)
    file_csv = f"url.csv"
    with open(file_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            content = json_data['data']['results']['content']
            for c in content:
                url_ad = f'https://www.copart.com/public/data/lotdetails/solr/lotImages/{c["ln"]}/USA'
                writer.writerow([url_ad])
    now = datetime.now()
    print(f'Получили список всех url в {now}')


def get_product(cookies, headers):

    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
            if not os.path.exists(filename):
                try:
                    response = requests.get(url[0], cookies=cookies, headers=headers)  # , proxies=proxi

                except Exception as e:
                    print(e)

                try:
                    data_json = response.json()
                except Exception as e:
                    data_json = None
                    print(e)
                    continue

                with open(filename, 'w') as f:
                    json.dump(data_json, f)
                    print(filename)
                time.sleep(5)
            print(f'Сохранил объявлений {counter}')
            counter += 1

"""Следующие 3 функции для работы с Selenium"""
def split_urls(urls, n):
    """Делит список URL-адресов на n равных частей."""
    avg = len(urls) // n
    urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
    return urls_split



def worker(sub_urls, start_counter):
    driver = get_chromedriver()
    for counter, url in enumerate(sub_urls, start=start_counter):
        try:
            filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
            if not os.path.exists(filename):
                driver.get(url[0])
                time.sleep(1)
                json_content = driver.page_source
                json_content = json_content.replace(
                    '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body style="margin: 0"><div></div><pre>',
                    '')
                json_content = json_content.replace('</pre></body></html>', '')
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(json_content)

        except Exception as e:
            print(f"Error processing URL {url[0]}: {e}")
    driver.quit()


def get_product_s():
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        max_workers = 10
        splitted_urls = split_urls(urls, max_workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker, sub_urls, idx * len(sub_urls))
"""Следующие 3 функции для работы с Selenium"""


def get_requests():
    total = 83067
    pages = (total // 50) +2
    for i in range(1, pages):
        filename = f"data_{i}.json"
        if not os.path.exists(filename):

            cookies = {
                'catalog_page_size': '50',
                'sessionid': 'e9p6sduf4r9vlnjmpwtgg6poulns1ibh',
                'cf_clearance': 'c7fFGka1cNttA.77DJqF0F9A.aBQXDxAX9TR7bM5cCU-1696687749-0-1-d29a0353.48b345ac.859b5cb3-0.2.1696687749',
                'crisp-client%2Fsession%2F980759c4-00d9-4b4b-85e6-c48036807fc0': 'session_b94fd2dc-888d-49ea-81bf-e6c6d8f0207d',
                'crisp-client%2Fsocket%2F980759c4-00d9-4b4b-85e6-c48036807fc0': '0',
            }

            headers = {
                'authority': 'exist.ua',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'uk',
                'baggage': 'sentry-environment=production,sentry-release=v2023.38.4,sentry-public_key=6541b6a63473425d99519d634760bb1a,sentry-trace_id=86da2d1aad624b28835999e416350318',
                'client-render': '1',
                # 'cookie': 'catalog_page_size=50; sessionid=e9p6sduf4r9vlnjmpwtgg6poulns1ibh; cf_clearance=c7fFGka1cNttA.77DJqF0F9A.aBQXDxAX9TR7bM5cCU-1696687749-0-1-d29a0353.48b345ac.859b5cb3-0.2.1696687749; crisp-client%2Fsession%2F980759c4-00d9-4b4b-85e6-c48036807fc0=session_b94fd2dc-888d-49ea-81bf-e6c6d8f0207d; crisp-client%2Fsocket%2F980759c4-00d9-4b4b-85e6-c48036807fc0=0',
                'dnt': '1',
                'old-session-enabled': '0',
                'page-url': '/uk/amortyzatory-stijky-pidvisky/',
                'referer': 'https://exist.ua/uk/amortyzatory-stijky-pidvisky/',
                'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sentry-trace': '86da2d1aad624b28835999e416350318-bc99ca082e4bad06-0',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            }

            params = {
                'page': i,
                'slug': 'amortyzatory-stijky-pidvisky',
            }

            response = requests.get('https://exist.ua/api/v1/catalogue/product-index/', params=params, cookies=cookies,
                                    headers=headers)

            # src = response.text
            json_data = response.json()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
            time.sleep(10)


def parsin():
    # Отображение оригинальных названий на алиасы
    key_aliases = {
        'upc': 'Номер товару',
        'trademark': 'Бренд',
        'name': 'Имя',
        'price': 'Прайс',
        'quantity': 'Количевство',
        'image':'Изображение'
    }
    folder = r'c:\DATA\exist\amortyzatory\*.json'
    files_json = glob.glob(folder)

    # Набор заголовков для CSV будет состоять из алиасов
    heandler_set = set(key_aliases.values())

    # Сначала соберем все уникальные названия из всех JSON файлов
    for file_path in files_json:
        with open(file_path, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
            dict_results = data_json['data']['results']
            for i in dict_results:
                attributes = i['attributes']
                for attr_item in attributes:
                    heandler_set.add(attr_item['name'])

    # Создаем CSV файл и записываем данные
    # with open('amortyzatory.csv', 'w', newline='', encoding='utf-8') as file:
    #     writer = csv.DictWriter(file, fieldnames=heandler_set, delimiter=";")
    #     writer.writeheader()  # записываем заголовки
    #
    #     for file_path in files_json:
    #         with open(file_path, 'r', encoding="utf-8") as f:
    #             data_json = json.load(f)
    #             dict_results = data_json['data']['results']
    #
    #             # Записываем данные в CSV
    #             for i in dict_results:
    #                 result_dict = {
    #                     key_aliases['upc']: i.get('upc', None),
    #                     key_aliases['trademark']: i.get('trademark', {}).get('description', None),
    #                     key_aliases['name']: i.get('description', None),
    #                     key_aliases['price']: i.get('price', {}).get('price', None),
    #                     key_aliases['quantity']: i.get('price', {}).get('quantity', None),
    #                     key_aliases['image']: i.get('image', None)
    #                 }
    #
    #                 for attr_item in i['attributes']:
    #                     # Если название столбца есть в нашем наборе, записываем значение
    #                     if attr_item['name'] in heandler_set:
    #                         result_dict[attr_item['name']] = attr_item['value']
    #
    #                 writer.writerow(result_dict)
    with open('url_amortyzatory.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
          # записываем заголовки

        for file_path in files_json:
            with open(file_path, 'r', encoding="utf-8") as f:
                data_json = json.load(f)
                dict_results = data_json['data']['results']

                # Записываем данные в CSV
                for i in dict_results:
                    base_url = 'https://exist.ua/uk/'
                    slug_brand = i['trademark']['slug']
                    skug_product = i['slug']
                    urls = f'{base_url}{slug_brand}-brand/{skug_product}'

                    writer.writerow([urls])


if __name__ == '__main__':
    # print("Вставьте ссылку")
    # url = 'https://exist.ua/uk/amortyzatory-stijky-pidvisky/'
    # curl_result = selenium_get_curl(url)  # сохраняем результат функции в переменную
    # get_cookie_header(curl_result)
    # server.stop()  # остановка сервера должна быть здесь
    # params, cookies, headers = get_cookie_header(curl_result)
    # # # save_to_file(url, params, cookies, headers)
    # totalElements = get_totalElements()
    # get_request(totalElements)
    # get_id_ad_and_url()
    # get_product_s()
    # get_requests()
    parsin()
