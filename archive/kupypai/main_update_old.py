from datetime import time as dt_time
import mysql.connector
import random
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
import time
import schedule


def main():
    """Новые объявления"""
    cnx = mysql.connector.connect(
        # host="localhost",  # ваш хост, например "localhost"
        host="185.65.245.79",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="4tz_{4!r%x8~E@W",  # ваш пароль
        database="kupypai_com"  # имя вашей базы данных
    )
    cursor = cnx.cursor()
    now = datetime.now()
    time_now = now.strftime("%H:%M")
    data_now = now.strftime("%Y-%m-%d")
    print(f'Подключился {time_now} {data_now} к БД для поиска новых id_av')
    cursor.execute("SELECT id_ad, status_ad FROM ad")  #

    data_dict = {}
    for row in cursor:
        data_dict[int(row[0])] = row[1]  # row[0] это id_ad, row[1] это status_ad

    dollars = course_dollars().replace(",", ".")
    dollars = float(dollars)
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
    all_ad = int(json_data['data']['pagination']['total'])
    pages_list = all_ad // 100
    # print(data_dict)
    print(f'Получил количество страниц {pages_list} в {time_now} {data_now}')
    for page_list in range(1, pages_list + 2):
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
                # print(id_ad)

                if id_ad not in data_dict:

                    id_ad = item['id']
                    print(id_ad)
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
                    response = requests.get(f'https://kupypai.com/api/v1/announcement/{id_ad}/retrieve-update/',
                                            cookies=cookies,
                                            headers=headers)
                    json_data = response.json()
                    id_ad = json_data['data']['item']['id']
                    title_holding = json_data['data']['item']['renterCompany']['holding']['title']
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
                    area_ad = json_data['data']['item']['area']  # Площа:.replace('.', ',')
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
                        contactPhone_ad, email_ad, title_holding
                    ]
                    insert_query = """
                                    INSERT INTO ad (
                                        id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad,
                                        price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01,
                                        locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add,
                                         formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad,
                                        rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                                        ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
                                        contactPhone_ad, email_ad, title_holding
                                    ) VALUES (
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                    )
                                """

                    cursor.execute(insert_query, data)
                    now = datetime.now()
                    time_now = now.strftime("%H:%M")
                    data_now = now.strftime("%Y-%m-%d")
                    print(f'Новое {id_ad} в {time_now} {data_now} со статусом {status_ad}')
                else:
                    print(f'Уже есть такой {id_ad}')
                    continue
        time.sleep(pause_time)

        offset = 100
        if page_list > 1:
            cookies = {
                'current_currency': 'UAH',
                '_ga': 'GA1.2.905147567.1689674622',
                'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
                'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
                '_gid': 'GA1.2.1888910465.1690273079',
                '_ga_MD7LGRXX6R': 'GS1.2.1690372363.28.1.1690372740.60.0.0',
            }

            headers = {
                'authority': 'kupypai.com',
                'accept': '*/*',
                'accept-language': 'uk',
                'content-type': 'application/json',
                # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gid=GA1.2.1888910465.1690273079; _ga_MD7LGRXX6R=GS1.2.1690372363.28.1.1690372740.60.0.0',
                'dnt': '1',
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
            id_ads = json_data['data']
            for item in id_ads['items']:
                id_ad = item['id']
                if id_ad not in data_dict:
                    id_ad = item['id']
                    print(id_ad)
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
                    response = requests.get(f'https://kupypai.com/api/v1/announcement/{id_ad}/retrieve-update/',
                                            cookies=cookies,
                                            headers=headers)
                    json_data = response.json()
                    id_ad = json_data['data']['item']['id']
                    title_holding = json_data['data']['item']['renterCompany']['holding']['title']
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
                    area_ad = json_data['data']['item']['area']  # Площа:.replace('.', ',')
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
                        contactPhone_ad, email_ad, title_holding
                    ]
                    insert_query = """
                                                        INSERT INTO ad (
                                                            id_ad, status_ad, area_ad, rentalYield_ad, pricePerOne_ad, pricePerOne_ad_dol, price_ad,
                                                            price_ad_dol, rentRateClean_ad, rentRateClean_ad_dol, locations_list_00, locations_list_01,
                                                            locations_list_02, locations_list_03, locations_list_04, formatted_date_row_add,
                                                             formatted_date_row_chn, formatted_time_row_chn, identifier_ad, cadastre_ad,
                                                            rentPeriod_ad, rentRate_ad, rentRate_ad_dol, purpose_ad, geoCoordinates_ad,
                                                            ownerEdrpou_ad, ownerName_ad, ownerPhone_ad, title_ad, edrpou_ad, contactName_ad,
                                                            contactPhone_ad, email_ad, title_holding
                                                        ) VALUES (
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                                        )
                                                    """

                    cursor.execute(insert_query, data)
                    now = datetime.now()
                    time_now = now.strftime("%H:%M")
                    data_now = now.strftime("%Y-%m-%d")
                    print(f'Новое {id_ad} в {time_now} {data_now} со статусом {status_ad}')
                    offset += 100
                    # Закрываем соединение
                else:
                    print(f'Уже есть такой {id_ad}')
                    continue
        time.sleep(pause_time)
    #
    cnx.commit()
    cnx.close()

    # """Обновляем статус"""
    # cnx = mysql.connector.connect(
    #     # host="185.65.245.79",  # ваш хост, например "localhost"
    #     host="localhost",  # ваш хост, например "localhost"
    #     user="python_mysql",  # ваше имя пользователя
    #     password="4tz_{4!r%x8~E@W",  # ваш пароль
    #     database="kupypai_com"  # имя вашей базы данных
    # )
    # # """Обновляем статус"""
    # # cnx = mysql.connector.connect(
    # #     host="localhost",  # ваш хост, например "localhost"
    # #     user="python_mysql",  # ваше имя пользователя
    # #     password="python_mysql",  # ваш пароль
    # #     database="kupypai_com"  # имя вашей базы данных
    # # )
    #
    # cursor = cnx.cursor()
    # cursor.execute("SELECT id_ad, status_ad, formatted_date_row_add FROM ad")
    # now = datetime.now()
    # time_now = now.strftime("%H:%M")
    # data_now = now.strftime("%Y-%m-%d")
    # print(f'Подключился в {time_now} {data_now} к БД для поиска новых статусов')
    # data_dict = {}
    # for row in cursor:
    #     data_dict[int(row[0])] = (row[1], row[2])  # row[0] это id_ad, row[1] это status_ad
    # # for id_ad, (status_ad, formatted_date_row_add) in data_dict.items():
    # #     print(f'ID: {id_ad}, Status: {status_ad}, Date: {formatted_date_row_add}')
    # cookies = {
    #     'current_currency': 'UAH',
    #     '_ga': 'GA1.2.905147567.1689674622',
    #     '_gid': 'GA1.2.555662714.1689674622',
    #     'csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
    #     'sessionid': 'nz041h2nmtl03vyfdjuf3jvgwzyvky3m',
    #     '_gat_UA-200319004-1': '1',
    #     '_ga_MD7LGRXX6R': 'GS1.2.1689941792.16.1.1689941999.60.0.0',
    # }
    #
    # headers = {
    #     'authority': 'kupypai.com',
    #     'accept': '*/*',
    #     'accept-language': 'uk',
    #     'cache-control': 'no-cache',
    #     'content-type': 'application/json',
    #     # 'cookie': 'current_currency=UAH; _ga=GA1.2.905147567.1689674622; _gid=GA1.2.555662714.1689674622; csrftoken=K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO; sessionid=nz041h2nmtl03vyfdjuf3jvgwzyvky3m; _gat_UA-200319004-1=1; _ga_MD7LGRXX6R=GS1.2.1689941792.16.1.1689941999.60.0.0',
    #     'dnt': '1',
    #     'pragma': 'no-cache',
    #     'referer': 'https://kupypai.com/profile/announcement/list/client',
    #     'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-platform': '"Windows"',
    #     'sec-fetch-dest': 'empty',
    #     'sec-fetch-mode': 'same-origin',
    #     'sec-fetch-site': 'same-origin',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    #     'x-csrftoken': 'K5uPBwwPeP67R82c5M5y2OTFiKChd4hKBCxR7b5PIUyYBNAXMveyjTHptqaimZiO',
    #     'x-requested-with': 'XMLHttpRequest',
    # }
    # params = {
    #     'limit': '100',
    # }
    # response = requests.get(
    #     'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
    #     params=params,
    #     cookies=cookies,
    #     headers=headers,
    # )
    # json_data = response.json()
    # all_ad = int(json_data['data']['pagination']['total'])
    # pages_list = all_ad // 100
    # offset = 100
    # now = datetime.now()
    # time_now = now.strftime("%H:%M")
    # data_now = now.strftime("%Y-%m-%d")
    #
    # # for page_list in range(1, 3):
    # for page_list in range(1, pages_list + 1):
    #     pause_time = random.randint(5, 10)
    #     if page_list == 1:
    #         params = {
    #             'limit': '100',
    #         }
    #         response = requests.get(
    #             'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
    #             params=params,
    #             cookies=cookies,
    #             headers=headers,
    #         )
    #         json_data = response.json()
    #         id_ads_site = json_data['data']
    #         site_data = []
    #
    #         for item_site in id_ads_site['items']:
    #             id_ad = item_site['id']
    #             status_ad = item_site['statusDisplay']
    #             site_data.append({'id': id_ad, 'status': status_ad})
    #
    #         for item in site_data:
    #             item_id = item['id']
    #             item_status = item['status']
    #             # print(item_status, data_dict[item_id][0].strip(), item_id)
    #             if item_id in data_dict:
    #                 if item_status != data_dict[item_id][0].strip():
    #                     formatted_date_row_add = data_dict[item_id][1]  # [1] это для formatted_date_row_add
    #
    #                     # Добавляем время 09:00 к formatted_date_row_add
    #                     nine_oclock = dt_time(9, 0)
    #                     formatted_date_row_add = datetime.combine(formatted_date_row_add, nine_oclock)
    #                     delta_time = now - formatted_date_row_add
    #
    #                     # Получаем количество часов из delta_time
    #                     delta_hours = delta_time.total_seconds() / 3600
    #                     hours = int(delta_hours)
    #                     now = datetime.now()
    #                     # data_now = now.date()  # Это дата
    #                     # time_now = now.time()  # Это время
    #                     # now_all = datetime.combine(data_now, time_now)
    #                     cursor.execute(
    #                         "UPDATE ad SET status_ad = %s, delta_time = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
    #                         (item_status, hours, time_now, data_now, item_id))
    #                     print(f'Был статус {data_dict[item_id][0]} у {item_id}, стал статус {item_status}')
    #
    #                 else:
    #                     continue
    #
    #             else:
    #                 continue
    #                 # print(f'Нет больше на сайте {item_id}')
    #                 # item_status = "Нет больше на сайте"
    #                 # cursor.execute(
    #                 #     "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
    #                 #     (item_status, time_now, data_now, item_id))
    #     time.sleep(pause_time)
    #     if page_list > 1:
    #         params = {
    #             'limit': '100',
    #             'offset': offset,
    #         }
    #         response = requests.get(
    #             'https://kupypai.com/api/v1/announcement/list/%3Bsort%3Dcreated_at_up/',
    #             params=params,
    #             cookies=cookies,
    #             headers=headers,
    #         )
    #         json_data = response.json()
    #         id_ads_site = json_data['data']
    #         site_data = []
    #
    #         for item_site in id_ads_site['items']:
    #             id_ad = item_site['id']
    #             status_ad = item_site['statusDisplay']
    #             site_data.append({'id': id_ad, 'status': status_ad})
    #
    #         for item in site_data:
    #             item_id = item['id']
    #             item_status = item['status']
    #
    #             if item_id in data_dict:
    #                 # print(item_status, data_dict[item_id][0].strip(), item_id)
    #                 if item_status != data_dict[item_id][0].strip():
    #
    #                     formatted_date_row_add = data_dict[item_id][1]  # [1] это для formatted_date_row_add
    #
    #                     # Добавляем время 09:00 к formatted_date_row_add
    #                     nine_oclock = dt_time(9, 0)
    #                     formatted_date_row_add = datetime.combine(formatted_date_row_add, nine_oclock)
    #                     delta_time = now - formatted_date_row_add
    #
    #                     # Получаем количество часов из delta_time
    #                     delta_hours = delta_time.total_seconds() / 3600
    #                     hours = int(delta_hours)
    #                     now = datetime.now()
    #                     # data_now = now.date()  # Это дата
    #                     # time_now = now.time()  # Это время
    #                     # now_all = datetime.combine(data_now, time_now)
    #                     cursor.execute(
    #                         "UPDATE ad SET status_ad = %s, delta_time = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
    #                         (item_status, hours, time_now, data_now, item_id))
    #                     print(f'Был статус {data_dict[item_id][0]} у {item_id}, стал статус {item_status}')
    #
    #                 else:
    #                     continue
    #
    #
    #             else:
    #                 continue
    #                 # print(f'Нет больше на сайте {item_id}')
    #                 # item_status = "Нет больше на сайте"
    #                 # cursor.execute(
    #                 #     "UPDATE ad SET status_ad = %s, formatted_time_row_chn = %s, formatted_date_row_chn = %s WHERE id_ad = %s",
    #                 #     (item_status, time_now, data_now, item_id))
    #         offset += 100
    #     time.sleep(pause_time)
    # cnx.commit()


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


if __name__ == '__main__':
    main()
