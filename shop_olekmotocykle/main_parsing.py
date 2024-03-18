import random
from typing import Optional
import csv
import time
import os
import asyncio
import aiofiles
import aiohttp
# import main_asio_photo


import pandas as pd
import glob
import json
import html
import re

import requests
from bs4 import BeautifulSoup
import csv
current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
category_path = os.path.join(temp_path, "category")
header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}

def parsing_product():
    proxies = [
        ('185.112.12.122', 2831, '36675', 'g6Qply4q'),
        ('185.112.14.126', 2831, '36675', 'g6Qply4q'),
        ('185.112.15.239', 2831, '36675', 'g6Qply4q'),
        ('195.123.189.137', 2831, '36675', 'g6Qply4q'),
        ('195.123.190.104', 2831, '36675', 'g6Qply4q'),
        ('195.123.193.81', 2831, '36675', 'g6Qply4q'),
        ('195.123.194.134', 2831, '36675', 'g6Qply4q'),
        ('195.123.197.233', 2831, '36675', 'g6Qply4q'),
        ('195.123.252.157', 2831, '36675', 'g6Qply4q'),
        ('212.86.111.68', 2831, '36675', 'g6Qply4q')
    ]
    
    folder = os.path.join(html_path, '*.html')

    files_html = glob.glob(folder)
    
    
    data = []
    filename_to_csv_output = os.path.join(current_directory, "output.csv")
    with open(filename_to_csv_output, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id_product', 'name', 'brandName', 'gtin', 'brutto_price', 'netto_price'])
        for item in files_html:
            
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'html.parser')
            script_tag = soup.find('script', {'id': 'datablock1'})
            try:
                json_content = script_tag.contents[0].strip().replace('},\n}\n}', '}\n}\n}')
            except:
                print(item)
                continue
            try:
                data = json.loads(json_content)
                id_product = soup.find('div', {'class': 'product-code-ui product-code-lq'}).text
                name = data['itemOffered']['productName'][0]['@value']
                brandName = data['itemOffered']['brand']['brandName'][0]['@value']
                gtin = data['itemOffered']['gtin']
                brutto_price = soup.find('div', {'class': 'brutto-price-ui'}).text.strip().replace(" PLN", "").replace("\nbrutto", "")
                netto_price = soup.find('div', {'class': 'netto-price-ui'}).text.strip().replace(" PLN", "").replace("\nnetto", "")
                writer.writerow([id_product, name, brandName, gtin, brutto_price, netto_price])
            except:
                print(item)
                continue
            # div = soup.find_all("div", {"class": "lazyslider-container-lq"})[0]
            # imgs = div.find_all("img", {"class": "open-gallery-lq"})
            #
            # urls_photo = []
            # for img in imgs:
            #     urls_photo.append('https://' + img["data-src"].replace("//", ""))
            #
            # coun = 0
            # file_path_1 = f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}.jpg'
            # file_path_2 = f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}_{coun}.jpg'
            # for u in urls_photo:
            #     """Настройка прокси серверов случайных"""
            #     proxy = random.choice(proxies)
            #     proxy_host = proxy[0]
            #     proxy_port = proxy[1]
            #     proxy_user = proxy[2]
            #     proxy_pass = proxy[3]
            #
            #     proxi = {
            #         'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
            #         'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            #     }
            #     coun += 1
            #     if len(urls_photo) == 1:
            #         if not os.path.exists(file_path_1):
            #             try:
            #                 img_data = requests.get(u, headers=header, proxies=proxi)
            #                 with open(file_path_1, 'wb') as file_img:
            #                     file_img.write(img_data.content)
            #             except:
            #                 print(f"Ошибка при выполнении запроса для URL: {u}")
            #                 continue
            #     elif len(urls_photo) > 1:
            #         if not os.path.exists(file_path_2):
            #             img_data = requests.get(u, headers=header, proxies=proxi)
            #             with open(file_path_2, 'wb') as file_img:
            #                 file_img.write(img_data.content)


if __name__ == '__main__':
    parsing_product()
