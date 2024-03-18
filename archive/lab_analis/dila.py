import csv
import glob
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

headers = {
    'authority': 'dila.ua',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'PHPSESSID=2blisbg9al9u2v59d1h5ta4p4d; _csrf=ba8ca219596450d0d53660f87b456e7fd2718945b1f8337e0b274d2302588997a%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22P8OGInbIrKLUU2OhVcyUnaPOyt0FFvou%22%3B%7D',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
}
current_directory = os.getcwd()
temp_directory = 'temp_dila'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
pages_path = os.path.join(temp_path, 'pages_dila')
product_path = os.path.join(temp_path, 'product_dila')


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, pages_path, product_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [pages_path, product_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


def get_pages():
    cookies = {
        'PHPSESSID': '2blisbg9al9u2v59d1h5ta4p4d',
        '_csrf': 'ba8ca219596450d0d53660f87b456e7fd2718945b1f8337e0b274d2302588997a%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22P8OGInbIrKLUU2OhVcyUnaPOyt0FFvou%22%3B%7D',
    }

    for page in range(1, 83):
        params = {
            'tab': 'research',
            'page': page,
            'per-page': '15',
        }
        name_files = Path('c:/Data_dila/') / f'data_0{page}.html'
        if not os.path.exists(name_files):
            response = requests.get('https://dila.ua/price.html', params=params, cookies=cookies, headers=headers)
            response.encoding = 'utf-8'
            src = response.text
            filename = name_files
            with open(filename, "w", encoding='utf-8') as file:
                file.write(src)


def parsing_pages():
    path = Path('c:/Data_dila/').glob('*.html')
    with open('url_product.csv', 'w', newline='') as csvfile:
        for item in path:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            analizes_list_table = soup.find_all('div', {'class', 'analizes-list-table-cell altc-name'})[1:16]
            for a in analizes_list_table:
                link_tag = a.find('a')
                if link_tag is None:
                    break
                href = link_tag.get('href')
                csvfile.write(href + '\n')


def parsing():
    path = Path(product_path).glob('*.html')
    heandler = ['name_analis', 'cod_analis', 'price_analis', 'time_analis', 'group01', 'group02', 'group03',
                'codu_group01',
                'codu_group02', 'codu_group03']
    with open('dila_output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in path:
            with open(item, encoding="utf-8") as file:
                src = file.read()

                # Используйте BeautifulSoup для парсинга HTML
                soup = BeautifulSoup(src, 'lxml')
                breadcrumbs = soup.find('div', {'class': 'breadcrumbs'})
                try:
                    breadcrumbs_all_span = breadcrumbs.find_all('span', {'itemprop': 'name'})[2:]
                except:
                    continue
                try:
                    group01 = breadcrumbs_all_span[0].get_text(strip=True)
                except:
                    group01 = None
                try:
                    group02 = breadcrumbs_all_span[1].get_text(strip=True)
                except:
                    group02 = None
                try:
                    group03 = breadcrumbs_all_span[2].get_text(strip=True)
                except:
                    group03 = None
                analizes_list_table = soup.find('div', {'class': 'analizes-list-table'})
                name_analis = analizes_list_table.find_all('div', {'class': 'analizes-list-table-cell altc-name'})[
                    1].get_text(
                    strip=True)
                cod_analis_row = soup.find('link', {'rel': 'alternate'}).get('href')
                # match_cod_analis_row = re.search(r'/(\d+)[_-]', cod_analis_row)
                match_cod_analis_row = re.search(r'/(\d+)[_-]|program_slug=(\d+)_', cod_analis_row)
                try:
                    cod_analis = match_cod_analis_row.group(1)
                except:
                    cod_analis = match_cod_analis_row.group(2)
                    # print(item)
                price_analis = analizes_list_table.find('span', {'class': 'js-item-price val'}).get_text(strip=True)
                time_analis = analizes_list_table.find('span', {'class': 'js-item-time val'}).get_text(strip=True)
                values = [name_analis, cod_analis, price_analis, time_analis, group01, group02, group03]

                for u in breadcrumbs.find_all('a'):
                    href = u.get('href')
                    if href and href.startswith('https://dila.ua/programs/'):
                        match = re.search(r'/(\d+)[_-]', href)
                        try:
                            number = match.group(1)
                        except:
                            continue
                        values.extend([number])

                writer.writerow(values)


def parsing_():
    file = "dila.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        analizes_list_table = soup.find_all('div', {'class', 'analizes-list-table-cell altc-name'})[1:16]
        for a in analizes_list_table:
            link_tag = a.find('a')
            if link_tag is None:
                break
            href = link_tag.get('href')
            print(href)


def get_asio():
    import aiohttp
    import asyncio
    import csv
    import os
    # from proxi import proxies
    # from headers_cookies_aiso import headers

    async def fetch(session, url, coun):
        # proxy = random.choice(proxies)
        # proxy_host = proxy[0]
        # proxy_port = proxy[1]
        # proxy_user = proxy[2]
        # proxy_pass = proxy[3]
        # proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
        filename = os.path.join(product_path, f'data_0{coun}.html')
        if not os.path.exists(filename):
            async with session.get(url, headers=headers) as response:  # , proxy=proxi
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(await response.text())

    async def main():
        filename = os.path.join(current_directory, 'url_product.csv')
        # global coun
        coun = 0
        async with aiohttp.ClientSession() as session:
            with open(filename, newline='', encoding='utf-8') as files:
                urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
                for i in range(0, len(urls), 10):  # Используйте срезы для создания пакетов по 100 URL
                    tasks = []
                    for row in urls[i:i + 10]:
                        coun += 1
                        url = row[0]
                        tasks.append(fetch(session, url, coun))
                    await asyncio.gather(*tasks)
                    print(f'Completed {coun} requests')
                    await asyncio.sleep(5)  # Пауза на 10 секунд после каждых 100 URL

    asyncio.run(main())


if __name__ == '__main__':
    delete_old_data()
    get_pages()
    parsing_pages()
    get_asio()
    parsing()
