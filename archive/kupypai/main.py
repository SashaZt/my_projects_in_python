import mysql.connector
import random
from bs4 import BeautifulSoup
import csv
import requests
import glob
import json
import os
from datetime import datetime
from dateutil import parser
import schedule
import time
import threading


def course_dollars():
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
    return course_dollars


def get_url_ad():

    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_gid': 'GA1.2.1888910465.1690273079',
        '_gat_UA-200319004-1': '1',
        '_ga_MD7LGRXX6R': 'GS1.2.1690372363.28.1.1690372740.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gid=GA1.2.1888910465.1690273079; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1690372363.28.1.1690372740.60.0.0',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://kupypai.com/profile/announcement/list/client',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    offset = 100
    for page_list in range(1, 9):
        if page_list == 1:
            params = {
                'limit': '100',
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            with open(f'json_list/data_0{page_list}.json', 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        if page_list > 1:
            params = {
                'limit': '100',
                'offset': offset,
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            with open(f'json_list/data_0{page_list}.json', 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
            offset += 100
        time.sleep(2)


def get_id_ad():
    """Получаем список всех объявлений"""
    folders_json = fr"C:\scrap_tutorial-master\kupypai\json_list\*.json"
    files_json = glob.glob(folders_json)

    with open('id_ad.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        for j in files_json:
            with open(j, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            id_ads = json_data['data']
            for item in id_ads['items']:
                id_ad = item['id']
                data_ad = item['createdAt']
                dt = parser.parse(data_ad)
                status_ad = item['statusDisplay']
                # Приведите объект datetime к нужному формату
                formatted_time = dt.strftime('%H:%M')
                formatted_date = dt.strftime('%d.%m.%Y')
                writer.writerow([id_ad, status_ad, formatted_time, formatted_date])

def get_ad():
    data = []

    with open('id_ad.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691463.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691463.60.0.0',
        'dnt': '1',
        'referer': 'https://kupypai.com/profile/announcement/2181/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    page = 0
    for d in data:
        page += 1
        name_files = f'json_ad/{d[0]}.json'
        pause_time = random.randint(5, 10)
        if not os.path.exists(name_files):
            response = requests.get(f'https://kupypai.com/api/v1/announcement/{d[0]}/retrieve-update/', cookies=cookies,
                                    headers=headers)
            json_data = response.json()
            with open(name_files, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
            time.sleep(pause_time)
        print(f'{len(data) - page}')


def parsing_ad():
    folders_json = fr"C:\scrap_tutorial-master\kupypai\json_ad\*.json"
    files_json = glob.glob(folders_json)
    dollars = course_dollars().replace(",", ".")
    dollars = float(dollars)
    data_row = []

    with open('id_ad.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data_row.append(row)
    data_dict = {}

    for row in data_row:
        id_ad_row, status_ad, formatted_time_row, formatted_date_row = row[0].split(';')
        data_dict[int(id_ad_row)] = (formatted_time_row, formatted_date_row)
    heandler = ['Id', 'Статус', 'Площа', 'Дохідність', 'Ціна за 1 га UAH', 'Ціна за 1 га $', 'Ціна ділянки UAH',
                'Ціна ділянки $', 'Річний орендний дохід після податків UAH',
                'Річний орендний дохід після податків $', 'Населений пункт', "",
                "Район", "Область", "Країна", 'Дата публікації', 'Час публікації', 'Оголошення ID', 'Кадастровий номер',
                'Термін оренди',
                'Орендна плата, за рік UAH', 'Орендна плата, за рік $', 'Призначення', 'Координати', "Власник ЄДРПО",
                "Власник", "Телефон", "Назва компанії",
                'ЄДРПО Компаніїї', "ПІБ", 'Контакти компанії', 'email'

                ]
    with open('ad.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        writer.writerow(heandler)
        for j in files_json[:1]:
            with open(j, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            id_ad = json_data['data']['item']['id']
            formatted_time_row = ''
            formatted_date_row = ''
            if id_ad in data_dict:
                formatted_time_row, formatted_date_row = data_dict[id_ad]
            title_holding = json_data['data']['item']['renterCompany']['holding']['title']
            status_ad = json_data['data']['item']['statusDisplay']
            currency_ad = json_data['data']['item']['currency']  # Валюта
            identifier_ad = json_data['data']['item']['identifier']  # Индификатор
            cadastre_ad = json_data['data']['item']['cadastre']  # Кадастровий номер
            price_ad = f"{json_data['data']['item']['price']} {currency_ad}"  # Ціна ділянки:
            price_ad_dol = round(int(json_data['data']['item']['price']) / dollars)  # Ціна ділянки $:
            pricePerOne_ad = f"{json_data['data']['item']['pricePerOne']} {currency_ad}"  # Ціна за 1 га
            pricePerOne_ad_dol = round(int(json_data['data']['item']['pricePerOne']) / dollars)  # Ціна за 1 га $
            rentPeriod_ad = json_data['data']['item']['rentPeriod']  # Термін оренди:
            rentRate_ad_dol = round(int(json_data['data']['item']['rentRate']) / dollars)  # Орендна плата, за рік $
            rentRate_ad = f"{json_data['data']['item']['rentRate']} {currency_ad}"  # Орендна плата, за рік
            rentRateClean_ad = f"{json_data['data']['item']['rentRateClean']} {currency_ad}"  # Річний орендний дохід після податків
            rentRateClean_ad_dol = round(
                int(json_data['data']['item']['rentRateClean']) / dollars)  # Річний орендний дохід після податків $
            area_ad = json_data['data']['item']['rentalYield'].replace('.', ',')  # Площа:
            purpose_ad = json_data['data']['item']['purpose']  # Призначення
            rentalYield_ad = json_data['data']['item']['rentalYield']  # Дохідність:
            koatuuLocation_ad = json_data['data']['item']['koatuuLocation']  # Адреса
            locations_list = koatuuLocation_ad.split(", ")
            if len(locations_list) == 4:
                locations_list.insert(0, None)
            locations_list += [None] * (5 - len(locations_list))
            geoCoordinates_ad = json_data['data']['item']['geoCoordinates']  # Координати
            ownerEdrpou_ad = json_data['data']['item']['ownerEdrpou']  # ЕДРПО
            ownerName_ad = json_data['data']['item']['ownerName']  # Назва
            ownerPhone_ad = json_data['data']['item']['ownerPhone']  # Телефон
            title_ad = json_data['data']['item']['renterCompany']['title']  # Назва фирми
            edrpou_ad = json_data['data']['item']['renterCompany']['edrpou']  # Фирми ЕДРПО
            contactName_ad = json_data['data']['item']['renterCompany']['contactName']  # Фирми ЕДРПО
            contactPhone_ad = json_data['data']['item']['renterCompany']['contactPhone']  # Фирми ЕДРПО
            email_ad = json_data['data']['item']['renterCompany']['email']  # Фирми ЕДРПО
            data = [
                       id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad,
                       pricePerOne_ad_dol, price_ad,
                       price_ad_dol, rentRateClean_ad,
                       rentRateClean_ad_dol] + locations_list + [formatted_date_row, formatted_time_row, identifier_ad,
                                                                 cadastre_ad, rentPeriod_ad, rentRate_ad,
                                                                 rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                                                                 ownerEdrpou_ad, ownerName_ad,
                                                                 ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
                                                                 contactPhone_ad, email_ad
                                                                 ]

            writer.writerow(data)


def update_ad():
    dollars = course_dollars().replace(",", ".")
    dollars = float(dollars)
    data_row = []
    with open('id_ad.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data_row.append(row)
    data_dict = {}
    for row in data_row:
        id_ad_row, status_ad, formatted_time_row, formatted_date_row = row[0].split(';')
        data_dict[int(id_ad_row)] = (status_ad, formatted_time_row, formatted_date_row)
    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_gat_UA-200319004-1': '1',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691128.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691128.60.0.0',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://kupypai.com/profile/announcement/list/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {
        'limit': '100',
    }
    response = requests.get(
        'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    now = datetime.now()
    formatted_now = now.strftime("%H_%M_%d.%m.%Y")
    json_data = response.json()
    id_ads = json_data['data']
    all_ad = int(json_data['data']['pagination']['total'])
    pages_list = all_ad // 100

    # for item in id_ads['items']:
    #     id_ad = item['id']
    #     if id_ad not in data_dict:
    #         print(id_ad)
    """Новые объявления"""
    with open('id_ad.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        for page_list in range(1, 2):  # Проверяем сугубо первую страницу
            if page_list == 1:
                params = {
                    'limit': '100',
                }
                response = requests.get(
                    'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()
                id_ads = json_data['data']
                for item in id_ads['items']:
                    id_ad = item['id']
                    if id_ad not in data_dict:
                        id_ad = item['id']
                        data_ad = item['createdAt']
                        dt = parser.parse(data_ad)
                        status_ad = item['statusDisplay']
                        formatted_time = dt.strftime('%H:%M')
                        formatted_date = dt.strftime('%d.%m.%Y')
                        writer.writerow([id_ad, status_ad, formatted_time, formatted_date])
                    else:
                        continue
    folders_json = r"C:\scrap_tutorial-master\kupypai\json_ad\*.json"
    files_json = glob.glob(folders_json)
    file_names = []

    for file in files_json:
        base = os.path.basename(file)  # Получение имени файла с расширением
        name = os.path.splitext(base)[0]  # Удаление расширения из имени файла
        file_names.append(name)

    data_row = []
    with open('id_ad.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data_row.append(row)

    data_dict = {}
    for row in data_row:
        id_ad_row, status_ad, formatted_time_row, formatted_date_row = row[0].split(';')
        data_dict[int(id_ad_row)] = (status_ad, formatted_time_row, formatted_date_row)

    file_names_int = [int(file) for file in file_names]  # Преобразуем имена файлов в целые числа
    heandler = ['Id', 'Статус', 'Площа', 'Дохідність', 'Ціна за 1 га UAH', 'Ціна за 1 га $', 'Ціна ділянки UAH',
                'Ціна ділянки $', 'Річний орендний дохід після податків UAH',
                'Річний орендний дохід після податків $', 'Населений пункт', "",
                "Район", "Область", "Країна", 'Дата публікації', 'Час публікації', 'Оголошення ID', 'Кадастровий номер',
                'Термін оренди',
                'Орендна плата, за рік UAH', 'Орендна плата, за рік $', 'Призначення', 'Координати', "Власник ЄДРПО",
                "Власник", "Телефон", "Назва компанії",
                'ЄДРПО Компаніїї', "ПІБ", 'Контакти компанії', 'email'

                ]
    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691463.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691463.60.0.0',
        'dnt': '1',
        'referer': 'https://kupypai.com/profile/announcement/2181/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    now = datetime.now()
    formatted_now = now.strftime("%H_%M_%d.%m.%Y")

    # with open(f'{formatted_now}.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile, delimiter=';', quotechar='|')
    #     writer.writerow(heandler)
    heandler_written = False  # Флаг, указывающий, были ли записаны заголовки
    writer = None  # Переменная, которая будет содержать объект writer в дальнейшем
    for key in data_dict.keys():
        if key not in file_names_int:
            if not heandler_written:
                with open(f'{formatted_now}.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';', quotechar='|')
                    writer.writerow(heandler)
                    heandler_written = True

                    pause_time = random.randint(5, 10)
                    response = requests.get(f'https://kupypai.com/api/v1/announcement/{key}/retrieve-update/',
                                            cookies=cookies,
                                            headers=headers)
                    name_files = f'json_ad/{key}.json'
                    json_data = response.json()
                    with open(name_files, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
                    id_ad = json_data['data']['item']['id']
                    formatted_time_row = ''
                    formatted_date_row = ''
                    if id_ad in data_dict:
                        id_ad_row, formatted_time_row, formatted_date_row = data_dict[id_ad]
                    status_ad = json_data['data']['item']['statusDisplay']
                    currency_ad = json_data['data']['item']['currency']  # Валюта
                    identifier_ad = json_data['data']['item']['identifier']  # Индификатор
                    cadastre_ad = json_data['data']['item']['cadastre']  # Кадастровий номер
                    price_ad = f"{json_data['data']['item']['price']} {currency_ad}"  # Ціна ділянки:
                    price_ad_dol = round(int(json_data['data']['item']['price']) / dollars)  # Ціна ділянки $:
                    pricePerOne_ad = f"{json_data['data']['item']['pricePerOne']} {currency_ad}"  # Ціна за 1 га
                    pricePerOne_ad_dol = round(
                        int(json_data['data']['item']['pricePerOne']) / dollars)  # Ціна за 1 га $
                    rentPeriod_ad = json_data['data']['item']['rentPeriod']  # Термін оренди:
                    rentRate_ad_dol = round(
                        int(json_data['data']['item']['rentRate']) / dollars)  # Орендна плата, за рік $
                    rentRate_ad = f"{json_data['data']['item']['rentRate']} {currency_ad}"  # Орендна плата, за рік
                    rentRateClean_ad = f"{json_data['data']['item']['rentRateClean']} {currency_ad}"  # Річний орендний дохід після податків
                    rentRateClean_ad_dol = round(
                        int(json_data['data']['item'][
                                'rentRateClean']) / dollars)  # Річний орендний дохід після податків $
                    area_ad = json_data['data']['item']['rentalYield'].replace('.', ',')  # Площа:
                    purpose_ad = json_data['data']['item']['purpose']  # Призначення
                    rentalYield_ad = json_data['data']['item']['rentalYield']  # Дохідність:
                    koatuuLocation_ad = json_data['data']['item']['koatuuLocation']  # Адреса
                    locations_list = koatuuLocation_ad.split(", ")
                    if len(locations_list) == 4:
                        locations_list.insert(0, None)
                    locations_list += [None] * (5 - len(locations_list))
                    geoCoordinates_ad = json_data['data']['item']['geoCoordinates']  # Координати
                    ownerEdrpou_ad = json_data['data']['item']['ownerEdrpou']  # ЕДРПО
                    ownerName_ad = json_data['data']['item']['ownerName']  # Назва
                    ownerPhone_ad = json_data['data']['item']['ownerPhone']  # Телефон
                    title_ad = json_data['data']['item']['renterCompany']['title']  # Назва фирми
                    edrpou_ad = json_data['data']['item']['renterCompany']['edrpou']  # Фирми ЕДРПО
                    contactName_ad = json_data['data']['item']['renterCompany']['contactName']  # Фирми ЕДРПО
                    contactPhone_ad = json_data['data']['item']['renterCompany']['contactPhone']  # Фирми ЕДРПО
                    email_ad = json_data['data']['item']['renterCompany']['email']  # Фирми ЕДРПО

                    data = [
                               id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad,
                               pricePerOne_ad_dol, price_ad,
                               price_ad_dol, rentRateClean_ad,
                               rentRateClean_ad_dol] + locations_list + [formatted_date_row, formatted_time_row,
                                                                         identifier_ad,
                                                                         cadastre_ad, rentPeriod_ad, rentRate_ad,
                                                                         rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                                                                         ownerEdrpou_ad, ownerName_ad,
                                                                         ownerPhone_ad, title_ad, edrpou_ad,
                                                                         contactName_ad,
                                                                         contactPhone_ad, email_ad
                                                                         ]

                    writer.writerow(data)
                    time.sleep(pause_time)


def update_status_ad():
    data_row = []
    with open('id_ad.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data_row.append(row)
    data_dict = {}
    for row in data_row:
        id_ad_row, status_ad, formatted_time_row, formatted_date_row = row[0].split(';')
        data_dict[int(id_ad_row)] = (status_ad, formatted_time_row, formatted_date_row)

    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_gat_UA-200319004-1': '1',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691128.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691128.60.0.0',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://kupypai.com/profile/announcement/list/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {
        'limit': '100',
    }
    response = requests.get(
        'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    json_data = response.json()
    all_ad = int(json_data['data']['pagination']['total'])
    pages_list = all_ad // 100
    offset = 100
    with open('new_status.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        now = datetime.now()
        formatted_now = now.strftime("%H_%M_%d.%m.%Y")
        # for page_list in range(1, 2):
        for page_list in range(1, pages_list + 1):
            missing_ids = []
            if page_list == 1:
                params = {
                    'limit': '100',
                }
                response = requests.get(
                    'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()
                id_ads = json_data['data']
                site_data = []

                for item in id_ads['items']:
                    id_ad = item['id']
                    status_ad = item['statusDisplay']
                    site_data.append({'id': id_ad, 'status': status_ad})
                for item in site_data:
                    item_id = item['id']
                    item_status = item['status']

                    if item_id in data_dict:
                        # Элемент найден в data_dict
                        if data_dict[item_id][0] != item_status:
                            # Статус изменился
                            writer.writerow([formatted_now, id_ad, status_ad])
                            # data_dict[item_id] = (item_status, *data_dict[item_id][1:])
                    else:

                        # Элемента нет в data_dict
                        missing_ids.append(f'Нет объявления с id:{item_id}')

            if page_list > 1:
                params = {
                    'limit': '100',
                    'offset': offset,
                }
                response = requests.get(
                    'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()
                id_ads = json_data['data']
                site_data = []

                for item in id_ads['items']:
                    id_ad = item['id']
                    status_ad = item['statusDisplay']
                    site_data.append({'id': id_ad, 'status': status_ad})
                for item in site_data:
                    item_id = item['id']
                    item_status = item['status']

                    if item_id in data_dict:
                        # Элемент найден в data_dict
                        if data_dict[item_id][0] != item_status:
                            # Статус изменился
                            writer.writerow([formatted_now, id_ad, status_ad])
                            # data_dict[item_id] = (item_status, *data_dict[item_id][1:])
                    else:
                        # Элемента нет в data_dict
                        missing_ids.append(f'Нет объявления с id:{item_id}')
                offset += 100
            writer.writerow(missing_ids)
            time.sleep(5)


def create_sql():

    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(user='python_mysql', password='python_mysql', host='localhost')

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    cursor.execute("CREATE DATABASE kupypai_com")

    # Указываем, что будем использовать эту базу данных
    cursor.execute("USE kupypai_com")

    # 3. В базе данных создаем таблицу ad
    # 4. Создаем необходимые колонки
    cursor.execute("""
    CREATE TABLE ad (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_ad INT,
        status_ad VARCHAR(255),
        area_ad FLOAT,
        rentalYield_ad FLOAT,
        pricePerOne_ad FLOAT,
        pricePerOne_ad_dol FLOAT,
        price_ad FLOAT,
        price_ad_dol FLOAT,
        rentRateClean_ad FLOAT,
        rentRateClean_ad_dol FLOAT,
        locations_list_00 VARCHAR(255),
        locations_list_01 VARCHAR(255),
        locations_list_02 VARCHAR(255),
        locations_list_03 VARCHAR(255),
        locations_list_04 VARCHAR(255),
        formatted_date_row_add DATE,
        formatted_date_row_chn DATE,
        formatted_time_row_chn TIME,
        identifier_ad VARCHAR(255),
        cadastre_ad VARCHAR(255),
        rentPeriod_ad VARCHAR(255),
        rentRate_ad FLOAT,
        rentRate_ad_dol FLOAT,
        purpose_ad VARCHAR(255),
        geoCoordinates_ad VARCHAR(255),
        ownerEdrpou_ad VARCHAR(255),
        ownerName_ad VARCHAR(255),
        ownerPhone_ad VARCHAR(255),
        title_ad VARCHAR(255),
        edrpou_ad VARCHAR(255),
        contactName_ad VARCHAR(255),
        contactPhone_ad VARCHAR(255),
        email_ad VARCHAR(255)
    )
    """)

    # Закрываем соединение
    cnx.close()


def parsing_ad_in_sql():
    folders_json = fr"C:\scrap_tutorial-master\kupypai\json_ad\*.json"
    files_json = glob.glob(folders_json)
    dollars = course_dollars().replace(",", ".")
    dollars = float(dollars)
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()
    for j in files_json:
        with open(j, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        id_ad = json_data['data']['item']['id']
        status_ad = json_data['data']['item']['statusDisplay']
        identifier_ad = json_data['data']['item']['identifier']  # Индификатор
        cadastre_ad = json_data['data']['item']['cadastre']  # Кадастровий номер
        price_ad = f"{json_data['data']['item']['price']}"  # Ціна ділянки:
        price_ad_dol = round(int(json_data['data']['item']['price']) / dollars)  # Ціна ділянки $:
        pricePerOne_ad = f"{json_data['data']['item']['pricePerOne']}"  # Ціна за 1 га
        pricePerOne_ad_dol = round(int(json_data['data']['item']['pricePerOne']) / dollars)  # Ціна за 1 га $
        rentPeriod_ad = json_data['data']['item']['rentPeriod']  # Термін оренди:
        rentRate_ad_dol = round(int(json_data['data']['item']['rentRate']) / dollars)  # Орендна плата, за рік $
        rentRate_ad = f"{json_data['data']['item']['rentRate']}"  # Орендна плата, за рік
        rentRateClean_ad = f"{json_data['data']['item']['rentRateClean']}"  # Річний орендний дохід після податків
        rentRateClean_ad_dol = round(
            int(json_data['data']['item']['rentRateClean']) / dollars)  # Річний орендний дохід після податків $
        area_ad = json_data['data']['item']['rentalYield']  # Площа:.replace('.', ',')
        purpose_ad = json_data['data']['item']['purpose']  # Призначення
        rentalYield_ad = json_data['data']['item']['rentalYield']  # Дохідність:
        koatuuLocation_ad = json_data['data']['item']['koatuuLocation']  # Адреса
        locations_list = koatuuLocation_ad.split(", ")
        if len(locations_list) == 4:
            locations_list.insert(0, None)
        locations_list += [None] * (5 - len(locations_list))
        locations_list_00 = locations_list[0]
        locations_list_01 = locations_list[1]
        locations_list_02 = locations_list[2]
        locations_list_03 = locations_list[3]
        locations_list_04 = locations_list[4]
        formatted_date_row_add = json_data['data']['item']['estimateDate']
        geoCoordinates_ad = ",".join(str(x) for x in json_data['data']['item']['geoCoordinates'])
        ownerEdrpou_ad = json_data['data']['item']['ownerEdrpou']  # ЕДРПО
        ownerName_ad = json_data['data']['item']['ownerName']  # Назва
        ownerPhone_ad = json_data['data']['item']['ownerPhone']  # Телефон
        title_ad = json_data['data']['item']['renterCompany']['title']  # Назва фирми
        edrpou_ad = json_data['data']['item']['renterCompany']['edrpou']  # Фирми ЕДРПО
        contactName_ad = json_data['data']['item']['renterCompany']['contactName']  # Фирми ЕДРПО
        contactPhone_ad = json_data['data']['item']['renterCompany']['contactPhone']  # Фирми ЕДРПО
        email_ad = json_data['data']['item']['renterCompany']['email']  # Фирми ЕДРПО
        formatted_date_row_chn = formatted_date_row_add
        formatted_time_row_chn = "00:00:00"
        data = [
            id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad,
            price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01,
            locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add,
            formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad,
            rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
            ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
            contactPhone_ad, email_ad
        ]
        insert_query = """
            INSERT INTO ad (
                id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad, 
                price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01, 
                locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add, 
                 formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad, 
                rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad, 
                ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad, 
                contactPhone_ad, email_ad
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        cursor.execute(insert_query, data)
    # Закрываем соединение
    cnx.commit()
    cnx.close()


def update_ad_in_sql():
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT id_ad, status_ad FROM ad")  #

    data_dict = {}
    for row in cursor:
        data_dict[int(row[0])] = row[1]  # row[0] это id_ad, row[1] это status_ad
    dollars = course_dollars().replace(",", ".")
    dollars = float(dollars)
    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_gat_UA-200319004-1': '1',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691128.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691128.60.0.0',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://kupypai.com/profile/announcement/list/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {
        'limit': '100',
    }
    response = requests.get(
        'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    json_data = response.json()
    all_ad = int(json_data['data']['pagination']['total'])
    pages_list = all_ad // 100
    """Новые объявления"""
    for page_list in range(1, pages_list + 1):
        pause_time = random.randint(5, 10)
        if page_list == 1:
            params = {
                'limit': '100',
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            id_ads = json_data['data']
            for item in id_ads['items']:
                id_ad = item['id']

                if id_ad not in data_dict:
                    id_ad = item['id']
                    cookies = {
                        'current_currency': 'UAH',
                        '_ga': 'GA1.2.905147567.1689674622',
                        '_gid': 'GA1.2.555662714.1689674622',
                        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
                        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
                        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691463.60.0.0',
                    }

                    headers = {
                        'authority': 'kupypai.com',
                        'accept': '*/*',
                        'accept-language': 'uk',
                        'content-type': 'application/json',
                        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691463.60.0.0',
                        'dnt': '1',
                        'referer': 'https://kupypai.com/profile/announcement/2181/client',
                        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'same-origin',
                        'sec-fetch-site': 'same-origin',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
                        'x-requested-with': 'XMLHttpRequest',
                    }
                    response = requests.get(f'https://kupypai.com/api/v1/announcement/{id_ad}/retrieve-update/',
                                            cookies=cookies,
                                            headers=headers)
                    json_data = response.json()
                    id_ad = json_data['data']['item']['id']
                    status_ad = json_data['data']['item']['statusDisplay']
                    identifier_ad = json_data['data']['item']['identifier']  # Индификатор
                    cadastre_ad = json_data['data']['item']['cadastre']  # Кадастровий номер
                    price_ad = f"{json_data['data']['item']['price']}"  # Ціна ділянки:
                    price_ad_dol = round(int(json_data['data']['item']['price']) / dollars)  # Ціна ділянки $:
                    pricePerOne_ad = f"{json_data['data']['item']['pricePerOne']}"  # Ціна за 1 га
                    pricePerOne_ad_dol = round(
                        int(json_data['data']['item']['pricePerOne']) / dollars)  # Ціна за 1 га $
                    rentPeriod_ad = json_data['data']['item']['rentPeriod']  # Термін оренди:
                    rentRate_ad_dol = round(
                        int(json_data['data']['item']['rentRate']) / dollars)  # Орендна плата, за рік $
                    rentRate_ad = f"{json_data['data']['item']['rentRate']}"  # Орендна плата, за рік
                    rentRateClean_ad = f"{json_data['data']['item']['rentRateClean']}"  # Річний орендний дохід після податків
                    rentRateClean_ad_dol = round(
                        int(json_data['data']['item'][
                                'rentRateClean']) / dollars)  # Річний орендний дохід після податків $
                    area_ad = json_data['data']['item']['rentalYield']  # Площа:.replace('.', ',')
                    purpose_ad = json_data['data']['item']['purpose']  # Призначення
                    rentalYield_ad = json_data['data']['item']['rentalYield']  # Дохідність:
                    koatuuLocation_ad = json_data['data']['item']['koatuuLocation']  # Адреса
                    locations_list = koatuuLocation_ad.split(", ")
                    if len(locations_list) == 4:
                        locations_list.insert(0, None)
                    locations_list += [None] * (5 - len(locations_list))
                    locations_list_00 = locations_list[0]
                    locations_list_01 = locations_list[1]
                    locations_list_02 = locations_list[2]
                    locations_list_03 = locations_list[3]
                    locations_list_04 = locations_list[4]
                    formatted_date_row_add = json_data['data']['item']['estimateDate']
                    geoCoordinates_ad = ",".join(str(x) for x in json_data['data']['item']['geoCoordinates'])
                    ownerEdrpou_ad = json_data['data']['item']['ownerEdrpou']  # ЕДРПО
                    ownerName_ad = json_data['data']['item']['ownerName']  # Назва
                    ownerPhone_ad = json_data['data']['item']['ownerPhone']  # Телефон
                    title_ad = json_data['data']['item']['renterCompany']['title']  # Назва фирми
                    edrpou_ad = json_data['data']['item']['renterCompany']['edrpou']  # Фирми ЕДРПО
                    contactName_ad = json_data['data']['item']['renterCompany']['contactName']  # Фирми ЕДРПО
                    contactPhone_ad = json_data['data']['item']['renterCompany']['contactPhone']  # Фирми ЕДРПО
                    email_ad = json_data['data']['item']['renterCompany']['email']  # Фирми ЕДРПО
                    formatted_date_row_chn = formatted_date_row_add
                    formatted_time_row_chn = "00:00:00"
                    data = [
                        id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad,
                        price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01,
                        locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add,
                        formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad,
                        rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                        ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
                        contactPhone_ad, email_ad
                    ]
                    insert_query = """
                                INSERT INTO ad (
                                    id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad, 
                                    price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01, 
                                    locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add, 
                                     formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad, 
                                    rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad, 
                                    ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad, 
                                    contactPhone_ad, email_ad
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """

                    cursor.execute(insert_query, data)
                    # print(f'Новое {id_ad}')
                else:
                    # print(f'Уже есть такой {id_ad}')
                    continue
        time.sleep(pause_time)

        offset = 100
        if page_list > 1:
            params = {
                'limit': '100',
                'offset': offset,
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            id_ads = json_data['data']
            for item in id_ads['items']:
                id_ad = item['id']
                if id_ad not in data_dict:
                    id_ad = item['id']
                    cookies = {
                        'current_currency': 'UAH',
                        '_ga': 'GA1.2.905147567.1689674622',
                        '_gid': 'GA1.2.555662714.1689674622',
                        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
                        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
                        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691463.60.0.0',
                    }

                    headers = {
                        'authority': 'kupypai.com',
                        'accept': '*/*',
                        'accept-language': 'uk',
                        'content-type': 'application/json',
                        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691463.60.0.0',
                        'dnt': '1',
                        'referer': 'https://kupypai.com/profile/announcement/2181/client',
                        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'same-origin',
                        'sec-fetch-site': 'same-origin',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
                        'x-requested-with': 'XMLHttpRequest',
                    }
                    response = requests.get(f'https://kupypai.com/api/v1/announcement/{id_ad}/retrieve-update/',
                                            cookies=cookies,
                                            headers=headers)
                    json_data = response.json()
                    id_ad = json_data['data']['item']['id']
                    status_ad = json_data['data']['item']['statusDisplay']
                    identifier_ad = json_data['data']['item']['identifier']  # Индификатор
                    cadastre_ad = json_data['data']['item']['cadastre']  # Кадастровий номер
                    price_ad = f"{json_data['data']['item']['price']}"  # Ціна ділянки:
                    price_ad_dol = round(int(json_data['data']['item']['price']) / dollars)  # Ціна ділянки $:
                    pricePerOne_ad = f"{json_data['data']['item']['pricePerOne']}"  # Ціна за 1 га
                    pricePerOne_ad_dol = round(
                        int(json_data['data']['item']['pricePerOne']) / dollars)  # Ціна за 1 га $
                    rentPeriod_ad = json_data['data']['item']['rentPeriod']  # Термін оренди:
                    rentRate_ad_dol = round(
                        int(json_data['data']['item']['rentRate']) / dollars)  # Орендна плата, за рік $
                    rentRate_ad = f"{json_data['data']['item']['rentRate']}"  # Орендна плата, за рік
                    rentRateClean_ad = f"{json_data['data']['item']['rentRateClean']}"  # Річний орендний дохід після податків
                    rentRateClean_ad_dol = round(
                        int(json_data['data']['item'][
                                'rentRateClean']) / dollars)  # Річний орендний дохід після податків $
                    area_ad = json_data['data']['item']['rentalYield']  # Площа:.replace('.', ',')
                    purpose_ad = json_data['data']['item']['purpose']  # Призначення
                    rentalYield_ad = json_data['data']['item']['rentalYield']  # Дохідність:
                    koatuuLocation_ad = json_data['data']['item']['koatuuLocation']  # Адреса
                    locations_list = koatuuLocation_ad.split(", ")
                    if len(locations_list) == 4:
                        locations_list.insert(0, None)
                    locations_list += [None] * (5 - len(locations_list))
                    locations_list_00 = locations_list[0]
                    locations_list_01 = locations_list[1]
                    locations_list_02 = locations_list[2]
                    locations_list_03 = locations_list[3]
                    locations_list_04 = locations_list[4]
                    formatted_date_row_add = json_data['data']['item']['estimateDate']
                    geoCoordinates_ad = ",".join(str(x) for x in json_data['data']['item']['geoCoordinates'])
                    ownerEdrpou_ad = json_data['data']['item']['ownerEdrpou']  # ЕДРПО
                    ownerName_ad = json_data['data']['item']['ownerName']  # Назва
                    ownerPhone_ad = json_data['data']['item']['ownerPhone']  # Телефон
                    title_ad = json_data['data']['item']['renterCompany']['title']  # Назва фирми
                    edrpou_ad = json_data['data']['item']['renterCompany']['edrpou']  # Фирми ЕДРПО
                    contactName_ad = json_data['data']['item']['renterCompany']['contactName']  # Фирми ЕДРПО
                    contactPhone_ad = json_data['data']['item']['renterCompany']['contactPhone']  # Фирми ЕДРПО
                    email_ad = json_data['data']['item']['renterCompany']['email']  # Фирми ЕДРПО
                    formatted_date_row_chn = formatted_date_row_add
                    formatted_time_row_chn = "00:00:00"
                    data = [
                        id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad,
                        price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01,
                        locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add,
                        formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad,
                        rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                        ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
                        contactPhone_ad, email_ad
                    ]
                    insert_query = """
                                INSERT INTO ad (
                                    id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad, 
                                    price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01, 
                                    locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add, 
                                     formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad, 
                                    rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad, 
                                    ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad, 
                                    contactPhone_ad, email_ad
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """

                    cursor.execute(insert_query, data)
                    # print(f'Новое {id_ad}')
                    offset += 100
                    # Закрываем соединение
                else:
                    # print(f'Уже есть такой {id_ad}')
                    continue
        time.sleep(pause_time)

    cnx.commit()
    cnx.close()

    """Обновляем статус"""
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT id_ad, status_ad FROM ad")  #

    data_dict = {}
    for row in cursor:
        data_dict[int(row[0])] = row[1]  # row[0] это id_ad, row[1] это status_ad
    cookies = {
        'current_currency': 'UAH',
        '_ga': 'GA1.2.905147567.1689674622',
        '_gid': 'GA1.2.555662714.1689674622',
        'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
        '_gat_UA-200319004-1': '1',
        '_ga_MD7LGRXX6R': 'GS1.2.1689689658.4.1.1689691128.60.0.0',
    }

    headers = {
        'authority': 'kupypai.com',
        'accept': '*/*',
        'accept-language': 'uk',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1689689658.4.1.1689691128.60.0.0',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://kupypai.com/profile/announcement/list/client',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {
        'limit': '100',
    }
    response = requests.get(
        'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    json_data = response.json()
    all_ad = int(json_data['data']['pagination']['total'])
    pages_list = all_ad // 100
    offset = 100
    now = datetime.now()
    time_now = now.strftime("%H:%M")
    data_now = now.strftime("%Y-%m-%d")

    for page_list in range(1, pages_list + 1):
        pause_time = random.randint(5, 10)
        if page_list == 1:
            params = {
                'limit': '100',
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            id_ads_site = json_data['data']
            site_data = []

            for item_site in id_ads_site['items']:
                id_ad = item_site['id']
                status_ad = item_site['statusDisplay']
                site_data.append({'id': id_ad, 'status': status_ad})

            for item in site_data:
                item_id = item['id']
                item_status = item['status']

                if item_id in data_dict:
                    if item_status != data_dict[item_id]:
                        cursor.execute(
                            "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
                            (item_status, time_now, data_now, item_id))
                        # print(f'Был статус {data_dict[item_id]}, стал статус {item_status}')
                    else:
                        continue

                else:
                    # print(item_id)
                    item_status = "Нет больше на сайте"
                    cursor.execute(
                        "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
                        (item_status, time_now, data_now, item_id))
        time.sleep(pause_time)
        if page_list > 1:
            params = {
                'limit': '100',
                'offset': offset,
            }
            response = requests.get(
                'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            id_ads_site = json_data['data']
            site_data = []

            for item_site in id_ads_site['items']:
                id_ad = item_site['id']
                status_ad = item_site['statusDisplay']
                site_data.append({'id': id_ad, 'status': status_ad})

            for item in site_data:
                item_id = item['id']
                item_status = item['status']

                if item_id in data_dict:
                    if item_status != data_dict[item_id]:
                        cursor.execute(
                            "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
                            (item_status, time_now, data_now, item_id))
                        # print(f'Был статус {data_dict[item_id]}, стал статус {item_status}')
                    else:
                        continue


                else:
                    # print(item_id)
                    item_status = "Нет больше на сайте"
                    cursor.execute(
                        "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
                        (item_status, time_now, data_now, item_id))
            offset += 100
        time.sleep(pause_time)
    cnx.commit()


def delete_data_in_ad():
    """"безвозвратно удаляет все данные из указанной таблицы"""
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()
    cursor.execute("TRUNCATE TABLE ad")

    # закрываем соединение
    cnx.close()


def delete_diblicate_ad():
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()

    # # получаем id_ad, которые дублируются
    # cursor.execute("""
    # SELECT id_ad, COUNT(id_ad)
    # FROM ad
    # GROUP BY id_ad
    # HAVING COUNT(id_ad) > 1
    # """)
    #
    # # выводим дубликаты
    # for (id_ad, count) in cursor:
    #     print(f"id_ad {id_ad} повторяется {count} раз(а)")
    #
    """Удалить колонку"""
    cursor.execute("""
        ALTER TABLE ad
        DROP COLUMN formatted_time_row_add
    """)
    cnx.commit()
    # удаляем дубликаты
    # cursor.execute("""
    #     DELETE a1 FROM ad a1
    #     JOIN (
    #         SELECT id_ad, MAX(id) AS max_id
    #         FROM ad
    #         GROUP BY id_ad
    #         HAVING COUNT(*) > 1
    #     ) a2 ON a1.id_ad = a2.id_ad AND a1.id != a2.max_id
    # """)
    #
    # cnx.commit()

    # закрываем соединение с базой данных
    cursor.close()
    cnx.close()


# def job():
#     update_ad_in_sql()
# # Задаем расписание
# for i in range(9, 22):  # 22 для того, чтобы включить 21:00 в диапазон
#     schedule.every().day.at(f"{i:02d}:00").do(job)
#
# if __name__ == "__main__":
#     while True:
#         # Время сейчас
#         now = datetime.now().hour
#
#         # Если время между 9 утра и 21 вечера, запустить все запланированные задания
#         if 9 <= now < 22:
#             schedule.run_pending()
#         time.sleep(1)
if __name__ == '__main__':
    get_url_ad()
#     # get_id_ad()
#     # get_ad()
#     parsing_ad()
#
#     # update_ad()
#     # update_status_ad()
#     # create_sql()
#     # parsing_ad_in_sql()
#     update_ad_in_sql()
#     # delete_data_in_ad()
#     # delete_diblicate_ad()
