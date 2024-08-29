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
import locale
import csv
import pandas as pd
import datetime
import threading


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

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies_curl_cffi():
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


def main():
    url = "https://static.abw.by/sitemap/adverts.xml"  # URL карты сайта
    data_directory = Path(
        "data_directory"
    )  # Директория для сохранения загруженных файлов
    data_directory.mkdir(
        parents=True, exist_ok=True
    )  # Создаем директорию, если она не существует

    csv_file_path = Path("data/output.csv")  # Путь для сохранения списка URL в CSV
    chosen_proxy = None  # Если требуется прокси, можно его указать здесь

    session = (
        requests.Session()
    )  # Создаем сессию для повторного использования соединений
    if chosen_proxy:
        session.proxies = {
            "http": chosen_proxy,
            "https": chosen_proxy,
        }  # Настраиваем прокси, если он указан

    logger.info(
        f"Starting sitemap processing for {url}"
    )  # Логируем начало обработки карты сайта
    downloaded_files = process_sitemap(
        session, url, data_directory
    )  # Обрабатываем карту сайта и загружаем файлы
    logger.info(
        f"Downloaded {len(downloaded_files)} files"
    )  # Логируем количество загруженных файлов

    all_urls = []
    for file_path in downloaded_files:
        urls = extract_urls_from_xml(
            file_path
        )  # Извлекаем URL из каждого загруженного XML файла
        all_urls.extend(urls)  # Добавляем извлеченные URL в общий список

    logger.info(
        f"Writing {len(all_urls)} URLs to {csv_file_path}"
    )  # Логируем количество URL для записи в CSV
    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["url"])  # Пишем заголовок столбца
        for url in all_urls:
            writer.writerow([url])  # Записываем каждый URL в CSV файл
    logger.info(
        f"Finished writing URLs to {csv_file_path}"
    )  # Логируем завершение записи в CSV


def process_sitemap(session, url, save_directory):
    """Обрабатывает карту сайта, загружает файлы и рекурсивно обрабатывает дочерние карты."""
    logger.info(f"Processing sitemap {url}")  # Логируем начало обработки карты сайта
    root = fetch_and_parse_xml(session, url)  # Загружаем и парсим XML

    sitemap_elements = root.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
    )  # Ищем все элементы sitemaps в XML

    downloaded_files = []

    if sitemap_elements:
        logger.info(
            f"Found {len(sitemap_elements)} sub-sitemaps in {url}"
        )  # Логируем количество найденных под-карт
        for sitemap_element in sitemap_elements:
            loc_element = sitemap_element.find(
                "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
            )  # Извлекаем URL под-карты
            if loc_element is not None:
                child_sitemap_url = loc_element.text  # Получаем текстовое значение URL
                logger.info(
                    f"Processing child sitemap {child_sitemap_url}"
                )  # Логируем обработку под-карты
                downloaded_files.extend(
                    process_sitemap(session, child_sitemap_url, save_directory)
                )  # Рекурсивно обрабатываем под-карту
    else:
        download_path = download_file(
            session, url, save_directory
        )  # Загружаем файл, если под-карт нет
        downloaded_files.append(
            download_path
        )  # Добавляем путь загруженного файла в список

    return downloaded_files  # Возвращаем список загруженных файлов


def download_file(session, url, save_directory):
    """Загружает файл по указанному URL и сохраняет его в заданную директорию."""
    file_name = Path(url).name  # Извлекаем имя файла из URL
    save_path = save_directory / file_name  # Определяем путь для сохранения файла

    logger.info(
        f"Downloading file from {url} to {save_path}"
    )  # Логируем начало загрузки
    response = session.get(url)  # Выполняем HTTP-запрос для загрузки файла
    response.raise_for_status()  # Проверяем успешность запроса

    with open(save_path, "wb") as file:
        file.write(response.content)  # Сохраняем содержимое файла
    logger.info(
        f"Successfully downloaded {url} to {save_path}"
    )  # Логируем успешную загрузку

    return save_path  # Возвращаем путь к загруженному файлу


def fetch_and_parse_xml(session, url):
    """Загружает XML файл по указанному URL и парсит его содержимое."""
    logger.info(
        f"Fetching and parsing XML from {url}"
    )  # Логируем начало загрузки и парсинга XML
    response = session.get(url)  # Выполняем HTTP-запрос для загрузки XML файла
    response.raise_for_status()  # Проверяем успешность запроса
    logger.info(f"Successfully fetched XML from {url}")  # Логируем успешную загрузку
    return ET.fromstring(response.content)  # Парсим XML и возвращаем корневой элемент


def extract_urls_from_xml(file_path):
    """Извлекает все URL из XML файла."""
    logger.info(f"Extracting URLs from {file_path}")  # Логируем начало извлечения URL
    tree = ET.parse(file_path)  # Парсим XML файл
    root = tree.getroot()  # Получаем корневой элемент
    urls = [
        elem.text
        for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]  # Извлекаем все элементы <loc> и получаем их текстовое значение (URL)
    return urls  # Возвращаем список URL


"""
___________________________________________________________________________________________

"""


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


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
                # Парсим HTML и извлекаем данные
                parsing(url_id, src, url, proxy, headers, cookies)
                successful_urls.add(url)
                # Если данные успешно обработны, записываем URL в CSV успешных загрузок
                write_to_csv(url, csv_file_successful)
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
        location = None
        publication_date = None
        mail_address = None
        phone_number = None

        # Получаем номер телефона и имя пользователя с помощью синхронной функции get_number
        user_name, phones = get_number(url_id, proxy, headers, cookies)
        phone_numbers_extracted = extract_phone_numbers(
            phones
        )  # Получаем список номеров
        location = extract_user_info(parser)

        # Извлекаем дату публикации с использованием соответствующей функции
        publication_date = extract_publication_date(parser)

        # Если phone_numbers_extracted содержит более одного номера, разделяем данные
        for phone_number in phone_numbers_extracted:
            data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            with write_lock:
                write_to_csv(data, csv_file_path)

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


def extract_phone_numbers(phones: list) -> list:
    """Проверяет валидность каждого номера телефона и форматирует их, возвращая уникальные номера."""
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

    for phone_number in phones:
        for pattern in patterns:
            if pattern.match(phone_number):
                number = re.sub(
                    r"[^\d]", "", phone_number
                )  # Удаляем все символы, кроме цифр
                number = re.sub(r"^0+", "", number)  # Удаляем ведущие нули
                number = re.sub(
                    r"^375", "375", number
                )  # Преобразуем префикс в международный формат
                unique_numbers.add(number)  # Добавляем номер в множество
                break  # Если найдено совпадение, выходим из цикла

    return list(unique_numbers)  # Преобразуем множество обратно в список для возврата


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

"""_______________________________________________________________________________________"""





if __name__ == "__main__":
    main()  # Запускаем основную функцию при выполнении скрипта напрямую
    get_html(max_workers=10)  # Устанавливаем количество потоков
