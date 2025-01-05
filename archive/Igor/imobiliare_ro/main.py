import random
import csv
from pathlib import Path
from configuration.logger_setup import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from pathlib import Path
import mysql.connector
import phonenumbers
import pandas as pd
import threading
import datetime
from bs4 import BeautifulSoup
import json
import html
import re
import requests
import datetime
import time

cookies = {
    "__cf_bm": "l0hfDxyt7QmsqKzGW4.b3eWd9IgDRzCV5ZLVlXGYDyQ-1725476372-1.0.1.1-AY1tSFeEU8TfNOMMEREmurw23SpmNBeu2FVg4pX1b.ktM_PDhoIEsBlnW670uh4Awz0qNFlIy89wXtGEK54xog",
    "datadome": "otvANUEPeclYq0SyQkoRQG4_MNNb4q0ZUFYARG8Jim3525CoHsZY4VevWCDIrFtThUbU4pxeFykZX9s4e~FosRHsXEOJgQCZkev1c3_CKOJgS~HcuRfVPN_bCirojoDB",
}


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "referer": "https://www.imobiliare.ro/oferta/apartament-de-inchiriat-sector-1-pipera-mobilat-2-camere-229194746",
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
current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

# Файлы для записи и проверки URL
csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = current_directory / "result.csv"


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def extract_urls_and_save_to_csv():
    # Установка директорий для логов и данных

    # Шаблон для поиска нужных URL
    url_pattern = re.compile(r"^https://www\.imobiliare\.ro/oferta/.*")

    # Список URL для обработки
    sitemap_urls = [
        "https://www.imobiliare.ro/sitemap-project-listings-ro.xml",
        "https://www.imobiliare.ro/sitemap-international-listings-ro.xml",
        "https://www.imobiliare.ro/sitemap-listings-index-ro.xml",
    ]

    # Список для хранения всех URL
    all_urls = []
    proxies = load_proxies()  # Загружаем список всех прокси
    logger.info("Обработка первых двух ссылок")
    for sitemap_url in sitemap_urls[:2]:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        response = requests.get(
            sitemap_url,
            proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
            if url_pattern.match(loc):
                all_urls.append(loc)

    logger.info("Обработка третьей ссылки")
    response = requests.get(
        sitemap_urls[2],
        proxies=proxies_dict,
        headers=headers,
        cookies=cookies,
    )
    tree = ET.ElementTree(ET.fromstring(response.content))
    root = tree.getroot()

    for sitemap in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        response = requests.get(
            loc,
            proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )
        sub_tree = ET.ElementTree(ET.fromstring(response.content))
        sub_root = sub_tree.getroot()

        for url in sub_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
            if url_pattern.match(loc):
                all_urls.append(loc)

    logger.info("Сохранение всех URL в основной CSV файл")
    with csv_file_path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["url"])
        for url in all_urls:
            writer.writerow([url])


def parsing(src, url):
    parsing_lock = threading.Lock()  # Локальная блокировка
    # Парсим HTML
    soup = BeautifulSoup(src, "html.parser")

    # Находим все div с атрибутом wire:initial-data
    divs_with_data = soup.find_all("div", {"wire:initial-data": True})

    try:
        location = None
        publication_date = None
        mail_address = None
        phone_numbers = set()
        url_national = url.split("/")[4]
        url_national = url_national.split("-")[0]
        with parsing_lock:
            for div in divs_with_data:
                try:
                    location_title = None
                    location_depth_1_title = None
                    phones = None
                    # Извлекаем значение атрибута wire:initial-data
                    wire_data_encoded = div["wire:initial-data"]

                    # Декодируем HTML сущности
                    wire_data_decoded = html.unescape(wire_data_encoded)

                    # Удаляем некорректные экранированные символы
                    wire_data_decoded = re.sub(
                        r'\\(?!["\\/bfnrt])', r"\\\\", wire_data_decoded
                    )

                    # Заменяем одинарные обратные слеши на двойные
                    wire_data_decoded = wire_data_decoded.replace("\\", "\\\\")

                    # Преобразуем строку в JSON
                    wire_data_json = json.loads(wire_data_decoded)

                    # Проверяем наличие ключа unmaskedMainPhoneNumber
                    if "unmaskedMainPhoneNumber" in wire_data_json.get(
                        "serverMemo", {}
                    ).get("data", {}):
                        # # Сохранение JSON-объекта в файл
                        # with open("found_data.json", "w", encoding="utf-8") as json_file:
                        #     json.dump(wire_data_json, json_file, ensure_ascii=False, indent=4)
                        # Извлекаем номер телефона
                        phones = wire_data_json["serverMemo"]["data"][
                            "unmaskedMainPhoneNumber"
                        ]
                        logger.info(phones)
                        phone_numbers.add(phones)
                        # Извлекаем "Pipera" из translated_properties -> ro -> location -> title
                        location_title = (
                            wire_data_json["serverMemo"]["data"]
                            .get("listingResult", {})
                            .get("_source", {})
                            .get("translated_properties", {})
                            .get("ro", {})
                            .get("location", {})
                            .get("title")
                        )
                        # if location_title:
                        #     logger.info(f"Местоположение: {location_title}")

                        # Извлекаем "Bucureşti" из translated_properties -> ro -> location_depth_1 -> title
                        location_depth_1_title = (
                            wire_data_json["serverMemo"]["data"]
                            .get("listingResult", {})
                            .get("_source", {})
                            .get("translated_properties", {})
                            .get("ro", {})
                            .get("location_depth_1", {})
                            .get("title")
                        )
                        # if location_depth_1_title:
                        #     logger.info(f"Город: {location_depth_1_title}")
                        # Извлекаем значение created_at из JSON
                        created_at_str = (
                            wire_data_json.get("serverMemo", {})
                            .get("data", {})
                            .get("listingResult", {})
                            .get("_source", {})
                            .get("created_at")
                        )
                        location = f"{location_depth_1_title}, {location_title}"
                        if created_at_str:
                            # Преобразуем строку в объект datetime
                            time_posted = datetime.datetime.strptime(
                                created_at_str, "%Y-%m-%d %H:%M:%S"
                            )

                            # Приводим к нужному формату
                            publication_date = time_posted.strftime("%Y-%m-%d")

                        break  # Останавливаем цикл, как только находим первый номер и нужные данные
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка обработки элемента: {e}")
                except Exception as e:
                    logger.error(f"Неожиданная ошибка: {e}")
            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phone_numbers:
                # for phone_number in phones:
                csv_result = current_directory / f"result_{location_depth_1_title}.csv"
                data = f'{phone_numbers};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                write_to_csv(data, csv_result)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 27  # id_site для 'https://abw.by/'

            # Заполнение таблицы numbers, если номера телефонов присутствуют
            if url_national != "international":
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
                        logger.error("Не удалось получить id_ogloszenia")
                        # Пропустить обработку, если id не найден
                        raise ValueError("Не удалось получить id_ogloszenia")

                    if phones and id_ogloszenia:
                        phone_numbers_extracted, invalid_numbers = (
                            extract_phone_numbers(phone_numbers)
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
                        raw_numbers = ", ".join(phone_numbers)
                        numbers_data = (id_ogloszenia, raw_numbers, clean_numbers)
                        cursor.execute(insert_numbers, numbers_data)

                        cnx.commit()
                        logger.info(
                            "Данные успешно добавлены в таблицы numbers и ogloszenia."
                        )
                    else:
                        logger.error(
                            "Нет номеров телефонов для добавления в таблицу numbers."
                        )

                except mysql.connector.Error as err:
                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                        logger.error(
                            "Ошибка доступа: Неверное имя пользователя или пароль"
                        )
                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                        logger.error("Ошибка базы данных: База данных не существует")
                    else:
                        logger.error(err)
                    return False
                finally:
                    cursor.close()
                    cnx.close()
                    logger.info("Соединение с базой данных закрыто.")
                    write_to_csv(url, csv_file_successful)

                return True
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML для URL {e}")
        return False


def get_html(max_workers=10):
    """Основная функция для обработки списка URL с использованием многопоточности."""
    proxies = load_proxies()  # Загружаем список всех прокси

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
                # url.split("/")[-1].replace(".html", ""),
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
        time.sleep(2)
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
                # if success:
                #     with fetch_lock:
                #         successful_urls.add(url)
                #         write_to_csv(url, csv_file_successful)
                # return
            # Пауза в 2 секунды

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


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


def extract_phone_numbers(data):
    phone_numbers = set()
    invalid_numbers = []
    phone_pattern = re.compile(
        r"(\+40\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|00\s?40\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|011-40\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|0\d{9}|\(0\d{2}\)\s?\d{6,7}|\b\d{6,9}\b|\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b|\(\d{3}\)\s?\d{3}-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}|\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b|800\s?\d{3}[\s-]?\d{3}\b)"
    )
    for entry in data:
        entry = re.sub(r"\D", "", entry)
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
    # extract_urls_and_save_to_csv()
    get_html(max_workers=10)  # Устанавливаем количество потоков
