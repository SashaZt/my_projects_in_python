import aiohttp
import asyncio
import os
import csv
import random
import sys
import json

cookies = {
    'test-session': '1',
    'CSRF_TOKEN': '82a663187eaf8afc434858917116538ba79c633122d3a8d7dbf8bee2bbf4fead',
    'test-persistent': '1',
    'test-session': '1',
    'visitedDashboard': '1',
    'PHPSESSID': 'd7752d8eebee1f7c2daf96d7dcb6a7c9',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    # 'cookie': 'test-session=1; CSRF_TOKEN=82a663187eaf8afc434858917116538ba79c633122d3a8d7dbf8bee2bbf4fead; test-persistent=1; test-session=1; visitedDashboard=1; PHPSESSID=d7752d8eebee1f7c2daf96d7dcb6a7c9',
    'dnt': '1',
    'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}
def load_proxy():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_proxy = os.path.join(application_path, "proxi.json")
    if not os.path.exists(filename_proxy):
        print("Нету файла с прокси-серверами!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)  # Завершаем выполнение скрипта с кодом ошибки 1
    else:
        with open(filename_proxy, "r") as file:
            proxies = json.load(file)
        proxy = random.choice(proxies)
        proxy_host, proxy_port, proxy_user, proxy_pass = proxy
        formatted_proxy_http = (
            f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        )
        formatted_proxy_https = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"  # Измените, если https требует другой прокси

        # Для requests
        proxies_dict = {"http": formatted_proxy_http, "https": formatted_proxy_https}

        # Для aiohttp (если вам нужен только один прокси, верните formatted_proxy_http или formatted_proxy_https)
        # Возвращаем оба формата для удобства
        return proxies_dict, formatted_proxy_http

async def download(url, counter):
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    products_path = os.path.join(temp_path, "products")
    async with aiohttp.ClientSession() as session:
        try:
            proxies_requests, proxy_aiohttp = load_proxy()
            async with session.get(url, cookies=cookies, headers=headers, proxy=proxy_aiohttp) as response: #, proxy=proxy, proxy_auth=proxy_auth
                content = await response.text()
                url_name = url.split("=")[-1]
                filename_html = os.path.join(products_path, f"{url_name}.html")
                if not os.path.isfile(filename_html):
                    with open(filename_html, "w", encoding="utf-8") as f:
                        f.write(content)
                    # print(f"Saved {url} to {filename}")
                else:
                    print(f"File {filename_html} already exists")

        except Exception as e:
            print(f"Error downloading {url}: {e}")


async def main():
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    list_path = os.path.join(temp_path, "list")
    products_path = os.path.join(temp_path, "products")
    """
    counter - счетчик начало отсчета
    limit - лимит запросов за один проход
    delay - пауза в секундах до следующего захода, random.randint(10,30) случайная пауза от 10 до 30 сек
    """
    # counter = 0
    limit = 10
    delay = 20

    filename_csv = os.path.join(current_directory, "unique_company_ids.csv")

    async with aiohttp.ClientSession() as session:
        tasks = []
        with open(filename_csv, encoding='latin-1') as f:
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
