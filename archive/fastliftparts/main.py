import json
import time

import csv
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Нажатие клавиш

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

useragent = UserAgent()


def save_link_all_product():
    for page in range(1, 8244):
        url = f"https://fastliftparts.com/collections/all?page={page}"
        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": f"{useragent.random}"
        }
        url_product = []
        if (page % 2):
            try:
                session = requests.Session()
                session.proxies = {
                    'http': 'http://37.233.3.100:9999',
                    'https': 'http://37.233.3.100:9999',
                }

                time.sleep(30)
                time_now = datetime.now().time()
                print(f'Текущее время {time_now} ссылка {url}')
                resp = session.get(url, headers=header)
                soup = BeautifulSoup(resp.text, 'lxml')
                # Получаем таблицу всех товаров
                try:
                    table = soup.find('ul', attrs={'id': 'product-grid'}).find_all("li")
                except:
                    table = print(f'Нет таблицы {url}')
                # Получаем список всех url на карточки
                for item in table:
                    href = 'https://fastliftparts.com/' + item.find('a').get('href')
                    url_product.append(
                        {
                            'url_name': href
                        })
            except:
                continue
        else:
            try:
                session = requests.Session()
                session.proxies = {
                    'http': 'http://80.77.34.218:9999',
                    'https': 'http://80.77.34.218:9999',
                }

                time.sleep(30)
                time_now = datetime.now().time()
                # получаем список всех карточек
                print(f'Текущее время {time_now} ссылка {url}')
                resp = session.get(url, headers=header)
                soup = BeautifulSoup(resp.text, 'lxml')
                # Получаем таблицу всех товаров
                try:
                    table = soup.find('ul', attrs={'id': 'product-grid'}).find_all("li")
                except:
                    table = print(f'Нет таблицы {url}')

                # Получаем список всех url на карточки
                for item in table:
                    href = href = 'https://fastliftparts.com/' + item.find('a').get('href')
                    url_product.append(
                        {
                            'url_name': href
                        })
            except:
                continue
        with open("url_product.json", 'a') as file:
            json.dump(url_product, file, indent=4, ensure_ascii=False)


def parsing_product():
    time_now = datetime.now().time()
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"}
    # Читание json
    with open('url_product.json') as file:
        all_site = json.load(file)
    for item in all_site[146981:]:
        time.sleep(5)
        try:
            resp = requests.get(item['url_name'], headers=header)
        except:
            continue
        soup = BeautifulSoup(resp.text, 'lxml')
        try:
            product_name = soup.find('div',
                                     attrs={'class': 'product__info-container product__info-container--sticky'}).find(
                "h1").text.replace("\n", "").strip()
        except:
            product_name = "Нет названия"
        try:
            product_price = soup.find('div', attrs={'class': 'price__regular'}).find('span', attrs={
                'class': 'price-item price-item--regular'}).text.replace("\n", "")
        except:
            product_price = "Нет цены"
        try:
            product_brand = soup.find('div',
                                      attrs={'class': 'product__info-container product__info-container--sticky'}).find(
                'p').text
        except:
            product_brand = "Not brand"
        try:
            product_img = soup.find('div', attrs={'class': 'product__media media media--transparent'}).find("img").get(
                "src").replace("//cdn", "cdn")
        except:
            product_img = "нет изображения"
        try:
            product_des = soup.find('div', attrs={'class': 'product__description rte'}).find("h2").text.replace("\n",
                                                                                                                "")
        except:
            product_des = "Нет каталога"
        with open("product.csv", "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    product_name,
                    product_price,
                    product_brand,
                    product_img,
                    product_des
                )
            )


# def write_csv(data):
#     # Создаём файл с заголовками
#     with open(f"test.csv", "w", errors='ignore') as file:
#         writer = csv.writer(file, delimiter=";", lineterminator="\r")
#         writer.writerow(
#             (
#                 'Название',
#                 'Цена',
#                 'Бренд',
#                 'Ссылка на изображение',
#                 'Название группы'
#
#             )
#         )
#         # Дописываем данные из списка data в файл
#         writer.writerows(
#             data
#         )


if __name__ == '__main__':
    # save_link_all_product()
    parsing_product()
