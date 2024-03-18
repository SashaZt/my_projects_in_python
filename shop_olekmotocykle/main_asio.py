import aiohttp
import asyncio
from pathlib import Path
import csv
import os
import random
from proxi import proxies
from headers_cookies import headers
current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
category_path = os.path.join(temp_path, "category")

coun = 0


async def fetch(session, url, coun):
    
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    async with session.get(url, headers=headers, proxy=proxi) as response:
        filename_html = os.path.join(html_path, f'data_{coun}.html')
        if not os.path.exists(filename_html):
            with open(filename_html, "w", encoding='utf-8') as file:
                file.write(await response.text())


async def main():
    filename_url = os.path.join(category_path, "url.csv")
    global coun

    async with aiohttp.ClientSession() as session:
        with open(filename_url, newline='', encoding='utf-8') as files:
            urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            for i in range(0, len(urls), 5):
                tasks = []
                for row in urls[i:i + 5]:
                    coun += 1
                    url = row[0]
                    filename_html = os.path.join(html_path, f'data_{coun}.html')
                    if not os.path.exists(filename_html):
                        tasks.append(fetch(session, url, coun))
                if tasks:
                    await asyncio.gather(*tasks)
                    print(f'Completed {coun} requests')
                    await asyncio.sleep(1)  # Пауза на 10 секунд после каждых 100 URL

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main())