import aiohttp
import asyncio
from pathlib import Path
import csv
import os
import ssl

import random
from proxi import proxies

"""Укр"""
# from headers_cookies_aiso import headers

"""Рус"""
from headers_cookies_aiso_rus import headers
coun = 0
delta = '''
avtolampa
'''


delta_list = delta.strip().split("\n")
"""Рабочий код"""
async def fetch(session, url, coun, folders):
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    """Укр"""
    # name_files = Path(f'c:/DATA/dok_ua/products/{folders}/ua/') / f'data_{coun}.html'
    """Рус"""
    name_files = Path(f'c:/DATA/dok_ua/products/{folders}/rus/') / f'data_{coun}.html'
    if not os.path.exists(name_files):
        # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # Используйте подходящую версию протокола
        # ssl_context.verify_mode = ssl.CERT_NONE  # Отключите проверку сертификата
        try:
            async with session.get(url, headers=headers, proxy=proxi) as response: #, ssl=ssl_context
                with open(name_files, "w", encoding='utf-8') as file:
                    file.write(await response.text())
        except Exception as e:
            print(f"An error occurred: {e}. Skipping this iteration.")

async def main():
    global coun
    for folders in delta_list:
        coun = 0  # Сброс счётчика для нового значения folders
        """Укр"""
        # name_files = Path(f'c:/scrap_tutorial-master/archive/dok.ua/link/') / f'{folders}.csv'
        """Рус"""
        name_files = Path(f'c:/scrap_tutorial-master/archive/dok.ua/link/') / f'{folders}_rus.csv'

        async with aiohttp.ClientSession() as session:
            with open(name_files, newline='', encoding='utf-8') as files:
                urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            for i in range(0, len(urls), 10):
                tasks = []
                for row in urls[i:i + 10]:
                    coun += 1
                    url = row[0]
                    tasks.append(fetch(session, url, coun, folders))  # передаем folders как аргумент
                await asyncio.gather(*tasks)
                print(f'Completed {coun} requests for {folders}')
                await asyncio.sleep(1)

asyncio.run(main())