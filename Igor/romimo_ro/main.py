from PIL import Image, ImageEnhance, ImageFilter
import base64
from io import BytesIO
import pytesseract
import requests
import random
import csv
from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
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

# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}

# Установка директорий для логов и данных

current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = data_directory / "xml"
png_directory = data_directory / "png"
data_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
png_directory.mkdir(parents=True, exist_ok=True)

csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"

# Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Linux
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}

romania_phone_patterns = {
    "full": r"\b((?:00|40)?\d{6,9})\b",  # Номер может начинаться с '00', '40', или без кода страны
    "split": r"(40\d{6,9})",  # Номера, начинающиеся с '40', и за ними от 6 до 9 цифр
    "final": r"\b(\d{6,9})\b",  # Только от 6 до 9 цифр, если код страны отсутствует
    "codes": [40],  # Код страны для Румынии
}

cookies = {
    "ClassifiedsSessionId": "f8a573d0-00d1-4c87-a924-f402b247b91f",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'ClassifiedsSessionId=f8a573d0-00d1-4c87-a924-f402b247b91f',
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


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def extract_phone_site(parser, proxy, headers, cookies, url_id):
    proxies = {"http": proxy, "https": proxy} if proxy else None
    encryptedphone = None
    # Находим элемент с ID 'EncryptedPhone'
    element = parser.css_first("#EncryptedPhone")

    # Извлекаем значение атрибута 'value'
    if element is not None:
        encryptedphone = element.attributes.get("value")

    params = {
        "Length": "8",
    }
    data = {
        "EncryptedPhone": encryptedphone,
        "body": "",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.post(
        "https://www.romimo.ro/DetailAd/PhoneNumberImages",
        params=params,
        cookies=cookies,
        headers=headers,
        proxies=proxies,
        data=data,
    )

    # Ваша закодированная строка Base64
    base64_string = response.text

    # Декодирование строки Base64 и сохранение изображения как PNG
    decoded_data = base64.b64decode(base64_string)
    file_name_png = png_directory / f"{url_id}.png"
    with open(file_name_png, "wb") as file:
        file.write(decoded_data)

    # Открытие сохраненного изображения
    image = Image.open(file_name_png)
    # Преобразование изображения в оттенки серого
    image = image.convert("L")

    # Увеличение контрастности изображения
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)

    # Применение порогового значения для улучшения четкости текста
    image = image.point(lambda p: p > 128 and 255)

    # Использование pytesseract для извлечения текста
    extracted_text = pytesseract.image_to_string(image, config="digits")

    # Вывод извлеченных цифр
    phone = re.sub(r"\D", "", extracted_text)
    return phone


# Основная функция для загрузки и обработки карт сайта
def get_sitemap_xml():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}

    sitemap_url = "https://www.romimo.ro/Sitemaps/sitemapindex-romimo.xml"
    response = requests.get(
        sitemap_url, proxies=proxies_dict, headers=headers, cookies=cookies
    )
    response.raise_for_status()

    # Сохраняем главный XML файл
    main_xml_file_path = xml_directory / "sitemapindex-romimo.xml"
    with open(main_xml_file_path, "wb") as main_xml_file:
        main_xml_file.write(response.content)

    # Парсим главный XML
    root = ET.fromstring(response.content)
    sitemap_urls = []

    # Находим ссылки по шаблону "sitemap-romimo-articles-by-city-*"
    for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        url = sitemap.text
        if "sitemap-romimo-articles-by-city-" in url:
            sitemap_urls.append(url)

    all_urls = []

    for url in sitemap_urls:
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}

        resp = requests.get(url, proxies=proxies_dict, headers=headers, cookies=cookies)
        resp.raise_for_status()

        # Сохраняем каждый XML файл в директорию xml_directory
        file_name = url.split("/")[-1]  # Берем последнюю часть URL как имя файла
        xml_file_path = xml_directory / file_name
        with open(xml_file_path, "wb") as xml_file:
            xml_file.write(resp.content)
        logger.info(xml_file_path)
        city_sitemap_root = ET.fromstring(resp.content)

        # Извлекаем все <loc> URL внутри XML
        for loc in city_sitemap_root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        ):
            all_urls.append(loc.text)

    # Сохраняем собранные URL в CSV файл
    with open(csv_file_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["url"])
        for url in all_urls:
            csvwriter.writerow([url])

    logger.info(f"Сохранено {len(all_urls)} URL в файл {csv_file_path}")
    # Удаляем временную папку
    shutil.rmtree(xml_directory)


# Извлечение местоположения
def extract_user_info(parser):
    location = None

    # Ищем div с классом "medium-5 columns"
    div_element = parser.css_first(
        "#content > div > div.row > div > div.detail-left.radius > div.row.detail-info > div.medium-5.columns"
    )

    if not div_element:
        return ""  # Если элемент не найден, возвращаем пустую строку

    # Ищем все ссылки <a> с атрибутом itemprop="url" внутри найденного div
    links = div_element.css('a[itemprop="url"]')

    # Извлекаем текст из каждой ссылки, соединяя их через запятую
    location = ", ".join(link.text(strip=True) for link in links)

    return location


def parsing(src, url, proxy, headers, cookies, url_id):
    csv_file_path = "result.csv"
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        parser = HTMLParser(src)
        location = None
        publication_date = None
        mail_address = None
        phone_numbers = set()

        with parsing_lock:

            phones = extract_phone_site(parser, proxy, headers, cookies, url_id)
            phone_numbers.add(phones)
            if not phones:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")
            logger.info(url)

            location = extract_user_info(parser)
            # logger.info(location)
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")

            publication_date = extract_publication_date(parser)
            # logger.info(publication_date)
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

            # logger.info(f"| {url} | Номера - {phones} | Локация - {location} |")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phone_numbers:
                # for phone_number in phones:
                data = f'{phone_numbers};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                write_to_csv(data, csv_file_path)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 32  # id_site для 'https://abw.by/'

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
                        phone_numbers
                    )
                    valid_numbers = [
                        num
                        for num in phone_numbers_extracted
                        if re.match(romania_phone_patterns["final"], num)
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
        logger.error(f"Ошибка при парсинге HTML для URL {url_id}: {e}")
        return False


# Извлечение даты публикации
def extract_publication_date(parser):
    # Ищем элемент по селектору
    date_element = parser.css_first(
        '#content > div > div.row > div > div.detail-left.radius > div.row.detail-info > div.medium-7.columns.medium-text-right > i[itemprop="validFrom"]'
    )

    if date_element is None:
        return None  # Если элемент не найден, возвращаем None

    # Извлекаем текст из найденного элемента
    date_text = date_element.text(strip=True)

    # Используем регулярное выражение для поиска даты
    match = re.search(
        r"Valabil din (\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2}):(\d{2})", date_text
    )

    if not match:
        return None  # Если дата не найдена, возвращаем None

    # Извлекаем день, месяц и год из найденной даты
    day, month, year = match.group(1), match.group(2), match.group(3)

    try:
        # Преобразуем в объект datetime
        time_posted = datetime.datetime(int(year), int(month), int(day))
    except ValueError:
        return None  # Если возникает ошибка, возвращаем None

    # Проверяем, является ли time_posted объектом datetime.datetime
    if isinstance(time_posted, datetime.datetime):
        formatted_date = time_posted.strftime("%Y-%m-%d")
        return formatted_date

    return None


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
                success = parsing(src, url, proxy, headers, cookies, url_id)
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


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


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
                url.split("/")[-1].replace(".html", ""),
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")


if __name__ == "__main__":
    get_sitemap_xml()
    get_html(max_workers=10)  # Устанавливаем количество потоков
    shutil.rmtree(png_directory)
