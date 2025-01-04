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

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor

def get_requests():
    import aiohttp
    import asyncio
    from pathlib import Path
    import csv
    import os
    import random
    # from proxi import proxies
    from headers_cookies_aiso import headers

    coun = 0

    async def fetch(session, url, coun):
        # proxy = random.choice(proxies)
        # proxy_host = proxy[0]
        # proxy_port = proxy[1]
        # proxy_user = proxy[2]
        # proxy_pass = proxy[3]
        # proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
        name_files = Path('c:/DATA/exist/product/') / f'data_{coun}.html'
        if not os.path.exists(name_files):
            await asyncio.sleep(5)
            async with session.get(url, headers=headers) as response: #, proxy=proxi
                    with open(name_files, "w", encoding='utf-8') as file:
                        file.write(await response.text())
        else:
            pass

    async def main():
        name_files = Path(f'c:/scrap_tutorial-master/exist/') / 'url_amortyzatory.csv'
        coun = 0  # Сделайте coun локальной переменной внутри функции main
        async with aiohttp.ClientSession() as session:
            with open(name_files, newline='', encoding='utf-8') as files:
                urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
                for i in range(0, len(urls), 10):
                    tasks = []
                    for row in urls[i:i + 10]:
                        coun += 1
                        url = row[0]
                        tasks.append(fetch(session, url, coun))
                    await asyncio.gather(*tasks)
                    print(f'Completed {coun} requests')
                    # await asyncio.sleep(5)

    asyncio.run(main())

# def get_requests():
#
#     # cookies = {
#     #     'sessionid': 'mrqjw8vnilh44diz8aryq5jrodokxq2f',
#     #     'cf_clearance': 'V4_Zy99exclmqrs8.cC4ve77WHggd.XueZk2zXkN5Wc-1697135038-0-1-d29a0353.7d7311cd.859b5cb3-0.2.1697135038',
#     #     'csrftoken': 'WSZtemNOAzSQPwzxwR5wyfn7flUj4wj3RSTiNoo3A4hohELJtB9WKEZW62v78dRY',
#     #     'crisp-client%2Fsession%2F980759c4-00d9-4b4b-85e6-c48036807fc0': 'session_1b713c7a-4fba-4d1f-a801-b184ce903e57',
#     #     'catalog_page_size': '50',
#     #     'crisp-client%2Fsocket%2F980759c4-00d9-4b4b-85e6-c48036807fc0': '0',
#     # }
#
#     headers = {
#         'authority': 'exist.ua',
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
#         'cache-control': 'no-cache',
#         # 'cookie': 'sessionid=mrqjw8vnilh44diz8aryq5jrodokxq2f; cf_clearance=V4_Zy99exclmqrs8.cC4ve77WHggd.XueZk2zXkN5Wc-1697135038-0-1-d29a0353.7d7311cd.859b5cb3-0.2.1697135038; csrftoken=WSZtemNOAzSQPwzxwR5wyfn7flUj4wj3RSTiNoo3A4hohELJtB9WKEZW62v78dRY; crisp-client%2Fsession%2F980759c4-00d9-4b4b-85e6-c48036807fc0=session_1b713c7a-4fba-4d1f-a801-b184ce903e57; catalog_page_size=50; crisp-client%2Fsocket%2F980759c4-00d9-4b4b-85e6-c48036807fc0=0',
#         'dnt': '1',
#         'pragma': 'no-cache',
#         'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
#     }
#
#     response = requests.get(
#         'https://exist.ua/uk/kyb-kayaba-brand/amortyzator-pidvisky-perednoji-gazomasljanyj-kyb-excel-g-335808-14866668/',
#         # cookies=cookies,
#         headers=headers,
#     )
#
#
#     # json_data = response.json()
#     # with open(f'test.json', 'w', encoding='utf-8') as f:
#     #     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
#     src = response.text
#     filename = f"amazon.html"
#     with open(filename, "w", encoding='utf-8') as file:
#         file.write(src)

def parsing():
    file = f"amazon.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')

    """Оригінальні номери"""
    try:
        links_original = soup.find('div', attrs={'data-numbers': '157'}).find_all('a')
    except:
        pass

    pattern = r"([A-Z0-9]+)\s+([A-Z0-9\s]+)"

    for link in links_original:
        match = re.search(pattern, link.text)
        if match:
            brand = match.group(1)
            part_number = match.group(2).strip()
            # print(f"{part_number},{brand}")

    """Аналоги (замінники)"""
    links_analog = soup.find('div', attrs={'aria-labelledby': 'react-tabs-4'}).find('tbody').find_all('td', attrs={'data-field': 'Найменування'})
    # print(="")
    for l in links_analog[:2]:
        brand = l.find('p').find('strong').text
        part_number = l.find('p').find('a').text



if __name__ == '__main__':
    get_requests()
    # parsing()
