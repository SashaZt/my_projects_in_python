from urllib.parse import urlparse
import asyncio
import csv
import random
import re
from collections import defaultdict
from datetime import datetime
import json
import html
import csv
import requests
from bs4 import BeautifulSoup
import os
import glob
from collections import defaultdict
import shutil

file_path = "proxy.txt"

def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if '@' in line and ':' in line]
    except FileNotFoundError:
        return []

def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None
def get_requests(url, use_proxy=True):
    cookies = {
        'cid': '149905558730700005005275127777618119701',
        'evoauth': 'wb52a1c0a48654244bc20f4f10d96b6b9',
        '_ga': 'GA1.1.834139681.1693817061',
        '_gcl_au': '1.1.788596630.1693817061',
        '_ga_T7S2G9Q21Q': 'GS1.1.1693817060.1.0.1693817062.0.0.0',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'max-age=0',
        # 'cookie': 'cid=149905558730700005005275127777618119701; csrf_token_company_site=6d036671fbdd4a97a70b683eae812906; evoauth=wb52a1c0a48654244bc20f4f10d96b6b9; _ga=GA1.1.834139681.1693817061; _gcl_au=1.1.788596630.1693817061; _ga_T7S2G9Q21Q=GS1.1.1693817060.1.0.1693817062.0.0.0',
        'dnt': '1',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
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
    user_profile = os.environ.get('USERPROFILE')
    new_folder_path = os.path.join(user_profile, 'prom')

    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    url = f'{url}testimonials'
    if proxy_dict:
        response = requests.get(url, cookies=cookies, headers=headers, proxies=proxy_dict)
    else:
        response = requests.get(url, cookies=cookies, headers=headers)

    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    pagin_old = int(soup.find('div', attrs={'class': 'b-pager'}).find('div', {'data-pagination-pages-count': True})[
                        'data-pagination-pages-count'])
    with open(f'{new_folder_path}\\urls.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(1, pagin_old + 1):
            page = f'{url}/page_{i}'
            writer.writerow([page])


def pars(site):
    user_profile = os.environ.get('USERPROFILE')
    new_folder_path = os.path.join(user_profile, 'prom')
    files_html = glob.glob(os.path.join(new_folder_path, '*.html'))
    file_csv = 'products.csv'

    if os.path.exists(file_csv):
        # Если существует, удаляем
        os.remove(file_csv)
    # with open(file_csv, 'w', newline='', encoding='windows-1251') as csvfile:
    with open('products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for item_html in files_html:
            with open(item_html, encoding="utf-8") as file:
            # with open(item_html, encoding="windows-1251") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            url_site = site
            url_site = url_site.replace("/ua/", "")

            regex_comments = re.compile('.*-comments__item')
            comments = soup.find_all('li', attrs={'class': regex_comments})
            for c in comments:
                regex_data_comments = re.compile('.*date')
                data_comments = c.find('time', attrs={'class': regex_data_comments}).get('datetime')
                dt_object = datetime.strptime(data_comments, "%Y-%m-%dT%H:%M:%S")
                formatted_date = dt_object.year
                regex_product_comments = re.compile('.*comments__answer')
                try:
                    product_comments = c.find('div', attrs={'class': regex_product_comments}).get(
                        'data-reviews-products')
                except:
                    product = []
                    product.append(formatted_date)  # Сначала дата
                    url_no_category = 'Нет url'
                    name_no_category = 'Без названия товара'
                    product.append(url_no_category)
                    product.append(name_no_category)
                    # product = [formatted_date, url_no_category.encode('windows-1251', 'ignore').decode('windows-1251'),
                    #            name_no_category.encode('windows-1251', 'ignore').decode('windows-1251')]

                    writer.writerow(product)
                if product_comments is not None:
                    decoded_str = html.unescape(product_comments)
                    data = json.loads(decoded_str)
                    for item in data:
                        product = []
                        if item['url']:
                            url = f"{url_site}{item['url']}"
                        else:
                            url = 'Нет url'
                        product.append(formatted_date)
                        product.append(url)
                        names = item['name']
                        product.append(names)
                        # product = [formatted_date,
                        #            url,  # Добавляем URL сюда
                        #            names.encode('windows-1251', 'ignore').decode('windows-1251'),
                        #            ]
                        writer.writerow(product)
                else:
                    product = []
                    product.append(formatted_date)  # Сначала дата
                    url_no_category = 'Нет url'
                    name_no_category = 'Без названия товара'
                    product.append(url_no_category)
                    product.append(name_no_category)
                    writer.writerow(product)


def analis_product(site):
    all_url = urlparse(site)
    # Извлекаем часть доменного имени с субдоменами
    domain_parts = all_url.netloc.split('.')
    subdomain = None
    if len(domain_parts) >= 2:
        subdomain = domain_parts[0]
    user_profile = os.environ.get('USERPROFILE')
    new_folder_path = os.path.join(user_profile, 'prom')
    data = []
    # with open('products.csv', 'r', encoding='windows-1251') as f:
    with open('products.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            data.append(row)
    stats_by_year_and_product = defaultdict(lambda: defaultdict(int))

    product_urls = {}  # для хранения URL каждого продукта
    unique_years = sorted({date.split('.')[-1] for date, _, _ in data}, reverse=True)

    # unique_years = sorted({date.split('.')[-1] for date, _, _ in data}, reverse=True)
    total_by_year = defaultdict(int)  # Итого по каждому году
    grand_total = 0  # Общий итог по всем продуктам и всем годам
    # with open(f'{subdomain}.csv', 'w', newline='', encoding='windows-1251') as f:
    with open(f'{subdomain}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        # writer.writerow(['Название продукта', 'url', 'unique_years','Итого'])
        writer.writerow(['Название продукта', 'url'] + unique_years + ['Итого'])
        for row in data:
            date, url, product_name = row
            years = date
            stats_by_year_and_product[product_name][years] += 1
            product_urls[product_name] = url  # сохраняем URL продукта
        for product_name, stats in stats_by_year_and_product.items():
            row = [product_name, product_urls.get(product_name, 'No URL')]  # извлекаем URL из словаря product_urls
            total_for_product = 0  # сумма отзывов для данного продукта по всем годам
            for year in unique_years:
                count_for_year = stats.get(year, 0)
                row.append(count_for_year)
                total_for_product += count_for_year
                total_by_year[year] += count_for_year  # обновляем итоговую сумму по каждому году
            row.append(total_for_product)  # добавляем колонку "Итого" в каждую строку
            grand_total += total_for_product  # суммируем все отзывы для общего итога
            writer.writerow(row)
        writer.writerow(['', ''] + [total_by_year[year] for year in unique_years] + [grand_total])
    """На финале раскомментировать"""
    if os.path.exists(new_folder_path):
        shutil.rmtree(new_folder_path)
    print("Все удачно выполнено")


def asyncio_run():
    cookies = {
        'cid': '149905558730700005005275127777618119701',
        'evoauth': 'wb52a1c0a48654244bc20f4f10d96b6b9',
        '_ga': 'GA1.1.834139681.1693817061',
        '_gcl_au': '1.1.788596630.1693817061',
        '_ga_T7S2G9Q21Q': 'GS1.1.1693817060.1.0.1693817062.0.0.0',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'max-age=0',
        # 'cookie': 'cid=149905558730700005005275127777618119701; csrf_token_company_site=6d036671fbdd4a97a70b683eae812906; evoauth=wb52a1c0a48654244bc20f4f10d96b6b9; _ga=GA1.1.834139681.1693817061; _gcl_au=1.1.788596630.1693817061; _ga_T7S2G9Q21Q=GS1.1.1693817060.1.0.1693817062.0.0.0',
        'dnt': '1',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])
    import csv
    import os
    import random
    import aiohttp
    import asyncio
    global coun
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
        proxy_url = None

        if use_proxy:
            proxies = load_proxies(file_path)
            if proxies:
                proxy = get_random_proxy(proxies)
                if proxy:
                    login_password, ip_port = proxy.split('@')
                    login, password = login_password.split(':')
                    ip, port = ip_port.split(':')
                    proxy_url = f'http://{login}:{password}@{ip}:{port}'
                    # proxy_dict = {'http': proxy_url}
                    # proxy_dict = {'http': proxy_url, 'https': proxy_url}
        if proxy_url:
            async with session.get(url, headers=headers, proxy=proxy_url) as response:
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
                    await asyncio.sleep(30)  # Пауза на 10 секунд после каждых 100 URL
    asyncio.run(main())



if __name__ == '__main__':
    print("Вставьте ссылку на сайт!")
    site = input()
    get_requests(site)
    asyncio_run()
    pars(site)
    analis_product(site)
