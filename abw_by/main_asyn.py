from phonenumbers.phonenumberutil import NumberParseException
import phonenumbers
from selectolax.parser import HTMLParser
import asyncio
import xml.etree.ElementTree as ET
import csv
import random
from curl_cffi.requests import AsyncSession
from pathlib import Path
from configuration.logger_setup import logger
import pandas as pd
import aiofiles
import glob
import json
import re
import locale
import datetime
from dateutil import parser as date_parser


# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
html_directory = temp_path / "html"
data_directory = current_directory / "data"

html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
cookies = {
    "_uid": "172406750548113",
    "cookiePolicy": "%7B%22accepted%22%3Atrue%2C%22technical%22%3Atrue%2C%22statistics%22%3A%22true%22%2C%22marketing%22%3A%22true%22%2C%22expire%22%3A1755603507%7D",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': '_uid=172406750548113; cookiePolicy=%7B%22accepted%22%3Atrue%2C%22technical%22%3Atrue%2C%22statistics%22%3A%22true%22%2C%22marketing%22%3A%22true%22%2C%22expire%22%3A1755603507%7D',
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


async def fetch_and_parse_xml(session, url):
    logger.info(f"Fetching and parsing XML from {url}")
    response = await session.get(url)
    response.raise_for_status()
    logger.info(f"Successfully fetched XML from {url}")
    return ET.fromstring(response.content)


async def download_file(session, url, save_directory):
    file_name = Path(url).name
    save_path = save_directory / file_name

    logger.info(f"Downloading file from {url} to {save_path}")
    response = await session.get(url)
    response.raise_for_status()

    async with aiofiles.open(save_path, "wb") as file:
        await file.write(response.content)
    logger.info(f"Successfully downloaded {url} to {save_path}")

    return save_path


async def process_sitemap(session, url, save_directory):
    logger.info(f"Processing sitemap {url}")
    root = await fetch_and_parse_xml(session, url)

    sitemap_elements = root.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
    )

    downloaded_files = []

    if sitemap_elements:
        logger.info(f"Found {len(sitemap_elements)} sub-sitemaps in {url}")
        for sitemap_element in sitemap_elements:
            loc_element = sitemap_element.find(
                "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
            )
            if loc_element is not None:
                child_sitemap_url = loc_element.text
                logger.info(f"Processing child sitemap {child_sitemap_url}")
                downloaded_files.extend(
                    await process_sitemap(session, child_sitemap_url, save_directory)
                )
    else:
        download_path = await download_file(session, url, save_directory)
        downloaded_files.append(download_path)

    return downloaded_files


async def extract_urls_from_xml(file_path):
    logger.info(f"Extracting URLs from {file_path}")
    urls = []
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        content = await file.read()
        root = ET.fromstring(content)
        url_elements = root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"
        )
        for url_element in url_elements:
            loc_element = url_element.find(
                "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
            )
            if loc_element is not None:
                urls.append(loc_element.text)
    logger.info(f"Extracted {len(urls)} URLs from {file_path}")
    return urls


async def main():
    url = "https://static.abw.by/sitemap/adverts.xml"
    data_directory = Path("data_directory")
    data_directory.mkdir(parents=True, exist_ok=True)

    csv_file_path = Path("data/output.csv")
    chosen_proxy = None  # Если прокси не используется, можно оставить None

    async with AsyncSession(proxy=chosen_proxy) as session:
        logger.info(f"Starting sitemap processing for {url}")
        downloaded_files = await process_sitemap(session, url, data_directory)
        logger.info(f"Downloaded {len(downloaded_files)} files")

        all_urls = []
        for file_path in downloaded_files:
            urls = await extract_urls_from_xml(file_path)
            all_urls.extend(urls)

        logger.info(f"Writing {len(all_urls)} URLs to {csv_file_path}")
        with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["url"])
            for url in all_urls:
                writer.writerow([url])
        logger.info(f"Finished writing URLs to {csv_file_path}")


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


# Обновленный код для чтения и форматирования прокси-серверов
async def load_proxies_curl_cffi():
    proxy_file_path = Path("configuration/proxies_with_auth.txt")

    # Чтение файла с прокси-серверами
    with open(proxy_file_path, "r") as f:
        raw_proxies = f.readlines()

    formatted_proxies = []
    for proxy in raw_proxies:
        proxy = proxy.strip()  # Убираем лишние пробелы и символы новой строки
        if proxy:
            # Проверяем и добавляем схему (http:// или https://) к прокси
            if not proxy.startswith("http://") and not proxy.startswith("https://"):
                proxy = f"http://{proxy}"
            formatted_proxies.append(proxy)

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


# Асинхронная функция для записи в CSV-файл
async def write_to_csv(file_path, data):
    async with aiofiles.open(file_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        await writer.writerow(data)


# Функция для чтения уже успешных URL из CSV-файла
def get_successful_urls(csv_file_successful):
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


# Обновленный код в функции fetch_url для правильной работы с прокси
async def fetch_url(
    url,
    proxies,
    headers,
    cookies,
    sem,
    count,
    csv_file_successful,
    successful_urls,
    url_id,
):
    async with sem:
        if url in successful_urls:
            logger.info(f"URL {url} already successfully downloaded, skipping.")
            return

        for proxy in proxies:
            if not proxy:  # Пропускаем пустые прокси
                continue
            async with AsyncSession() as session:
                try:
                    response = await session.get(
                        url, proxy=proxy, headers=headers, cookies=cookies
                    )
                    response.raise_for_status()

                    src = await response.text()

                    if response.status_code == 200:
                        # Если статус ответа 200, записываем URL в CSV успешных загрузок
                        await write_to_csv(csv_file_successful, [url])
                        await parsing(url_id, src, url, proxy, headers, cookies)
                        successful_urls.add(url)
                        return
                    else:
                        logger.error(
                            f"Unexpected status code {response.status_code} for {url}"
                        )

                except Exception as e:
                    logger.error(f"Failed to fetch {url} with proxy {proxy}: {e}")
                    continue  # Переходим к следующему прокси

            await asyncio.sleep(10)

        logger.error(f"Failed to fetch {url} with all proxies.")


# Основная функция для распределения URL по прокси и запуска задач
async def get_html():
    tasks = []
    proxies = await load_proxies_curl_cffi()  # Загружаем список всех прокси
    sem = asyncio.Semaphore(10)  # Ограничение на 10 одновременно выполняемых задач
    csv_file_path = Path("data/output.csv")
    csv_file_successful = Path("data/urls_successful.csv")

    # Получение списка уже успешных URL
    successful_urls = get_successful_urls(csv_file_successful)

    urls_df = pd.read_csv(csv_file_path)
    for count, url in enumerate(urls_df["url"], start=1):
        url_id = url.split("/")[-1]
        tasks.append(
            fetch_url(
                url,
                proxies,  # Передаем весь список прокси
                headers,
                cookies,
                sem,
                count,
                csv_file_successful,
                successful_urls,
                url_id,
            )
        )

    await asyncio.gather(*tasks)


async def get_number(url_id, proxy, headers, cookies):
    url = f"https://b.abw.by/api/v2/adverts/{url_id}/phones"

    async with AsyncSession() as session:
        response = await session.get(url, proxy=proxy, headers=headers, cookies=cookies)
        response.raise_for_status()
        logger.info(response.raise_for_status())

        # Извлекаем JSON из ответа
        json_data = await response.json()

        # Извлекаем необходимые данные
        user_name = json_data.get("title")
        phones = json_data.get("phones", [])
        number = phones[0] if phones else None

        logger.info(f"User name: {user_name}")
        logger.info(f"Number: {number}")

        return user_name, number


async def parsing(url_id, src, url, proxy, headers, cookies):
    try:
        # Создаем объект HTMLParser
        parser = HTMLParser(src)

        # Получаем номер телефона и имя пользователя
        number, user_name = await get_number(url_id, proxy, headers, cookies)

        # Извлекаем данные с использованием соответствующих функций
        publication_date = extract_publication_date(parser)
        logger.info(f"Publication date for {url_id}: {publication_date}")
    except Exception as e:
        logger.error(f"Failed to parse HTML for {url_id}: {e}")


async def parsing_page():
    folder = Path(html_directory)
    files_html = list(folder.glob("*.html"))
    all_datas = []

    time_posted = datetime.datetime.now().strftime("%Y-%m-%d")
    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()

        # Создаем объект HTMLParser
        parser = HTMLParser(src)

        # Извлекаем данные с использованием соответствующих функций
        publication_date = extract_publication_date(parser)

        user_name, location = extract_user_info(parser)

        phone_number = extract_phone_number(parser)
        logger.info(phone_number)
        # logger.info(phone_number)
        link = extract_meta_url(parser)
        mail_address = None
        data_dict_ = {
            "date": publication_date,
            "user_name": user_name,
            "location": location,
            "phone_number": phone_number,
            "link": link,
            "mail_address": mail_address,
            "time_posted": time_posted,
        }

        data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{link};{mail_address};{time_posted}'
        all_datas.append(data)
    await write_to_result(all_datas)


async def write_to_result(all_datas, file_path="result.csv"):
    async with aiofiles.open(file_path, mode="w", encoding="utf-8", newline="") as f:
        for data in all_datas:
            line = data + "\n"  # Добавляем новую строку в конец каждой строки данных
            await f.write(line)


def extract_meta_url(parser: HTMLParser) -> str:
    """Извлекает URL из мета-тега в HTML."""
    meta_element = parser.css_first("head > meta:nth-child(25)")
    if meta_element:
        url = meta_element.attrs.get("content")
        if url:
            return url
    return "URL не найден"


"""Извлекает дату публикации """


def extract_publication_date(parser: HTMLParser) -> str:
    locale.setlocale(
        locale.LC_TIME, "ru_RU.UTF-8"
    )  # Устанавливаем локаль на русский язык

    date_element = parser.css_first(
        "#__nuxt > div > div.application > div > div > main > div.page-loader > div:nth-child(2) > div.container > div > div > section.ch-content > div > div.ch-content-header-actions > p"
    )

    if date_element:
        date_element_text = date_element.text(strip=True)

        # Ищем дату между "Создано" и "/"
        match = re.search(r"Создано\s+(.+?)\s+/", date_element_text)
        if match:
            date_str = match.group(1)

            # Месяцы на русском языке и их числовые эквиваленты
            months = {
                "Января": "01",
                "Февраля": "02",
                "Марта": "03",
                "Апреля": "04",
                "Мая": "05",
                "Июня": "06",
                "Июля": "07",
                "Августа": "08",
                "Сентября": "09",
                "Октября": "10",
                "Ноября": "11",
                "Декабря": "12",
            }

            # Разбиваем строку на компоненты
            day, month, year = date_str.split()
            month = months.get(month)

            if month:
                # Форматируем дату в нужный формат
                formatted_date = f"{year}-{month}-{int(day):02d}"
                return formatted_date
            else:
                return "Месяц не распознан"

    return "Дата не найдена"


"""Извлекает имя пользователя и местоположение """


def extract_user_info(parser: HTMLParser) -> dict:

    user_info = {
        "user_name": None,
        "local": None,
    }
    user_name = None
    local = None
    # Извлечение имени пользователя
    user_element = parser.css_first(
        "div.card-wrapper.card-wrapper__white.cover-desktop-aside > a.seller__link"
    )
    if user_element:
        user_name = user_element.text(strip=True)
    # Извлечение местоположения
    location_row = parser.css_first(
        "div > div > div.detail-content-cover.detail-content-cover--border > div.card-wrapper.card-wrapper__white.cover-desktop-aside > div.vin"
    )

    if location_row:
        local = location_row.text(strip=True)

    # logger.info(f"Извлеченная информация: {user_name, local}")
    return user_name, local


def extract_phone_number(parser: HTMLParser) -> str:
    """Извлекает номер телефона из JavaScript кода в HTML и проверяет его валидность."""
    script_elements = parser.css("script")

    # Шаблон регулярного выражения для поиска телефонных номеров
    phone_pattern = re.compile(
        r"\d{3}\s\d{3}\s\d{3}|"  # Формат: 123 456 789
        r"\(\d{3}\)\s\d{3}\-\d{3}|"  # Формат: (123) 456-789
        r"\b\d[\d\s\(\)\-]{6,}\b|"  # Общий формат с минимальной длиной
        r"\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"  # Формат: 123-456-789 (разделенные символами)
    )
    phone_number_pattern_1 = re.compile(r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b")
    phone_number_pattern_2 = re.compile(r"\+\d{2}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3}\b")

    phone_numbers = set()

    for script_element in script_elements:
        script_text = script_element.text()

        # Сначала проверяем наличие строки `this.phone`
        if "this.phone" in script_text:
            # Поиск всех возможных телефонных номеров по всем паттернам
            phone_numbers.update(phone_pattern.findall(script_text))
            phone_numbers.update(phone_number_pattern_1.findall(script_text))
            phone_numbers.update(phone_number_pattern_2.findall(script_text))

    if phone_numbers:
        # Если найдено несколько номеров, выбираем первый и очищаем его
        phone_number = next(iter(phone_numbers))
        phone_number = re.sub(
            r"[^\d]", "", phone_number
        )  # Удаление всех символов, кроме цифр
        phone_number = re.sub(r"^0+", "", phone_number)  # Удаление ведущих нулей
        phone_number = re.sub(r"^48", "", phone_number)  # Удаление префикса "48"
        return phone_number

    return "Телефон не найден"

    # # Если `this.phone` не найден, ищем числовые последовательности по основному паттерну
    # potential_numbers = phone_pattern.findall(script_text)
    # if potential_numbers:
    #     phone_number = potential_numbers[0]  # Берем первый найденный номер
    #     logger.info(f"Найденная числовая последовательность: {phone_number}")
    #     phone_number = re.sub(
    #         r"[^\d]", "", phone_number
    #     )  # Удаление всех символов, кроме цифр
    #     phone_number = re.sub(r"^0+", "", phone_number)  # Удаление ведущих нулей
    #     return phone_number

    # return "Телефон не найден"


# def validate_and_format_phone_number(phone_number: str) -> str:
#     """Проверяет валидность телефонного номера и возвращает его в международном формате с кодом страны PL."""
#     try:
#         # Если номер начинается с '48' или другого кода, мы предполагаем, что это международный формат
#         if not phone_number.startswith("48"):
#             phone_number = f"48{phone_number}"  # Добавляем код страны Польши

#         # Парсинг номера
#         parsed_number = phonenumbers.parse(phone_number, "PL")

#         # Проверка валидности номера
#         if phonenumbers.is_valid_number(parsed_number):
#             # Возвращаем номер в международном формате
#             return phonenumbers.format_number(
#                 parsed_number, phonenumbers.PhoneNumberFormat.E164
#             )
#         else:
#             return None
#     except NumberParseException:
#         return None


# def extract_phone_number(parser: HTMLParser) -> str:
#     """Извлекает номер телефона из JavaScript кода в HTML."""
#     script_elements = parser.css("script")
#     phone_number_pattern = re.compile(
#         r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b"
#     )  # Поиск числовых последовательностей в формате телефона
#     phone_number_pattern_1 = re.compile(r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b")
#     phone_number_pattern_2 = re.compile(r"\+\d{2}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3}\b")

#     for script_element in script_elements:
#         script_text = script_element.text()

#         # Сначала проверяем наличие строки `this.phone`
#         if "this.phone" in script_text:
#             # Поиск всех возможных телефонных номеров по всем паттернам
#             phone_numbers = []
#             phone_numbers += phone_number_pattern.findall(script_text)
#             phone_numbers += phone_number_pattern_1.findall(script_text)
#             phone_numbers += phone_number_pattern_2.findall(script_text)

#             logger.info(phone_numbers)

#             if phone_numbers:
#                 # Возвращаем первый найденный номер
#                 phone_number = phone_numbers[0]
#                 phone_number = phone_number.strip().replace(" ", "").replace("-", "")
#                 return phone_number.strip()

#         # Если `this.phone` не найден, ищем числовые последовательности
#         potential_numbers = phone_number_pattern.findall(script_text)
#         if potential_numbers:
#             phone_number = potential_numbers[0]  # Берем первый найденный номер
#             logger.info(f"Найденная числовая последовательность: {phone_number}")
#             return phone_number

#     return "Телефон не найден"


# def extract_phone_numbers(data):
#     phone_numbers = set()  # Для хранения уникальных корректных номеров
#     invalid_numbers = []  # Для хранения некорректных номеров

#     # Регулярное выражение для поиска различных форматов телефонных номеров
#     phone_pattern = re.compile(
#         r"\d{3}\s\d{3}\s\d{3}|"  # Формат: 123 456 789
#         r"\(\d{3}\)\s\d{3}\-\d{3}|"  # Формат: (123) 456-789
#         r"\b\d[\d\s\(\)\-]{6,}\b|"  # Общий формат с минимальной длиной
#         r"\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"  # Формат: 123-456-789 (разделенные символами)
#     )

#     for entry in data:
#         if isinstance(entry, str):
#             # Поиск всех совпадений с шаблоном
#             matches = phone_pattern.findall(entry)
#             for match in matches:
#                 original_match = match
#                 # Удаление всех символов, кроме цифр
#                 match = re.sub(r"[^\d]", "", match)
#                 # Удаление ведущих нулей
#                 match = re.sub(r"^0+", "", match)
#                 try:
#                     # Попытка парсинга номера с предположением, что он относится к Польше (код "PL")
#                     parsed_number = phonenumbers.parse(match, "PL")
#                     # Проверка валидности номера
#                     if phonenumbers.is_valid_number(parsed_number):
#                         # Преобразование номера в национальный формат
#                         national_number = phonenumbers.format_number(
#                             parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
#                         )
#                         # Удаление всех символов, кроме цифр, для чистого представления номера
#                         clean_number = "".join(filter(str.isdigit, national_number))
#                         phone_numbers.add(clean_number)
#                     else:
#                         invalid_numbers.append(original_match)
#                 except NumberParseException:
#                     # Добавление в список некорректных номеров при возникновении ошибки парсинга
#                     invalid_numbers.append(original_match)

#     return phone_numbers, invalid_numbers


if __name__ == "__main__":
    # Запуск асинхронной функции
    # from asyncio import WindowsSelectorEventLoopPolicy

    # # # Установим политику цикла событий для Windows
    # asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    # asyncio.run(main())

    asyncio.run(get_html())

    # asyncio.run(parsing_page())
