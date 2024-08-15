from selectolax.parser import HTMLParser
import asyncio
import xml.etree.ElementTree as ET
import csv
import random
from curl_cffi.requests import AsyncSession
from pathlib import Path
from configuration.logger_setup import logger
import pandas as pd
import glob
import json
import re

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
html_directory = temp_path / "html"
data_directory = current_directory / "data"

html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
cookies = {
    "PHPSESSID": "61d10f9937ace73e3c3970f2b80e4608",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'PHPSESSID=61d10f9937ace73e3c3970f2b80e4608',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://twojaoferta.com.pl/sitemap.xml",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}


# Функция для чтения прокси-серверов из файла
def load_proxies(filename):
    proxies = []
    try:
        with open(filename, "r") as file:
            for line in file:
                proxy = line.strip()
                if proxy:
                    proxies.append(proxy)
    except FileNotFoundError:
        logger.warning(f"Файл {filename} не найден. Продолжаем без него.")
    return proxies


# Загрузить прокси-серверы из файла
def load_proxies_curl_cffi():
    proxy_file_path = Path("configuration/proxies_with_auth.txt")

    # Чтение файла с прокси-серверами
    with open(proxy_file_path, "r") as f:
        raw_proxies = f.readlines()

    formatted_proxies = []
    for proxy in raw_proxies:
        proxy = proxy.strip()  # Убираем лишние пробелы и символы новой строки
        if proxy:
            formatted_proxies.append(f"http://{proxy}")

    return formatted_proxies


# Функция для выбора случайного прокси
def get_random_proxy():
    # Определение пути к файлу с прокси
    proxy_file_path = Path("configuration/proxies_with_auth.txt")

    # Загрузка прокси из файла
    proxies_with_auth = load_proxies(proxy_file_path)

    if not proxies_with_auth:
        return None  # Нет доступных прокси

    # Выбор случайного прокси
    return random.choice(proxies_with_auth)


async def download_and_parse_xml():
    url = "https://twojaoferta.com.pl/sitemap/sitemap_classified_0.xml"  # Здесь укажите вашу ссылку
    output_csv = Path("data/urls.csv")

    # Получаем случайный прокси
    chosen_proxy = get_random_proxy()

    # Создаем асинхронную сессию
    async with AsyncSession(proxy=chosen_proxy) as session:
        # Скачивание XML файла
        response = await session.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()  # проверка успешности запроса

        # Парсинг XML данных
        root = ET.fromstring(response.content)

        # Сбор всех URL из XML
        urls = []
        for url_element in root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"
        ):
            loc_element = url_element.find(
                "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
            )
            if loc_element is not None:
                urls.append(loc_element.text)

        # Запись URL в CSV файл с заголовком
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Записываем заголовок
            writer.writerow(["url"])
            # Записываем сами URL
            for url in urls:
                writer.writerow([url])


# Функция для выполнения запроса
async def fetch_url(url, proxy, headers, cookies, sem, count):
    async with sem:
        async with AsyncSession() as session:
            filename_html = Path(html_directory) / f"0{count}.html"

            if not filename_html.exists():
                try:
                    response = await session.get(
                        url, proxy=proxy, headers=headers, cookies=cookies
                    )
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
    # Устанавливаем ограничение на количество одновременно выполняемых задач
    sem = asyncio.Semaphore(10)  # Ограничение на 100 одновременно выполняемых задач
    csv_file_path = Path("data/urls.csv")
    # Чтение CSV файла
    urls_df = pd.read_csv(csv_file_path)
    for count, url in enumerate(urls_df["url"], start=1):
        proxy = proxies[count % proxy_count]
        tasks.append(fetch_url(url, proxy, headers, cookies, sem, count))

    await asyncio.gather(*tasks)


async def parsing_page():
    folder = Path(html_directory)
    files_html = list(folder.glob("*.html"))
    all_datas = []

    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()

        # Создаем объект HTMLParser
        parser = HTMLParser(src)

        # Извлекаем данные с использованием соответствующих функций
        publication_date = extract_publication_date(parser)
        user_name, local = extract_user_info(parser)
        phone_number = extract_phone_number(parser)
        # if phone_number == "Телефон не найден":
        logger.info(item_html)
        logger.info(phone_number)
        # Сохраняем все данные в список (или другой контейнер)
        data = {
            "date": publication_date,
            "user_name": user_name,
            "local": local,
            "phone_number": phone_number,
        }
        all_datas.append(data)
    logger.info(all_datas)
    return all_datas


"""Извлекает дату публикации """


def extract_publication_date(parser: HTMLParser) -> str:

    date_element = parser.css_first(
        "#classified__panel > p.small.text-muted > span:nth-child(1)"
    )
    if date_element:
        date_element_text = date_element.text(strip=True).replace("Opublikowano: ", "")

        return date_element_text
    return "Дата не найдена"


"""Извлекает имя пользователя и местоположение """


def extract_user_info(parser: HTMLParser) -> dict:

    user_info = {
        "user_name": None,
        "local": None,
    }

    # Поиск таблицы с информацией
    table_element = parser.css_first("table.table-borderless.table-sm")
    if table_element:
        # Извлечение имени пользователя
        user_element = table_element.css_first("a.color-primary")
        if user_element:
            user_name = user_element.text(strip=True)
        # Извлечение местоположения
        location_row = table_element.css_first("table.table-borderless.table-sm")

        if location_row:
            location_element = location_row.css_first(
                "tr:nth-child(2) > td:nth-child(2)"
            )

            if location_element:
                local = location_element.text(strip=True)

    # logger.info(f"Извлеченная информация: {user_name, local}")
    return user_name, local


def extract_phone_number(parser: HTMLParser) -> str:
    """Извлекает номер телефона из JavaScript кода в HTML."""
    script_elements = parser.css("script")
    phone_number_pattern = re.compile(
        r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b"
    )  # Поиск числовых последовательностей в формате телефона
    phone_number_pattern_1 = re.compile(r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b")
    phone_number_pattern_2 = re.compile(r"\+\d{2}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3}\b")

    for script_element in script_elements:
        script_text = script_element.text()

        # Сначала проверяем наличие строки `this.phone`
        if "this.phone" in script_text:
            # Поиск всех возможных телефонных номеров по всем паттернам
            phone_numbers = []
            phone_numbers += phone_number_pattern.findall(script_text)
            phone_numbers += phone_number_pattern_1.findall(script_text)
            phone_numbers += phone_number_pattern_2.findall(script_text)

            logger.info(phone_numbers)

            if phone_numbers:
                # Возвращаем первый найденный номер
                phone_number = phone_numbers[0]
                phone_number = phone_number.strip().replace(" ", "").replace("-", "")
                return phone_number.strip()

        # Если `this.phone` не найден, ищем числовые последовательности
        potential_numbers = phone_number_pattern.findall(script_text)
        if potential_numbers:
            phone_number = potential_numbers[0]  # Берем первый найденный номер
            logger.info(f"Найденная числовая последовательность: {phone_number}")
            return phone_number

    return "Телефон не найден"


if __name__ == "__main__":
    # # Запуск асинхронной функции
    # from asyncio import WindowsSelectorEventLoopPolicy

    # # Установим политику цикла событий для Windows
    # asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    # asyncio.run(download_and_parse_xml())

    # asyncio.run(get_html())

    asyncio.run(parsing_page())
