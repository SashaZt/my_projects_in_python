import requests
from bs4 import BeautifulSoup
from threading import Lock
from configuration.logger_setup import logger
import random
from pathlib import Path
import csv
from phonenumbers import NumberParseException
from mysql.connector import errorcode
from threading import Lock
import mysql.connector
import phonenumbers
import threading
import requests
import datetime
import random
import json
import os
import re


# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}
croatian_phone_patterns = {
    "full": r"\b(385\d{8,9}|\d{8,9})\b",
    "split": r"(385\d{8,9})",
    "final": r"\b(\d{8,9})\b",
    "codes": [385],
}

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
href_directory = current_directory / "href"
data_directory.mkdir(parents=True, exist_ok=True)
href_directory.mkdir(parents=True, exist_ok=True)
csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_file_categories = data_directory / "urls_categories.csv"
cookies = {
    "__uzma": "8319a3d2-e332-4445-a1ea-7de538d8368d",
    "__uzmb": "1724935081",
    "__uzme": "5674",
    "njuskalo_privacy_policy": "12",
    "didomi_token": "eyJ1c2VyX2lkIjoiMTkxOWUyNDgtZDkwOS02ZTZhLTlmNWQtOTExZDM4YTRjMDQzIiwiY3JlYXRlZCI6IjIwMjQtMDgtMjlUMTI6Mzg6MDEuMzYwWiIsInVwZGF0ZWQiOiIyMDI0LTA4LTI5VDEyOjM4OjAyLjYyMloiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmhvdGphciIsImM6bmV3LXJlbGljIiwiYzpjb21tMTAwIiwiYzpsaXZlY2hhdCIsImM6Ym9va2l0c2gtS2I4bmJBRGgiLCJjOmNvbW0xMDB2aS13ZG1NbTRKNiIsImM6Ym9va2l0bGEtTWFSZ2dtUE4iLCJjOmRvdG1ldHJpYy1nYjJmaktDSiIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzptaWRhcy1lQm5UR1hMRiIsImM6Z29vZ2xlYW5hLTRUWG5KaWdSIiwiYzpwaWFub2h5YnItUjNWS0MycjQiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmdlbWl1c3NhLW1ja2lRYW5LIiwiYzppbnN1cmFkcy1KZ0NGNnBtWCIsImM6aG90amFyLVpMUExleFZiIiwiYzpnb29nbGVhbmEtOGlIR1JDdFUiLCJjOm9wdGltYXhtZS1OSFhlUWNDayIsImM6ZGlkb21pLW5rR2pHZHhqIiwiYzpzbWFydGFkc2UtN1dNOFhnVEYiLCJjOmNyaXRlb3NhLWdqcGNybWdCIiwiYzpnb29nbGVhZHYtWlo5ZTdZZGkiLCJjOm5qdXNrYWxvbi1BWWNOTmFpdyIsImM6Ymlkc3dpdGNoLUV0YjdMYTRSIiwiYzphZGFnaW8tRllnZjR3UkQiLCJjOm5qdXNrYWxvbi1BN2NQVmVFYSIsImM6YW1hem9uYWQtQzJ5bk5VbjkiLCJjOnlhaG9vYWRlLW1SSFFraG1VIiwiYzptZHByaW1pcy1XTVpBUm13NiIsImM6YW1hem9uLUw4NHRKUXg0IiwiYzpkaWRvbWkiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsiZGV2aWNlX2NoYXJhY3RlcmlzdGljcyIsImdlb2xvY2F0aW9uX2RhdGEiLCJvZ2xhc2l2YWNrLVE0RDlibVRHIiwiYXVkaWVuY2VtLWhKeGFlR3JSIiwiYW5hbHl0aWNzLXhHSHhHcFRMIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpib3hub3dkLTN4TmlKamZCIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==",
    "euconsent-v2": "CQEHUQAQEHUQAAHABBENBDFsAP_gAEPgAAAAKYtV_G__bWlr8X73aftkeY1P9_h77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIAu3bBIQNlGJDUTVCgaogVryDMak2coTNKJ6BkiFMRe2dYCF5vmwtj-QKY5vr991dx2B-t7dr83dzyz4VHn3a5_2a0WJCdA5-tDfv9bROb-9IOd_x8v4v8_F_rE2_eT1l_tevp7D9-cts7_XW-9_fff79Ln_-uB_--Cl4BJhoVEAZYEhIQaBhBAgBUFYQEUCAAAAEgaICAEwYFOwMAl1hIgBACgAGCAEAAKMgAQAAAQAIRABAAUCAACAQKAAMACAYCAAgYAAQASAgEAAIDoEKYEECgWACRmREKYEIQCQQEtlQgkAQIK4QhFngAQCImCgAAAAAKwABAWCwOJJASoSCBLiDaAAAgAQCCACoQScmAAIAzZag8GTaMrSANHzBIhpgGACOgAgJk.f_wACHwAAAAA",
    "df_uid": "21e6b96a-9ed5-4b80-8dc0-881dc343099d",
    "njuskalo_adblock_detected": "true",
    "PHPSESSID": "451cad51d518605334aad22aaf741cc9",
    "__uzmc": "8816656818501",
    "__uzmd": "1725194450",
}


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'nuka-fp=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; login_2fa=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; __uzma=8319a3d2-e332-4445-a1ea-7de538d8368d; __uzmb=1724935081; __uzme=5674; njuskalo_privacy_policy=12; didomi_token=eyJ1c2VyX2lkIjoiMTkxOWUyNDgtZDkwOS02ZTZhLTlmNWQtOTExZDM4YTRjMDQzIiwiY3JlYXRlZCI6IjIwMjQtMDgtMjlUMTI6Mzg6MDEuMzYwWiIsInVwZGF0ZWQiOiIyMDI0LTA4LTI5VDEyOjM4OjAyLjYyMloiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmhvdGphciIsImM6bmV3LXJlbGljIiwiYzpjb21tMTAwIiwiYzpsaXZlY2hhdCIsImM6Ym9va2l0c2gtS2I4bmJBRGgiLCJjOmNvbW0xMDB2aS13ZG1NbTRKNiIsImM6Ym9va2l0bGEtTWFSZ2dtUE4iLCJjOmRvdG1ldHJpYy1nYjJmaktDSiIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzptaWRhcy1lQm5UR1hMRiIsImM6Z29vZ2xlYW5hLTRUWG5KaWdSIiwiYzpwaWFub2h5YnItUjNWS0MycjQiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmdlbWl1c3NhLW1ja2lRYW5LIiwiYzppbnN1cmFkcy1KZ0NGNnBtWCIsImM6aG90amFyLVpMUExleFZiIiwiYzpnb29nbGVhbmEtOGlIR1JDdFUiLCJjOm9wdGltYXhtZS1OSFhlUWNDayIsImM6ZGlkb21pLW5rR2pHZHhqIiwiYzpzbWFydGFkc2UtN1dNOFhnVEYiLCJjOmNyaXRlb3NhLWdqcGNybWdCIiwiYzpnb29nbGVhZHYtWlo5ZTdZZGkiLCJjOm5qdXNrYWxvbi1BWWNOTmFpdyIsImM6Ymlkc3dpdGNoLUV0YjdMYTRSIiwiYzphZGFnaW8tRllnZjR3UkQiLCJjOm5qdXNrYWxvbi1BN2NQVmVFYSIsImM6YW1hem9uYWQtQzJ5bk5VbjkiLCJjOnlhaG9vYWRlLW1SSFFraG1VIiwiYzptZHByaW1pcy1XTVpBUm13NiIsImM6YW1hem9uLUw4NHRKUXg0IiwiYzpkaWRvbWkiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsiZGV2aWNlX2NoYXJhY3RlcmlzdGljcyIsImdlb2xvY2F0aW9uX2RhdGEiLCJvZ2xhc2l2YWNrLVE0RDlibVRHIiwiYXVkaWVuY2VtLWhKeGFlR3JSIiwiYW5hbHl0aWNzLXhHSHhHcFRMIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpib3hub3dkLTN4TmlKamZCIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==; euconsent-v2=CQEHUQAQEHUQAAHABBENBDFsAP_gAEPgAAAAKYtV_G__bWlr8X73aftkeY1P9_h77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIAu3bBIQNlGJDUTVCgaogVryDMak2coTNKJ6BkiFMRe2dYCF5vmwtj-QKY5vr991dx2B-t7dr83dzyz4VHn3a5_2a0WJCdA5-tDfv9bROb-9IOd_x8v4v8_F_rE2_eT1l_tevp7D9-cts7_XW-9_fff79Ln_-uB_--Cl4BJhoVEAZYEhIQaBhBAgBUFYQEUCAAAAEgaICAEwYFOwMAl1hIgBACgAGCAEAAKMgAQAAAQAIRABAAUCAACAQKAAMACAYCAAgYAAQASAgEAAIDoEKYEECgWACRmREKYEIQCQQEtlQgkAQIK4QhFngAQCImCgAAAAAKwABAWCwOJJASoSCBLiDaAAAgAQCCACoQScmAAIAzZag8GTaMrSANHzBIhpgGACOgAgJk.f_wACHwAAAAA; nuka-recommender-fp=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; nuka-ppid=964b08c6-ca4d-491e-8222-42ea7ec74aba; df_uid=21e6b96a-9ed5-4b80-8dc0-881dc343099d; njuskalo_adblock_detected=true; PHPSESSID=105bbf0604e7e68f677d653d7e694f5a; __uzmd=1725046535; __uzmc=6482852343457',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def load_proxies():
    file_path = "roman.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Функция для записи в CSV
def save_to_csv(urls_categories):
    with open(csv_file_categories, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for url in urls_categories:
            writer.writerow([url])
    logger.info(f"Data has been written to {csv_file_categories}")


# Функция для чтения URL категорий из CSV
def read_urls_from_csv(csv_file_path):
    urls_categories = []
    with open(csv_file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        urls_categories = [row[0] for row in reader]
    return urls_categories


def get_url(url):
    # Счетчик ошибок, чтобы отслеживать количество ошибок при запросе
    counter_error = 0

    # Логируем начало процесса получения страницы по заданному URL
    # Загрузка списка прокси из файла
    proxies = load_proxies()
    # Пока есть доступные прокси, пытаемся загрузить страницу
    while proxies:
        # Если в списке есть прокси, выбираем случайный
        if len(proxies) > 0:
            proxy = random.choice(proxies)
        else:
            # Если список прокси пуст, логируем и возвращаем None
            logger.error("Список прокси пуст")
            return None

        # Подготовка словаря прокси для передачи в запрос
        proxies_dict = {
            "http": proxy,
            "https": proxy,
        }

        try:
            # Установка заголовков, включая случайный User-Agent

            # Отправка GET-запроса на сайт
            response = requests.get(
                url=url,
                timeout=60,
                headers=headers,
                cookies=cookies,
                proxies=proxies_dict,
            )

            # Если ответ успешный (200), возвращаем HTML-код страницы
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                return soup
            elif response.status_code == 403:
                # Если сайт возвращает ошибку 403 (доступ запрещен), удаляем прокси и пробуем другой
                logger.error(
                    f'{datetime.datetime.now().strftime("%H:%M:%S")} - Код ошибки 403. Сайт нас подрезал.'
                )
                proxies.remove(proxy)
                logger.error(proxy)
                logger.error(
                    f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}'
                )
                counter_error += 1
                # Если количество ошибок достигает 10, логируем и возвращаем None
                if counter_error == 10:
                    logger.error(
                        f'{datetime.datetime.now().strftime("%H:%M:%S")} - Перезапуск, нас подрезали.'
                    )
                    return None
            else:
                # Если произошла другая ошибка (например, 404), возвращаем None
                return None
        except requests.exceptions.TooManyRedirects:
            # Обработка случая, когда превышено количество редиректов
            logger.error("Произошла ошибка: Exceeded 30 redirects. Пропуск.")
            return "Редирект"
        except (requests.exceptions.ProxyError, requests.exceptions.Timeout):
            # Обработка ошибок прокси или тайм-аута, удаляем текущий прокси и пробуем следующий
            proxies.remove(proxy)
            logger.error(proxy)
            logger.error(
                f'{datetime.datetime.now().strftime("%H:%M:%S")} - Осталось прокси {len(proxies)}'
            )
        except Exception as e:
            # Обработка любых других исключений и продолжение работы с другим прокси
            logger.error(f"Произошла ошибка: {e}")
            continue

    # Если все прокси испробованы и не удалось получить HTML, возвращаем None
    return None


def collect_links_by_category(url, pages, lock, page_file):
    # Открываем файл для записи ссылок
    with open(page_file, "w", encoding="utf-8") as f:
        # Проходим по всем страницам от 1 до pages
        for page in range(1, pages + 1):
            # Формируем URL для текущей страницы
            page_url = f"{url}?page={page}"
            logger.info(
                f'{datetime.datetime.now().strftime("%H:%M:%S")} - Обрабатывается страница {page_url}.'
            )

            # Получаем HTML-код страницы
            with lock:
                soup = get_url(url=page_url)

            # Проверяем, загрузилась ли страница корректно
            if soup is None:
                logger.info(
                    f'{datetime.datetime.now().strftime("%H:%M:%S")} - Не удалось загрузить страницу {page_url}.'
                )
                break

            # Поиск списка элементов на странице
            entity_list = soup.find("ul", {"class": "EntityList-items"})
            if not entity_list:
                logger.info(
                    f'{datetime.datetime.now().strftime("%H:%M:%S")} - Не удалось найти список объявлений на странице {page_url}.'
                )
                break

            # Поиск всех заголовков объявлений внутри списка
            titles = entity_list.find_all("h3", {"class": "entity-title"})
            if not titles:
                logger.info(
                    f'{datetime.datetime.now().strftime("%H:%M:%S")} - Объявления не найдены на странице {page_url}.'
                )
                break

            # Извлечение всех ссылок и запись их в файл
            for title in titles:
                link = title.find("a", href=True)
                if link:
                    href = f'https://www.njuskalo.hr{link["href"]}'
                    f.write(href + "\n")
                    # Получаем HTML-код страницы товара
                    product_soup = get_url(href)

                    # Проверяем, загрузилась ли страница товара корректно
                    if product_soup is not None:
                        # Передаем HTML-код страницы товара в функцию для его разбора
                        parsing(product_soup, href)
                    else:
                        logger.info(
                            f'{datetime.datetime.now().strftime("%H:%M:%S")} - Не удалось загрузить страницу товара {href}.'
                        )


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


def extract_phone_site(soup):
    try:
        # Поиск элемента <script> по его селектору
        script_tag = soup.select_one(
            "body > div.wrap-main > div.wrap-content.ClassifiedDetail.cf > main > article > div.content-primary > div > div.content-main > div.ClassifiedDetailOwnerDetailsWrap--positionPrimary > div > div.ClassifiedDetailOwnerDetails > div.ClassifiedDetailOwnerDetails-col.ClassifiedDetailOwnerDetails-col--content > script"
        )
        if not script_tag:
            logger.error("Не удалось найти элемент <script> с нужным контентом.")
            return None

        # Извлечение текста из <script>
        script_content = script_tag.string.strip()

        # Удаление app.boot.push( в начале и ); в конце
        if script_content.startswith("app.boot.push(") and script_content.endswith(
            ");"
        ):
            json_str = script_content[len("app.boot.push(") : -2]
        else:
            logger.error("Строка не соответствует ожидаемому формату.")
            return None

        # Преобразование строки в JSON объект
        json_obj = json.loads(json_str)

        # Извлечение необходимых значений
        country_code = json_obj["values"]["phones"][0]["countryCode"]
        area_code = json_obj["values"]["phones"][0]["areaCode"]
        number = json_obj["values"]["phones"][0]["number"]

        # Формирование полного телефонного номера
        full_phone_number = f"{country_code}{area_code}{number}"
        return full_phone_number

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Ошибка при обработке JSON или при доступе к данным: {e}")
        return None


def extract_location_and_date(soup):
    location_text = None
    publication_date = None
    try:
        # Извлечение локации
        location_tag = soup.select_one(
            "body > div.wrap-main > div.wrap-content.ClassifiedDetail.cf > main > article > div.content-aside > div:nth-child(1) > div > div > div.ClassifiedDetailOwnerDetails > div.ClassifiedDetailOwnerDetails-col.ClassifiedDetailOwnerDetails-col--content > ul > li:nth-child(1)"
        )
        location_text = location_tag.get_text(strip=True) if location_tag else None
        if location_text is not None:
            location_text = location_text.replace("Adresa:", "").strip()

        # Извлечение даты публикации
        publication_date_tag = soup.select_one(
            "dl.ClassifiedDetailSystemDetails-list.cf > dd.ClassifiedDetailSystemDetails-listData"
        )
        if publication_date_tag:
            publication_date_text = publication_date_tag.get_text(strip=True)

            # Преобразуем текст даты в объект datetime
            time_posted = datetime.datetime.strptime(
                publication_date_text, "%d.%m.%Y. u %H:%M"
            )

            # Форматируем дату в нужный формат
            publication_date = time_posted.strftime("%Y-%m-%d")
        else:
            publication_date = None

        return location_text, publication_date

    except Exception as e:
        print(f"Ошибка при извлечении данных: {e}")
        return None, None


def parsing(soup, url):
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        location = None
        publication_date = None
        mail_address = None
        phone_number = None

        with parsing_lock:

            phones = extract_phone_site(soup)
            phone_numbers = set()
            phone_numbers.add(phones)
            location, publication_date = extract_location_and_date(soup)
            logger.info(f"{phones} | {location} | {phone_numbers}")
            if not phones:
                logger.warning(f"Не удалось извлечь номера телефонов для URL: {url}")
            if not location:
                logger.warning(f"Не удалось извлечь местоположение для URL: {url}")
            if not publication_date:
                logger.warning(f"Не удалось извлечь дату публикации для URL: {url}")

            data = f'{None};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
            if location and publication_date and phones:
                for phone_number in phones:
                    data = f'{phone_number};{location};{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")};{url};{mail_address};{publication_date}'
                    write_to_csv(data, csv_file_path)

            # Разбиваем строку на переменные
            _, location, timestamp, link, mail_address, time_posted = data.split(";")
            date_part, time_part = timestamp.split(" ")

            # Параметры для вставки в таблицу
            site_id = 31  # id_site для 'https://abw.by/'

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
                        if re.match(croatian_phone_patterns["final"], num)
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
                write_to_csv(url, csv_file_successful)
                return True
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML для URL : {e}")
        return False


def extract_phone_numbers(data):
    phone_numbers = set()
    invalid_numbers = []
    # phone_pattern = re.compile(
    #     r"(\+40\d{9}|00\s?40\d{9}|011-40\d{9}|0\d{9}|\(0\d{2}\)\s?\d{6,7}|\b\d{6,9}\b|\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b|\(\d{3}\)\s?\d{3}-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}|\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b)"
    # )
    phone_pattern = re.compile(
        r"(\+385\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|00\s?385\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|011-385\s?\d{3}[\s-]?\d{3}[\s-]?\d{3}|0\d{8,9}|\(0\d{2}\)\s?\d{6,7}|\b\d{6,9}\b|\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b|\(\d{3}\)\s?\d{3}-\d{3}|\b\d[\d\s\(\)\-]{6,}\b|\d{3}[^0-9a-zA-Z]*\d{3}[^0-9a-zA-Z]*\d{3}|\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b|800\s?\d{3}[\s-]?\d{3}\b)"
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
                    parsed_number = phonenumbers.parse(match, "HR")
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


# Основная функция, которая обрабатывает URL в отдельном потоке
def main_thread(url, thread_id, lock):
    url_id = url.split("/")[-1]
    page_file = href_directory / f"{url_id}.csv"
    # Получаем HTML-код страницы категории
    with lock:
        soup = get_url(url=url)

    # Находим элемент, содержащий количество объявлений
    entity_meta = soup.find("div", {"class": "entity-list-meta"})
    if not entity_meta:
        logger.error(
            f"Не удалось найти div с классом 'entity-list-meta' для URL: {url}"
        )
        return

    # Извлекаем количество объявлений
    count_str = entity_meta.find("strong", {"class": "entities-count"}).text
    try:
        count = int(count_str)
    except ValueError:
        logger.error(
            f"Не удалось преобразовать количество объявлений в целое число: {count_str}"
        )
        return

    # Рассчитываем количество страниц
    pages = count // 25 if count > 10000 else (count // 25) + 1
    logger.info(f"Calculated Pages for URL {url}: {pages}")
    # Запускаем функцию для сбора ссылок по всем страницам категории
    collect_links_by_category(url, pages, lock, page_file)


def main():
    # Открываем файл csv_file_categories в режиме чтения, считываем его содержимое и разбиваем на строки.
    urls = open(csv_file_categories, "r", encoding="utf-8").read().splitlines()

    # Инициализируем пустой список для хранения потоков.
    threads = []

    # Создаем объект Lock для синхронизации потоков.
    lock = Lock()

    # Проходим по всем URL-ам из файла.
    for i, url in enumerate(urls):
        # Создаем новый поток, который будет выполнять функцию main_thread с аргументами: URL, индекс и объект lock.
        thread = threading.Thread(target=main_thread, args=(url, i, lock))

        # Добавляем созданный поток в список threads.
        threads.append(thread)

        # Запускаем выполнение потока.
        thread.start()

    # Ожидаем завершения работы всех потоков.
    for thread in threads:
        # Вызываем метод join, чтобы основной поток ожидал завершения каждого потока в списке threads.
        thread.join()


# Эта часть кода проверяет, является ли текущий скрипт основным модулем, и если да, то запускает функцию main().
if __name__ == "__main__":
    main()


# Получаем категории
# urls_categories = fetch_category_urls()
# logger.info("Categories URLs:", urls_categories)
# save_to_csv(urls_categories)
# Получаем данные пагинации для каждой категории
# fetch_pagination_details()
# logger.info("Pagination Details:", pagination_details)
# r_c()
