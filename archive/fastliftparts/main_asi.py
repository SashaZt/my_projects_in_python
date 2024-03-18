import csv
import datetime
import time
import json
from datetime import datetime

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

useragent = UserAgent()

# Создаём список куда будем выгружать всё необходимые данные
data = []


async def get_page_data(session, i):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"
    }

    async with aiohttp.ClientSession() as session:
        resp_url = await session.get(i, headers=header)
        soup = BeautifulSoup(await resp_url.text(), 'lxml')
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

        #     print(product_name, product_price, product_brand, product_img,product_katalog)
        #     Добавляем в список data все необходимые поля для дальнейшей передачи в csv
        data.append(
            [product_name, product_price, product_brand, product_img, product_des, i]
        )
    write_csv(data)


# Функция, которая будет записывать данные из списка data
def write_csv(data):
    # Создаём файл с заголовками
    with open(f"test.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Название',
                'Цена',
                'Бренд',
                'Ссылка на изображение',
                'Название группы'

            )
        )
        # Дописываем данные из списка data в файл
        writer.writerows(
            data
        )


# Функция для создания задач для асинхронного получение данных
# async def gather_data():
#     # Переходим по ссылкам
#     for page in range(1, 8244):
#         # url = f"https://shop.moderngroup.com/fleetguard/?sort=bestselling&page={page}"
#         url = f"https://fastliftparts.com/collections/all?page={page}"
#         header = {
#             "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#             "user-agent": f"{useragent.random}"
#
#         }
#         # Создаём асинхронную ссеию
#         async  with aiohttp.ClientSession() as session:
#             # создаём список задач
#             tasks = []
#             try:
#                 if (page % 2):
#                     time.sleep(30)
#                     time_now = datetime.now().time()
#                     # получаем список всех карточек
#                     print(f'Текущее время {time_now} ссылка {url}')
#                     response = await session.get(url=url, headers=header, proxy="http://37.233.3.100:9999")
#                     soup = BeautifulSoup(await response.text(), 'lxml')
#                     # Получаем таблицу всех товаров
#                     try:
#                         table = soup.find('ul', attrs={'id': 'product-grid'}).find_all("li")
#                     except:
#                         print(f'Нет таблицы {url}')
#                     url_product = []
#                     # Получаем список всех url на карточки
#                     for item in table:
#                         href = item.find('a').get("href")
#                         url_product.append(f"https://fastliftparts.com/{href}")
#                     # Добавляем всё url в список задач
#                     for i in url_product:
#                         task = asyncio.create_task(get_page_data(session, i))
#                         tasks.append(task)
#                     await asyncio.gather(*tasks)
#             except:
#                 continue
#             else:
#                 try:
#                     time.sleep(30)
#                     time_now = datetime.now().time()
#                     # получаем список всех карточек
#                     print(f'Текущее время {time_now} ссылка {url}')
#                     response = await session.get(url=url, headers=header, proxy="http://80.77.34.218:9999")
#                     soup = BeautifulSoup(await response.text(), 'lxml')
#                     # Получаем таблицу всех товаров
#                     try:
#                         table = soup.find('ul', attrs={'id': 'product-grid'}).find_all("li")
#                     except:
#                         print(f'Нет таблицы {url}')
#                     url_product = []
#                     # Получаем список всех url на карточки
#                     for item in table:
#                         href = item.find('a').get("href")
#                         url_product.append(f"https://fastliftparts.com/{href}")
#                     # Добавляем всё url в список задач
#                     for i in url_product:
#                         task = asyncio.create_task(get_page_data(session, i))
#                         tasks.append(task)
#                     await asyncio.gather(*tasks)
#                 except:
#                     continue


async def gather_data_url():
    async  with aiohttp.ClientSession() as session:
        tasks = []
        with open('url_product.json') as file:
            all_site = json.load(file)
        for i in all_site:
            task = asyncio.create_task(get_page_data(session, i['url_name']))
            tasks.append(task)
        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data_url())


if __name__ == '__main__':
    main()
