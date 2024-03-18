import aiohttp
import asyncio
from pathlib import Path
import csv
import os
import random
from proxi import proxies
from headers_cookies_aiso import headers
import json
import aiofiles


def count_lines_in_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return sum(1 for line in f)
def count_files_in_directory(directory):
    return len([f for f in Path(directory).iterdir() if f.is_file()])


async def fetch(session, url, coun):
    proxy = random.choice(proxies)

    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]

    proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    name_files = Path('c:/DATA/copart/product/') / f'data_{coun}.json'
    if not os.path.exists(name_files):
        try:
            async with session.get(url, headers=headers, proxy=proxi) as response:
                if response.headers.get('Content-Type').startswith('application/json'):
                    data_json = await response.json()
                    async with aiofiles.open(name_files, 'w') as f:
                        await f.write(json.dumps(data_json))
                else:
                    print(f"Unexpected content type {response.headers.get('Content-Type')} for URL {url}")

        except Exception as e:
            print(f"Error fetching {url}: {e}")


async def main():
    name_files = Path('c:/scrap_tutorial-master/copart/') / 'url.csv'
    directory_to_check = Path('c:/DATA/copart/product/')


    total_urls = count_lines_in_csv(name_files)

    while True:  # Основной цикл для повторного выполнения, если необходимо
        coun = 0
        async with aiohttp.ClientSession() as session:
            with open(name_files, newline='', encoding='utf-8') as files:
                urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
                for i in range(0, len(urls), 100):  # Используйте срезы для создания пакетов по 10 URL
                    tasks = []
                    for row in urls[i:i + 100]:
                        coun += 1
                        url = row[0]
                        tasks.append(fetch(session, url, coun))
                    await asyncio.gather(*tasks)
                    print(f'Completed {coun} requests')
                    await asyncio.sleep(2)  # Пауза на 1 секунду после каждых 10 URL

        total_files = count_files_in_directory(directory_to_check)

        if total_files >= total_urls * 0.9:
            break  # Если достигнуто или превышено ожидаемое количество файлов, выйдите из цикла

        print("Not all files are present. Re-running...")
        await asyncio.sleep(10)  # Пауза перед повторным выполнением. Можете изменить длительность.


asyncio.run(main())
