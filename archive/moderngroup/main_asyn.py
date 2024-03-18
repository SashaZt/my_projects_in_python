import datetime
import csv
import lxml
import time
import asyncio
import aiohttp
import aiofiles
from aiocsv import AsyncWriter
from random import randint

from bs4 import BeautifulSoup
import csv
import random

from fake_useragent import UserAgent

useragent = UserAgent()

# Создаем список куда будем выгружать все необходимые данные
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
            product_name = soup.find('div', attrs={'class': 'productView-product'}).find("h1").text
        except:
            product_name = "Нет названия"
        try:
            product_sky = soup.find('dl', attrs={'class': "productView-info"}).find('dd', attrs={
                'class': "productView-info-value"}).text
        except:
            product_sky = "Нет кода"
        try:
            product_katalog = soup.find('h2', attrs={'class': 'productView-brand'}).find("span").text
        except:
            product_katalog = "Нет каталога"
        try:
            product_price = soup.find('div', attrs={'class': 'productView-price'}).find('span', attrs={
                'class': 'price price--withoutTax'}).text
        except:
            product_price = "Нет цены"
        try:
            product_img = soup.find('figure', attrs={'class': 'productView-image fancy-gallery'}).get("href")
        except:
            product_img = "нет изображения"
        # Добавляем в список data все необходимые поля для дальнейшей передачи в csv
        data.append(
            [product_name, product_sky, product_katalog, product_price, product_img]
        )
    write_csv(data)


# Функция которая будет записывать данные из списка data
def write_csv(data):
    # Создаем файл с заголовками
    with open(f"C:\\scrap_tutorial-master\\moderngroup\\test.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'Название',
                'Каталожный номер',
                'Название группы',
                'Цена',
                'Ссылка на изображение'
            )
        )
        # Дописываем данные из списка data в файл
        writer.writerows(
            data
        )

# Функция для создания задач для асинхронного получение данных
async def gather_data():
    # Переходим по ссылкам
    for page in range(1, 278):
        url = f"https://shop.moderngroup.com/fleetguard/?sort=bestselling&page={page}"
        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": f"{useragent.random}"

        }
        # Создаем асинхронную ссеию
        async  with aiohttp.ClientSession() as session:
            # создаем список задач
            tasks = []
            # получаем список всех карточек
            response = await session.get(url=url, headers=header)
            soup = BeautifulSoup(await response.text(), 'lxml')
            table = soup.find('ul', attrs={'class': 'productGrid visible'}).find_all("li")
            url_product = []
            # Получаем список всех url на карточки
            for item in table[0:20]:
                href = item.find('a').get("href")
                url_product.append(href)
            #Добавляем все url в список задач
            for i in url_product:
               task = asyncio.create_task(get_page_data(session, i))
               tasks.append(task)
            await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())


if __name__ == '__main__':
    main()
