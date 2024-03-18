import csv
import glob
import json
import os
import random

import mysql.connector
import requests

from headers_cookies import cookies, headers
from proxi import proxies

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

    response = requests.post('https://www.copart.com/public/lots/search-results', cookies=cookies,
                             headers=headers, json=json_data, proxies=proxy_dict)

    data_json = response.json()
    totalElements = data_json['data']['results']['totalElements']
    print(f'Статус {response.status_code}запроса, всего {totalElements}')
    return totalElements


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

            with open(filename, 'w') as f:
                json.dump(data, f)
        page += 1
        start += 100
    print(f'Все {page_ad} страницы скачаны')


def get_id_ad_and_url():
    folders_html = r"c:\DATA\copart\list\*.json"
    files_html = glob.glob(folders_html)
    with open(f"url.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            content = json_data['data']['results']['content']
            for c in content:
                url_ad = f'https://www.copart.com/public/data/lotdetails/solr/lotImages/{c["ln"]}/USA'
                writer.writerow([url_ad])


def get_product():
    cookies = {
        'userLang': 'en',
        'visid_incap_242093': 'b10WPaAoQtW25aL5NGxPAtWWDGUAAAAAQkIPAAAAAACApSSvAcEY3SKdh0ZytGc5HWZgHrhpgB6M',
        'nlbi_242093': 'DFzjOiL08U2PoqUlJDHybgAAAAB4O0Di4JvIRrWJfqmBXSvD',
        'timezone': 'Europe%2FKiev',
        '_gcl_au': '1.1.1197976300.1695323867',
        '_gid': 'GA1.2.1555460196.1695323868',
        '_fbp': 'fb.1.1695323867835.1820581379',
        '_tt_enable_cookie': '1',
        '_ttp': 'nolPRjYYFLwIsswEHMXsi5BqvZk',
        '_cc_id': '28f975cc550190c89fe3c94c79bb4c7',
        'panoramaId_expiry': '1695928668508',
        'panoramaId': '07fc0ce1f5213a3786ea58a82aa016d539389e0c77adff97b4570b17d419e11d',
        'panoramaIdType': 'panoIndiv',
        'g2app.search-table-rows': '100',
        'userCategory': 'RPU',
        'copartTimezonePref': '%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D',
        'g2usersessionid': 'b059377eb1fae1b858f4e810aca4e1db',
        'G2JSESSIONID': 'F077C144265BF9A41C68799B0510E822-n1',
        '_clck': '16em929|2|ff8|0|1359',
        'granify.new_user.JUFHS': 'false',
        'usersessionid': 'a464acc53ef4b4804afa8864eaa2ad5e',
        'OAID': '87b6a0f519a3817d5dc84b84fd421928',
        '__gads': 'ID=9337394839a00378:T=1695323868:RT=1695360311:S=ALNI_MZTh6tI-iGiDkHTAWFq4saLOTMB2g',
        '__gpi': 'UID=00000c7b3288cda9:T=1695323868:RT=1695360311:S=ALNI_MZEFuwZZTQIj3TlXVwF2Hz-UXw-vQ',
        'FCNEC': '%5B%5B%22AKsRol_tnxmijiAU78yFFnDS2pyG6Xzx6HQN4ln-nklnbDlvTP4BzrAyN-hTMVJSt53zazODGTDgblkq9aNR6Jm04_MrHodJ2EoeCcTO_ICHrwhOrab27XXwjE9TDbVMXcbm_gpvUItelDlZgV51drn1WudrNpoHew%3D%3D%22%5D%2Cnull%2C%5B%5D%5D',
        '_clsk': 'g9mq3k|1695360793629|2|0|w.clarity.ms/collect',
        'incap_ses_325_242093': 'tyihYOasiDjxXPsneKKCBPgnDWUAAAAAARkb5mr8C12EtmG6qJSyVw==',
        'reese84': '3:cI8P9mCCUl+8G9zqTyPg4A==:xvbxWNggwy/P/8M44OFm/ZadDM54oB/CymrUci+lHMj6ka8xf2AXFEnWws+YKHyEF3vbEY2zCA/HHDeDPjDiRs5k8dsiRXGhAQZAaHx/CDGGHHErZW/STlc73XmpLVeyXu0o/sFtwZzY0ji5STPW8QV1mkVPLhR2WLYS1EkTwvUdja0iUQwUSr5PhFdsygzxeME1vl0MEQgqVwki/zZvZKEZgPzRl0RO28w73SLI5sjh6qd6LilZ8uGoGG/iqWcj52DPkD6PMUIMWlqHqCoPqJmVuxngsz8zTYB1p1g0vLSv8d/8hdY16KeOx+XFhx4mDjQBvF03kUMYewX2apt7/4VEp3zcYET2FcmYmwNJbEj0RUsj6ZcwkaYRQjp27kwvNS1bFhEMYDHgtD2O+RykrSWlLMg8PHCAT/ErdKzI3XWHLJo3/4ZqaCp7Cq0jPaMF4JZUvSrRUY4W8vJ7GkntZ5h4TgwMeL5vfem+vQUi+wDpZFk2+xZ344ZVhtMuKE3m:Qyim4T/Fpuwno7pyvXytNqrMCJcCaihgwxdw6oPQTqc=',
        'incap_ses_536_242093': 'BClAMKrSfQekU6wyKUJwBzgoDWUAAAAAMcFeIJi7oPSuj7BdMBd8Og==',
        'nlbi_242093_2147483392': 'Qvb+Xi6bzGPsBAmDJDHybgAAAACL5UIYFOMzvmgYjXHH2irG',
        '_uetsid': '8c9c0b8058b311eeb611a1410aa0531a',
        '_uetvid': '8c9c665058b311ee83714337c2a9d80b',
        '_ga': 'GA1.1.2100030463.1695323868',
        'granify.uuid': '0b440fec-740f-433c-b9d6-7a2a6d3eeffd',
        'granify.session.JUFHS': '-1',
        '_ga_VMJJLGQLHF': 'GS1.1.1695360306.2.1.1695361082.47.0.0',
    }

    headers = {
        'authority': 'www.copart.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru',
        'access-control-allow-headers': 'Content-Type, X-XSRF-TOKEN',
        'cache-control': 'no-cache',
        # 'cookie': 'userLang=en; visid_incap_242093=b10WPaAoQtW25aL5NGxPAtWWDGUAAAAAQkIPAAAAAACApSSvAcEY3SKdh0ZytGc5HWZgHrhpgB6M; nlbi_242093=DFzjOiL08U2PoqUlJDHybgAAAAB4O0Di4JvIRrWJfqmBXSvD; timezone=Europe%2FKiev; _gcl_au=1.1.1197976300.1695323867; _gid=GA1.2.1555460196.1695323868; _fbp=fb.1.1695323867835.1820581379; _tt_enable_cookie=1; _ttp=nolPRjYYFLwIsswEHMXsi5BqvZk; _cc_id=28f975cc550190c89fe3c94c79bb4c7; panoramaId_expiry=1695928668508; panoramaId=07fc0ce1f5213a3786ea58a82aa016d539389e0c77adff97b4570b17d419e11d; panoramaIdType=panoIndiv; g2app.search-table-rows=100; userCategory=RPU; copartTimezonePref=%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D; g2usersessionid=b059377eb1fae1b858f4e810aca4e1db; G2JSESSIONID=F077C144265BF9A41C68799B0510E822-n1; _clck=16em929|2|ff8|0|1359; granify.new_user.JUFHS=false; usersessionid=a464acc53ef4b4804afa8864eaa2ad5e; OAID=87b6a0f519a3817d5dc84b84fd421928; __gads=ID=9337394839a00378:T=1695323868:RT=1695360311:S=ALNI_MZTh6tI-iGiDkHTAWFq4saLOTMB2g; __gpi=UID=00000c7b3288cda9:T=1695323868:RT=1695360311:S=ALNI_MZEFuwZZTQIj3TlXVwF2Hz-UXw-vQ; FCNEC=%5B%5B%22AKsRol_tnxmijiAU78yFFnDS2pyG6Xzx6HQN4ln-nklnbDlvTP4BzrAyN-hTMVJSt53zazODGTDgblkq9aNR6Jm04_MrHodJ2EoeCcTO_ICHrwhOrab27XXwjE9TDbVMXcbm_gpvUItelDlZgV51drn1WudrNpoHew%3D%3D%22%5D%2Cnull%2C%5B%5D%5D; _clsk=g9mq3k|1695360793629|2|0|w.clarity.ms/collect; incap_ses_325_242093=tyihYOasiDjxXPsneKKCBPgnDWUAAAAAARkb5mr8C12EtmG6qJSyVw==; reese84=3:cI8P9mCCUl+8G9zqTyPg4A==:xvbxWNggwy/P/8M44OFm/ZadDM54oB/CymrUci+lHMj6ka8xf2AXFEnWws+YKHyEF3vbEY2zCA/HHDeDPjDiRs5k8dsiRXGhAQZAaHx/CDGGHHErZW/STlc73XmpLVeyXu0o/sFtwZzY0ji5STPW8QV1mkVPLhR2WLYS1EkTwvUdja0iUQwUSr5PhFdsygzxeME1vl0MEQgqVwki/zZvZKEZgPzRl0RO28w73SLI5sjh6qd6LilZ8uGoGG/iqWcj52DPkD6PMUIMWlqHqCoPqJmVuxngsz8zTYB1p1g0vLSv8d/8hdY16KeOx+XFhx4mDjQBvF03kUMYewX2apt7/4VEp3zcYET2FcmYmwNJbEj0RUsj6ZcwkaYRQjp27kwvNS1bFhEMYDHgtD2O+RykrSWlLMg8PHCAT/ErdKzI3XWHLJo3/4ZqaCp7Cq0jPaMF4JZUvSrRUY4W8vJ7GkntZ5h4TgwMeL5vfem+vQUi+wDpZFk2+xZ344ZVhtMuKE3m:Qyim4T/Fpuwno7pyvXytNqrMCJcCaihgwxdw6oPQTqc=; incap_ses_536_242093=BClAMKrSfQekU6wyKUJwBzgoDWUAAAAAMcFeIJi7oPSuj7BdMBd8Og==; nlbi_242093_2147483392=Qvb+Xi6bzGPsBAmDJDHybgAAAACL5UIYFOMzvmgYjXHH2irG; _uetsid=8c9c0b8058b311eeb611a1410aa0531a; _uetvid=8c9c665058b311ee83714337c2a9d80b; _ga=GA1.1.2100030463.1695323868; granify.uuid=0b440fec-740f-433c-b9d6-7a2a6d3eeffd; granify.session.JUFHS=-1; _ga_VMJJLGQLHF=GS1.1.1695360306.2.1.1695361082.47.0.0',
        'dnt': '1',
        'if-modified-since': 'Mon, 26 Jul 1997 05:00:00 GMT',
        'pragma': 'no-cache',
        'referer': 'https://www.copart.com/lot/27612510/clean-title-2009-volkswagen-jetta-s-tx-houston-east',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': 'a61623c9-a481-4477-ab7a-13a41cd436a8',
    }
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            filename = f"c:\\DATA\\copart\\product\\data_{counter}.json"
            if not os.path.exists(filename):
                # proxy = get_random_proxy(proxies)
                ip = '64.42.176.123'
                port = 10161
                login = 'azinchyk6527'
                password = 'c7cbc8'
                # login_password, ip_port = proxy.split('@')
                # login, password = login_password.split(':')
                # ip, port = ip_port.split(':')
                proxy_dict = {
                    "http": f"http://{login}:{password}@{ip}:{port}",
                    "https": f"http://{login}:{password}@{ip}:{port}"
                }

                try:
                    response = requests.get(url[0], cookies=cookies, headers=headers,
                                            proxies=proxy_dict)  # , proxies=proxi
                    print(f'Статус {response.status_code} ----{url[0]}')
                except Exception as e:
                    print(e)

                try:
                    data_json = response.json()
                except Exception as e:
                    continue

                with open(filename, 'w') as f:
                    json.dump(data_json, f)
            print(f'Сохранил объявлений {counter}')
            counter += 1


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


def create_sql():

    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(
        # host="localhost",  # ваш хост, например "localhost"
        host="vpromo2.mysql.tools",  # ваш хост, например "localhost"
        user="vpromo2_usa",  # ваше имя пользователя
        password="^~Hzd78vG4",  # ваш пароль
        database="vpromo2_usa"  # имя вашей базы данных
    )

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute("USE vpromo2_usa")

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
sale_location VARCHAR(255)
)
    """)

    # Закрываем соединение
    cnx.close()


if __name__ == '__main__':
    # totalElements = get_totalElements()
    # get_request(totalElements)
    # get_id_ad_and_url()
    # get_product()
    # parsin()
    create_sql()
