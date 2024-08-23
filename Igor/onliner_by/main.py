from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers.phonenumberutil import NumberParseException
import phonenumbers
import requests
from pathlib import Path
from configuration.logger_setup import logger
import csv
import xml.etree.ElementTree as ET
from selectolax.parser import HTMLParser
import re
import random
import locale
import csv
import pandas as pd
import datetime
import threading
import requests
import gzip
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from itertools import cycle


# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
html_directory = temp_path / "html"
data_directory = current_directory / "data"

html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
# Создаем глобальную блокировку
write_lock = threading.Lock()

cookies = {
    "stid": "9ddfc9584e848b034a08d6194dc885a1297a2dc80e523a4a1577b1cda945effb",
    "ouid": "snyBDmbDM0tWegvsAyl/Ag==",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}
# Параметры подключения к базе данных
config = {"user": "", "password": "", "host": "", "database": ""}
"""Читает и форматирует прокси-серверы из файла."""
belarus_phone_patterns = {
    "full": r"\b(80\d{9}|375\d{9}|\d{9})\b",
    "split": r"(375\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [375],
}


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def download_and_extract_gz():
    url = "https://ab.onliner.by/sitemap/cars-1.xml.gz"
    output_gz_file = Path("data/cars-1.xml.gz")
    output_xml_file = Path("data/cars-1.xml")
    output_csv_file = Path("data/output.csv")
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    while True:
        try:

            response = requests.get(
                url,
                stream=True,
                proxies=proxies_dict,
            )
            if response.status_code == 200:
                with open(output_gz_file, "wb") as f:
                    f.write(response.content)
                break  # Успешно скачали файл, выходим из цикла
            else:
                logger.error(
                    f"Не удалось скачать файл через {proxy}, статус код: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при использовании прокси {proxy}: {e}")
            if not proxies_dict:
                raise  # Если нет прокси, выходим с ошибкой

    with gzip.open(output_gz_file, "rb") as f_in:
        with open(output_xml_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    links = parse_xml_for_links(output_xml_file)
    save_links_to_csv(links, output_csv_file)


def parse_xml_for_links(output_xml_file):
    tree = ET.parse(output_xml_file)
    root = tree.getroot()

    # Определение пространства имен
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Поиск всех URL с учетом пространства имен
    links = [
        url.find("ns:loc", namespaces).text
        for url in root.findall("ns:url", namespaces)
    ]

    logger.info(links)

    return links


def save_links_to_csv(links, output_csv_file):
    output_csv_file.parent.mkdir(
        parents=True, exist_ok=True
    )  # Создаем директории, если их нет
    with open(output_csv_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["URL"])  # Заголовок CSV файла
        for link in links:
            writer.writerow([link])


"""
___________________________________________________________________________________________

"""


def write_to_csv(file_path, data):
    """Записывает данные в CSV-файл."""
    with open(file_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


def fetch_url(
    url, proxies, headers, cookies, csv_file_successful, successful_urls, url_id
):
    """Выполняет HTTP-запрос для заданного URL, используя прокси, и парсит ответ."""
    if url in successful_urls:
        # logger.info(f"URL {url} already successfully downloaded, skipping.")
        return

    for proxy in proxies:
        if not proxy:  # Пропускаем пустые прокси
            continue
        try:
            response = requests.get(
                url,
                proxies={"http": proxy, "https": proxy},
                headers=headers,
                cookies=cookies,
            )
            response.raise_for_status()

            src = response.text

            if response.status_code == 200:
                # Если статус ответа 200, записываем URL в CSV успешных загрузок
                write_to_csv(csv_file_successful, [url])
                # Парсим HTML и извлекаем данные
                parsing(url_id, src, url, proxy, headers, cookies)
                successful_urls.add(url)
                return
            else:
                logger.error(f"Unexpected status code {response.status_code} for {url}")

        except Exception as e:
            logger.error(f"Failed to fetch {url} with proxy {proxy}: {e}")
            continue  # Переходим к следующему прокси

    logger.error(f"Failed to fetch {url} with all proxies.")


def get_html(max_workers=10):
    """Основная функция для обработки списка URL с использованием многопоточности."""
    proxies = load_proxies_curl_cffi()  # Загружаем список всех прокси
    csv_file_path = Path("data/output.csv")
    csv_file_successful = Path("data/urls_successful.csv")

    # Получение списка уже успешных URL
    successful_urls = get_successful_urls(csv_file_successful)

    urls_df = pd.read_csv(csv_file_path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                fetch_url,
                url,
                proxies,  # Передаем весь список прокси
                headers,
                cookies,
                csv_file_successful,
                successful_urls,
                url.split("/")[-1],
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")


def parsing(url_id, src, url, proxy, headers, cookies):
    csv_file_path = "result.csv"
    """Синхронная функция для парсинга HTML-контента и извлечения данных."""
    try:
        # Создаем объект HTMLParser для парсинга HTML-контента
        parser = HTMLParser(src)
        time_posted = datetime.datetime.now().strftime("%Y-%m-%d")
        mail_address = None

        # Получаем номер телефона и имя пользователя с помощью синхронной функции get_number
        user_name, phones = get_number(url_id, proxy, headers, cookies)
        phone_numbers_extracted = extract_phone_numbers(phones)
        location = extract_user_info(parser)

        # Извлекаем дату публикации с использованием соответствующей функции
        publication_date = extract_publication_date(parser)

        # Формируем строку данных для записи в CSV
        data = [
            phone_numbers_extracted,
            location,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            url,
            mail_address,
            time_posted,
        ]

        # Записываем данные в CSV с использованием блокировки
        with write_lock:
            write_result_to_csv(csv_file_path, data)

    except Exception as e:
        logger.error(f"Failed to parse HTML for {url_id}: {e}")


def write_result_to_csv(csv_file_path, data):
    """Функция для записи данных в CSV-файл."""
    with open(csv_file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(
            file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        # Записываем строку данных
        writer.writerow(data)


"""Проверяет валидность номера телефона и форматирует его."""


def extract_phone_numbers(phone_numbers: list) -> str:
    """Проверяет валидность каждого номера телефона в списке и форматирует их."""

    # Шаблоны регулярных выражений для поиска и извлечения номеров телефонов
    patterns = [
        re.compile(r"\+375(\d{9})"),  # Формат: +375299422341
        re.compile(r"\d{3}\s\d{3}\s\d{3}"),  # Формат: 123 456 789
        re.compile(r"\(\d{3}\)\s\d{3}\-\d{3}"),  # Формат: (123) 456-789
        re.compile(r"\b\d[\d\s\(\)\-]{6,}\b"),  # Общий формат с минимальной длиной
        re.compile(r"\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"),  # Формат: 123-456-789
        re.compile(r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b"),  # Формат: 12 345 67 89
        re.compile(
            r"\+\d{2}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3}\b"
        ),  # Формат: +12 345 678 789
    ]

    unique_numbers = set()  # Используем множество для хранения уникальных номеров

    # Проходим по каждому номеру в списке phone_numbers
    for phone_number in phone_numbers:
        for pattern in patterns:
            match = pattern.match(phone_number)
            if match:
                # Очищаем найденный номер и добавляем его в множество уникальных номеров
                number = re.sub(
                    r"[^\d]", "", phone_number
                )  # Удаление всех символов, кроме цифр
                number = re.sub(r"^0+", "", number)  # Удаление ведущих нулей
                number = re.sub(r"^375", "", number)  # Удаление префикса "375"
                unique_numbers.add(number)  # Добавляем номер в множество
                break  # Если номер подошел под один паттерн, прекращаем дальнейшие проверки

    if unique_numbers:
        # Возвращаем строку, содержащую все уникальные номера, разделенные запятыми
        clean_numbers = ", ".join(
            sorted(unique_numbers)
        )  # Сортируем для удобства чтения
        logger.info(clean_numbers)
        return clean_numbers

    return "Телефоны не найдены"


# def extract_phone_numbers(data: str) -> str:
#     phone_numbers = set()
#     invalid_numbers = []
#     phone_pattern = re.compile(
#         r"\d{3}\s\d{3}\s\d{3}|\(\d{3}\)\s\d{3}\-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"
#     )
#     for entry in data:
#         if isinstance(entry, str):
#             matches = phone_pattern.findall(entry)
#             for match in matches:
#                 original_match = match
#                 match = re.sub(r"[^\d]", "", match)
#                 match = re.sub(r"^0+", "", match)
#                 try:
#                     parsed_number = phonenumbers.parse(match, "BY")
#                     if phonenumbers.is_valid_number(parsed_number):
#                         national_number = phonenumbers.format_number(
#                             parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
#                         )
#                         clean_number = "".join(filter(str.isdigit, national_number))
#                         phone_numbers.add(clean_number)
#                     else:
#                         invalid_numbers.append(original_match)
#                 except NumberParseException:
#                     invalid_numbers.append(original_match)
#     logger.info(phone_numbers)
#     return phone_numbers, invalid_numbers


# Извлечение местоположения
def extract_user_info(parser: HTMLParser) -> dict:

    location = None
    # Извлечение местоположения
    location_row = parser.css_first(
        "div > div > div.detail-content-cover.detail-content-cover--border > div.card-wrapper.card-wrapper__white.cover-desktop-aside > div.vin"
    )

    if location_row:
        location = location_row.text(strip=True).replace("VIN", "")

    return location


# Извлечение даты публикации
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


"""Выполняет HTTP-запрос для получения номера телефона и имени пользователя."""


def get_number(url_id, proxy, headers, cookies):

    url = f"https://b.abw.by/api/v2/adverts/{url_id}/phones"

    # Настраиваем прокси для запроса, если он указан
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        # Выполняем HTTP-запрос с использованием requests
        response = requests.get(url, proxies=proxies, headers=headers, cookies=cookies)
        response.raise_for_status()  # Проверяем успешность запроса
        # Извлекаем JSON из ответа
        json_data = response.json()
        # Извлекаем необходимые данные
        user_name = json_data.get("title")
        phones = json_data.get("phones", [])
        # number = phones[0] if phones else None
        logger.info(phones)
        return user_name, phones

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch number for {url_id} with proxy {proxy}: {e}")
        return None, None


if __name__ == "__main__":
    # download_and_extract_gz()  # Запускаем основную функцию при выполнении скрипта напрямую
    # get_html(max_workers=10)  # Устанавливаем количество потоков
