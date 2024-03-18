from pathlib import Path
from bs4 import BeautifulSoup
import random
from proxi import proxies
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

cookies = {
    'ak_bmsc': 'EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53',
    'bm_mi': '358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1',
    'bm_sv': '8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
}

headers = {
    'authority': 'www.tesla.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'ak_bmsc=EA9961D4BA849D3AC4CB97CC1C162EA6~000000000000000000000000000000~YAAQDQxAFw0pm9uIAQAAMY6F3RRnVuXFv4jC/DzpcHz8wr4R5Jtr5VTNvGrch9m1g/NzHfRG3zxgATE+LCELn1HESJumYUgLV9nECNF7wGzlRLAhrc7U4P2CQXAVXjEUEemBowLkRk6umFmr/GgGoD9TswWMtSx6mAxUJTuk4DZ4YxEr2ebl7no7YGAWMv5Jeno0qlyI+5m4+JXttGPtupH6rkFwtL2JckEUkKklgQuFAo9jJeZVN+bUhpZ0njZCWWduOGZHr4/AYqb52LGMb5T4q3tdOeXCKGCCdIsupUJTsa6VLSwPyyFURrgns+T/kHnkJMHDTUBcOAtZmhNz1AotifjdjYN+HOJ5ddKwNXwdBgvL3SOiK/oWvCvtC7pZTo/TAiLhrq53; bm_mi=358A0D18C4DAD9BFA09771FC5AB403C4~YAAQDQxAF60wnNuIAQAAv4GJ3RRjWk57jfsblbuIKwMwsO5DBEnts97/tCHs4oTJ2WG9etYkQA+UjHbplreoaacyd11aa1J1bpbf41cbq3FZ2vpr4Q/tjEIvyonyYO//NYGCkRFufc1CSay0el9XXBXkS30kehveHX2xwsTNDFwJxXI+ffwIxDVWLQv6lypazcpvnlAPpHTPRSg+UrLQ6Zgmw5AsbJF139jLNlOaozuvPJzaViygYhHFnG4QM+fLp8G7sH1zUpQLFAx0QUoWSJEqSb/g6ow09hE1qOBnnIVWU7KCjScTzrMQfg9otIgGWq6AWUEcogaJ9EyWIxf9p9X8enHw~1; bm_sv=8D7D22C834C4108B2E3B28CCD234DE6C~YAAQDQxAF64wnNuIAQAAv4GJ3RS2BqJNjwW50vYdaE7tC3qz6poW/tZglurMfsps6OSDO6k7t6/pNCtK7SH+GEpHXhoogIHaiTsM/wRXxP0kCFBVFkLwjcjfRizsE+aP9L2rJnNhCfW0Tz77ZfYidkFcSiVjCF5wYs+cFNKDdbfXdrLYvN8GRBlrivyyZsaJlRHqBBEbxX5HRizu8FNh3qJgyGWMk4xkxbD5DlCkurmyMXfNtRdPy51QfQSfAI4=~1',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


def get_requests():
    response = requests.get(
        'https://www.tesla.com/findus/list',
        cookies=cookies,
        headers=headers,

    )
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    filename = f"tesla.html"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


def url_all():
    file = f"tesla.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    table_product = soup.find('section', attrs={'class': 'find-us-list-main'}).find_all('section', attrs={'class': 'row'})
    tesla_stores = []
    with open('category.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in table_product:
            l_i = i.find_all('li')
            for l in l_i:
                url_stores = 'https://www.tesla.com' + l.find('a')['href']
                tesla_stores.append(url_stores)
                writer.writerow([url_stores])
def get_url():
    response = requests.get(
        'https://www.tesla.com/findus/location/supercharger/bregenzsupercharger',
        cookies=cookies,
        headers=headers,

    )
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    name_files = Path('c:/DATA/tesla/') / 'all_categories_url.html'
    filename = f"tesla.html"

    with open(filename, "w", encoding='utf-8') as file:
        file.write(src)


def folders():
    name_files = Path(f'c:/scrap_tutorial-master/tesla/url/') / 'url_tesla.csv'
    coun = 0
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for row in urls:
            pause_time = random.randint(1, 5)
            coun += 1
            """Настройка прокси серверов случайных"""
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            # Предполагается, что URL это первый элемент строки
            url = row[0]

            # Отправляем запрос
            name_files = Path('c:/DATA/tesla/') / f'data_{coun}.html'
            if not os.path.exists(name_files):
                response = requests.get(url, headers=headers, cookies=cookies, proxies=proxi)
                with open(name_files, "w", encoding='utf-8') as file:
                    file.write(response.text)
                print(f'Осталось {len(urls) - coun}')
                time.sleep(pause_time)
            else:
                print(f'В наличии {name_files}')
                continue

def parsing():
    folder = r'c:\DATA\tesla\*.html'
    files_html = glob.glob(folder)
    company = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        # name = soup.find("span", {"class": "street-address"}).text
        # address = soup.find("span", {"class": "locality"}).text
        # directions = soup.find("a", href=True)['href']
        # roadside_assistance = soup.find("span", {"class": "value"}).text.strip()
        # charging_info = soup.find("strong", text="Charging").parent.text
        # ccs_compatibility_info = soup.find("i").text.strip()
        # amenities_info = [link.text.strip() for link in
        #                   soup.find("ul", {"class": "amenities-icons"}).find_all("a", href=True)]
        #
        # # Выводим данные
        # print("Name:", name)
        # print("Address:", address)
        # print("Directions:", directions)
        # print("Roadside Assistance:", roadside_assistance)
        # print("Charging Info:", charging_info)
        # print("CCS Compatibility Info:", ccs_compatibility_info)
        # print("Amenities Info:", amenities_info)
        table_firma = soup.find('div', attrs={'id': 'find-us-list-container'})
        city = table_firma.find('h1').text
        name_category = soup.find('li', {'itemprop': 'name'}).text.strip()
        address = ' '.join(soup.find('span', {'class': 'street-address'}).text.split())
        locality = ' '.join(soup.find('span', {'class': 'locality'}).text.split())
        directions = soup.find('a', {'target': '_blank'}).text
        assistance = soup.find('span', {'class': 'tel'}).text.strip().replace('\n', '')
        charging_info = soup.find("strong", string="Charging").parent.text
        #Сервисы, нужно проверять
        amenities_info = [link.text.strip() for link in
                          soup.find("ul", {"class": "amenities-icons"}).find_all("a", href=True)]
        try:
            charger_availability = soup.find('i').text
        except:
            charger_availability = None

        amenities = soup.find_all('strong')
        print(amenities[1].text)
        location_map = soup.find("div", {"id": "location-map"})
        img_src = location_map.find('img')['src']  # Получить значение атрибута 'src' у тега 'img'
        coordinates = re.search('&center=(.*?)&zoom=', img_src)  # Использовать регулярное выражение для поиска координат
        map_coor = str(coordinates.group(1))
        company.append(
            {
                "name_category:": name_category,
                "city": city,
                "address": address,
                "locality": locality,
                "directions": directions,
                "assistance": assistance,
                "charging_info": charging_info,
                "charger_availability": charger_availability,
                "coordinates": map_coor

            }
        )
        # with open(f"company.json", 'a', encoding="utf-8") as file:
        #     json.dump(company, file, indent=4, ensure_ascii=False)



        # print(charger_availability)







if __name__ == '__main__':
    # get_requests()
    # url_all()
    # get_url()
    # folders()
    parsing()
