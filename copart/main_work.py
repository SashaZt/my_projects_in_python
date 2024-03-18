import csv
import glob
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
import schedule
import mysql.connector
import requests
import random

from headers_cookies import cookies, headers
url = 'https://www.copart.com/vehicleFinderSearch?displayStr=%5B0%20TO%209999999%5D,%5B2011%20TO%202024%5D&from=%2FvehicleFinder&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22NLTS%22:%5B%22expected_sale_assigned_ts_utc:%5BNOW%2FDAY-1DAY%20TO%20NOW%2FDAY%5D%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D'
"""Получаем общее количество объявлений"""

file_path = "proxy.txt"  # Тут все прокси которые есть


def load_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if '@' in line and ':' in line]


def get_random_proxy(proxies):
    return random.choice(proxies)


proxies = load_proxies(file_path)
def get_totalElements():
    proxy = get_random_proxy(proxies)
    login_password, ip_port = proxy.split('@')
    login, password = login_password.split(':')
    ip, port = ip_port.split(':')
    proxy_dict = {
        "http": f"http://{login}:{password}@{ip}:{port}",
        "https": f"http://{login}:{password}@{ip}:{port}"
    }
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

    response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies, headers=headers,
                             json=json_data, proxies=proxy_dict)

    data_json = response.json()
    totalElements = data_json['data']['results']['totalElements']
    print(f'Всего {totalElements}')
    return totalElements


"""Получаем все объявления"""


def get_request(totalElements):
    proxy = get_random_proxy(proxies)
    login_password, ip_port = proxy.split('@')
    login, password = login_password.split(':')
    ip, port = ip_port.split(':')
    proxy_dict = {
        "http": f"http://{login}:{password}@{ip}:{port}",
        "https": f"http://{login}:{password}@{ip}:{port}"
    }

    ad = totalElements
    page_ad = ad // 100
    start = 0
    page = 0
    # for i in range(0, 1):
    for i in range(page_ad + 1):
        filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
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
                                         headers=headers, json=json_data, proxies=proxy_dict)
            except:
                continue
            data = response.json()
            time.sleep(5)

            with open(filename, 'w') as f:
                json.dump(data, f)
        page += 1
        start += 100
    print(f'Все {page_ad} страницы скачаны')


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
    print('Получили список всех url')


def split_urls_r(urls, n):
    """Делит список URL-адресов на n равных частей."""
    avg = len(urls) // n
    urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
    return urls_split


def worker_r(sub_urls, start_counter):

    proxy = get_random_proxy(proxies)
    login_password, ip_port = proxy.split('@')
    login, password = login_password.split(':')
    ip, port = ip_port.split(':')
    proxy_dict = {
        "http": f"http://{login}:{password}@{ip}:{port}",
        "https": f"http://{login}:{password}@{ip}:{port}"
    }
    for counter, url in enumerate(sub_urls, start=start_counter):
        filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
        if not os.path.exists(filename):
            try:
                response = requests.get(url[0], cookies=cookies, headers=headers)  #  proxies=proxy_dict
                print(response.status_code)
                data_json = response.json()
                with open(filename, 'w') as f:
                    json.dump(data_json, f)
                time.sleep(1)
                print(f'Сохранил объявлений {counter}')
            except Exception as e:
                print(e)


def get_product_r():
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        max_workers = 3
        splitted_urls = split_urls_r(urls, max_workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker_r, sub_urls, idx * len(sub_urls))


"""получаем все объявления"""


def parsin():
    cnx = mysql.connector.connect(
        # host="localhost",  # ваш хост, например "localhost"
        host="vpromo2.mysql.tools",  # ваш хост, например "localhost"
        user="vpromo2_usa",  # ваше имя пользователя
        password="^~Hzd78vG4",  # ваш пароль
        database="vpromo2_usa"  # имя вашей базы данных
    )

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()
    folders_html = r"c:\DATA\copart\product\*.json"
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
        url_img_full = data_json['data']['imagesList']['FULL_IMAGE']
        urls_full = str(",".join([u['url'] for u in url_img_full]))
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



# def job():
    # print('Начинаем работать')
    # totalElements = get_totalElements()
    # get_request(totalElements)
    # get_id_ad_and_url()
    # get_product_r()
    # parsin()

if __name__ == '__main__':
    # totalElements = get_totalElements()
    # get_request(totalElements)
    # get_id_ad_and_url()
    get_product_r()
    # parsin()

# schedule.every().day.at("08:24").do(job)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)


