from curl_cffi.requests import AsyncSession
import glob
import json
import asyncio
import os
import pandas as pd
from selectolax.parser import HTMLParser

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
page_path = os.path.join(temp_path, "page")
html_path = os.path.join(temp_path, "html")


# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(page_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Загрузить прокси-серверы из файла
def load_proxies_curl_cffi():
    filename = "proxi.json"
    with open(filename, "r") as f:
        raw_proxies = json.load(f)

    formatted_proxies = []
    for proxy in raw_proxies:
        ip, port, username, password = proxy
        formatted_proxies.append(f"http://{username}:{password}@{ip}:{port}")

    return formatted_proxies


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


async def fetch_page(session, url):
    response = await session.get(url)
    response.raise_for_status()
    return response.text


async def extract_pagination(html):
    parser = HTMLParser(html)
    pagination = parser.css_first("div.row div.pagination")
    total_pages = 1
    if pagination:
        pag_items = pagination.css("div.pag-item")
        if len(pag_items) > 1:
            # Взять предпоследний элемент и получить его текст
            total_pages = int(pag_items[-2].text())
    return total_pages


async def extract_hrefs_from_page(html):
    parser = HTMLParser(html)
    slide_conts = parser.css("div.slide-cont")
    hrefs = []
    for slide_cont in slide_conts:
        first_a_tag = slide_cont.css_first("a")
        if first_a_tag:
            href = first_a_tag.attributes.get("href")
            if href:
                hrefs.append(href)
    return hrefs


async def get_url():
    url = "https://jabko.ua/brand/apple/mfp/312-pristr-y,iphone,ipad,macbook?sort=p.price&order=ASC"
    async with AsyncSession() as session:
        # Получаем первую страницу для извлечения пагинации
        first_page_html = await fetch_page(session, url)
        total_pages = await extract_pagination(first_page_html)
        print(f"Total pages: {total_pages}")

        all_hrefs = []

        # Проходим по всем страницам
        for page in range(1, total_pages + 1):
            page_url = f"{url}&page={page}"
            print(f"Fetching {page_url}")
            page_html = await fetch_page(session, page_url)
            hrefs = await extract_hrefs_from_page(page_html)
            all_hrefs.extend(hrefs)
            await asyncio.sleep(10)

        # Записываем все href в CSV файл
        df = pd.DataFrame(all_hrefs, columns=["href"])
        df.to_csv("hrefs.csv", index=False)
        print("All hrefs saved to hrefs.csv")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(get_url())
