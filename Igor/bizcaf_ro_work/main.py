import requests
import random
import csv
from pathlib import Path
from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
import ssl
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from pathlib import Path
import mysql.connector
import phonenumbers
import threading
import datetime
import csv
import re
from phonenumbers import PhoneNumberMatcher, NumberParseException


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
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

# Файлы для записи и проверки URL
csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = current_directory / "result.csv"

cookies = {
    "PHPSESSID": "6sriqfh8gtur218g3pm8m1d7j0",
    "temp_uid": "5f6def73f858a0422c4ca84838e237a0",
    "uui_req": "54115114105",
    "lang": "fr",
    "UI": "_",
    "FavStatus": "open_0",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': 'PHPSESSID=6sriqfh8gtur218g3pm8m1d7j0; temp_uid=5f6def73f858a0422c4ca84838e237a0; uui_req=54115114105; lang=fr; UI=_; FavStatus=open_0',
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


class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)


def create_session_with_ssl():
    """Создает сессию с пониженным уровнем безопасности SSL."""
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")
    session = requests.Session()
    adapter = SSLAdapter(ssl_context=ssl_context)
    session.mount("https://", adapter)
    return session


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_total_pages(session, proxies):
    """Определяет общее количество страниц с объявлениями на сайте."""
    url = "https://www.bizcaf.ro/"
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        response = session.get(
            url, headers=headers, cookies=cookies, proxies=proxies_dict, timeout=10
        )
        if response.status_code == 200:
            tree = HTMLParser(response.text)

            # Извлечение количества объявлений
            total_ads_text = tree.css_first(
                "#main_content1 > div > div.links > table > tbody > tr:nth-child(1) > td > table > tbody > tr > td:nth-child(1)"
            ).text()
            total_ads = int(
                total_ads_text.split("din")[1]
                .split("anunturi")[0]
                .strip()
                .replace(".", "")
            )

            # Вычисление количества страниц
            ads_per_page = 24
            total_pages = (total_ads // ads_per_page) + (
                1 if total_ads % ads_per_page > 0 else 0
            )
            logger.info(f"Найдено {total_ads} объявлений на {total_pages} страницах.")
            return total_pages
        else:
            logger.error(f"Ошибка: статус код {response.status_code}")
            return 0

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении количества страниц: {e}")
        return 0


def collect_urls_from_page(page_num, proxies, session):
    """Функция для сбора URL с одной страницы."""
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    url = f"https://www.bizcaf.ro/anunturi/?pg={page_num}"
    try:
        response = session.get(url, headers=headers, proxies=proxies_dict, timeout=10)
        if response.status_code == 200:
            tree = HTMLParser(response.text)

            # Используем CSS-селектор для поиска всех элементов <tr> с атрибутом itemprop="itemListElement"
            tr_elements = tree.css('tr[itemprop="itemListElement"]')

            urls = []
            for tr in tr_elements:
                # Внутри каждого <tr> ищем ссылку с атрибутом itemprop="url"
                a_element = tr.css_first('a[itemprop="url"]')
                if a_element:
                    urls.append(a_element.attributes["href"])

            return urls
        else:
            logger.error(
                f"Ошибка: статус код {response.status_code} на странице {page_num}"
            )
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обработке страницы {page_num}: {e}")
        return []


def collect_urls(total_pages):
    """Проходит по страницам и собирает URL-адреса объявлений, записывая их в CSV файл с использованием многопоточности."""
    proxies = load_proxies()
    session = create_session_with_ssl()

    # Загружаем успешные URL из csv_file_successful
    successful_urls = set()
    if csv_file_successful.exists():
        with open(csv_file_successful, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            successful_urls = {row[0] for row in reader}

    # Проверяем, существует ли файл и не пуст ли он, чтобы добавить заголовок
    file_exists = csv_file_path.exists()
    file_is_empty = csv_file_path.stat().st_size == 0 if file_exists else True

    with csv_file_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Добавляем заголовок, если файл пуст
        if file_is_empty:
            writer.writerow(["url"])

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_page = {
                executor.submit(
                    collect_urls_from_page, page_num, proxies, session
                ): page_num
                for page_num in range(1, total_pages + 1)
            }
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    urls = future.result()
                    for ad_url in urls:
                        if ad_url in successful_urls:
                            logger.info(
                                f"URL {ad_url} уже был успешно обработан. Прекращение сбора."
                            )
                            return
                        else:
                            writer.writerow([ad_url])
                            logger.info(f"URL {ad_url} добавлен в файл.")
                except Exception as exc:
                    logger.error(f"Ошибка при обработке страницы {page_num}: {exc}")


"""_________________________________________________________________________________________________"""


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


# Извлечение местоположения
def extract_user_info(parser):
    location = None
    # Извлечение местоположения
    location_row = parser.css_first(
        "div > div > div.detail-content-cover.detail-content-cover--border > div.card-wrapper.card-wrapper__white.cover-desktop-aside > div.vin"
    )

    if location_row:
        location = location_row.text(strip=True).replace("VIN", "")

    return location


def extract_publication_date(parser):
    # Находим элемент с классом 'detail-user'
    detail_user_element = parser.css_first("span.detail-user")

    if detail_user_element:
        # Извлекаем текст элемента
        text = detail_user_element.text(strip=True)

        # Ищем дату с помощью регулярного выражения
        date_match = re.search(r"(\d{2}) (\w+) (\d{4})", text)

        if date_match:
            day, month_str, year = date_match.groups()

            # Сопоставляем месяцы на румынском языке с их числовыми значениями
            months = {
                "ianuarie": 1,
                "februarie": 2,
                "martie": 3,
                "aprilie": 4,
                "mai": 5,
                "iunie": 6,
                "iulie": 7,
                "august": 8,
                "septembrie": 9,
                "octombrie": 10,
                "noiembrie": 11,
                "decembrie": 12,
            }
            month = months.get(month_str.lower(), 0)  # Если не найден месяц, вернется 0

            try:
                # Преобразуем в объект datetime
                time_posted = datetime.datetime(int(year), month, int(day))

                # Проверяем, является ли time_posted объектом datetime.datetime
                if isinstance(time_posted, datetime.datetime):
                    formatted_date = time_posted.strftime("%Y-%m-%d")
                    return formatted_date
            except ValueError:
                return ""  # Если возникает ошибка, возвращаем пустую строку

    # Возвращаем None, если дата не найдена или не распарсилась
    return None


def extract_phone_numbers(data):
    phone_numbers = set()
    invalid_numbers = []

    # Обрабатываем каждый элемент из списка data
    for entry in data:
        # Используем PhoneNumberMatcher для поиска номеров в тексте
        for match in PhoneNumberMatcher(entry, "RO"):  # Обрабатываем румынские номера
            try:
                parsed_number = phonenumbers.parse(match.raw_string, "RO")
                if phonenumbers.is_valid_number(parsed_number):
                    # Извлекаем национально значимый номер (только цифры)
                    clean_number = phonenumbers.national_significant_number(
                        parsed_number
                    )
                    phone_numbers.add(clean_number)
                else:
                    invalid_numbers.append(match.raw_string)
            except NumberParseException:
                invalid_numbers.append(match.raw_string)

    return phone_numbers, invalid_numbers


def parsing(src, url):
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        parser = HTMLParser(src)
        location = None
        publication_date = None
        mail_address = None
        phone_number = None

        with parsing_lock:

            phones, location = extract_phone_site_and_location(parser)
            phone_numbers = set()
            phone_numbers.add(phones)
            logger.info(phones)
            if not phones:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")
            publication_date = extract_publication_date(parser)
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phone_numbers:
                for phone_number in phone_numbers:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_result)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 28  # id_site для 'https://abw.by/'

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
                    logger.error("Ошибка доступа: Неверное имя пользователя или пароль")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    logger.error("Ошибка базы данных: База данных не существует")
                else:
                    logger.error(err)
                return False
            finally:
                cursor.close()
                cnx.close()
                logger.info("Соединение с базой данных закрыто.")
                return True
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML для URL : {e}")
        return False


def fetch_url(url, proxies, headers, csv_file_successful, successful_urls, session):
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
            response = session.get(
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


def extract_phone_site_and_location(parser):
    # Инициализируем переменные для хранения результатов
    phone_number = None
    location = None

    # Находим все элементы с классом 'feature' внутри 'td.rightbox'
    feature_elements = parser.css("td.rightbox .feature")

    for feature in feature_elements:
        # Проверяем, содержит ли элемент текст "Telefon:"
        if "Telefon:" in feature.text(strip=True):
            phone_element = feature.css_first("div#cell_t_int_bizcaf b")
            if phone_element:
                # Извлекаем весь текст из элемента <b>
                full_text = phone_element.html  # Это вернет весь HTML элемента <b>

                # Извлекаем текст до тега <simbiz>
                raw_phone = re.split(r"<simbiz>", full_text)[
                    0
                ].strip()  # Текст до <simbiz>
                logger.info(f"Основная часть телефона: {raw_phone}")

                # Извлекаем текст внутри тега <simbiz>
                simb_element = phone_element.css_first("simbiz")
                if simb_element:
                    simb_text = simb_element.text(strip=True)

                    # Проверяем, больше ли 4 цифр в simb_text, и удаляем первую цифру, если нужно
                    if len(simb_text) > 4:
                        simb_text = simb_text[1:]  # Удаляем первую цифру
                    logger.info(f"Часть телефона из <simbiz>: {simb_text}")

                    # Объединяем основную часть и текст внутри <simbiz>
                    full_phone = raw_phone + simb_text
                else:
                    full_phone = raw_phone

                # Удаляем все нецифровые символы для получения финального номера
                phone_number = re.sub(r"\D", "", full_phone)
                logger.info(f"Полный номер телефона: {phone_number}")

        # Проверяем, содержит ли элемент текст "Localitate:"
        if "Localitate:" in feature.text(strip=True):
            location_element = feature.css_first("b")
            if location_element:
                location = location_element.text(strip=True)

        # Проверяем, содержит ли элемент текст "Zona/amplasament:"
        if "Zona/amplasament:" in feature.text(strip=True):
            zone_element = feature.css_first("b")
            if zone_element:
                location += ", " + zone_element.text(strip=True)

    # Возвращаем номер телефона и местоположение
    return phone_number, location


def get_html(max_workers=10, session=None):
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
                csv_file_successful,
                successful_urls,
                session,
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")


if __name__ == "__main__":
    session = create_session_with_ssl()
    # total_pages = get_total_pages(session, load_proxies())
    # collect_urls(total_pages)
    get_html(max_workers=10, session=session)
