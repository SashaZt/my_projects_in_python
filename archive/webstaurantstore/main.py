import csv
import re
import random
import datetime
import aiohttp
import asyncio
import concurrent.futures
from math import floor
from bs4 import BeautifulSoup

# Создаем список куда будем выгружать все необходимые данные
data = []


async def get_page_data(session, href):
    with open('proxies.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        # print(random.choice(csv_reader))

        proxy = f'http://{random.choice(csv_reader)[0]}'
        proxy_auth = aiohttp.BasicAuth('USQ5Q5FG3', 'pN5hqMms')

        # # start_time = datetime.datetime.now()
        # proxy = 'http://141.145.205.4:31281'
        # proxy_auth = aiohttp.BasicAuth('proxy_alex', 'DbrnjhbZ88')
        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

        }
        async with aiohttp.ClientSession() as session:
            resp_url = await session.get(href, headers=header, proxy=proxy, proxy_auth=proxy_auth)
            if resp_url.status == 200:
                soup = BeautifulSoup(await resp_url.text(), 'lxml')

                try:
                    product_name = soup.find('h1', attrs={'id': 'page-header-description'}).text
                except:
                    product_name = "not product_name"
                try:
                    product_sky = soup.find('div', attrs={'class': "product__stat"}).text.replace("\n", "")
                except:
                    product_sky = "not product_sky"
                # regex_price = re.compile('price*')
                try:
                    product_price = soup.find('div', attrs={'class': 'pricing'}).text.replace("\n", "")
                except:
                    product_price = "not product_price"
                if not soup.find('div', attrs={'id': "unavailableContainer"}):
                    availability = 1
                else:
                    availability = 0
                data.append(
                    [href, product_name, product_sky, product_price, availability]
                )

        write_csv(data)


# Функция для создания задач для асинхронного получение данных
async def gather_data():
    # with open('proxies.csv', newline='', encoding='utf-8') as files:
    #     csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
    #     # print(random.choice(csv_reader))
    #
    #     #
    #     # proxy = f'http://194.104.9.200:8080'
    #     proxy = f'http://{random.choice(csv_reader)[0]}'
    #
    #     proxy_auth = aiohttp.BasicAuth('USQ5Q5FG3', 'pN5hqMms')
    #     header = {
    #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
    #
    #     }
    #     # Переходим по ссылкам
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        tasks = []
        for row in csv_reader[:10]:
            href = row[0]
            # Создаем асинхронную ссесию

            async  with aiohttp.ClientSession() as session:
                # создаем список задач
                tasks = []
                # # получаем список всех карточек
                # response = await session.get(url=href, headers=header, proxy=proxy, proxy_auth=proxy_auth)
                # soup = BeautifulSoup(await response.text(), 'lxml')
                # table = soup.find('ul', attrs={'class': 'productGrid visible'}).find_all("li")
                # url_product = []
                # # Получаем список всех url на карточки
                # for item in table[0:20]:
                #     href = item.find('a').get("href")
                #     url_product.append(href)
                # # Добавляем все url в список задач
                # for i in url_product:
                task = asyncio.create_task(get_page_data(session, href))
                tasks.append(task)
            await asyncio.gather(*tasks)


# Функция которая будет записывать данные из списка data
def write_csv(data):
    # Создаем файл с заголовками
    with open(f"C:\\scrap_tutorial-master\\webstaurantstore\\test.csv", "w", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'href',
                'product_name',
                'product_sky',
                'product_price',
                'availability'
            )
        )
        # Дописываем данные из списка data в файл
        writer.writerows(
            data
        )


def main():
    asyncio.run(gather_data())


if __name__ == '__main__':
    main()
