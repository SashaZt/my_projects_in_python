import aiohttp
import asyncio
import os
import csv
import random
import re

cookies = {
    'test-session': '1',
    'CSRF_TOKEN': '27049938f262c4d945ff09032720e8035973c63b8406d6ce868598079374c98f',
    'test-persistent': '1',
    'test-session': '1',
    'visitedDashboard': '1',
    'BVBRANDID': '620af17a-81da-42a6-8734-2797d91a1470',
    'PHPSESSID': 'a3772f85e62bb053a15170b3bba43690',
}

headers = {
    'authority': 'www.centraldispatch.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'test-session=1; CSRF_TOKEN=27049938f262c4d945ff09032720e8035973c63b8406d6ce868598079374c98f; test-persistent=1; test-session=1; visitedDashboard=1; BVBRANDID=620af17a-81da-42a6-8734-2797d91a1470; PHPSESSID=a3772f85e62bb053a15170b3bba43690',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.centraldispatch.com/protected/rating/client-snapshot?id=900767da-49b7-4036-9ac0-925ea3d250d7',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
from proxi import proxies

async def download(url, counter):
    async with aiohttp.ClientSession() as session:
        try:
            proxy = random.choice(proxies)
            ip, port, user, password = proxy
            proxy_auth_str = f'http://{user}:{password}@{ip}:{port}'
            async with session.get(url, cookies=cookies, headers=headers, proxy=proxy_auth_str) as response: #, proxy=proxy, proxy_auth=proxy_auth
                content = await response.text()
                filename = f"c:\\DATA\\centraldispatch\\products\\data_{counter}.html"
                if not os.path.isfile(filename):
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    # print(f"Saved {url} to {filename}")
                else:
                    print(f"File {filename} already exists")

        except Exception as e:
            print(f"Error downloading {url}: {e}")


async def main():
    """
    counter - счетчик начало отсчета
    limit - лимит запросов за один проход
    delay - пауза в секундах до следующего захода, random.randint(10,30) случайная пауза от 10 до 30 сек
    """
    # counter = 0
    limit = 1000
    delay = 10

    csv_folder = "c:\\scrap_tutorial-master\\centraldispatch\\url\\"  # Путь к папке с CSV файлами
    csv_files = [file for file in os.listdir(csv_folder) if file.endswith(".csv")]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for csv_file in csv_files:
            with open(os.path.join(csv_folder, csv_file), encoding='latin-1') as f:
                reader = csv.reader(f)
                urls = [row[0] for row in reader]

            counter = 0
            for url in urls:
                # delay = random.randint(10,30)

                tasks.append(download(url, counter))
                counter += 1
                if counter % limit == 0:
                    await asyncio.gather(*tasks)
                    tasks = []
                    print(f"Waiting for {delay} seconds... {counter}")
                    await asyncio.sleep(delay)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
