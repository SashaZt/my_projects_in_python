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


# Функция для выполнения запроса
async def fetch_url(url, proxy, headers, sem, count):
    async with sem:
        async with AsyncSession() as session:
            filename_html = os.path.join(html_path, f"0{count}.html")
            if not os.path.exists(filename_html):
                try:
                    response = await session.get(url, proxy=proxy, headers=headers)
                    response.raise_for_status()
                    src = response.text
                    with open(filename_html, "w", encoding="utf-8") as f:
                        f.write(src)
                except Exception as e:
                    print(f"Failed to fetch {url} with proxy {proxy}: {e}")
                await asyncio.sleep(1)


# Основная функция для распределения URL по прокси и запуска задач
async def get_html():

    tasks = []
    proxies = load_proxies_curl_cffi()
    proxy_count = len(proxies)
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "max-age=0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    # Устанавливаем ограничение на количество одновременно выполняемых задач
    sem = asyncio.Semaphore(10)  # Ограничение на 100 одновременно выполняемых задач
    csv_file_path = "urls.csv"
    # Чтение CSV файла
    urls_df = pd.read_csv(csv_file_path)
    for count, url in enumerate(urls_df["url"], start=1):
        proxy = proxies[count % proxy_count]
        tasks.append(fetch_url(url, proxy, headers, sem, count))

    await asyncio.gather(*tasks)


async def parsing_page():
    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()

        parser = HTMLParser(src)
        # Пытаемся найти элемент по первому пути
        title_element = parser.css_first('h1[itemprop="name"]')
        title = title_element.text(strip=True) if title_element else None
        price = None
        # Если элемент не найден, пробуем второй путь
        price_element = parser.css_first("span.b-prod-price__new-col2 span")
        price = (
            price_element.attributes.get("data-num-animate") if price_element else None
        )

        data = {
            "title": title,
            "price": price,
        }
        all_datas.append(data)
    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Запись DataFrame в Excel
    output_file = "output.xlsx"
    df.to_excel(output_file, index=False)


if __name__ == "__main__":
    asyncio.run(get_html())
    asyncio.run(parsing_page())
