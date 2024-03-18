import csv
import random

import aiohttp
import asyncio

datas = []


async def get_page(session, url):
    bad_url = []
    good_url = []
    proxy_list = ['193.233.211.146:8080', '45.67.213.20:8080', '5.183.253.50:8080', '85.239.59.39:8080',
                  '93.177.116.11:8080', '85.209.150.34:8080', '178.159.107.86:8080', '45.145.131.200:8080',
                  '85.239.59.210:8080', '194.104.9.70:8080']
    proxy = f'http://{random.choice(proxy_list)}'
    proxy_auth = aiohttp.BasicAuth('USQ5Q5FG3', 'pN5hqMms')
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    async with session.get(url, headers=header, proxy=proxy, proxy_auth=proxy_auth) as r:
        if r.status == 200:
            good_url.append(url)
            return await r.text()
        else:
            bad_url.append(url)
            with open(f'bad_url.csv', "a",
                      newline='', errors='ignore') as file:
                writer = csv.writer(file)
                writer.writerow(bad_url)


async def get_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(get_page(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    await parse(results)

async def main(urls):
    async with aiohttp.ClientSession() as session:
        data = await get_all(session, urls)
        return data
async def parse(results, counter):
    for i in results:
        if i != None:
            counter += 1
            with open(
                    f"c:\\DATA_webstaurantstore\\0_{counter}.html",
                    "w", encoding='utf-8') as file:
                file.write(i)
        else:
            continue
    return counter


async def mains():
    async with aiohttp.ClientSession() as session:
        with open(f'url.csv', newline='',
                  encoding='utf-8') as files:
            csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
            counter = 0
            while len(csv_reader) > 0:
                url_batch = csv_reader[:100]
                urls = [row[0] for row in url_batch]
                results = await asyncio.gather(get_all(session, urls))
                counter = await parse(results[0], counter)
                csv_reader = csv_reader[100:]
                """Таймер перерыва в секундах"""
                await asyncio.sleep(10)

    # Остановить петлю событий и закрыть все async context managers
    await asyncio.sleep(0)
    await asyncio.get_running_loop().shutdown_asyncgens()
    results = asyncio.run(main(urls))









































# """ Рабочий скрипт, вводим вручную категорию"""
# import csv
# import aiohttp
# import asyncio
#
# datas = []
# category = "meskie"
#
# async def get_page(session, url):
#     bad_url = []
#     good_url = []
#     proxy = 'http://141.145.205.4:31281'
#     proxy_auth = aiohttp.BasicAuth('proxy_alex', 'DbrnjhbZ88')
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#     }
#
#     async with session.get(url, headers=header, proxy=proxy, proxy_auth=proxy_auth) as r:
#         if r.status == 200:
#             good_url.append(url)
#             return await r.text()
#         else:
#             bad_url.append(url)
#             with open(f'c:\\nbsklep_pl\\csv_url\\{category}\\bad_url.csv', "a",
#                       newline='', errors='ignore') as file:
#                 writer = csv.writer(file)
#                 writer.writerow(bad_url)
#
#
# async def get_all(session, urls):
#     tasks = []
#     for url in urls:
#         task = asyncio.create_task(get_page(session, url))
#         tasks.append(task)
#     results = await asyncio.gather(*tasks)
#     return results
#
#
# async def parse(results, counter):
#     for i in results:
#         if i != None:
#             counter += 1
#             with open(
#                     f"c:\\nbsklep_pl\\html_product\\{category}\\0_{counter}.html",
#                     "w", encoding='utf-8') as file:
#                 file.write(i)
#         else:
#             continue
#     return counter
#
#
# async def main():
#     urls = []
#     category = input("Введите категорию (damskie, dzieciece, meskie): ")
#
#     async with aiohttp.ClientSession() as session:
#         with open(f'c:\\nbsklep_pl\\csv_url\\{category}\\url.csv', newline='',
#                   encoding='utf-8') as files:
#             csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
#             counter = 0
#             while len(csv_reader) > 0:
#                 url_batch = csv_reader[:100]
#                 urls = [row[0] for row in url_batch]
#                 results = await asyncio.gather(get_all(session, urls))
#                 counter = await parse(results[0], counter)
#                 csv_reader = csv_reader[100:]
#                 """Таймер перерыва в секундах"""
#                 await asyncio.sleep(10)
#
#     # Остановить петлю событий и закрыть все async context managers
#     await asyncio.sleep(0)
#     await asyncio.get_running_loop().shutdown_asyncgens()
#
#
# if __name__ == '__main__':
#     asyncio.run(main())
















































# """Тут ничего не изменять, рабочий асинхронный парсер"""
# import csv
# import aiohttp
# import asyncio
#
# datas = []
# damskie = "damskie"
# dzieciece = "dzieciece"
# meskie = "meskie"
#
# async def get_page(session, url):
#     bad_url = []
#     good_url = []
#     proxy = 'http://141.145.205.4:31281'
#     proxy_auth = aiohttp.BasicAuth('proxy_alex', 'DbrnjhbZ88')
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#     }
#
#     async with session.get(url, headers=header, proxy=proxy, proxy_auth=proxy_auth) as r:
#         if r.status == 200:
#             good_url.append(url)
#             return await r.text()
#         else:
#             bad_url.append(url)
#             with open(f'c:\\nbsklep_pl\\csv_url\\meskie\\bad_url.csv', "a",
#                       newline='', errors='ignore') as file:
#                 writer = csv.writer(file)
#                 writer.writerow(bad_url)
#
#
# async def get_all(session, urls):
#     tasks = []
#     for url in urls:
#         task = asyncio.create_task(get_page(session, url))
#         tasks.append(task)
#     results = await asyncio.gather(*tasks)
#     return results
#
#
# async def parse(results, counter):
#     for i in results:
#         if i != None:
#             counter += 1
#             with open(
#                     f"c:\\nbsklep_pl\\html_product\\meskie\\0_{counter}.html",
#                     "w", encoding='utf-8') as file:
#                 file.write(i)
#         else:
#             continue
#     return counter
#
#
# async def main():
#     urls = []
#
#     async with aiohttp.ClientSession() as session:
#         with open(f'c:\\nbsklep_pl\\csv_url\\meskie\\url.csv', newline='',
#                   encoding='utf-8') as files:
#             csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
#             counter = 2000
#             while len(csv_reader) > 0:
#                 url_batch = csv_reader[:100]
#                 urls = [row[0] for row in url_batch]
#                 results = await asyncio.gather(get_all(session, urls))
#                 counter = await parse(results[0], counter)
#                 csv_reader = csv_reader[100:]
#                 """Таймер перерыва в секундах"""
#                 await asyncio.sleep(10)
#
#     # Остановить петлю событий и закрыть все async context managers
#     await asyncio.sleep(0)
#     await asyncio.get_running_loop().shutdown_asyncgens()
#
#
# if __name__ == '__main__':
#     asyncio.run(main())

# """Тестовый код где проверяется появился ли bad_url в папке а так же удаляет дубликаты"""
# import csv
# import os
# import aiohttp
# import asyncio
# from collections import Counter
#
#
# async def get_page(session, url):
#     bad_url = []
#     good_url = []
#     proxy = 'http://141.145.205.4:31281'
#     proxy_auth = aiohttp.BasicAuth('proxy_alex', 'DbrnjhbZ88')
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
#     }
#
#     async with session.get(url, headers=header, proxy=proxy, proxy_auth=proxy_auth) as r:
#         if r.status == 200:
#             good_url.append(url)
#             return await r.text()
#         else:
#             bad_url.append(url)
#             with open(f'c:\\nbsklep_pl\\csv_url\\damskie\\bad_url.csv', "a",
#                       newline='', errors='ignore') as file:
#                 writer = csv.writer(file)
#                 writer.writerow(bad_url)
#
#
# async def get_all(session, urls):
#     tasks = []
#     for url in urls:
#         task = asyncio.create_task(get_page(session, url))
#         tasks.append(task)
#     results = await asyncio.gather(*tasks)
#     return results
#
#
# async def parse(results, counter):
#     for i in results:
#         if i != None:
#             counter += 1
#             with open(
#                     f"c:\\nbsklep_pl\\html_product\\damskie\\0_{counter}.html",
#                     "w", encoding='utf-8') as file:
#                 file.write(i)
#         else:
#             continue
#     return counter
#
#
# async def main():
#     urls = []
#
#     async with aiohttp.ClientSession() as session:
#         with open(f'c:\\nbsklep_pl\\csv_url\\damskie\\url.csv', newline='',
#                   encoding='utf-8') as files:
#             csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
#             counter = 0
#             while len(csv_reader) > 0:
#                 url_batch = csv_reader[:100]
#                 urls = [row[0] for row in url_batch]
#                 results = await asyncio.gather(get_all(session, urls))
#                 counter = await parse(results[0], counter)
#                 csv_reader = csv_reader[100:]
#                 """Таймер перерыва в секундах"""
#                 await asyncio.sleep(10)
#                 # проверяем, есть ли файл с плохими URL-адресами
#                 if os.path.isfile(
#                         f'c:\\nbsklep_pl\\csv_url\\meskie\\bad_url.csv'):
#                     # открываем файл с плохими URL-адресами и удаляем дубликаты строк
#                     with open(f'c:\\nbsklep_pl\\csv_url\\meskie\\bad_url.csv',
#                               'r', newline='', encoding='utf-8') as csvfile:
#                         reader = csv.reader(csvfile)
#                         rows = [row for row in reader]
#                         rows = list(set(map(tuple, rows)))
#                     # перезаписываем файл с плохими URL-адресами без дубликатов строк
#                     with open(f'c:\\nbsklep_pl\\csv_url\\meskie\\url.csv',
#                               'w', newline='', encoding='utf-8') as csvfile:
#                         writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
#                         for row in rows:
#                             writer.writerow(row)
#
#     # Остановить петлю событий и закрыть все async context managers
#     await asyncio.sleep(0)
#     await asyncio.get_running_loop().shutdown_asyncgens()
