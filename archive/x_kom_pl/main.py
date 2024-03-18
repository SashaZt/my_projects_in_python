from pathlib import Path
import json
import os
import time
import csv
import glob
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor


# from selenium import webdriver


def get_totalElements():
    # print('Получаем количество страниц')
    cookies = {
        '__cf_bm': '7Oy.knRQnCkwbVRHIdJtHnt1_Yha1NuFpJYMZPm9R8c-1695897744-0-AWdCW4aG631MM/MGNAhxup13LCCFnj1+4Zf4OWvoll+vJ1Gny/HzWo/uBIoIPUHeH9uvlK0SVuwo8CxfYu6at42J573h69OKEb/kMOvZBq4e',
        'cf_clearance': '41CUbaBjtOeCFzYYyH5Qp4dnfPrWdtv0dTCZ1MOWiJM-1695897745-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695897745',
        'startquestion-session': '%7B%22expirationDate%22%3A1695901565373%2C%22data%22%3A%7B%22pageTime%22%3A4320%2C%22numberOfVisitedPages%22%3A3%7D%7D',
        'ai_user': 'CDFrB3qerVuJxBY0vQECfN|2023-09-28T10:46:10.553Z',
        'breakpointName': 'md',
        'trackingPermissionConsentsValue': '%7B%22cookies_analytics%22%3Afalse%2C%22cookies_personalization%22%3Afalse%2C%22cookies_advertisement%22%3Afalse%7D',
        'ai_session': 'qh0XVX55tyaQVs+sMTiOUh|1695897971812|1695898136962',
        'recently_viewed': '[%221148249%22]',
    }

    headers = {
        'authority': 'www.x-kom.pl',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': '__cf_bm=7Oy.knRQnCkwbVRHIdJtHnt1_Yha1NuFpJYMZPm9R8c-1695897744-0-AWdCW4aG631MM/MGNAhxup13LCCFnj1+4Zf4OWvoll+vJ1Gny/HzWo/uBIoIPUHeH9uvlK0SVuwo8CxfYu6at42J573h69OKEb/kMOvZBq4e; cf_clearance=41CUbaBjtOeCFzYYyH5Qp4dnfPrWdtv0dTCZ1MOWiJM-1695897745-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695897745; startquestion-session=%7B%22expirationDate%22%3A1695901565373%2C%22data%22%3A%7B%22pageTime%22%3A4320%2C%22numberOfVisitedPages%22%3A3%7D%7D; ai_user=CDFrB3qerVuJxBY0vQECfN|2023-09-28T10:46:10.553Z; breakpointName=md; trackingPermissionConsentsValue=%7B%22cookies_analytics%22%3Afalse%2C%22cookies_personalization%22%3Afalse%2C%22cookies_advertisement%22%3Afalse%7D; ai_session=qh0XVX55tyaQVs+sMTiOUh|1695897971812|1695898136962; recently_viewed=[%221148249%22]',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html?page=2&producent=4-hp&producent=5-microsoft&producent=7-msi&producent=14-lg&producent=27-asus&producent=28-toshiba&producent=46-lenovo&producent=57-gigabyte&producent=227-razer&producent=230-acer&producent=396-dell&producent=475-huawei&producent=731-krugermatz&hide_unavailable=1&__cf_chl_tk=iVtIwVSAJL7bSxWdnn04ZjtGjc30Oqy1rDsJxKoV6Nc-1695897742-0-gaNycGzNEmU',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    response = requests.get(
        'https://www.x-kom.pl/p/1148249-notebook-laptop-156-lenovo-thinkpad-e15-i5-1235u-16gb-512-win11p.html',
        cookies=cookies,
        headers=headers,
    )

    print(response.status_code)
    # data_json = response.json()
    # totalElements = data_json['TotalPages']
    # print(f'Всего {totalElements}')
    # return totalElements


def get_requests():
    totalElements = 56
    for i in range(1, totalElements + 1):
        filename = f"c:\\DATA\\x_kom_pl\\list\\data_{i}.html"
        if not os.path.exists(filename):
            cookies = {
                'ai_user': 'ohLCwL5YFWMJmZs3Oqzo6b|2023-09-28T17:54:04.779Z',
                'trackingPermissionConsentsValue': '%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D',
                '__cf_bm': '1ltSz9Ar9NetiHGVRHzXUNhlqbfFmXd5l.10ItgjJPI-1695964979-0-AR+Ne5vSeZbsHaVxPwaNKWNHBpyXuZzvVw11BmAhIWmESNKDUJ7jzuyfGCFFCG4HCZ4ZYqbROTBN1i0uDzeZuJHk+cP1AZioKMLVIm0MeWZs',
                'cf_chl_2': 'e13fd3fe31c9464',
                'cf_clearance': 'ujMjHigtJF6zEQNnKlsYnPqv01VQt_UWq4hjJREzcE4-1695965020-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695965020',
                'ai_session': '0PVcNBBSblYC5Pk8empDEZ|1695965021019|1695965021019',
                'breakpointName': 'md',
                'startquestion-session': '%7B%22expirationDate%22%3A1695968641178%2C%22data%22%3A%7B%22pageTime%22%3A5255%2C%22numberOfVisitedPages%22%3A18%7D%7D',
            }

            headers = {
                'authority': 'www.x-kom.pl',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
                'cache-control': 'no-cache',
                # 'cookie': 'ai_user=ohLCwL5YFWMJmZs3Oqzo6b|2023-09-28T17:54:04.779Z; trackingPermissionConsentsValue=%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D; __cf_bm=1ltSz9Ar9NetiHGVRHzXUNhlqbfFmXd5l.10ItgjJPI-1695964979-0-AR+Ne5vSeZbsHaVxPwaNKWNHBpyXuZzvVw11BmAhIWmESNKDUJ7jzuyfGCFFCG4HCZ4ZYqbROTBN1i0uDzeZuJHk+cP1AZioKMLVIm0MeWZs; cf_chl_2=e13fd3fe31c9464; cf_clearance=ujMjHigtJF6zEQNnKlsYnPqv01VQt_UWq4hjJREzcE4-1695965020-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695965020; ai_session=0PVcNBBSblYC5Pk8empDEZ|1695965021019|1695965021019; breakpointName=md; startquestion-session=%7B%22expirationDate%22%3A1695968641178%2C%22data%22%3A%7B%22pageTime%22%3A5255%2C%22numberOfVisitedPages%22%3A18%7D%7D',
                'dnt': '1',
                'pragma': 'no-cache',
                'referer': 'https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html?page=2&producent=4-hp&producent=5-microsoft&producent=7-msi&producent=14-lg&producent=27-asus&producent=28-toshiba&producent=46-lenovo&producent=57-gigabyte&producent=227-razer&producent=230-acer&producent=396-dell&producent=475-huawei&producent=731-krugermatz&hide_unavailable=1&__cf_chl_tk=F2T9sMTe72.9IEM.JW_u7Um9dwpAGYb3_ekiFfmAflA-1695965010-0-gaNycGzNFHs',
                'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            }

            params = {
                'page': f'{i}',
                'producent': [
                    '4-hp',
                    '5-microsoft',
                    '7-msi',
                    '14-lg',
                    '27-asus',
                    '28-toshiba',
                    '46-lenovo',
                    '57-gigabyte',
                    '227-razer',
                    '230-acer',
                    '396-dell',
                    '475-huawei',
                    '731-krugermatz',
                ],
                'hide_unavailable': '1',
            }

            response = requests.get(
                'https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            src = response.text
            with open(filename, "w", encoding='utf-8') as file:
                file.write(src)


def get_urls_products():
    folder = r'c:\DATA\x_kom_pl\list\*.html'
    files_html = glob.glob(folder)
    url_all = []

    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')

        tables_product = soup.find('div', attrs={'id': 'listing-container'})
        product_card = tables_product.find_all('div', attrs={'data-name': 'productCard'})

        with open('categories.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for i in product_card:
                url = f"https://www.x-kom.pl{i.find('a').get('href')}"
                url_all.append(url)
            for url in url_all:
                writer.writerow([url])


def get_prodict_html():
    cookies = {
        '__cf_bm': '4cTrv2JuK0YFMDcun6_QB6rSttAxdGTJk8KlsfgW1sA-1695968651-0-AQ6ZbGE5otcUSQFKD+aiUD5IwfiO0Nn+pXaMjlhSgfV9a7QsOO1H7cxUQ+W1MMDIveBzkSPsGVj7l2dTiWun350VBJzDPD7dQqd7tJAngKna',
        'cf_clearance': '3xXv.8VE2z5kRXm7ateOi11iBupSi0PSRgF5tVDvU6g-1695968659-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695968659',
        'ai_session': 'NDr9zdhTfVUJRxsUblP4MZ|1695968660400|1695968748820',
        'trackingPermissionConsentsValue': '%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D',
        'startquestion-session': '%7B%22expirationDate%22%3A1695972350678%2C%22data%22%3A%7B%22pageTime%22%3A6000%2C%22numberOfVisitedPages%22%3A21%7D%7D',
    }

    headers = {
        'authority': 'www.x-kom.pl',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': '__cf_bm=4cTrv2JuK0YFMDcun6_QB6rSttAxdGTJk8KlsfgW1sA-1695968651-0-AQ6ZbGE5otcUSQFKD+aiUD5IwfiO0Nn+pXaMjlhSgfV9a7QsOO1H7cxUQ+W1MMDIveBzkSPsGVj7l2dTiWun350VBJzDPD7dQqd7tJAngKna; cf_clearance=3xXv.8VE2z5kRXm7ateOi11iBupSi0PSRgF5tVDvU6g-1695968659-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695968659; ai_session=NDr9zdhTfVUJRxsUblP4MZ|1695968660400|1695968748820; trackingPermissionConsentsValue=%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D; startquestion-session=%7B%22expirationDate%22%3A1695972350678%2C%22data%22%3A%7B%22pageTime%22%3A6000%2C%22numberOfVisitedPages%22%3A21%7D%7D',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html?producent=4-hp&producent=5-microsoft&producent=7-msi&producent=14-lg&producent=27-asus&producent=28-toshiba&producent=46-lenovo&producent=57-gigabyte&producent=227-razer&producent=230-acer&producent=396-dell&producent=475-huawei&producent=731-krugermatz&hide_unavailable=1&__cf_chl_tk=YOs6gbQRfmNDOXaPusUj17x5C3fV6.cIYN8H3ym61RA-1695968655-0-gaNycGzNEVA',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }
    name_files = Path(f'c:/scrap_tutorial-master/x_kom_pl/') / 'categories.csv'
    coun = 0
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in urls:
            filename = f"c:\\DATA\\x_kom_pl\\product\\data_{coun}.html"
            print(filename)
            if not os.path.exists(filename):
                response = requests.get(row[0], headers=headers, cookies=cookies)
                src = response.text
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src)

                time.sleep(1)
                print(f'Сохранил {filename}')
            coun += 1






def split_urls_r(urls, n):
    """Делит список URL-адресов на n равных частей."""
    avg = len(urls) // n
    urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
    return urls_split


def worker_r(sub_urls, start_counter):
    cookies = {
        'ai_user': 'ohLCwL5YFWMJmZs3Oqzo6b|2023-09-28T17:54:04.779Z',
        'trackingPermissionConsentsValue': '%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D',
        '__cf_bm': '1ltSz9Ar9NetiHGVRHzXUNhlqbfFmXd5l.10ItgjJPI-1695964979-0-AR+Ne5vSeZbsHaVxPwaNKWNHBpyXuZzvVw11BmAhIWmESNKDUJ7jzuyfGCFFCG4HCZ4ZYqbROTBN1i0uDzeZuJHk+cP1AZioKMLVIm0MeWZs',
        'cf_chl_2': 'e13fd3fe31c9464',
        'cf_clearance': 'ujMjHigtJF6zEQNnKlsYnPqv01VQt_UWq4hjJREzcE4-1695965020-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695965020',
        'ai_session': '0PVcNBBSblYC5Pk8empDEZ|1695965021019|1695965043180',
        'breakpointName': 'sm',
        'startquestion-session': '%7B%22expirationDate%22%3A1695969080288%2C%22data%22%3A%7B%22pageTime%22%3A5520%2C%22numberOfVisitedPages%22%3A19%7D%7D',
    }

    headers = {
        'authority': 'www.x-kom.pl',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'ai_user=ohLCwL5YFWMJmZs3Oqzo6b|2023-09-28T17:54:04.779Z; trackingPermissionConsentsValue=%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D; __cf_bm=1ltSz9Ar9NetiHGVRHzXUNhlqbfFmXd5l.10ItgjJPI-1695964979-0-AR+Ne5vSeZbsHaVxPwaNKWNHBpyXuZzvVw11BmAhIWmESNKDUJ7jzuyfGCFFCG4HCZ4ZYqbROTBN1i0uDzeZuJHk+cP1AZioKMLVIm0MeWZs; cf_chl_2=e13fd3fe31c9464; cf_clearance=ujMjHigtJF6zEQNnKlsYnPqv01VQt_UWq4hjJREzcE4-1695965020-0-1-d29a0353.e9be5546.2e36fbca-160.2.1695965020; ai_session=0PVcNBBSblYC5Pk8empDEZ|1695965021019|1695965043180; breakpointName=sm; startquestion-session=%7B%22expirationDate%22%3A1695969080288%2C%22data%22%3A%7B%22pageTime%22%3A5520%2C%22numberOfVisitedPages%22%3A19%7D%7D',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html?page=2&producent=4-hp&producent=5-microsoft&producent=7-msi&producent=14-lg&producent=27-asus&producent=28-toshiba&producent=46-lenovo&producent=57-gigabyte&producent=227-razer&producent=230-acer&producent=396-dell&producent=475-huawei&producent=731-krugermatz&hide_unavailable=1&__cf_chl_tk=F2T9sMTe72.9IEM.JW_u7Um9dwpAGYb3_ekiFfmAflA-1695965010-0-gaNycGzNFHs',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }
    # Используйте сессию для повторного использования TCP-соединений
    with requests.Session() as session:
        session.cookies.update(cookies)
        session.headers.update(headers)

        for counter, u in enumerate(sub_urls, start=start_counter):
            filename = f"c:\\DATA\\x_kom_pl\\product\\data_{counter}.json"
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
    with open("categories.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files))
        max_workers = 3
        splitted_urls = split_urls_r(urls, max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker_r, sub_urls, idx * len(sub_urls))







def pars_html():
    folder = r'c:\DATA\x_kom_pl\product\*.html'
    files_html = glob.glob(folder)
    url_all = []
    heandler = ['Link', 'Name', 'kod producenta', 'kod x-kom', 'Price']
    with open('pr.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(heandler)
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            script_json = soup.find_all('script', type="application/ld+json")[0]
            try:
                data_json = json.loads(script_json.string)
            except:
                data_json = ""
            tag = soup.find('meta', attrs={'data-react-helmet': 'true', 'name': 'DC.identifier'})
            content_url = None
            # Если тег найден, извлекаем содержимое атрибута 'content'
            if tag:
                content_url = tag['content']
            else:
                print("Тег не найден")
            name = data_json['name']
            product_id = data_json['productID']
            mpn = data_json['mpn']
            price = data_json['offers']['price']
            datas = [content_url, name, mpn,product_id, price]
            writer.writerow(datas)


if __name__ == '__main__':
    # totalElements = get_totalElements()
    # get_requests()
    # get_urls_products()
    # get_product_r()
    # get_prodict_html()

    pars_html()
