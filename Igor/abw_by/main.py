from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from selectolax.parser import HTMLParser
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from pathlib import Path
import mysql.connector
import phonenumbers
import pandas as pd
import threading
import datetime
import requests
import random
import locale
import csv
import re

# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}

belarus_phone_patterns = {
    "full": r"\b(80\d{9}|375\d{9}|\d{9})\b",
    "split": r"(375\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [375],
}

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

        with parsing_lock:
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
                logger.error(
                    f"Failed to fetch number for {url_id} with proxy {proxy}: {e}"
                )
                phones = []

            if not phones:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")

            location = extract_user_info(parser)
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")

            publication_date = extract_publication_date(parser)
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

            logger.info(f"| {url} | Номера - {phones} | Локация - {location} |")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phones:
                for phone_number in phones:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_file_path)
            logger.info(data)
            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 27  # id_site для 'https://abw.by/'

            # Подключение к базе данных и запись данных
            try:
                cnx = mysql.connector.connect(**config)
                cursor = cnx.cursor(
                    buffered=True
                )  # Используем buffered=True для извлечения всех результатов

                insert_announcement = (
                    "INSERT INTO ogloszenia (id_site, poczta, adres, data, czas, link_do_ogloszenia, time_posted) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )

                announcement_data = (
                    site_id,
                    mail_address,
                    location,
                    date_part,
                    time_part,
                    link,
                    time_posted,
                )

                cursor.execute(insert_announcement, announcement_data)

                cnx.commit()  # Убедитесь, что изменения зафиксированы, прежде чем получить id

                # Получение id_ogloszenia с помощью SELECT-запроса
                select_query = (
                    "SELECT id_ogloszenia FROM ogloszenia "
                    "WHERE id_site = %s AND poczta = %s AND adres = %s AND data = %s AND czas = %s AND link_do_ogloszenia = %s AND time_posted = %s"
                )
                cursor.execute(
                    select_query,
                    (
                        site_id,
                        mail_address,
                        location,
                        date_part,
                        time_part,
                        link,
                        time_posted,
                    ),
                )

                # Извлечение результата и проверка наличия данных
                result = cursor.fetchone()
                if result:
                    id_ogloszenia = result[0]
                else:
                    print("Не удалось получить id_ogloszenia")
                    # Пропустить обработку, если id не найден
                    raise ValueError("Не удалось получить id_ogloszenia")

                # Заполнение таблицы numbers, если номера телефонов присутствуют
                if phones and id_ogloszenia:
                    phone_numbers_extracted, invalid_numbers = extract_phone_numbers(
                        phones
                    )
                    valid_numbers = [
                        num
                        for num in phone_numbers_extracted
                        if re.match(belarus_phone_patterns["final"], num)
                    ]
                    if valid_numbers:
                        clean_numbers = ", ".join(valid_numbers)
                    else:
                        clean_numbers = "invalid"

                    insert_numbers = (
                        "INSERT INTO numbers (id_ogloszenia, raw, correct) "
                        "VALUES (%s, %s, %s)"
                    )
                    raw_numbers = ", ".join(phones)
                    numbers_data = (id_ogloszenia, raw_numbers, clean_numbers)
                    cursor.execute(insert_numbers, numbers_data)

                    cnx.commit()
                    print("Данные успешно добавлены в таблицы numbers и ogloszenia.")
                else:
                    print("Нет номеров телефонов для добавления в таблицу numbers.")

            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Ошибка доступа: Неверное имя пользователя или пароль")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Ошибка базы данных: База данных не существует")
                else:
                    print(err)
                return False
            finally:
                cursor.close()
                cnx.close()
                print("Соединение с базой данных закрыто.")
                return True
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML для URL {url_id}: {e}")
        return False


def fetch_url(
    url, proxies, headers, cookies, csv_file_successful, successful_urls, url_id
):
    fetch_lock = threading.Lock()  # Локальная
    counter_error = 0  # Счетчик ошибок

    if url in successful_urls:
        logger.info(f"| Объявление уже было обработано, пропускаем. |")
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
                timeout=60,  # Тайм-аут для предотвращения зависания
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
            proxies.remove(proxy)
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


def extract_phone_numbers(data):
    phone_numbers = set()
    invalid_numbers = []
    phone_pattern = re.compile(
        r"(\+375\d{9}|\d{3}\s\d{3}\s\d{3}|\(\d{3}\)\s\d{3}\-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}|\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b|\+\d{2}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3}\b)"
    )
    for entry in data:
        if isinstance(entry, str):
            matches = phone_pattern.findall(entry)
            for match in matches:
                original_match = match
                match = re.sub(r"[^\d]", "", match)
                match = re.sub(r"^0+", "", match)
                try:
                    parsed_number = phonenumbers.parse(match, "BY")
                    # region = geocoder.description_for_number(parsed_number, "ru")  # Регион на русском языке
                    # operator = carrier.name_for_number(parsed_number, "ru")  # Оператор на русском языке
                    # print(f'parsed_number = {parsed_number} | Валид = {phonenumbers.is_valid_number(parsed_number)} | Регион = {region} | Оператор = {operator}')
                    if phonenumbers.is_valid_number(parsed_number):
                        # national_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
                        national_number = str(parsed_number.national_number)
                        national_number = re.sub(r"[^\d]", "", national_number)
                        national_number = re.sub(r"^0+", "", national_number)
                        clean_number = "".join(filter(str.isdigit, national_number))
                        phone_numbers.add(clean_number)
                    else:
                        invalid_numbers.append(original_match)
                except NumberParseException:
                    invalid_numbers.append(original_match)
    return phone_numbers, invalid_numbers


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
def extract_publication_date(parser):
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
                # Преобразуем дату в объект datetime
                date_obj = datetime.datetime.strptime(
                    f"{day} {month} {year}", "%d %m %Y"
                )
                return date_obj.strftime("%Y-%m-%d")
            else:
                return None

    return None


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
