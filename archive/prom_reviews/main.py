from urllib.parse import urlparse
import pandas as pd
import csv
from configuration.logger_setup import logger
import asyncio
import random
import re
from datetime import datetime
import json
import html
import requests
from bs4 import BeautifulSoup
import os
import glob
from collections import defaultdict
import shutil
from pathlib import Path

# Установка директорий для логов и данных

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = data_directory / "html"
data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

url_csv = data_directory / "urls.csv"
products_csv = data_directory / "products.csv"

cookies = {
    "evoauth": "wbca764ed2b9a4d68a80cb9da2765a7b8",
    "cid": "295631840821182912240168823420841329403",
    "csrf_token_company_site": "f98a2d41b42a4514bb9c7cab96281812",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'evoauth=wbca764ed2b9a4d68a80cb9da2765a7b8; cid=295631840821182912240168823420841329403; csrf_token_company_site=f98a2d41b42a4514bb9c7cab96281812',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "proxy.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    # logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_requests(url):
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    url = f"{url}testimonials"
    try:
        response = requests.get(
            url, cookies=cookies, headers=headers, proxies=proxies_dict
        )
    except:
        response = requests.get(url, cookies=cookies, headers=headers)

    src = response.text
    soup = BeautifulSoup(src, "lxml")
    pagin_old = int(
        soup.find("div", attrs={"class": "b-pager"}).find(
            "div", {"data-pagination-pages-count": True}
        )["data-pagination-pages-count"]
    )
    with open(url_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for i in range(1, pagin_old + 1):
            page = f"{url}/page_{i}"
            writer.writerow([page])


def pars(site):
    files_html = list(html_directory.glob("*.html"))

    if os.path.exists(products_csv):
        # Если существует, удаляем
        os.remove(products_csv)
    # with open(file_csv, 'w', newline='', encoding='windows-1251') as csvfile:
    with open(products_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        for item_html in files_html:
            with open(item_html, encoding="utf-8") as file:
                # with open(item_html, encoding="windows-1251") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            url_site = site
            url_site = url_site.replace("/ua/", "")

            regex_comments = re.compile(".*-comments__item")
            comments = soup.find_all("li", attrs={"class": regex_comments})
            for c in comments:
                regex_data_comments = re.compile(".*date")
                data_comments = c.find(
                    "time", attrs={"class": regex_data_comments}
                ).get("datetime")
                dt_object = datetime.strptime(data_comments, "%Y-%m-%dT%H:%M:%S")
                formatted_date = dt_object.year
                regex_product_comments = re.compile(".*comments__answer")
                try:
                    product_comments = c.find(
                        "div", attrs={"class": regex_product_comments}
                    ).get("data-reviews-products")
                except:
                    product = []
                    product.append(formatted_date)  # Сначала дата
                    url_no_category = "Нет url"
                    name_no_category = "Без названия товара"
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
                        if item["url"]:
                            url = f"{url_site}{item['url']}"
                        else:
                            url = "Нет url"
                        product.append(formatted_date)
                        product.append(url)
                        names = item["name"]
                        product.append(names)
                        # product = [formatted_date,
                        #            url,  # Добавляем URL сюда
                        #            names.encode('windows-1251', 'ignore').decode('windows-1251'),
                        #            ]
                        writer.writerow(product)
                else:
                    product = []
                    product.append(formatted_date)  # Сначала дата
                    url_no_category = "Нет url"
                    name_no_category = "Без названия товара"
                    product.append(url_no_category)
                    product.append(name_no_category)
                    writer.writerow(product)


def analis_product(site):
    all_url = urlparse(site)
    # Извлекаем часть доменного имени с субдоменами
    domain_parts = all_url.netloc.split(".")
    subdomain = None
    if len(domain_parts) >= 2:
        subdomain = domain_parts[0]
    subdomain_excel = current_directory / f"{subdomain}.xlsx"  # Для сохранения в Excel
    data = []

    # Чтение данных из CSV
    with open(products_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            data.append(row)

    stats_by_year_and_product = defaultdict(lambda: defaultdict(int))
    product_urls = {}  # для хранения URL каждого продукта
    unique_years = sorted({date.split(".")[-1] for date, _, _ in data}, reverse=True)
    total_by_year = defaultdict(int)  # Итого по каждому году
    grand_total = 0  # Общий итог по всем продуктам и всем годам

    rows = []  # Здесь будут храниться все строки для DataFrame

    # Обработка данных
    for row in data:
        date, url, product_name = row
        years = date
        stats_by_year_and_product[product_name][years] += 1
        product_urls[product_name] = url  # сохраняем URL продукта

    # Формирование данных для записи в Excel
    for product_name, stats in stats_by_year_and_product.items():
        row = [
            product_name,
            product_urls.get(product_name, "No URL"),
        ]  # Извлекаем URL из словаря product_urls
        total_for_product = 0  # Сумма отзывов для данного продукта по всем годам
        for year in unique_years:
            count_for_year = stats.get(year, 0)
            row.append(count_for_year)
            total_for_product += count_for_year
            total_by_year[
                year
            ] += count_for_year  # обновляем итоговую сумму по каждому году
        row.append(total_for_product)  # Добавляем колонку "Итого"
        grand_total += total_for_product  # Суммируем все отзывы для общего итога
        rows.append(row)  # Добавляем строку в общий список

    # Добавляем строку с итогами по каждому году и общим итогом
    rows.append(
        ["", ""] + [total_by_year[year] for year in unique_years] + [grand_total]
    )

    # Создаем DataFrame и записываем его в Excel
    columns = ["Название продукта", "url"] + unique_years + ["Итого"]
    df = pd.DataFrame(rows, columns=columns)

    # Сохранение в Excel
    df.to_excel(subdomain_excel, index=False, engine="openpyxl")
    logger.info(f"Данные успешно записаны в {subdomain_excel}")
    """На финале раскомментировать"""
    if os.path.exists(data_directory):
        shutil.rmtree(data_directory)
    print("Все удачно выполнено")


def asyncio_run():
    headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    import csv
    import os
    import random
    import aiohttp
    import asyncio

    global coun
    coun = 0

    async def fetch(session, url, coun, proxies_dict):
        name_file = html_directory / f"data_{coun}.html"
        try:
            async with session.get(
                url, headers=headers, proxy=proxies_dict
            ) as response:
                if not os.path.exists(name_file):
                    with open(name_file, "w", encoding="utf-8") as file:
                        file.write(await response.text())
        except:
            async with session.get(url, headers=headers) as response:

                if not os.path.exists(name_file):
                    with open(name_file, "w", encoding="utf-8") as file:
                        file.write(await response.text())

    async def main():
        # Создаем путь к новой папке
        global coun
        proxies = load_proxies()  # Загружаем список всех прокси
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        async with aiohttp.ClientSession() as session:
            with open(url_csv, newline="", encoding="utf-8") as files:
                urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
                # Используйте срезы для создания пакетов по 100 URL
                for i in range(0, len(urls), 20):
                    tasks = []
                    for row in urls[i : i + 20]:
                        coun += 1
                        url = row[0]
                        tasks.append(fetch(session, url, coun, proxies_dict))
                    await asyncio.gather(*tasks)
                    logger.info(f"Выполнено {coun} запросов")
                    await asyncio.sleep(1)  # Пауза на 10 секунд после каждых 100 URL

    asyncio.run(main())


if __name__ == "__main__":
    print("Вставьте ссылку на сайт!")
    site = input()
    get_requests(site)
    asyncio_run()
    pars(site)
    analis_product(site)
