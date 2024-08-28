from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from selectolax.parser import HTMLParser
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from pathlib import Path
import mysql.connector
import phonenumbers
import pandas as pd
import threading
import datetime
import requests
import random
import csv
import re


# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}


polish_phone_patterns = {
    "full": r"\b(48\d{9}|\d{9})\b",
    "split": r"(48\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [48],
}
# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
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

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def download_and_parse_xml():
    url = "https://twojaoferta.com.pl/sitemap/sitemap_classified_0.xml"  # Здесь укажите вашу ссылку
    output_csv = Path("data/urls.csv")
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    # Получаем случайный прокси
    # Скачивание XML файла
    response = requests.get(
        url,
        proxies=proxies_dict,
        cookies=cookies,
        headers=headers,
    )
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


def extract_phone_site(parser):
    # Используем метод select_one для поиска скрипта по указанному селектору
    script_tag = parser.select_one("body > script:nth-child(16)")

    if script_tag:
        script_text = script_tag.string
        # Поиск строки с номером телефона
        phone_match = re.search(r'this\.phone\s*=\s*"(.*?)"', script_text)
        if phone_match:
            phone_number = phone_match.group(1)
            return phone_number
        else:
            return None
    else:
        return None


def parsing(src, url):
    csv_file_path = "result.csv"
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:

        parser = HTMLParser(src)
        soup = BeautifulSoup(src, "lxml")
        location = None
        publication_date = None
        mail_address = None
        phone_numbers = set()

        with parsing_lock:

            phones = extract_phone_site(soup)
            phone_numbers.add(phones)
            location = extract_user_info(parser)
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")

            publication_date = extract_publication_date(parser)
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")
            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'

            if location and publication_date and phone_numbers:
                # logger.info(phones)
                for phone_number in phone_numbers:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_file_path)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 33  # id_site для 'twojaoferta.com.pl'

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
                if phone_numbers and id_ogloszenia:
                    phone_numbers_extracted, invalid_numbers = extract_phone_numbers(
                        phone_numbers
                    )
                    valid_numbers = [
                        num
                        for num in phone_numbers_extracted
                        if re.match(polish_phone_patterns["final"], num)
                    ]
                    if valid_numbers:
                        clean_numbers = ", ".join(valid_numbers)
                    else:
                        clean_numbers = "invalid"

                    insert_numbers = (
                        "INSERT INTO numbers (id_ogloszenia, raw, correct) "
                        "VALUES (%s, %s, %s)"
                    )
                    raw_numbers = ", ".join(phone_numbers)
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
        # logger.error(f"Ошибка при парсинге HTML для URL {e}")
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
            response.raise_for_status()
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
            elif response.status_code == 410:
                return None
            else:
                logger.error(f"Unexpected status code {response.status_code} for {url}")

        except requests.exceptions.TooManyRedirects:
            logger.error("Произошла ошибка: Exceeded 30 redirects. Пропуск URL.")
            return "Редирект"

        except (requests.exceptions.ProxyError, requests.exceptions.Timeout) as e:
            pass

        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            continue

    logger.error(f"Не удалось загрузить {url} ни с одним из прокси.")
    return None


def get_html(max_workers=10):
    """Основная функция для обработки списка URL с использованием многопоточности."""
    proxies = load_proxies()  # Загружаем список всех прокси
    csv_file_path = Path("data/urls.csv")
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
        r"\d{3}\s\d{3}\s\d{3}|\(\d{3}\)\s\d{3}\-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}"
    )
    for entry in data:
        if isinstance(entry, str):
            matches = phone_pattern.findall(entry)
            for match in matches:
                original_match = match
                match = re.sub(r"[^\d]", "", match)
                match = re.sub(r"^0+", "", match)
                try:
                    parsed_number = phonenumbers.parse(match, "PL")
                    if phonenumbers.is_valid_number(parsed_number):
                        national_number = phonenumbers.format_number(
                            parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                        )
                        clean_number = "".join(filter(str.isdigit, national_number))
                        phone_numbers.add(clean_number)
                    else:
                        invalid_numbers.append(original_match)
                except NumberParseException:
                    invalid_numbers.append(original_match)
    return phone_numbers, invalid_numbers


# Извлечение местоположения
def extract_user_info(parser):
    location = None
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
                location = location_element.text(strip=True)

    return location


# Извлечение даты публикации
def extract_publication_date(parser):
    date_element = parser.css_first(
        "#classified__panel > p.small.text-muted > span:nth-child(1)"
    )
    if date_element:
        date_element_text = date_element.text(strip=True).replace("Opublikowano: ", "")

        # Преобразование строки в объект datetime
        publication_date_obj = datetime.datetime.strptime(date_element_text, "%d-%m-%Y")

        # Преобразование объекта datetime в строку в нужном формате
        publication_date = publication_date_obj.strftime("%Y-%m-%d")

        return publication_date

    else:
        return None


if __name__ == "__main__":
    download_and_parse_xml()  # Запускаем основную функцию при выполнении скрипта напрямую
    get_html(max_workers=10)  # Устанавливаем количество потоков
