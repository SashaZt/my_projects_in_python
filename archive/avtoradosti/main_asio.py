import aiohttp
import asyncio
from pathlib import Path
import csv
import os
import random
from proxi import proxies
from headers_cookies_aiso import headers


coun = 0

async def fetch(session, url, coun):
    name_files = Path('c:/DATA/avtoradosti/pages/ru/') / f'data_{coun}.html'
    if os.path.exists(name_files):
        return  # Если файл уже существует, то завершаем выполнение функции

    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'

    async with session.get(url, headers=headers, proxy=proxi) as response:
        with open(name_files, "w", encoding='utf-8') as file:
            file.write(await response.text())

async def main():
    name_files = Path(f'c:/scrap_tutorial-master/avtoradosti/') / 'url_ru.csv'
    global coun
    async with aiohttp.ClientSession() as session:
        with open(name_files, newline='', encoding='utf-8') as files:
            urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            for i in range(0, len(urls), 10):  # Используйте срезы для создания пакетов по 100 URL
                tasks = []
                for row in urls[i:i+10]:
                    coun += 1
                    url = row[0]
                    tasks.append(fetch(session, url, coun))
                await asyncio.gather(*tasks)
                print(f'Completed {coun} requests')
                await asyncio.sleep(1)  # Пауза на 10 секунд после каждых 100 URL

asyncio.run(main())