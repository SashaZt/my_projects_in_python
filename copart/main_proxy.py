import csv
import glob
import json
import os
import re
import threading
import datetime
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import schedule
import mysql.connector
import requests
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# import config
from config import db_config, url, use_bd, use_table, start_time
# from headers_cookies import cookies, headers

# Определите текущую директорию, где находится скрипт
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')

# Доступ к другим переменным
# url = config.url
# use_bd = config.use_bd
# use_table = config.use_table
def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        # print(f'Очистил папку {os.path.basename(folder)}')



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

    s = Service(executable_path=f"{current_directory}\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver


"""Получаем curl с помощью Selenium и browsermob-proxy"""


def selenium_get_curl(url):
    proxy.new_har("copart.com", options={'captureHeaders': True, 'captureContent': True})
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
    for entry in entries:
        # print(entry)
        """Указываем тут url который нужно отслеживать"""
        if entry['request']['url'].startswith('https://www.copart.com/public/lots/vehicle-finder-search-results'):
            # Method (GET, POST, etc.)
            curl_command += "-X {} ".format(entry['request']['method'])

            # URL
            curl_command += "'{}' \\\n".format(entry['request']['url'])

            # Headers
            for header in entry['request']['headers']:
                header_name = header['name']
                header_value = header['value']
                curl_command += "  -H '{}: {}' \\\n".format(header_name, header_value)

            if entry['request']['method'] == 'POST' and 'postData' in entry['request']:
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

    # return url, params, cookies, headers
    return params, cookies, headers


"""Получаем общее количество объявлений"""


def get_totalElements(cookies, headers):
    """Используем каждый фильтр со своими данными"""
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
    # json_data = {
    #     'query': [
    #         '*',
    #     ],
    #     'filter': {},
    #     'sort': None,
    #     'page': 0,
    #     'size': 100,
    #     'start': 0,
    #     'watchListOnly': False,
    #     'freeFormSearch': False,
    #     'hideImages': False,
    #     'defaultSort': False,
    #     'specificRowProvided': False,
    #     'displayName': '',
    #     'searchName': '',
    #     'backUrl': '',
    #     'includeTagByField': {},
    #     'rawParams': {},
    # }
    response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
                             headers=headers, json=json_data)

    data_json = response.json()
    totalElements = data_json['data']['results']['totalElements']
    print(f'Всего {totalElements}')
    return totalElements


"""Получаем все объявления"""


def get_data_mysql():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(f"SELECT lot_number FROM {use_bd}.{use_table};")
    lot_numbers_set = set()
    for row in cursor:
        lot_numbers_set.add(int(row[0]))
    cursor.close()
    cnx.close()
    return lot_numbers_set

# def get_request(totalElements):
#
#     ad = totalElements
#     page_ad = ad // 100
#     start = 0
#     page = 0
#     # for i in range(0, 1):
#     for i in range(page_ad + 1):
#         filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
#         if not os.path.exists(filename):
#             # Создаем сессию
#             json_data = {
#                 'query': [
#                     '*',
#                 ],
#                 'filter': {},
#                 'sort': None,
#                 'page': page,
#                 'size': 100,
#                 'start': start,
#                 'watchListOnly': False,
#                 'freeFormSearch': False,
#                 'hideImages': False,
#                 'defaultSort': False,
#                 'specificRowProvided': False,
#                 'displayName': '',
#                 'searchName': '',
#                 'backUrl': '',
#                 'includeTagByField': {},
#                 'rawParams': {},
#             }
#
#             try:
#                 response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
#                                          headers=headers, json=json_data)
#             except:
#                 continue
#             data = response.json()
#             print(f'Пауза 1 сек')
#             time.sleep(1)
#
#             with open(filename, 'w') as f:
#                 json.dump(data, f)
#         page += 1
#         start += 100
#     now = datetime.now()
#     print(f'Все {page_ad} страницы скачаны в {now}')
def get_request_thread(start_page, end_page,cookies, headers):

    for page in range(start_page, end_page):
        start = page * 100
        filename = f"{temp_path}\list\data_{page}.json"
        if not os.path.exists(filename):
            json_data = {
                'query': [
                    '*',
                ],
                'filter': {},
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
                data = response.json()
                time.sleep(1)
                with open(filename, 'w') as f:
                    json.dump(data, f)
            except:
                pass


def multi_threaded_get_request(totalElements, thread_count,cookies, headers):
    ad = totalElements
    page_ad = ad // 100

    pages_per_thread = (page_ad + 1) // thread_count
    threads = []

    for i in range(thread_count):
        start_page = i * pages_per_thread
        end_page = (i + 1) * pages_per_thread if i != thread_count - 1 else page_ad + 1
        t = threading.Thread(target=get_request_thread, args=(start_page, end_page, cookies, headers))
        threads.append(t)
        t.start()

    # Дождитесь завершения выполнения всех потоков
    for t in threads:
        t.join()

    now = datetime.now()
    print(f'Все {page_ad} страницы скачаны в {now}')


"""Собираем все ссылки"""


def get_id_ad_and_url(lot_numbers_set):
    folders_html = f"{list_path}/*.json"
    files_html = glob.glob(folders_html)
    file_csv = "url.csv"  # Поправил, чтобы указать строку напрямую
    with open(file_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            content = json_data['data']['results']['content']
            for c in content:
                ln = int(c["ln"])
                if ln not in lot_numbers_set:
                    url_ad = f'https://www.copart.com/public/data/lotdetails/solr/lotImages/{ln}/USA'
                    writer.writerow([url_ad])
    with open('url.csv', 'r') as file:
        count = sum(1 for line in file)

    print(f"Новых объявлений {count}")

def get_product(cookies, headers):

    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            filename = os.path.join(product_path, f"data_{counter}.json")
            # filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
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


# def split_urls(urls, n):
#     """Делит список URL-адресов на n равных частей."""
#     avg = len(urls) // n
#     urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
#     return urls_split
def split_urls(urls, n):
    """Делит список URL-адресов на n равных частей."""
    total_urls = len(urls)
    if total_urls < n:  # если количество URL-ов меньше желаемого количества потоков
        n = total_urls  # установите количество потоков равным количеству URL-ов

    avg = total_urls // n
    urls_split = [urls[i:i + avg] for i in range(0, total_urls, avg)]

    # Если остались нераспределенные URL-ы из-за деления, добавляем их к последней группе
    if total_urls % n != 0:
        urls_split[-1].extend(urls[-(total_urls % n):])

    return urls_split

def worker(sub_urls, start_counter):
    driver = get_chromedriver()
    for counter, url in enumerate(sub_urls, start=start_counter):
        try:
            filename = os.path.join(product_path, f"data_{counter}.json")
            if not os.path.exists(filename):
                driver.get(url[0])
                time.sleep(1)
                json_content = driver.page_source
                json_content = json_content.replace(
                    '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body style="margin: 0"><div></div><pre>',
                    '')
                json_content = json_content.replace('</pre></body></html>', '')
                json_content = json_content.replace('<html><head><meta name="color-scheme" content="light dark"></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">', '')

                with open(filename, "w", encoding="utf-8") as file:
                    file.write(json_content)

        except Exception as e:
            print(f"Error processing URL {url[0]}: {e}")
    driver.quit()


def get_product_s():
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        max_workers = 2
        splitted_urls = split_urls(urls, max_workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker, sub_urls, idx * len(sub_urls))


"""Следующие 3 функции для работы с Selenium"""


def parsin():
    now = datetime.now()
    print(f'Передача данных в Mysql началась в {now}')
    cnx = mysql.connector.connect(**db_config)
    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()
    folders_html = f"{product_path}/*.json"
    files_html = glob.glob(folders_html)
    for i in files_html:
        with open(i, 'r', encoding='utf-8') as f:
            # content = f.read()

            # Удаляем нежелательную строку
            # content_cleaned = content.replace(
            #     '<html><head><meta name="color-scheme" content="light dark"></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">',
            #     '')

            try:
                # Загрузить JSON из очищенного содержимого
                # data_json = json.loads(content_cleaned)
                """Разкоментировать после загрузки на сайт"""
                # try:
                    # Загрузить JSON из файла
                data_json = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"Ошибка при чтении файла: {i}")
                continue

        try:
            ln = data_json['data']['lotDetails']['ln']
        except:
            continue
        url_lot = f"https://www.copart.com/lot/{ln}"
        try:
            url_img_full = data_json['data']['imagesList']['FULL_IMAGE']
            urls_full = str(",".join([u['url'] for u in url_img_full]))
        except:
            urls_full = None
        try:
            url_img_high = data_json['data']['imagesList']['HIGH_RESOLUTION_IMAGE']
            urls_high = str(",".join([u_h['url'] for u_h in url_img_high]))
        except:
            urls_high = None

        try:
            name_lot = data_json['data']['lotDetails']['ld']
        except:
            name_lot = None
        try:
            lotNumberStr = data_json['data']['lotDetails']['lotNumberStr']
        except:
            lotNumberStr = None
        try:
            td = data_json['data']['lotDetails']['td']
        except:
            td = None
        try:
            ts = data_json['data']['lotDetails']['ts']
        except:
            ts = None
        td_ts = f"{td}-{ts}"
        try:
            hk = data_json['data']['lotDetails']['hk']
        except:
            hk = None
        try:
            la = data_json['data']['lotDetails']['la']
        except:
            la = None
        try:
            dd = data_json['data']['lotDetails']['dd']
        except:
            dd = None
        try:
            cy = data_json['data']['lotDetails']['cy']
        except:
            cy = None
        try:
            bstl = data_json['data']['lotDetails']['bstl']
        except:
            bstl = None
        try:
            tmtp = data_json['data']['lotDetails']['tmtp']
        except:
            tmtp = 'YES'
        try:
            drv = data_json['data']['lotDetails']['drv']
        except:
            drv = None
        try:
            egn = data_json['data']['lotDetails']['egn']
        except:
            egn = None
        try:
            vehTypDesc = data_json['data']['lotDetails']['vehTypDesc']
        except:
            vehTypDesc = None
        try:
            ft = data_json['data']['lotDetails']['ft']
        except:
            ft = None
        try:
            clr = data_json['data']['lotDetails']['clr']
        except:
            clr = None
        try:
            ess = data_json['data']['lotDetails']['ess']
        except:
            ess = None
        try:
            currentBid = data_json['data']['lotDetails']['dynamicLotDetails']['currentBid']
        except:
            currentBid = None
        try:
            odometer_lot = data_json['data']['lotDetails']['orr']
        except:
            odometer_lot = None

        try:
            highlights_lot = data_json['data']['lotDetails']['lcd']
        except:
            highlights_lot = None
        try:
            sale_location = data_json['data']['lotDetails']['yn']
        except:
            sale_location = None
        try:
            sale_date_row = data_json['data']['lotDetails']['ad']
            timestamp_seconds_sale_date = sale_date_row / 1000.0
            sale_date = datetime.utcfromtimestamp(timestamp_seconds_sale_date)
            sale_date = sale_date.date()
        except:
            sale_date = None

        try:
            last_updated_row = data_json['data']['lotDetails']['lu']
            timestamp_seconds_last_updated = last_updated_row / 1000.0
            last_updated = datetime.utcfromtimestamp(timestamp_seconds_last_updated)
            last_updated = last_updated.date()
        except:
            last_updated = None
        now = datetime.now()
        current_date = now.date()
        parsing_date =current_date
        datas = [url_lot, urls_full, urls_high, name_lot, lotNumberStr, td_ts, odometer_lot, hk, tmtp, la, dd, cy, bstl,
                 drv, egn, vehTypDesc, ft, clr, highlights_lot, ess, currentBid, sale_location,sale_date, last_updated, parsing_date]
        insert_query = """
       INSERT INTO copart
        (url_lot, url_img_full, url_img_high, name_lot, lot_number, title_code, odometer, `keys`, transmission, price, primary_damage, cylinders,body_style,
               drive,engine_type,vehicle_type,fuel,color,highlights,sale_status,current_bid,sale_location,sale_date, last_updated, parsing_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, datas)
    cnx.commit()
    cnx.close()
    now = datetime.now()
    print(f'Загрузил данны в БД {now}')


def create_sql():

    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 3. В базе данных создаем таблицу ad
    # 4. Создаем необходимые колонки
    cursor.execute("""
        CREATE TABLE copart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url_lot VARCHAR(500),
            url_img_full VARCHAR(1000),
            url_img_high VARCHAR(1000),
            name_lot VARCHAR(255),
            lot_number INT,
            title_code VARCHAR(255),
            odometer FLOAT,
            `keys` VARCHAR(255), -- Используем обратные кавычки для ключевого слова "keys"
            transmission VARCHAR(255),
            price FLOAT,
            primary_damage VARCHAR(255),
            cylinders INT,
            body_style VARCHAR(255),
            drive VARCHAR(255),
            engine_type VARCHAR(255),
            vehicle_type VARCHAR(255),
            fuel VARCHAR(255),
            color VARCHAR(255),
            highlights VARCHAR(255),
            sale_status VARCHAR(255),
            current_bid FLOAT,
            sale_location VARCHAR(255),
            sale_date DATE,  -- Изменим на DATETIME, если нужно хранить и время
            last_updated DATE, -- Изменим на DATETIME, если нужно хранить и время
            parsing_date DATE  -- Изменим на DATETIME, если нужно хранить и время
        )
    """)

    # Закрываем соединение
    cnx.close()





if __name__ == '__main__':
    # """Создание таблицы"""
    # create_sql()

    delete_old_data()
    lot_numbers_set = get_data_mysql()

    curl_result = selenium_get_curl(url)  # сохраняем результат функции в переменную
    # get_cookie_header(curl_result)
    server.stop()  # остановка сервера должна быть здесь
    params, cookies, headers = get_cookie_header(curl_result)
    totalElements = get_totalElements(cookies, headers)
    multi_threaded_get_request(totalElements, 10,cookies, headers)
    # # get_request(totalElements)
    get_id_ad_and_url(lot_numbers_set)
    get_product_s()
    parsin()
