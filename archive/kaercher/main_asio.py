import aiohttp
import asyncio
from pathlib import Path
import csv
import os
import random
from proxi import proxies
from headers_cookies_aiso import headers
from all_urls_one import urls

coun = 0

async def fetch(session, url, coun):
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    name_files = Path('c:/DATA/kaercher/one/') / f'data_{coun}.html'
    if not os.path.exists(name_files):
        async with session.get(url, headers=headers, proxy=proxi) as response:
            with open(name_files, "w", encoding='utf-8') as file:
                file.write(await response.text())

async def main():
    # name_files = Path(f'c:/data_wmmotor/list/') / 'data.csv'
    global coun
    async with aiohttp.ClientSession() as session:
        # with open(name_files, newline='', encoding='utf-8') as files:
        #     urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for i in range(0, len(urls), 100):  # Используйте срезы для создания пакетов по 100 URL
            tasks = []
            for row in urls[i:i+100]:
                coun += 1
                url = row
                tasks.append(fetch(session, url, coun))
            await asyncio.gather(*tasks)
            print(f'Completed {coun} requests')
            await asyncio.sleep(10)  # Пауза на 10 секунд после каждых 100 URL

asyncio.run(main())