import asyncio
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
html_files_directory = current_directory / "html_files"
html_page_directory = current_directory / "html_page"


configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)


output_csv_file = data_directory / "output.csv"
config_txt_file = configuration_directory / "config.txt"


def get_cookies():
    """Извлекает заголовки и cookies из файла конфигурации.

    Функция читает конфигурационный файл, содержащий строку cURL, и извлекает из неё
    значения заголовков и cookies для последующего использования в HTTP-запросах.

    Returns:
        tuple: Кортеж, содержащий два словаря - headers и cookies, которые могут
        быть переданы в запросы для авторизации и других настроек.
    """
    with open(config_txt_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def read_cities_from_csv(input_csv_file: str) -> List[str]:
    """Читает список URL из столбца 'url' CSV-файла.

    Args:
        input_csv_file (str): Путь к входному CSV-файлу.

    Returns:
        List[str]: Список URL-адресов из столбца 'url'.

    Raises:
        ValueError: Если файл не содержит столбца 'url'.
        FileNotFoundError: Если файл не найден.
        pd.errors.EmptyDataError: Если файл пустой.
    """
    try:
        df = pd.read_csv(input_csv_file)

        if "url" not in df.columns:
            raise ValueError("Входной файл не содержит столбца 'url'.")

        urls = df["url"].dropna().tolist()  # Удаляем пустые значения, если они есть
        return urls

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Файл {input_csv_file} не найден.") from e
    except pd.errors.EmptyDataError as e:
        raise pd.errors.EmptyDataError(f"Файл {input_csv_file} пустой.") from e


def get_all_pages(soup):
    pagination = soup.find("div", {"class": "paging-container pull-right"}).find(
        "ul", {"class": "pagination pagination-sm"}
    )
    last_page = None
    if pagination:
        last_page_link = pagination.find_all("li")[-1].find("a")
        if last_page_link and last_page_link.has_attr("href"):
            last_page_href = last_page_link["href"]
            last_page = last_page_href.rsplit("/", maxsplit=1)[-1]
    return last_page


def scrape_category(category_url):
    headers, cookies = get_cookies()

    category_name = category_url.rsplit("/", maxsplit=1)[-1]
    response = requests.get(
        category_url,
        cookies=cookies,
        headers=headers,
        timeout=60,
    )
    if response.status_code != 200:
        logger.error(f"Failed to retrieve data from {category_url}")
    soup = BeautifulSoup(response.text, "lxml")
    last_page = int(get_all_pages(soup))
    for page in range(0, last_page + 1):
        page_html_file = html_page_directory / f"{category_name}_0{page}.html"
        if page_html_file.exists():
            continue
        url = f"{category_url}_/{page}"
        save_page(url, headers, cookies, page_html_file)


def save_page(url, headers, cookies, page_html_file):
    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        timeout=60,
    )
    src = response.text
    with open(page_html_file, "w", encoding="utf-8") as file:
        file.write(src)


# def main():
#     categories = read_cities_from_csv(output_csv_file)

#     for category_url in categories[:2]:
#         scrape_category(category_url)


def parsing_product():
    # file_path = Path("page.html")

    # import requests

    # cookies = {
    #     "session": "89p3h63buiiodnim295gapsi45",
    #     "route": "1732107681.185.132827.203180|4ea7291f9f635e972563a972b641033c",
    # }

    # headers = {
    #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "accept-language": "ru,en;q=0.9,uk;q=0.8",
    #     "cache-control": "no-cache",
    #     # 'cookie': 'session=89p3h63buiiodnim295gapsi45; route=1732107681.185.132827.203180|4ea7291f9f635e972563a972b641033c',
    #     "dnt": "1",
    #     "pragma": "no-cache",
    #     "priority": "u=0, i",
    #     "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-platform": '"Windows"',
    #     "sec-fetch-dest": "document",
    #     "sec-fetch-mode": "navigate",
    #     "sec-fetch-site": "cross-site",
    #     "sec-fetch-user": "?1",
    #     "upgrade-insecure-requests": "1",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # }

    # response = requests.get(
    #     "https://as-pl.com/ru/p/A0001", cookies=cookies, headers=headers
    # )
    # if response.status_code == 200 and "text/html" in response.headers.get(
    #     "Content-Type", ""
    # ):
    #     file_path.write_text(response.text, encoding="utf-8")
    file_path = Path("A0001.html")

    # Чтение HTML и парсинг
    html_content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "lxml")
    product_name = soup.find("h1", {"class": "product-name"}).text.strip()
    pull_left_categories = soup.find(
        "div", {"class": "pull-left categories"}
    ).text.strip()
    photos_raw = soup.find(
        "div", {"class": "col-md-3 col-sm-6 col-xs-12 images"}
    ).find_all("a")
    # Генератор списка

    urls = [url.get("href") for url in photos_raw if url.get("href")]
    manufacturer = soup.find("strong", {"itemprop": "manufacturer"}).text.strip()
    table_table_bordered_table_properties = soup.find(
        "table", {"class": "table table-bordered table-properties"}
    )
    # Извлекаем строки
    rows = table_table_bordered_table_properties.find_all("tr")

    # Словарь для хранения данных
    table_data = {}

    # Проходим по строкам таблицы
    for row in rows:
        cells = row.find_all("td")
        if len(cells) == 2:  # Убедимся, что строка содержит 2 ячейки
            key = cells[0].text.strip()  # Текст из первой ячейки
            value = cells[1].text.strip()  # Текст из второй ячейки
            table_data[key] = value
        # Ищем все элементы с классом "_referenceRow_1s9a0_47"
    # reference_rows = soup.find_all("div", class_="_referenceRow_1s9a0_47")
    reference_rows = soup.find_all("div", {"class": "_referenceRow_1s9a0_47"})

    # Создаем словарь для хранения результатов
    references_dict = {}

    # Проходим по каждому элементу и извлекаем данные
    for row in reference_rows:

        code = row.find(
            "div", class_="_code_1s9a0_56"
        ).text.strip()  # Код (например, A0001)
        producer = row.find(
            "div", class_="_producer_1s9a0_56"
        ).text.strip()  # Производитель (например, AS-PL)
        references_dict[code] = producer
    logger.info(table_data)


# # Функция для получения контента сайта и сохранения в HTML и TXT
# async def main():
#     url = "https://as-pl.com/ru/p/A0001"
#     website_name = url.rsplit("/", maxsplit=1)[-1]
#     logger.info(website_name)
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         page = await browser.new_page()
#         try:
#             page.goto(
#                 url, timeout=10000, wait_until="networkidle"
#             )  # Устанавливаем таймаут на 10 секунд
#             time.sleep(2)
#             # Проверяем, если загрузился тег body, переходим дальше
#             if page.locator("body").is_visible():
#                 pass

#             # Получаем HTML контент страницы
#             html_content = page.content()

#             # Сохраняем HTML в файл
#             website_name = url.rsplit("/", maxsplit=1)[-1]

#             html_filename = f"{website_name}.html"
#             with open(file_path, "w", encoding="utf-8") as html_file:
#                 html_file.write(html_content)

#             browser.close()
#         except Exception as e:
#             print(f"Ошибка при обработке сайта {url}: {e}")
#             browser.close()


async def extract_data_hrefs_and_texts(page):
    data_hrefs = {}
    usage_elements = await page.query_selector_all(".usage-el")
    for element in usage_elements:
        data_href = await element.get_attribute("data-href")
        data_href = f"https://as-pl.com{data_href}"

        text = (await element.inner_text()).strip()
        data_hrefs[text] = data_href
    return data_hrefs


# Асинхронная функция для сохранения HTML контента в файл
async def save_html_to_file(page, filename):
    content = await page.content()
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)


# Асинхронный запуск Playwright
async def main():
    url = "https://as-pl.com/ru/p/A0001"
    website_name = url.rsplit("/", maxsplit=1)[-1]
    html_product_directory = html_files_directory / website_name
    html_product_directory.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        output_html_file = html_product_directory / f"{website_name}.html"
        if output_html_file.exists():
            pass
        await page.goto(url, timeout=10000, wait_until="networkidle")

        await save_html_to_file(page, output_html_file)
        # Извлекаем данные
        data_hrefs_and_texts = await extract_data_hrefs_and_texts(page)
        # Переходим на каждую страницу и сохраняем контент в HTML файл
        for text, data_href in data_hrefs_and_texts.items():
            await page.goto(data_href)
            output_html_file = html_product_directory / f"{text}.html"

            await save_html_to_file(page, output_html_file)


if __name__ == "__main__":
    # main()
    # get_all_pages()
    parsing_product()
    # get_website_content()
    # asyncio.run(main())
