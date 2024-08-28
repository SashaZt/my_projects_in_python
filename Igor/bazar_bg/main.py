import requests
import random
import csv

from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
import ssl
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
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
import locale
import re
import gzip
import shutil

bulgaria_phone_patterns = {
    "full": r"\b((?:00|011|\+|00-|\+0)?359[\s-]?\d{6,9})\b",  # Номер может начинаться с '00', '011', '+', '00-', '+0' с кодом страны '359'
    "split": r"(359\d{6,9})",  # Номера, начинающиеся с '359', и за ними от 6 до 9 цифр
    "final": r"\b(\d{6,9})\b",  # Только от 6 до 9 цифр, если код страны отсутствует
    "codes": [359],  # Код страны для Болгарии
}

# Установка директорий для логов и данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
gz_directory = data_directory / "gz"
xml_directory = data_directory / "xml"
data_directory.mkdir(parents=True, exist_ok=True)
gz_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)

# Файлы для записи и проверки URL
csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"
cookies = {
    "uuid": "1e161d17-bfd6-4dfe-92b3-307d8234c184",
    "bc": "%7B%22device_id%22%3A%225628e326-b4a7-4e8a-b669-7e8851d950d0%22%7D",
    "CookieScriptConsent": '{"googleconsentmap":{"ad_storage":"targeting","analytics_storage":"performance","ad_personalization":"targeting","ad_user_data":"targeting","functionality_storage":"functionality","personalization_storage":"functionality","security_storage":"functionality"},"bannershown":1,"action":"accept","consenttime":1721801677,"categories":"[\\"functionality\\",\\"performance\\",\\"targeting\\"]","GoogleACString":"2~70.89.93.108.122.149.196.259.311.323.415.486.494.495.540.574.864.981.1051.1095.1097.1205.1276.1301.1415.1423.1449.1516.1570.1577.1651.1878.1889.2072.2253.2328.2357.2526.2568.2575.2583.2677.3100.3296.3331~dv.","CMP":"CQEAuYAQEAuYAF2ACBENBDFsAP_gAEPgAAAAI3pB7CbFIWFAwG53YKsEMAEDRNAAQoQgAASBAGAAQAKQMAQCgkAQBASgBCACAAAAICRBIQIECAAACEAAQAAAIAAEAAQAAAAIIAAAgAAAAEAIAAACAAAAAQAIgAIEEAAAmAgAAAIAGEAAhAAAAAAAAAAAAAABAgAAAAAAAAAAAAAAACAAAQIAAAAAAAAAAAAII3wNwAFgAPAAqABwAEAAMgAaAA8ACIAEcAJgAUgAqgBdADEAGgAPQAfgBCACIAEcAJwAUYAwABhgDKAHIAPYAfoBCACIgEWAI4AXUAvoBigDPgHEAOoAe0BCACLwFIgKyAWiAtgBeYC-gF_gMEgZMBk4DLAGqgQhAjeAAAAA.YAAAAAAAAAAA","key":"0030a4ca-a0b9-469a-a7d6-b1da8262d776"}',
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def download_and_parse_sitemaps():
    main_url = "https://bazar.bg/sitemap-new.xml"
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    # Шаг 1: Скачиваем основной XML файл
    response = requests.get(
        main_url,
        headers=headers,
        proxies=proxies_dict,
    )
    response.raise_for_status()
    main_xml_content = response.content

    # Шаг 2: Парсим основной XML и находим ссылки по шаблону
    root = ET.fromstring(main_xml_content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    pattern = re.compile(r"sitemap-ads-\d+\.xml\.gz")

    gz_links = [
        elem.text
        for elem in root.findall(".//ns:loc", namespaces=namespace)
        if pattern.search(elem.text)
    ]

    # Функция для скачивания одного архива
    def download_gz_file(gz_link):
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}

        gz_filename = gz_link.split("/")[-1]
        gz_file_path = gz_directory / gz_filename

        # Скачиваем архив
        gz_response = requests.get(gz_link, proxies=proxies_dict)
        gz_response.raise_for_status()
        with open(gz_file_path, "wb") as gz_file:
            gz_file.write(gz_response.content)
        logger.info(gz_file_path)
        return gz_file_path

    # Шаг 3: Многопоточное скачивание архивов
    with ThreadPoolExecutor(max_workers=10) as executor:
        gz_file_paths = list(executor.map(download_gz_file, gz_links))

    # Шаг 4: Распаковка и парсинг каждого распакованного XML
    urls = []
    for gz_file_path in gz_file_paths:
        xml_filename = gz_file_path.stem  # Убираем .gz
        xml_file_path = xml_directory / xml_filename

        # Распаковываем архив
        with gzip.open(gz_file_path, "rb") as f_in:
            with open(xml_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Парсим XML и собираем ссылки
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        urls.extend(
            [
                url_elem.text
                for url_elem in root.findall(".//ns:url/ns:loc", namespaces=namespace)
            ]
        )

    # Шаг 5: Записываем результаты в CSV файл
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["URL"])
        for url in urls:
            writer.writerow([url])

    logger.info(f"Все ссылки успешно записаны в {csv_file_path}")
    # Удаление директорий со всеми файлами
    shutil.rmtree(gz_directory)
    shutil.rmtree(xml_directory)


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
                url.split("/")[-2].replace("obiava-", ""),
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")


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

            # phone_numbers_extracted = extract_phone_numbers(phones)
            # if not phone_numbers_extracted:
            #     logger.warning(f"Извлеченные номера телефонов пусты для URL: {url}")

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
                # return True
            # else:
            #     missing_data = []
            #     if not location:
            #         missing_data.append("location")
            #     if not publication_date:
            #         missing_data.append("publication_date")
            #     if not phones:
            #         missing_data.append("phone_numbers")

            #     logger.error(
            #         f"Отсутствуют необходимые данные для URL: {url}. Недостающие данные: {', '.join(missing_data)}"
            #     )
            #     # return False

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 25  # id_site для 'https://abw.by/'

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
                        if re.match(bulgaria_phone_patterns["final"], num)
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


if __name__ == "__main__":
    # download_and_parse_sitemaps()
    get_html(max_workers=10)  # Устанавливаем количество потоков
