import aiohttp
import asyncio
import os
import csv
import random
import re

cookies = {
    'v': '1687848153_74d4366d-1573-4382-bc2c-be266fb756cc_96b40c8110d3f894f963285720be83e7',
    'vct': 'en-US-CR%2FZhJpk8B%2FZhJpkSBzZhJpk4R3ZhJpk4h3ZhJpk',
    '_csrf': 'StX0ZKuTVQBTQ0mDfF0sXLIu',
    'documentWidth': '1920',
    '_gid': 'GA1.2.1863417168.1687848156',
    '_gat': '1',
    '_gcl_au': '1.1.2033939751.1687848156',
    '_dc_gtm_UA-3519678-1': '1',
    '_ga': 'GA1.1.319988719.1687848156',
    '_ga_PB0RC2CT7B': 'GS1.1.1687848156.1.0.1687848156.60.0.0',
    'hzd': '986105c2-7640-4ab8-b1af-2c27229df6d8%3A%3A%3A%3A%3ASendMessage',
    '_uetsid': 'cd4ee82014b511ee8b4eb1f8dba29af2',
    '_uetvid': 'cd4f245014b511ee9f593927fb7eeb6c',
    'IR_gbd': 'houzz.com',
    'IR_5455': '1687848156366%7C0%7C1687848156366%7C%7C',
    'ln_or': 'eyIzODE1NzE2IjoiZCJ9',
    '_pin_unauth': 'dWlkPVlXTmpNVGRrWkdRdE9EWmhPUzAwTTJRMExUazVZMlV0WkdJeFlqTTRaV1F4TUdWaA',
    'crossdevicetracking': 'f3b0fe77-6c60-4f86-9405-a1c54c483085',
    'jdv': '1%2BDQmxez6xvavGde',
}

headers = {
    'authority': 'www.houzz.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': 'v=1687848153_74d4366d-1573-4382-bc2c-be266fb756cc_96b40c8110d3f894f963285720be83e7; vct=en-US-CR%2FZhJpk8B%2FZhJpkSBzZhJpk4R3ZhJpk4h3ZhJpk; _csrf=StX0ZKuTVQBTQ0mDfF0sXLIu; documentWidth=1920; _gid=GA1.2.1863417168.1687848156; _gat=1; _gcl_au=1.1.2033939751.1687848156; _dc_gtm_UA-3519678-1=1; _ga=GA1.1.319988719.1687848156; _ga_PB0RC2CT7B=GS1.1.1687848156.1.0.1687848156.60.0.0; hzd=986105c2-7640-4ab8-b1af-2c27229df6d8%3A%3A%3A%3A%3ASendMessage; _uetsid=cd4ee82014b511ee8b4eb1f8dba29af2; _uetvid=cd4f245014b511ee9f593927fb7eeb6c; IR_gbd=houzz.com; IR_5455=1687848156366%7C0%7C1687848156366%7C%7C; ln_or=eyIzODE1NzE2IjoiZCJ9; _pin_unauth=dWlkPVlXTmpNVGRrWkdRdE9EWmhPUzAwTTJRMExUazVZMlV0WkdJeFlqTTRaV1F4TUdWaA; crossdevicetracking=f3b0fe77-6c60-4f86-9405-a1c54c483085; jdv=1%2BDQmxez6xvavGde',
    'dnt': '1',
    'pragma': 'no-cache',
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

async def download(url, counter, group):
    async with aiohttp.ClientSession() as session:
        try:
            proxy = random.choice(proxies)
            ip, port, user, password = proxy
            proxy_auth_str = f'http://{user}:{password}@{ip}:{port}'
            async with session.get(url, cookies=cookies, headers=headers, proxy=proxy_auth_str) as response: #, proxy=proxy, proxy_auth=proxy_auth
                content = await response.text()
                filename = f"c:\\DATA\\houzz_com\\product\\{group}\\data_{counter}.html"
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
    delay = 1

    csv_folder = "c:\\scrap_tutorial-master\\houzz_es\\url\\"  # Путь к папке с CSV файлами
    csv_files = [file for file in os.listdir(csv_folder) if file.endswith(".csv")]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for csv_file in csv_files:
            with open(os.path.join(csv_folder, csv_file), encoding='latin-1') as f:
                reader = csv.reader(f)
                urls = [row[0] for row in reader]

            group = re.findall(r"([^\\/:*?\"<>|]+)\.csv", csv_file)[0]  # Извлекаем группу из имени файла

            counter = 0
            for url in urls:
                # delay = random.randint(10,30)

                tasks.append(download(url, counter, group))
                counter += 1
                if counter % limit == 0:
                    await asyncio.gather(*tasks)
                    tasks = []
                    print(f"Waiting for {delay} seconds... {counter}")
                    await asyncio.sleep(delay)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
