import csv
import time
import datetime
from random import randint

import requests
from bs4 import BeautifulSoup


def get_content(url):
    start_time = datetime.datetime.now()
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=header)
    soup = BeautifulSoup(resp.text, 'lxml')

    # with open("zoo.csv", "w") as file:
    #     writer = csv.writer(file, delimiter=";", lineterminator="\r")
    #     writer.writerow(
    #         (
    #             "Название продукта",
    #             "Новая цена",
    #             "Старая цена",
    #             "Страна производитель"
    #         )
    #     )
    pagan_list = soup.find('ul', attrs={'class': 'pagination'}).find_all('li')

    print(pagan_list)
    # for item in range(1, 25):
    #     if item == 1:
    #         resp = requests.get(url, headers=header)
    #     elif item > 1:
    #         resp = requests.get(url + f'/f/page/{item}', headers=header)
    #     time.sleep(randint(1, 5))
    #     soup = BeautifulSoup(resp.text, 'lxml')
    #     tab_content = soup.find('div', attrs={'id': 'js-prodscont'})
    #     print(tab_content)
        # catalog_product_item = tab_content.find_all('div', attrs={'class': 'catalog-product-item'})
        # for item in catalog_product_item:
        #     product = item.find('a', attrs={"class": "product-t js-prodclick"}).text
        #     product_price_new = item.find('span', attrs={"class": "change-prise"}).text.strip().replace(' ₴',
        #                                                                                                 '').replace('.',
        #                                                                                                             ',')
        #     product_price_old = item.find('span', attrs={"class": "product-old-prise"}).text.replace(' ₴', '').replace(
        #         '.', ',')
        #     product_country = item.find('div', attrs={"class": "product-components mt-3"}).find('span').text
        #     product_logo = item.find('img', attrs={"class": "img-fluid"}).get('src')
        #
        #     with open("zoo.csv", "a", errors='ignore') as file:  # errors='ignore' игнорирует ошибку при записи
        #         writer = csv.writer(file, delimiter=";",
        #                             lineterminator="\r")  # lineterminator="\r". Это разделитель между строками таблицы, delimiter Устанавливает символ, с помощью которого разделяются элементы в файле
        #         writer.writerow(
        #             (
        #                 product,
        #                 product_price_new,
        #                 product_price_old,
        #                 product_country
        #             )
        #         )
    diff_time = datetime.datetime.now() - start_time
    print(diff_time)


def parse_content():
    url = "https://e-zoo.com.ua/ua/promo/skidki-i-podarki-ko-dnyu-rozhdeniya-e-zoo"
    get_content(url)


if __name__ == '__main__':
    parse_content()
