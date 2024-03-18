import csv
import os
import random
import aiohttp
import asyncio
from headers_cookies_aiso import headers

coun = 0
file_path = "proxy.txt"

def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if '@' in line and ':' in line]
    except FileNotFoundError:
        return []

def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None

async def fetch(session, url, coun, new_folder_path, use_proxy=True):
    proxy_dict = None

    if use_proxy:
        proxies = load_proxies(file_path)
        if proxies:
            proxy = get_random_proxy(proxies)
            if proxy:
                login_password, ip_port = proxy.split('@')
                login, password = login_password.split(':')
                ip, port = ip_port.split(':')
                proxy_url = f'http://{login}:{password}@{ip}:{port}'
                proxy_dict = {'http': proxy_url, 'https': proxy_url}
    if proxy_dict:
        async with session.get(url, headers=headers, proxy=proxy_dict) as response:
            name_file = f'{new_folder_path}\\data_{coun}.html'
            if not os.path.exists(name_file):
                with open(name_file, "w", encoding='utf-8') as file:
                    file.write(await response.text())
    else:
        async with session.get(url, headers=headers) as response:
            name_file = f'{new_folder_path}\\data_{coun}.html'
            if not os.path.exists(name_file):
                with open(name_file, "w", encoding='utf-8') as file:
                    file.write(await response.text())


async def main():
    # Получаем значение переменной окружения USERPROFILE
    user_profile = os.environ.get('USERPROFILE')

    # Создаем путь к новой папке
    new_folder_path = os.path.join(user_profile, 'prom')
    name_files = f'{new_folder_path}\\urls.csv'
    global coun
    async with aiohttp.ClientSession() as session:
        with open(name_files, newline='', encoding='utf-8') as files:
            urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            for i in range(0, len(urls), 10):  # Используйте срезы для создания пакетов по 100 URL
                tasks = []
                for row in urls[i:i + 10]:
                    coun += 1
                    url = row[0]
                    tasks.append(fetch(session, url, coun, new_folder_path))
                await asyncio.gather(*tasks)
                print(f'Completed {coun} requests')
                await asyncio.sleep(1)  # Пауза на 10 секунд после каждых 100 URL


if __name__ == '__main__':
    asyncio.run(main())
