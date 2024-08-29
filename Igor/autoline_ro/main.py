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
from urllib.parse import urlparse


cookies = {
    "page_load_speed_data": "%7B%22encodedRequestId%22%3A%22MTcyNDYxNDc2NzYyMjE5MTA3Ng%3D%3D%22%2C%22domContentLoadedEventStartTime%22%3A562.6999999880791%2C%22domContentLoadedEventEndTime%22%3A582.7999999821186%2C%22loadEventStartTime%22%3A713%2C%22redirectCount%22%3A0%7D",
    "SID": "1f2817c3afa4a14712f1a6a875ac2b45",
    "userKey": "1724587576379964940",
    "assets-preloaded": "1",
    "last-locale-usage": "ro_ro",
    "dis_linemedia_agency_b": "1",
    "ga_user_props": "eyJkIjoiR3B0eGlmcElDZWxKY2hiU0VkaU9cL1E9PSIsImEiOjEsImFkIjp7ImsiOjF9fQ%3D%3D",
    "utmTags": "eyJkIjoiOXpzQ1FsWWd3eHJyeGJiUE54UTdTZz09IiwiYSI6MSwiYWQiOnsiayI6Mn19",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'page_load_speed_data=%7B%22encodedRequestId%22%3A%22MTcyNDYxNDc2NzYyMjE5MTA3Ng%3D%3D%22%2C%22domContentLoadedEventStartTime%22%3A562.6999999880791%2C%22domContentLoadedEventEndTime%22%3A582.7999999821186%2C%22loadEventStartTime%22%3A713%2C%22redirectCount%22%3A0%7D; SID=1f2817c3afa4a14712f1a6a875ac2b45; userKey=1724587576379964940; assets-preloaded=1; last-locale-usage=ro_ro; dis_linemedia_agency_b=1; ga_user_props=eyJkIjoiR3B0eGlmcElDZWxKY2hiU0VkaU9cL1E9PSIsImEiOjEsImFkIjp7ImsiOjF9fQ%3D%3D; utmTags=eyJkIjoiOXpzQ1FsWWd3eHJyeGJiUE54UTdTZz09IiwiYSI6MSwiYWQiOnsiayI6Mn19',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}
# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}
romanian_phone_patterns = {
    "full": r"\b(40\d{9}|0\d{9}|\d{9})\b",
    "split": r"(40\d{9}|0\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [40],
}

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


class SitemapProcessor:
    def __init__(self, session, save_directory):
        self.session = session
        self.save_directory = save_directory
        self.downloaded_files = []

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

    """Загружает файл по указанному URL и сохраняет его в заданную директорию."""

    def download_file(self, url):

        proxies = load_proxies()
        if not proxies:
            logger.error("No proxies available")
            raise ValueError("Proxy list is empty")

        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}

        file_name = Path(url).name
        save_path = self.save_directory / file_name

        try:
            response = self.session.get(
                url,
                proxies=proxies_dict,
                headers=headers,  # Убедитесь, что переменная headers определена
                cookies=cookies,  # Убедитесь, что переменная cookies определена
            )
            response.raise_for_status()

            with open(save_path, "wb") as file:
                file.write(response.content)

            logger.info(f"Successfully downloaded {url} to {save_path}")
            return save_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url} using proxy {proxy}: {e}")
            raise

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


def filter_urls_in_csv(csv_file_path):
    """
    Загружает URL из CSV файла, фильтрует их по наличию подстроки '--c', наличию папки,
    а также по шаблону 'https://url/любая папка/любое имя.html' и сохраняет обновленные URL в новый CSV файл.

    :param csv_file_path: Путь к исходному CSV файлу.
    """
    filtered_urls = []

    def has_folder(url):
        """Проверяет, содержит ли URL путь, указывающий на наличие папки."""
        path = urlparse(url).path
        return len(path.strip("/").split("/")) == 1

    def matches_html_pattern(url):
        """Проверяет, соответствует ли URL шаблону 'https://url/любая папка/любое имя.html'."""
        path = urlparse(url).path
        segments = path.strip("/").split("/")
        return len(segments) == 2 and segments[1].endswith(".html")

    # Чтение CSV файла и фильтрация URL
    with open(csv_file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Сохраняем заголовок
        for row in reader:
            url = row[0]  # Предполагается, что URL находятся в первом столбце
            if (
                "--c" not in url
                and not has_folder(url)
                and not matches_html_pattern(url)
            ):
                filtered_urls.append(url)

    # Запись отфильтрованных URL в новый CSV файл
    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)  # Записываем заголовок
        for url in filtered_urls:
            writer.writerow([url])


def main():
    url = "https://autoline.ro/sitemap.xml"
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
    filter_urls_in_csv(csv_file_path)


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


def extract_phone_site(parser):
    phone_pattern = re.compile(
        r"\b\d{1,4}(?:[\s-]?\d{1,4}){0,3}\b"
        # r"\d{3}\s\d{3}\s\d{3}|\(\d{3}\)\s\d{3}\-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"
    )
    phone_numbers = []
    phone_selector = "#content > div.sales-full-container.sfc-status-active > div.sales-full-container__main > div.sf-wrapper.ecommerce-item.sf-wrapper_with-menu > div.sf-wrapper__menu"

    # Получаем все элементы <a> с классом "full-number"
    phone_elements = parser.css(phone_selector + " a.full-number")

    for element in phone_elements:
        href = element.attrs.get("href", "")
        if href.startswith("tel:"):
            phone_number = href.replace("tel:", "").strip()
            phone_numbers.append(phone_number)
    logger.info(phone_numbers)
    return phone_numbers


def extract_publication_date_and_location(parser):
    # Селектор для основного блока
    block_selector = "#content > div.sales-full-container.sfc-status-active > div.sales-full-container__main > div.sf-wrapper.ecommerce-item.sf-wrapper_with-menu > div.sf-wrapper-main.sf-wrapper__main > div.sf-descr > div.sf-main > div.sf-data.sf-data-main > div.block"
    block_element = parser.css_first(block_selector)

    if not block_element:
        return None, None  # Возвращаем None, если основной блок не найден

    # Получаем текущую дату
    today = datetime.datetime.today()

    # Ищем дату публикации
    date_element = None
    for item in block_element.css("div.item"):
        field = item.css_first("span.field")
        if field and "Data publicării:" in field.text():
            date_element = item.css_first("span.value")
            break

    if date_element:
        date_text = date_element.text(strip=True).lower()

        if date_text == "ieri":  # Если дата указана как "вчера"
            publication_date = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            try:
                day, month, year = date_text.split(" ")
                months = {
                    "ian.": 1,
                    "feb.": 2,
                    "mar.": 3,
                    "apr.": 4,
                    "mai": 5,
                    "iun.": 6,
                    "iul.": 7,
                    "aug.": 8,
                    "sep.": 9,
                    "oct.": 10,
                    "nov.": 11,
                    "dec.": 12,
                }
                month_number = months.get(month.lower(), 0)
                # Преобразуем в объект datetime
                time_posted = datetime.datetime(int(year), month_number, int(day))
            except ValueError:
                time_posted = (
                    today  # Если дата не распарсилась, используем текущую дату
                )

        # Форматируем дату, если это объект datetime
        if isinstance(time_posted, datetime.datetime):
            publication_date = time_posted.strftime("%Y-%m-%d")
        else:
            return "Некорректный формат даты"

    # Ищем местоположение
    location_element = None
    for item in block_element.css("div.item"):
        field = item.css_first("span.field")
        if field and "Locul de amplasare:" in field.text():
            location_element = item.css_first("span.value")
            break

    if location_element:
        country_element = location_element.css_first(".loc-country")
        city_element = location_element.css_first(".loc-city")
        if country_element and city_element:
            location = (
                f"{country_element.text(strip=True)},{city_element.text(strip=True)}"
            )
        else:
            location = None
    else:
        location = None

    return publication_date, location


def parsing(src, url):
    csv_file_path = "result.csv"
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        parser = HTMLParser(src)
        location = None
        publication_date = None
        mail_address = None
        phone_number = None

        with parsing_lock:

            phones = extract_phone_site(parser)
            if not phones:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")

            publication_date, location = extract_publication_date_and_location(parser)
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

            logger.info(f"| {url} | Номера - {phones} | Локация - {location} |")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phones:
                for phone_number in phones:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_file_path)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 28  # id_site для 'https://autoline.ro/'

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
                        if re.match(romanian_phone_patterns["final"], num)
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
        logger.error(f"Ошибка при парсинге HTML для URL  {e}")
        return False


def fetch_url(url, proxies, headers, cookies, csv_file_successful, successful_urls):
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
            # response.raise_for_status()
            if response.status_code == 200:
                src = response.text
                success = parsing(src, url)
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


def get_html(max_workers=2):
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
                # url.split("/")[-1],
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
                    parsed_number = phonenumbers.parse(match, "RO")
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


if __name__ == "__main__":
    # main()
    get_html(max_workers=2)
