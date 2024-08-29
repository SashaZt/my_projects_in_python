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
import gzip
import shutil
from itertools import cycle

cookies = {
    "stid": "9ddfc9584e848b034a08d6194dc885a1297a2dc80e523a4a1577b1cda945effb",
    "ouid": "snyBDmbDM0tWegvsAyl/Ag==",
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Connection": "keep-alive",
    # 'Cookie': 'stid=9ddfc9584e848b034a08d6194dc885a1297a2dc80e523a4a1577b1cda945effb; ouid=snyBDmbDM0tWegvsAyl/Ag==',
    "DNT": "1",
    "If-None-Match": 'W/"d4efd8e5e9ad503cb348813937d335cc"',
    "Referer": "https://ab.onliner.by/toyota/4runner/279415",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

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
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

output_gz_file = data_directory / "cars-1.xml.gz"
output_xml_file = data_directory / "cars-1.xml"
output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def download_and_extract_gz():
    url = "https://ab.onliner.by/sitemap/cars-1.xml.gz"

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
    counter_error = 0
    csv_file_path = "result.csv"
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        parser = HTMLParser(src)
        location = None
        publication_date = None
        mail_address = None
        phone_numbers = set()

        with parsing_lock:

            # Прямое извлечение данных из JSON (интеграция get_number)
            number_url = f"https://ab.onliner.by/sdapi/ab.api/vehicles/{url_id}/phones"
            ad_data_url = f"https://ab.onliner.by/sdapi/ab.api/vehicles/{url_id}"
            proxies = {"http": proxy, "https": proxy} if proxy else None

            try:
                json_data_ad_data = None
                json_data_number = None
                response_ad_data = requests.get(
                    ad_data_url, proxies=proxies, headers=headers, cookies=cookies
                )
                if response_ad_data.status_code == 200:

                    json_data_ad_data = response_ad_data.json()
                    counter_error = 0
                elif response_ad_data.status_code == 403:
                    # Если код ошибки 403, удаляем прокси и пробуем другой
                    print(
                        f'{datetime.datetime.now().strftime("%H:%M:%S")} - Код ошибки 403. Сайт нас подрезал.'
                    )
                    counter_error += 1
                    if counter_error == 10:
                        print(
                            f'{datetime.datetime.now().strftime("%H:%M:%S")} - Перезапуск, нас подрезали.'
                        )
                        return None
                else:
                    return None

                response_number = requests.get(
                    number_url, proxies=proxies, headers=headers, cookies=cookies
                )
                if response_number.status_code == 200:
                    json_data_number = response_number.json()
                    counter_error = 0
                elif response_number.status_code == 403:
                    # Если код ошибки 403, удаляем прокси и пробуем другой
                    print(
                        f'{datetime.datetime.now().strftime("%H:%M:%S")} - Код ошибки 403. Сайт нас подрезал.'
                    )
                    counter_error += 1
                    if counter_error == 10:
                        print(
                            f'{datetime.datetime.now().strftime("%H:%M:%S")} - Перезапуск, нас подрезали.'
                        )
                        return None
                else:
                    return None

                if isinstance(json_data_number, list) and json_data_number:
                    phones = json_data_number[0]
                    phone_numbers.add(phones)
                # Извлечение данных
                location_json = json_data_ad_data.get("location", {})

                # Получение имени региона
                region = location_json.get("region", {})
                region_name = region.get("name", "Не указано")

                # Получение имени города
                city = location_json.get("city", {})
                city_name = city.get("name", "Не указано")
                location = f"{region_name}, {city_name}"

                # Предполагаем, что json_data_ad_data - это ваш JSON объект
                created_at_str = json_data_ad_data.get("created_at", "")

                # Проверяем, что строка не пустая
                if created_at_str:
                    try:
                        # Парсим строку даты в объект datetime
                        dt = datetime.datetime.strptime(
                            created_at_str, "%Y-%m-%dT%H:%M:%S%z"
                        )

                        # Извлекаем год, месяц и день
                        year = dt.year
                        month = dt.month
                        day = dt.day

                        # Форматируем дату в нужный формат
                        publication_date = f"{year}-{month:02d}-{day:02d}"
                    except ValueError as e:
                        logger.error(f"Ошибка при разборе даты: {e}")

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Failed to fetch number for {url_id} with proxy {proxy}: {e}"
                )

            if not phone_numbers:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phone_numbers:
                for phone_number in phone_numbers:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_file_path)

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
                if phone_numbers and id_ogloszenia:
                    phone_numbers_extracted, invalid_numbers = extract_phone_numbers(
                        phone_numbers
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
                    raw_numbers = ", ".join(phone_numbers)
                    numbers_data = (id_ogloszenia, raw_numbers, clean_numbers)
                    logger.info(numbers_data)
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

    # Получение списка уже успешных URL
    successful_urls = get_successful_urls(csv_file_successful)

    urls_df = pd.read_csv(output_csv_file)

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
            for count, url in enumerate(urls_df["URL"], start=1)
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


"""Выполняет HTTP-запрос для получения номера телефона и имени пользователя."""


if __name__ == "__main__":
    download_and_extract_gz()  # Запускаем основную функцию при выполнении скрипта напрямую
    get_html(max_workers=10)  # Устанавливаем количество потоков
