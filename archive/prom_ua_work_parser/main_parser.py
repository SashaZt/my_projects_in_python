import json
import csv
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Нажатие клавиш

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

useragent = UserAgent()


def save_link_all_product():
    url = "https://prom.ua/c3352790-woman-space.html?product_group=87914822&a18=263634"
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}

    resp = requests.get(url, headers=header)
    soup = BeautifulSoup(resp.text, 'lxml')
    try:
        # Как найти количество листов пагинация
        pagin = int(soup.find_all('a', attrs={'class': 'VS-Ex vtaL- oBR0- _4-SzE'})[-2].text)
    except:
        pagin = print('Not pagin')
    url_product = []
    for item in range(1, 5):
        if item == 1:
            resp = requests.get('https://prom.ua/c3352790-woman-space.html?product_group=87914822&a18=263634',
                                headers=header)
            soup = BeautifulSoup(resp.text, 'lxml')
            table_products = soup.find('div', attrs={'data-qaid': 'product_gallery'}).find_all('div', attrs={
                'class': 'M3v0L DUxBc sMgZR _5R9j6 qzGRQ IM66u J5vFR hxTp1'})
            for i in table_products:
                hrefs = "https://prom.ua" + i.find('a').get("href")
                url_product.append(
                    {
                        'url_name': hrefs
                    })
                # print(hrefs)
        if item > 1:
            resp = requests.get(f'https://prom.ua/c3352790-woman-space{item}.html?product_group=87914822&a18=263634',
                                headers=header)
            soup = BeautifulSoup(resp.text, 'lxml')
            table_products = soup.find('div', attrs={'data-qaid': 'product_gallery'}).find_all('div', attrs={
                'class': 'M3v0L DUxBc sMgZR _5R9j6 qzGRQ IM66u J5vFR hxTp1'})
            for i in table_products:
                hrefs = "https://prom.ua" + i.find('a').get("href")
                url_product.append(
                    {
                        'url_name': hrefs
                    })
                # print(hrefs)

    with open("url_product.json", 'w') as file:
        json.dump(url_product, file, indent=4, ensure_ascii=False)


def parsing_product():
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}
    # Читание json
    with open('url_product.json') as file:
        all_site = json.load(file)
    for item in all_site:
        resp = requests.get(item['url_name'], headers=header)
        soup = BeautifulSoup(resp.text, 'lxml')
        name_product = soup.find('div', attrs={'class': 'MafxA _6xArK WIR6H'}).find('h1').text
        price_product = soup.find('div', attrs={'class': 'M3v0L -pUjB YKUY6 zG-pk'}).find('span').text
        img_product = soup.find('div', attrs={'data-qaid': 'image_block'}).find('img').get("src")
        manuf_product = \
            soup.find('ul', attrs={'class': 'nujFR WIvKn'}).find('li', attrs={'class': 'YSmsd'}).find('div', attrs={
                'class': 'l-GwW fvQVX'}).find_all('span')[-1].text
        desc_product = soup.find('div', attrs={'data-qaid': 'descriptions'}).text.replace("\n", " ")
        with open("product.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    name_product,
                    price_product,
                    img_product,
                    manuf_product,
                    desc_product
                )
            )


if __name__ == '__main__':
    save_link_all_product()
    parsing_product()
