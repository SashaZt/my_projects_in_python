import random
from concurrent.futures import ThreadPoolExecutor, as_completed
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
data_directory = current_directory / "data"

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

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


class SitemapProcessor:
    def __init__(self, session, save_directory):
        self.session = session  # Используем requests.Session для повторного использования соединений
        self.save_directory = (
            save_directory  # Директория для сохранения загруженных файлов
        )
        self.downloaded_files = []  # Список загруженных файлов

    def process_sitemap(self, url):
        """Обрабатывает карту сайта, загружает файлы и рекурсивно обрабатывает дочерние карты."""
        root = self.fetch_and_parse_xml(url)

        sitemap_elements = root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
        )

        if sitemap_elements:
            logger.info(f"Found {len(sitemap_elements)} sub-sitemaps in {url}")
            for sitemap_element in sitemap_elements:
                loc_element = sitemap_element.find(
                    "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                )
                if loc_element is not None:
                    child_sitemap_url = loc_element.text
                    self.process_sitemap(child_sitemap_url)
        else:
            download_path = self.download_file(url)
            self.downloaded_files.append(download_path)

    def download_file(self, url):
        """Загружает файл по указанному URL и сохраняет его в заданную директорию."""
        file_name = Path(url).name
        save_path = self.save_directory / file_name

        response = self.session.get(url)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Successfully downloaded {url} to {save_path}")

        return save_path

    def fetch_and_parse_xml(self, url):
        """Загружает XML файл по указанному URL и парсит его содержимое."""
        response = self.session.get(url)
        response.raise_for_status()
        return ET.fromstring(response.content)

    def extract_urls_from_files(self):
        """Извлекает все URL из загруженных XML файлов."""
        all_urls = []
        for file_path in self.downloaded_files:
            tree = ET.parse(file_path)
            root = tree.getroot()
            urls = [
                elem.text
                for elem in root.findall(
                    ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                )
            ]
            all_urls.extend(urls)
        return all_urls


def main():
    url = "https://static.abw.by/sitemap/adverts.xml"
    data_directory = Path("data_directory")
    data_directory.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    processor = SitemapProcessor(session, data_directory)

    logger.info(f"Starting sitemap processing for {url}")
    processor.process_sitemap(url)
    logger.info(f"Downloaded {len(processor.downloaded_files)} files")

    all_urls = processor.extract_urls_from_files()

    csv_file_path = Path("data/output.csv")
    logger.info(f"Writing {len(all_urls)} URLs to {csv_file_path}")
    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["url"])
        for url in all_urls:
            writer.writerow([url])
    logger.info(f"Finished writing URLs to {csv_file_path}")


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


def parsing(url_id, src, url, proxy, headers, cookies):
    csv_file_path = "result.csv"
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        parser = HTMLParser(src)
        location = None
        publication_date = None
        mail_address = None
        phone_number = None

        # Прямое извлечение данных из JSON (интеграция get_number)
        number_url = f"https://b.abw.by/api/v2/adverts/{url_id}/phones"
        proxies = {"http": proxy, "https": proxy} if proxy else None

        try:
            response = requests.get(
                number_url, proxies=proxies, headers=headers, cookies=cookies
            )
            response.raise_for_status()
            json_data = response.json()
            user_name = json_data.get("title")
            phones = json_data.get("phones", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch number for {url_id} with proxy {proxy}: {e}")
            phones = []

        if not phones:
            logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")

        phone_numbers_extracted = extract_phone_numbers(phones)
        if not phone_numbers_extracted:
            logger.warning(f"Извлеченные номера телефонов пусты для URL: {url}")

        location = extract_user_info(parser)
        if not location:
            logger.warning(f"Не удалось извлечь местоположение для URL: {url}")

        publication_date = extract_publication_date(parser)
        if not publication_date:
            logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

        if location and publication_date and phone_numbers_extracted:
            for phone_number in phone_numbers_extracted:
                data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                with parsing_lock:
                    write_to_csv(data, csv_file_path)
            return True
        else:
            missing_data = []
            if not location:
                missing_data.append("location")
            if not publication_date:
                missing_data.append("publication_date")
            if not phone_numbers_extracted:
                missing_data.append("phone_numbers")

            logger.error(
                f"Отсутствуют необходимые данные для URL: {url}. Недостающие данные: {', '.join(missing_data)}"
            )
            return False

    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML для URL {url_id}: {e}")
        return False


def fetch_url(
    url, proxies, headers, cookies, csv_file_successful, successful_urls, url_id
):
    fetch_lock = threading.Lock()  # Локальная
    counter_error = 0  # Счетчик ошибок

    if url in successful_urls:
        return

    while proxies:
        proxy = random.choice(proxies)  # Выбираем случайный прокси

        if not proxy:
            continue
        proxies_dict = {"http": proxy, "https": proxy}

        try:
            response = requests.get(
                url,
                proxies=proxies_dict,
                headers=headers,
                cookies=cookies,
                timeout=10,  # Тайм-аут для предотвращения зависания
            )
            response.raise_for_status()

            if response.status_code == 200:
                src = response.text
                success = parsing(url_id, src, url, proxy, headers, cookies)
                if success:
                    with fetch_lock:
                        successful_urls.add(url)
                        write_to_csv(url, csv_file_successful)
                return

            elif response.status_code == 403:
                logger.error(f"Код ошибки 403. Прокси заблокирован: {proxy}")
                counter_error += 1
                logger.info(f"Осталось прокси: {len(proxies)}. Ошибок: {counter_error}")
                if counter_error == 10:
                    logger.error(f"Перезапуск из-за 10 ошибок 403. Прокси: {proxy}")
                    return None

            else:
                logger.error(f"Unexpected status code {response.status_code} for {url}")

        except requests.exceptions.TooManyRedirects:
            logger.error("Произошла ошибка: Exceeded 30 redirects. Пропуск URL.")
            return "Редирект"

        except (requests.exceptions.ProxyError, requests.exceptions.Timeout) as e:
            logger.error(f"Ошибка прокси или таймаут: {e}. Прокси удален: {proxy}")
            logger.info(f"Осталось прокси: {len(proxies)}")

        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            continue

    logger.error(f"Не удалось загрузить {url} ни с одним из прокси.")
    return None


def get_html(max_workers=10):
    """Основная функция для обработки списка URL с использованием многопоточности."""
    proxies = load_proxies()  # Загружаем список всех прокси
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
        return user_name, phones

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch number for {url_id} with proxy {proxy}: {e}")
        return None, None


if __name__ == "__main__":
    main()  # Запускаем основную функцию при выполнении скрипта напрямую
    get_html(max_workers=10)  # Устанавливаем количество потоков
