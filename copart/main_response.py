import csv
import glob
import json
import os
import time
import re
from datetime import datetime
import subprocess

# """Используется для Chrome баузера"""
# from concurrent.futures import ProcessPoolExecutor
"""Используется для response"""
from concurrent.futures import ThreadPoolExecutor
import mysql.connector
import requests
from headers_cookies import cookies, headers
current_directory = os.getcwd()

"""Получаем общее количество объявлений"""

def get_cookies():
    now = datetime.now()
    print(f'Запуск скрипта {now} ')
    file_name = f"{current_directory}/temp/cookies.txt"
    if os.path.exists(file_name):
        # Удаляем файл
        os.remove(file_name)
    # Создаем команду curl с использованием заголовков и кук
    cmd = [
        'curl',
    '-c', f'{file_name}',
    '-H', f'authority: www.copart.com',
    '-H', f'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    '-H', f'accept-language: ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    '-H', f'referer: https://www.copart.com',
    '-H', f'sec-ch-ua: "Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    # '-x', '141.145.205.4:31281',  # Указываем адрес и порт прокси-сервера
    # '-U', 'proxy_alex:DbrnjhbZ88',
        # Указываем имя пользователя и пароль для аутентификации на прокси-сервере
    '-H', f'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    "https://www.copart.com"
    ]
    # cmd = [
    #     'curl',
    #     '-c', f'{file_name}',
    #     "https://www.copart.com"
    # ]
    # session = requests.Session()
    #
    # # Отправляем GET-запрос на веб-сайт
    # response = session.get('https://www.example.com')
    #
    # # Куки будут автоматически сохранены в сессии
    # # Вы можете получить их следующим образом
    # cookies = session.cookies.get_dict()
    #
    # # Теперь у вас есть словарь с куками, который вы можете использовать в дальнейших запросах
    # print(cookies)


    # Запускаем команду curl
    subprocess.run(cmd)
    with open(file_name, "r") as file:
        # Считываем содержимое файла
        content = file.read()

    # Разбиваем содержимое файла на строки
    lines = content.split('\n')

    # Создаем словарь для хранения куки
    new_cookie_value_incap_ses = {}

    # Обрабатываем каждую строку
    for line in lines:
        parts = line.split('\t')
        if len(parts) == 7:
            domain, _, _, _, _, key, value = parts
            # if key.startswith('incap_ses'):
            if key.startswith('incap_ses'):
                new_cookie_value_incap_ses[key] = value

    file_headers_cookies = f"{current_directory}/headers_cookies.py"

    # Открываем файл headers_cookies.py для чтения
    with open(file_headers_cookies, "r") as file:
        content = file.read()

    search_cookie_pattern_incap_ses = r'"incap_ses_\d+_\d+": "[^"]+"'


    # Ищем и заменяем куки для incap_ses
    match_incap_ses = re.search(search_cookie_pattern_incap_ses, content)
    if match_incap_ses:
        # Получаем найденную строку
        old_cookie_string = match_incap_ses.group(0)

        # Преобразуем новый блок кук в строку JSON
        new_cookie_json = json.dumps(new_cookie_value_incap_ses)

        # Удаляем квадратные скобки из строки JSON
        new_cookie_json = new_cookie_json[1:-1]
        # Заменяем строку с куками
        content = content.replace(old_cookie_string, new_cookie_json)

    # Ищем и заменяем куки для visid_incap
    new_cookie_value_visid_incap = {}
    search_cookie_pattern_visid_incap = r'"visid_incap_\d+_\d+": "[^"]+"'
    for line in lines:
        parts = line.split('\t')
        if len(parts) == 7:
            domain, _, _, _, _, key, value = parts
            # if key.startswith('incap_ses'):
            if key.startswith('visid_incap'):
                new_cookie_value_visid_incap[key] = value
    match_visid_incap = re.search(search_cookie_pattern_visid_incap, content)
    if match_visid_incap:
        # Получаем найденную строку
        old_cookie_string = match_visid_incap.group(0)
        # print(old_cookie_string)

        # Преобразуем новый блок кук в строку JSON
        new_cookie_json = json.dumps(new_cookie_value_visid_incap)

        # Удаляем квадратные скобки из строки JSON
        new_cookie_json = new_cookie_json[1:-1]
        # Заменяем строку с куками
        content = content.replace(old_cookie_string, new_cookie_json)

    # Записываем обновленное содержимое файла
    with open(file_headers_cookies, "w") as file:
        file.write(content)
    # match_visid_incap = re.search(search_cookie_pattern_visid_incap, content)
    # if match_incap_ses:
    #     # Получаем найденную строку
    #     old_cookie_string = match_visid_incap.group(0)
    #
    #     # Преобразуем новый блок кук в строку JSON
    #     new_cookie_json = json.dumps(new_cookie_value)
    #
    #     # Удаляем квадратные скобки из строки JSON
    #     new_cookie_json = new_cookie_json[1:-1]
    #
    #     # Заменяем строку с куками
    #     content = content.replace(old_cookie_string, new_cookie_json)
    #
    #     # Записываем обновленное содержимое файла
    #     with open(file_headers_cookies, "w") as file:
    #         file.write(content)


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
        # """Для Windows """
        # filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
        """Для Linux"""
        filename = f"{current_directory}/list/data_{page}.json"

        if not os.path.exists(filename):
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

            time.sleep(1)

            with open(filename, 'w') as f:
                json.dump(data, f)
        page += 1
        # print(f'Осталось {page_ad + 1 - page}')
        start += 100
    now = datetime.now()
    print(f'Все {page_ad} страницы скачаны в {now}')


"""Собираем все ссылки"""


def get_id_ad_and_url():
    # """Для Windows """
    # folders_html = r"c:\DATA\copart\list\*.json"
    """Для Linux"""
    folders_html = rf"{current_directory}/list/*.json"
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
    print('Получили список всех url')

def get_cookies_json():
    now = datetime.now()
    print(f'Запуск скрипта {now} ')
    file_name = f"{current_directory}/temp/cookies.txt"
    if os.path.exists(file_name):
        # Удаляем файл
        os.remove(file_name)
    # Создаем команду curl с использованием заголовков и кук
    cmd = [
        'curl',
    '-c', f'{file_name}',
    '-H', f'authority: www.copart.com',
    '-H', f'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    '-H', f'accept-language: ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    '-H', f'referer: https://www.copart.com',
    '-H', f'sec-ch-ua: "Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    # '-x', '141.145.205.4:31281',  # Указываем адрес и порт прокси-сервера
    # '-U', 'proxy_alex:DbrnjhbZ88',
        # Указываем имя пользователя и пароль для аутентификации на прокси-сервере
    '-H', f'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    "https://www.copart.com"
    ]
    # cmd = [
    #     'curl',
    #     '-c', f'{file_name}',
    #     "https://www.copart.com"
    # ]
    # session = requests.Session()
    #
    # # Отправляем GET-запрос на веб-сайт
    # response = session.get('https://www.copart.com/vehicleFinderSearch?displayStr=%5B0%20TO%209999999%5D,%5B2011%20TO%202024%5D&from=%2FvehicleFinder&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22NLTS%22:%5B%22expected_sale_assigned_ts_utc:%5BNOW%2FDAY-1DAY%20TO%20NOW%2FDAY%5D%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D')
    #
    # # Куки будут автоматически сохранены в сессии
    # # Вы можете получить их следующим образом
    # cookies = session.cookies.get_dict()
    #
    # # Теперь у вас есть словарь с куками, который вы можете использовать в дальнейших запросах
    # print(cookies)


    # Запускаем команду curl
    subprocess.run(cmd)

    with open(file_name, "r") as file:
        # Считываем содержимое файла
        content = file.read()

    # Разбиваем содержимое файла на строки
    lines = content.split('\n')

    # Создаем словарь для хранения куки
    new_cookie_value = {}

    # Обрабатываем каждую строку
    for line in lines:
        parts = line.split('\t')
        if len(parts) == 7:
            domain, _, _, _, _, key, value = parts
            # if key.startswith('incap_ses'):
            if key.startswith('incap_ses') or key.startswith('visid_incap'):
                new_cookie_value[key] = value

    file_headers_cookies = f"{current_directory}/headers_cookies.py"

    # Открываем файл headers_cookies.py для чтения
    with open(file_headers_cookies, "r") as file:
        content = file.read()

    # Определяем регулярное выражение для поиска старой строки с куками
    search_cookie_pattern_incap = r'"incap_ses_\d+_\d+": "[^"]+"'
    search_cookie_pattern_visid = r'"visid_incap_\d+_\d+": "[^"]+"'

    # Ищем первое вхождение куки
    match = re.search(search_cookie_pattern_incap, content)
    if match:
        # Получаем найденную строку
        old_cookie_string = match.group(0)

        # Преобразуем новый блок кук в строку JSON
        new_cookie_json = json.dumps(new_cookie_value)

        # Удаляем квадратные скобки из строки JSON
        new_cookie_json = new_cookie_json[1:-1]

        # Заменяем строку с куками
        content = content.replace(old_cookie_string, new_cookie_json)

        # Записываем обновленное содержимое файла
        with open(file_headers_cookies, "w") as file:
            file.write(content)

        print(f"Значение куки успешно обновлено.")
    else:
        print(f"Не удается найти куки, соответствующие шаблону .")
def split_urls_r(urls, n):
    """Делит список URL-адресов на n равных частей."""
    avg = len(urls) // n
    urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
    return urls_split


def worker_r(sub_urls, start_counter):

    # Используйте сессию для повторного использования TCP-соединений
    with requests.Session() as session:
        session.cookies.update(cookies)
        session.headers.update(headers)

        for counter, u in enumerate(sub_urls, start=start_counter):
            # """Для Windows """
            # filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
            """Для Linux"""
            filename = f"{current_directory}/product/data_{counter}.json"
            if not os.path.exists(filename):
                try:
                    response = session.get(u[0])  # proxies можно добавить, если они нужны

                    data_json = response.json()


                    with open(filename, 'w') as f:
                        json.dump(data_json, f)
                    time.sleep(1)
                except:
                    print(u[0])


def get_product_r():
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files))
        max_workers = 100
        splitted_urls = split_urls_r(urls, max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker_r, sub_urls, idx * len(sub_urls))


"""получаем все объявления"""


def parsin():
    print('Передаем данные в Mysql')
    cnx = mysql.connector.connect(
        # host="localhost",  # ваш хост, например "localhost"
        host="vpromo2.mysql.tools",  # ваш хост, например "localhost"
        user="vpromo2_usa",  # ваше имя пользователя
        password="^~Hzd78vG4",  # ваш пароль
        database="vpromo2_usa"  # имя вашей базы данных
    )

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()
    # """Для Windows """
    # folders_html = r"c:\DATA\copart\product\*.json"
    """Для Linux"""
    folders_html = f"{current_directory}/product/*.json"

    files_html = glob.glob(folders_html)
    for i in files_html:
        with open(i, 'r') as f:
            # Загрузить JSON из файла
            data_json = json.load(f)

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

        name_lot = data_json['data']['lotDetails']['ld']
        lotNumberStr = data_json['data']['lotDetails']['lotNumberStr']
        td_ts = f"{data_json['data']['lotDetails']['ts']}-{data_json['data']['lotDetails']['td']}"
        hk = data_json['data']['lotDetails']['hk']
        la = data_json['data']['lotDetails']['la']
        dd = data_json['data']['lotDetails']['dd']
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

        currentBid = data_json['data']['lotDetails']['dynamicLotDetails']['currentBid']
        odometer_lot = data_json['data']['lotDetails']['orr']

        try:
            highlights_lot = data_json['data']['lotDetails']['lcd']
        except:
            highlights_lot = None
        try:
            sale_location = data_json['data']['lotDetails']['yn']
        except:
            sale_location = None
        datas = [url_lot, urls_full, urls_high, name_lot, lotNumberStr, td_ts, odometer_lot, hk, tmtp, la, dd, cy, bstl,
                 drv, egn, vehTypDesc, ft, clr, highlights_lot, ess, currentBid, sale_location]
        insert_query = """
       INSERT INTO copart
        (url_lot, url_img_full, url_img_high, name_lot, lot_number, title_code, odometer, `keys`, transmission, price, primary_damage, cylinders,body_style,
               drive,engine_type,vehicle_type,fuel,color,highlights,sale_status,current_bid,sale_location) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, datas)
    cnx.commit()
    cnx.close()
    now = datetime.now()
    print(f'Загрузил данны в БД {now} ')


if __name__ == '__main__':
    # get_cookies()
    url = 'https://www.copart.com/vehicleFinderSearch?displayStr=%5B0%20TO%209999999%5D,%5B2011%20TO%202024%5D&from=%2FvehicleFinder&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22NLTS%22:%5B%22expected_sale_assigned_ts_utc:%5BNOW%2FDAY-1DAY%20TO%20NOW%2FDAY%5D%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D'
    totalElements = get_totalElements()
    get_request(totalElements)
    get_id_ad_and_url()
    get_product_r()
    parsin()
