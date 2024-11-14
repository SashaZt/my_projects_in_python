import asyncio
import json
import logging
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import aiohttp
import pandas as pd
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv
from tqdm import tqdm

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_page_directory = current_directory / "html_page"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)

csv_output_file = current_directory / "output.csv"
json_result = data_directory / "result.json"
xlsx_result = data_directory / "result.xlsx"


# Указать путь к .env файлу
env_path = os.path.join(os.getcwd(), "configuration", ".env")
API_KEY = os.getenv("API_KEY")


# Используем строку "20" как значение по умолчанию
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))


# Функция для чтения городов из CSV файла


def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def save_to_csv(href_set):
    # Создаем DataFrame из уникальных ссылок
    df = pd.DataFrame(href_set, columns=["url"])
    # Сохраняем DataFrame в CSV файл
    df.to_csv(csv_output_file, index=False, encoding="utf-8")
    logger.info(f"Данные успешно сохранены в {csv_output_file}")


def get_url():
    all_urls = read_cities_from_csv(csv_output_file)  # Чтение URL из CSV файла

    for url in all_urls:  # Ограничено одной URL для теста
        html_company = html_files_directory / f"{url.split('/')[-1]}.html"

        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            continue  # Переходим к следующей итерации цикла
        payload = {"api_key": API_KEY, "url": url}
        r = requests.get(
            "https://api.scraperapi.com/",
            params=payload,
            timeout=30,
        )
        if r.status_code == 200:
            with open(html_company, "w", encoding="utf-8") as file:
                file.write(r.text)
            logger.info(html_company)
        else:
            logger.info(r.status_code)


def get_all_page_html(url_start):

    html_company = html_page_directory / "url_start.html"
    payload = {"api_key": API_KEY, "url": url_start}

    # Проверяем, существует ли уже файл первой страницы
    if html_company.exists():
        logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
        max_page = parsin_page()  # Получаем max_page из существующего файла
    else:
        # Запрос к API для первой страницы
        r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)

        if r.status_code == 200:
            src = r.text
            with open(html_company, "w", encoding="utf-8") as file:
                file.write(src)
            max_page = (
                parsin_page()
            )  # Получаем max_page из только что сохраненного файла
            logger.info(f"Сохранена первая страница: {html_company}")
        else:
            logger.error(
                f"Ошибка при запросе первой страницы: {
                    r.status_code}"
            )
            return  # Если запрос не успешен, выходим из функции

    # Запрашиваем страницы с 2 по max_page, если max_page определен
    if max_page:
        for page in range(2, max_page + 1):
            html_company = html_page_directory / f"url_start_{page}.html"
            # Обновляем payload для каждой страницы
            payload = {"api_key": API_KEY, "url": f"{url_start}&p={page}"}

            if html_company.exists():
                logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            else:
                r = requests.get(
                    "https://api.scraperapi.com/", params=payload, timeout=60
                )

                if r.status_code == 200:
                    src = r.text
                    with open(html_company, "w", encoding="utf-8") as file:
                        file.write(src)
                    logger.info(f"Сохранена страница {page}: {html_company}")
                else:
                    logger.error(
                        f"Ошибка при запросе страницы {
                            page}: {r.status_code}"
                    )


def parsin_page():
    max_page = None
    html_company = html_page_directory / "url_start.html"

    # Открываем локально сохранённый файл первой страницы
    with open(html_company, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Находим div с атрибутом aria-label="paginacja"
    pagination_div = soup.find("div", {"aria-label": "paginacja"})

    # Извлекаем максимальное количество страниц
    if pagination_div:
        span_element = pagination_div.find("span")
        if span_element:
            try:
                max_page_text = span_element.get_text(strip=True)
                max_page = int(max_page_text)
            except ValueError:
                logger.error("Не удалось преобразовать max_page_text в число")
        else:
            logger.error(
                "Элемент span не найден или не является объектом BeautifulSoup"
            )
    else:
        logger.error("Элемент div с aria-label='paginacja' не найден")

    return max_page


def get_url_html_csv():
    # Инициализируем set для хранения уникальных ссылок
    unique_links = set()
    for html_file in html_page_directory.glob("*.html"):
        # Открываем локально сохранённый файл первой страницы
        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        # Находим контейнер для всех товаров
        search_results_div = soup.select_one(
            "#search-results > div:nth-child(5) > div > div > div > div > div > div"
        )

        # Проверяем каждый <article> элемент с учетом диапазона от 2 до 73
        if search_results_div:
            # Проверяем, что контейнер найден и содержит достаточное количество article
            articles = search_results_div.find_all("article")

            for ar in articles:
                # Ищем ссылку внутри целевого article
                link = ar.find("a", href=True)
                # Проверяем, что ссылка найдена, и добавляем в set
                if link:
                    unique_links.add(link["href"])
    logger.info(len(unique_links))
    # Преобразуем set в DataFrame и сохраняем в CSV
    df = pd.DataFrame(list(unique_links), columns=["url"])
    df.to_csv(csv_output_file, index=False, encoding="utf-8")

    logger.info(f"Ссылки успешно сохранены в {csv_output_file}")


# Асинхронная функция для загрузки HTML по URL и сохранения в файл
async def fetch_and_save_html(url, session):
    html_company = html_files_directory / f"{url.split('/')[-1]}.html"

    if html_company.exists():
        logger.warning(f"Файл {html_company} уже существует, пропускаем.")
        return

    payload = {"api_key": API_KEY, "url": url}

    try:
        async with session.get(
            "https://api.scraperapi.com/", params=payload, timeout=30
        ) as response:
            if response.status == 200:
                html_content = await response.text()
                with open(html_company, "w", encoding="utf-8") as file:
                    file.write(html_content)
                logger.info(f"Сохранен файл: {html_company}")
            else:
                logger.warning(f"Ошибка {response.status} при загрузке URL: {url}")
    except Exception as e:
        logger.error(f"Ошибка при запросе {url}: {e}")


# Асинхронная функция для запуска задач в очереди с ограниченным количеством потоков
async def process_urls(urls):
    queue = asyncio.Queue()

    # Добавляем URL в очередь
    for url in urls:
        await queue.put(url)

    async with ClientSession() as session:
        tasks = []
        # Запускаем указанное количество потоков
        for _ in range(MAX_WORKERS):
            task = asyncio.create_task(worker(queue, session))
            tasks.append(task)

        # Ожидаем выполнения всех задач
        await queue.join()

        # Завершаем все задачи
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


# Асинхронная функция для обработки задач из очереди
async def worker(queue, session):
    while True:
        url = await queue.get()
        await fetch_and_save_html(url, session)
        queue.task_done()


# Главная функция для запуска асинхронной загрузки
def get_url_async():
    urls = read_cities_from_csv(csv_output_file)
    asyncio.run(process_urls(urls))


def parse_ean_product(soup):
    """Извлекает EAN продукта."""
    ean_tag = soup.find("meta", itemprop="gtin")
    return ean_tag["content"] if ean_tag else None


def parse_brand_product(soup):
    """Извлекает бренд продукта."""
    brand_tag = soup.find("meta", itemprop="brand")
    return brand_tag["content"] if brand_tag else None


def parse_name_product(soup):
    """Извлекает название продукта."""
    name_tag = soup.find("meta", itemprop="name")
    return name_tag["content"] if name_tag else None


def parse_url_product(soup):
    """Извлекает URL продукта."""
    url_tag = soup.find("meta", itemprop="url")
    return url_tag["content"] if url_tag else None


def parse_price_product(soup):
    """Извлекает цену продукта."""
    price_tag = soup.find("meta", itemprop="price")
    return price_tag["content"] if price_tag else None


def parse_sales_product(soup):
    """Извлекает количество продаж продукта."""
    sales_tag = soup.find(string=lambda text: text and "tę ofertę" in text)
    if sales_tag:
        sales_text = sales_tag.strip()
        sales_number = "".join(filter(str.isdigit, sales_text))
        return int(sales_number) if sales_number else None
    return None


def parse_average_rating(soup):
    """Извлекает средний рейтинг продукта."""
    rating_tag = soup.find(
        "span", {"aria-label": lambda value: value and value.startswith("ocena:")}
    )
    if rating_tag:
        rating_text = rating_tag.text.strip()
        return rating_text
    return None


def parse_weight_product(soup):
    """Извлекает вес продукта."""
    weight_tag = soup.find("td", string=lambda text: text and "Waga produktu" in text)
    if weight_tag:
        weight_value_tag = weight_tag.find_next_sibling("td")
        if weight_value_tag:
            weight_text = weight_value_tag.text.strip()
            return weight_text
    return None


def parse_condition(soup):
    """Извлекает состояние продукта."""
    condition_tag = soup.find("meta", itemprop="itemCondition")
    return condition_tag["content"].split("/")[-1] if condition_tag else None


def parse_warehouse_balances(soup):
    """Извлекает количество товара на складе."""
    script_tags = soup.find_all("script", type="application/json")
    for script_tag in script_tags:
        try:
            data = json.loads(script_tag.string)
            if isinstance(data, dict):
                # Проверка в структуре данных на наличие количества товара
                if (
                    "watchButtonProps" in data
                    and "watchEventCustomParams" in data["watchButtonProps"]
                ):
                    item_data = data["watchButtonProps"]["watchEventCustomParams"].get(
                        "item", {}
                    )
                    if "quantity" in item_data:
                        return item_data["quantity"]
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return None


def parse_single_html(file_html):
    """Парсит один HTML-файл для извлечения данных о продукте.

    Args:
        file_html (Path): Путь к HTML-файлу.

    Returns:
        dict or None: Словарь с данными о продукте или None, если данные не найдены.
    """
    with open(file_html, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    company_data = {
        "EAN_product": parse_ean_product(soup),
        "brand_product": parse_brand_product(soup),
        "name_product": parse_name_product(soup),
        "url_product": parse_url_product(soup),
        "price_product": parse_price_product(soup),
        "sales_product": parse_sales_product(soup),
        "weight_product": parse_weight_product(soup),
        "condition": parse_condition(soup),
        "warehouse_balances": parse_warehouse_balances(soup),
        "average_rating": parse_average_rating(soup),
    }

    return company_data


def parsing_html():
    """Выполняет многопоточный парсинг всех HTML-файлов в директории.

    Returns:
        list: Список словарей с данными о продуктах из всех файлов.
    """

    all_files = list_html()
    # Инициализация прогресс-бараedrpou.csv
    total_urls = len(all_files)
    progress_bar = tqdm(
        total=total_urls,
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )

    # Многопоточная обработка файлов
    all_results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(parse_single_html, file_html): file_html
            for file_html in all_files
        }

        # Сбор результатов по мере завершения каждого потока
        for future in as_completed(futures):
            file_html = futures[future]
            try:
                result = future.result()
                if result is not None:
                    all_results.append(result)
            except Exception as e:
                logger.error(
                    f"Ошибка при обработке файла {
                    file_html}: {e}"
                )
                # Добавление трассировки стека
                logger.error(traceback.format_exc())
            finally:
                # Обновляем прогресс-бар после завершения обработки каждого файла
                progress_bar.update(1)

    # Закрываем прогресс-бар
    progress_bar.close()
    return all_results


def list_html():
    """Возвращает список HTML-файлов в заданной директории.

    Returns:
        list: Список файлов (Path) в директории html_files_directory.
    """

    # Получаем список всех файлов в html_files_directory
    file_list = [file for file in html_files_directory.iterdir() if file.is_file()]

    logger.info(f"Всего файлов для обработки: {len(file_list)}")
    return file_list


def save_results_to_json(all_results):
    """Сохраняет результаты парсинга в JSON-файл.

    Args:
        all_results (list): Список словарей с данными о продуктах.
    """
    # Сохранить результаты в JSON файл
    try:
        with open(json_result, "w", encoding="utf-8") as json_file:
            json.dump(all_results, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Данные успешно сохранены в файл {json_result}")
    except Exception as e:
        logger.error(
            f"Ошибка при сохранении данных в файл {
            json_result}: {e}"
        )
        raise


def save_json_to_excel(json_file_path, excel_file_path):
    """Сохраняет данные из JSON-файла в Excel-файл с помощью pandas.

    Args:
        json_file_path (str or Path): Путь к JSON-файлу с данными.
        excel_file_path (str or Path): Путь к создаваемому Excel-файлу.
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        df = pd.DataFrame(data)
        df.to_excel(excel_file_path, index=False)
        logger.info(f"Данные успешно сохранены в Excel файл {excel_file_path}")
    except Exception as e:
        logger.error(
            f"Ошибка при сохранении данных в Excel файл {
                     excel_file_path}: {e}"
        )
        raise


if __name__ == "__main__":
    url_start = "https://allegro.pl/kategoria/narzedzia-mlotowiertarki-147650?price_from=200&price_to=800&stan=nowe"
    get_all_page_html(url_start)
    parsin_page()
    get_url_html_csv()
    # get_url()
    get_url_async()
    all_results = parsing_html()
    save_results_to_json(all_results)
    save_json_to_excel(json_result, xlsx_result)
