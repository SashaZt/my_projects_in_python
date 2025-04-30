# Рабочий код с использованеим прокси.
import concurrent.futures
import hashlib
import json
import os
import queue
import random
import re
import threading
import time
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from requests.exceptions import ConnectTimeout, HTTPError, ProxyError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)

config_file = config_directory / "config.json"

# Глобальная переменная для хранения прокси-серверов
proxy_list = []


def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)

                # Проверяем формат данных в config.json
                if "proxy_server" in config and isinstance(
                    config["proxy_server"], list
                ):
                    proxy_list = config["proxy_server"]
                    logger.info(
                        f"Загружено {len(proxy_list)} прокси-серверов из config.json"
                    )
                else:
                    logger.warning("В config.json отсутствует список прокси-серверов")
        else:
            logger.warning("Файл config.json не найден")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации прокси: {str(e)}")


def get_random_proxy():
    """
    Возвращает случайный прокси из списка
    """
    if not proxy_list:
        return None

    proxy_url = random.choice(proxy_list)
    # Удаляем лишние пробелы в URL прокси (если они есть)
    proxy_url = proxy_url.strip()

    return {"http": proxy_url, "https": proxy_url}


@retry(
    stop=stop_after_attempt(10),  # Максимум 10 попыток
    wait=wait_fixed(10),  # Задержка 10 секунд между попытками
    retry=retry_if_exception_type(
        (HTTPError, ProxyError, ConnectTimeout)
    ),  # Повторять при указанных ошибках
)
def make_request(url, headers=None, cookies=None):
    """
    Выполняет HTTP-запрос с автоматическими повторными попытками при ошибках,
    используя случайный прокси-сервер из списка.

    Args:
        url (str): URL для запроса
        headers (dict): Заголовки запроса
        cookies (dict): Cookies для запроса

    Returns:
        str: HTML-содержимое страницы

    Raises:
        HTTPError: Если статус ответа не 200
    """
    # Получаем случайный прокси
    proxies = get_random_proxy()

    try:
        if proxies:
            response = requests.get(
                url,
                headers=headers or {},
                cookies=cookies or {},
                proxies=proxies,
                timeout=30,
            )
        else:
            response = requests.get(
                url, headers=headers or {}, cookies=cookies or {}, timeout=30
            )

        response.raise_for_status()  # Вызывает HTTPError, если статус не 200
        return response.text

    except (ProxyError, ConnectTimeout) as e:
        logger.warning(f"Ошибка прокси: {str(e)}. Попробуем другой прокси.")
        # Попытаемся исключить проблемный прокси из списка
        if proxies and proxies["http"] in proxy_list:
            proxy_list.remove(proxies["http"])
            logger.info(
                f"Прокси {proxies['http']} удален из списка. Осталось {len(proxy_list)} прокси."
            )

        # Вызываем исключение, чтобы сработал retry
        raise

    except Exception as e:
        logger.error(f"Ошибка при запросе к {url}: {str(e)}")
        raise


cookies = {
    "__uzma": "c711b6ea-749f-4089-8b2a-b0911d6b8378",
    "__uzmb": "1745774743",
    "__uzme": "0350",
    "totp": "1745777444628.rWQ4rsQTOcn3J/4qtLOHSohczYE9gHbkUP2YdLCira6WuiRHe/cpqffaGtoL+Z3xBldDEBr6GD/aLR3khBudrw==.FsWOPAFQ8gZCpoviBh8GEiMWoZiT9ni1fy59Lis9mYI",
    "_tk": "AQAIAAAAcF2JP5oOOoTwFCjIEzTdFEzvwgocWumeeujUa208uV3MZDw91oGkP6ViB25nR5juJayADFA5B3Q1xdFmqRydjD2TI0RKkJHzfZznvSH6iOPPGHP9LfR7IWYii50cwp0TqcNtv0AU9VQn4auYGqS+n5o=",
    "__deba": "2zgDZoXJokGngAdo3OEADht4gp7R5qVyEimR4VmyuErTPrlh8SVw389_7KVXBGqwXR8UW1J2_XMwSXzXGqPFGFdSrLwt58hVpgGQstyYniB1OaRkL0feJg8xwIr4ZQYI_vTiJUMy932QByWJCX0d5w==",
    "s": "CgADuAEpoEpWPMTQGaHR0cHM6Ly93d3cuZWJheS5jb20vYi9DYXItVHJ1Y2stRnVzZXMtRnVzZS1Cb3hlcy8yNjIyMjEvYm5fNzExNzg4MzE3NwcA+AAgaBKQ4zcyNmE2OTI2MTk2MGE1NDhjMjg1NmQwMGZmYjZjMGFlQNjDuQ**",
    "__uzmc": "713583174759",
    "__uzmd": "1745994389",
    "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736318423215402-54c77452207b1f75436",
    "ebay": "%5Ejs%3D1%5Esbf%3D%23000000%5E",
    "ak_bmsc": "C0865B860ABF1DDA5B7269141802C4CF~000000000000000000000000000000~YAAQbEx1aA+RsWuWAQAAPfPEhRvfIFq97oHe1R4nGr7mtiWuvA4mNmCkO0/7ISYvODouEqO0XFsyKXEoVnKg9n7Kpmjw0VI+Ar1O822/ktCJSx7mePh0w5ywkpElq/nAudDUxzZALEvz4grrShl1Ds47cRkloJ7yuqKH2NeOSfnf1BUAN0QzcfA1+Beq19QIdhBMT2riflg0Lgdoq49PlKLSU1kzO6FXZXndbnZwQnxHtv0pLV1iGkQzbqLMpMru2OkYC4ZjYAaclXotVO2Jx7tjbxKL4KfZoNb7iKqBMkW8My1GSI5wMW4/UhPxUmczyG6R7rlGZ1iEk2d7ZlrFeX2xPm58uZ1kMIRH8rnoZCZp8rOrMOidQ/muoRh21MUPWeSClyAFda4=",
    "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bd4436b^kms/in6bd4436b^pbf/%230000e400e0000000800000000069f30feb^u1f/Bohdan6bd4436b^bl/DEen-US6bd4436b^",
    "nonsession": "BAQAAAZZay1gcAAaAADMABGnzD+ssUE9MAMoAIGvUQ2s3MjZhNjkyNjE5NjBhNTQ4YzI4NTZkMDBmZmI2YzBhZQDLAAFoEeNzM+s2KyHGjaOFPujnLifFPr1XOybo",
    "bm_sv": "63B83F5869A34CC98139B5DD42C72A53~YAAQbEx1aBOSsWuWAQAAfAXFhRtdhzpNoO9uuAF7Ez44BdhpLUu9ZhYaJbbauuFNjfjtcWKClhC4IdrWU2xIpYt58CsgiLLRJHRBAvMRSLzOyS/iiyssGe07OXAP1GPAk7M551EwuMZvQiq2QftxPBS0/WABeDpyWuNEeHyWCoBjg/HGwtxkk0dyco9S59Vi5Mvm8LfhBcFcRIeYZnEcJ6oy1hv+2jlFX0crfYP3Gk+2Y9qRbB9dCk70o+oRhA==~1",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-full-version": '"135.0.7049.115"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"19.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}


def get_pagination(max_pages=None):
    """
    Функция для сбора ссылок с пагинацией с заданным максимальным количеством страниц

    Args:
        max_pages (int, optional): Максимальное количество страниц для обхода.
                                  None означает без ограничений.

    Returns:
        list: Список собранных ссылок
    """
    # Загружаем прокси в начале работы
    load_proxies()

    # Список для хранения всех href
    all_hrefs = []

    # Базовый URL
    url = "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?rt=nc&mag=1&Items%2520Included=ABS%2520Pump"

    def scrape_page(url, current_page):
        try:
            logger.info(f"Обработка страницы {current_page} по URL: {url}")

            # Используем функцию make_request с retry декоратором
            src = make_request(url, headers=headers)  # , cookies=cookies
            soup = BeautifulSoup(src, "lxml")

            # Локальный список для хранения ссылок текущей страницы
            page_hrefs = []

            # Ищем структурированные данные JSON-LD
            json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

            # Обрабатываем каждый блок JSON-LD
            for script in json_ld_scripts:
                try:
                    # Извлекаем JSON-данные из тега script
                    if script.string and script.string.strip():
                        json_data = json.loads(script.string)

                        # Проверяем, есть ли данные о товарах
                        if (
                            "about" in json_data
                            and "offers" in json_data["about"]
                            and "itemOffered" in json_data["about"]["offers"]
                        ):
                            # Извлекаем список товаров
                            items = json_data["about"]["offers"]["itemOffered"]

                            # Перебираем товары и извлекаем URL
                            for item in items:
                                if "url" in item:
                                    # Очищаем URL от параметров отслеживания, если необходимо
                                    item_url = item["url"]
                                    if "?" in item_url:
                                        base_url = item_url.split("?")[0]
                                        page_hrefs.append(base_url)
                                    else:
                                        page_hrefs.append(item_url)
                except json.JSONDecodeError:
                    logger.warning("Не удалось разобрать JSON-LD")
                    continue
                except Exception as e:
                    logger.warning(f"Ошибка при обработке JSON-LD: {str(e)}")
                    continue

            # Если из JSON-LD не удалось получить товары, пробуем обычные способы
            if not page_hrefs:
                # Ищем основной блок с товарами
                main_section = soup.find("section", {"class": "brw-river"})

                if main_section:
                    # Пробуем разные селекторы для поиска ссылок на товары
                    items = []

                    # Стратегия 1: Стандартные ссылки товаров
                    items = main_section.select("a.s-item__link")

                    # Стратегия 2: Ссылки в информационных блоках
                    if not items:
                        items = main_section.select("div.s-item__info a")

                    # Стратегия 3: Ссылки в карточках товаров
                    if not items:
                        items = main_section.select(
                            "li.brwrvr__item-card a.bsig__title__wrapper"
                        )

                    # Стратегия 4: Поиск span с классом bsig__title и получение родительской ссылки
                    if not items:
                        title_spans = main_section.select("span.bsig__title")
                        items = [
                            span.parent
                            for span in title_spans
                            if span.parent.name == "a"
                        ]

                    # Собираем все найденные ссылки
                    for item in items:
                        if "href" in item.attrs:
                            page_hrefs.append(item["href"])

            # Добавляем найденные ссылки в общий список
            all_hrefs.extend(page_hrefs)
            logger.info(f"На странице {current_page} найдено {len(page_hrefs)} ссылок")

            # Проверяем наличие следующей страницы
            next_url = find_next_page(soup, url, current_page)

            # Возвращаем следующий URL и флаг успешности
            return next_url, True

        except Exception as e:
            logger.error(f"Ошибка при обработке {url}: {str(e)}")
            return None, False

    def find_next_page(soup, current_url, current_page):
        """
        Находит URL следующей страницы пагинации

        Args:
            soup (BeautifulSoup): Объект BeautifulSoup с содержимым текущей страницы
            current_url (str): URL текущей страницы
            current_page (int): Номер текущей страницы

        Returns:
            str or None: URL следующей страницы или None, если следующей страницы нет
        """
        # 1. Стандартная кнопка перехода на следующую страницу
        next_button = soup.select_one("a.pagination__next")

        # Проверяем, что кнопка существует, имеет атрибут href и не отключена
        if next_button and "href" in next_button.attrs:
            disabled_next = soup.select_one('a.pagination__next[aria-disabled="true"]')

            if not disabled_next:
                next_url = next_button["href"]
                logger.info(f"Найдена ссылка на следующую страницу: {next_url}")
                return next_url

        # 2. Если на странице 167 не найдена кнопка, ищем прямую ссылку на страницу 168
        if current_page == 167:
            # Ищем все ссылки пагинации
            pagination_links = soup.select("a.pagination__item")

            for link in pagination_links:
                try:
                    # Проверяем, есть ли это ссылка на страницу 168
                    if link.text.strip() == "168" and "href" in link.attrs:
                        next_url = link["href"]
                        logger.info(
                            f"Найдена прямая ссылка на страницу 168: {next_url}"
                        )
                        return next_url
                except Exception:
                    continue

            # Если не нашли прямую ссылку, создаем ее программно

            logger.info("Создаем программно ссылку на страницу 168")

            # Разбираем текущий URL
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            # Устанавливаем параметр _pgn=168
            query_params["_pgn"] = ["168"]

            # Собираем URL заново
            new_query = urlencode(query_params, doseq=True)
            next_url = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment,
                )
            )

            logger.info(f"Программно создана ссылка на страницу 168: {next_url}")
            return next_url

        # Не найдена ссылка на следующую страницу
        logger.info("Ссылка на следующую страницу не найдена")
        return None

    # Начинаем с первой страницы
    current_url = url
    page_count = 1
    consecutive_failures = 0
    max_failures = 3

    while current_url:
        # Проверяем ограничение по максимальному количеству страниц
        if max_pages is not None and page_count > max_pages:
            logger.info(f"Достигнуто максимальное количество страниц ({max_pages})")
            break

        # Обрабатываем текущую страницу
        next_url, success = scrape_page(current_url, page_count)

        # Отслеживаем последовательные неудачи
        if not success:
            consecutive_failures += 1
            logger.warning(f"Неудачная попытка {consecutive_failures}/{max_failures}")

            if consecutive_failures >= max_failures:
                logger.error(
                    "Превышено максимальное число последовательных неудач. Останавливаем скрапинг."
                )
                break
        else:
            consecutive_failures = 0

        # Сохраняем промежуточные результаты каждые 10 страниц
        if page_count % 10 == 0:
            temp_df = pd.DataFrame(all_hrefs, columns=["href"])
            file_name_temp = f"all_urls_page_{page_count}.csv"
            output_temp_csv_path = data_directory / file_name_temp
            temp_df.to_csv(output_temp_csv_path, index=False)
            logger.info(
                f"Промежуточное сохранение: {len(all_hrefs)} ссылок в all_urls_page_{page_count}.csv"
            )

        # Переходим на следующую страницу, если она есть
        if next_url:
            current_url = next_url
            page_count += 1

            # Пауза между запросами с небольшой рандомизацией
            delay = random.uniform(2.0, 4.0)

            # Для страницы 167 увеличиваем задержку
            if page_count == 168:  # После перехода с 167 на 168
                delay = random.uniform(5.0, 10.0)
                logger.info(
                    f"Увеличенная пауза для критической страницы: {delay:.2f} сек"
                )
            else:
                logger.info(f"Пауза перед следующим запросом: {delay:.2f} сек")

            time.sleep(delay)
        else:
            logger.info("Следующая страница не найдена, завершаем обход")
            break

    file_name = "all_urls.csv"
    output_csv_path = data_directory / file_name
    # Сохраняем в CSV с помощью pandas
    df = pd.DataFrame(all_hrefs, columns=["href"])
    df.to_csv(output_csv_path, index=False)

    logger.info(f"Собрано {len(all_hrefs)} ссылок и сохранено в all_urls.csv")
    return all_hrefs


# def get_pagination_th(threads=10):
#     """
#     Функция для сбора всех ссылок на товары с использованием многопоточности.

#     Args:
#         threads (int): Количество потоков для параллельной обработки страниц пагинации

#     Returns:
#         list: Список всех собранных URL товаров
#     """

#     # Заголовки из curl-запроса
#     headers = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "accept-language": "ru,en;q=0.9,uk;q=0.8",
#         "dnt": "1",
#         "priority": "u=0, i",
#         "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
#         "sec-ch-ua-full-version": '"135.0.7049.96"',
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-model": '""',
#         "sec-ch-ua-platform": '"Windows"',
#         "sec-ch-ua-platform-version": '"19.0.0"',
#         "sec-fetch-dest": "document",
#         "sec-fetch-mode": "navigate",
#         "sec-fetch-site": "same-origin",
#         "sec-fetch-user": "?1",
#         "upgrade-insecure-requests": "1",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
#     }

#     # Куки из curl-запроса (упрощённые, возможно, потребуется их обновить)
#     cookies = {
#         "__uzma": "97357116-b531-48ea-a787-9a1cdbc0d2a3",
#         "__uzmb": "1737571173",
#         "__uzme": "0889",
#         "__ssds": "2",
#         "__ssuzjsr2": "a9be0cd8e",
#         "__uzmaj2": "f52997a6-1322-426e-8b54-c2c2eac61cf7",
#         "__uzmbj2": "1737571182",
#     }

#     # Базовый URL
#     base_url = "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?Items%2520Included=ABS%2520Accumulator&mag=1&rt=nc"

#     # Список для хранения всех ссылок на товары
#     all_hrefs = []
#     # Блокировка для безопасного добавления ссылок в общий список
#     all_hrefs_lock = threading.Lock()

#     # Список для хранения URL страниц пагинации
#     pagination_urls = []
#     pagination_lock = threading.Lock()

#     def extract_product_links(url):
#         """
#         Извлекает ссылки на товары с одной страницы категории.

#         Args:
#             url (str): URL страницы категории

#         Returns:
#             tuple: (список ссылок на товары, ссылка на следующую страницу или None)
#         """
#         try:
#             response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
#             response.raise_for_status()
#             soup = BeautifulSoup(response.text, "lxml")

#             page_hrefs = []
#             next_page_url = None

#             # Ищем структурированные данные JSON-LD
#             json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

#             # Обрабатываем каждый блок JSON-LD
#             for script in json_ld_scripts:
#                 try:
#                     # Извлекаем JSON-данные из тега script
#                     json_data = json.loads(script.string)

#                     # Проверяем, есть ли данные о товарах
#                     if (
#                         "about" in json_data
#                         and "offers" in json_data["about"]
#                         and "itemOffered" in json_data["about"]["offers"]
#                     ):
#                         # Извлекаем список товаров
#                         items = json_data["about"]["offers"]["itemOffered"]

#                         # Перебираем товары и извлекаем URL
#                         for item in items:
#                             if "url" in item:
#                                 # Очищаем URL от параметров отслеживания
#                                 item_url = item["url"]
#                                 if "?" in item_url:
#                                     clean_url = item_url.split("?")[0]
#                                     page_hrefs.append(clean_url)
#                                 else:
#                                     page_hrefs.append(item_url)
#                 except json.JSONDecodeError:
#                     continue

#             # Если из JSON-LD не удалось получить товары, пробуем обычные способы
#             if not page_hrefs:
#                 # Ищем основной блок с товарами
#                 main_section = soup.find("section", {"class": "brw-river"})

#                 if main_section:
#                     # Пробуем разные селекторы для поиска ссылок на товары
#                     items = []

#                     # Стратегия 1: Стандартные ссылки товаров
#                     items = main_section.select("a.s-item__link")

#                     # Стратегия 2: Ссылки в информационных блоках
#                     if not items:
#                         items = main_section.select("div.s-item__info a")

#                     # Стратегия 3: Ссылки в карточках товаров
#                     if not items:
#                         items = main_section.select(
#                             "li.brwrvr__item-card a.bsig__title__wrapper"
#                         )

#                     # Стратегия 4: Поиск span с классом bsig__title и получение родительской ссылки
#                     if not items:
#                         title_spans = main_section.select("span.bsig__title")
#                         items = [
#                             span.parent
#                             for span in title_spans
#                             if span.parent.name == "a"
#                         ]

#                     # Собираем все найденные ссылки
#                     for item in items:
#                         if "href" in item.attrs:
#                             page_hrefs.append(item["href"])

#             # Проверяем наличие следующей страницы
#             next_button = soup.select_one("a.pagination__next")

#             # Проверяем, что кнопка существует, имеет атрибут href и не отключена
#             if next_button and "href" in next_button.attrs:
#                 disabled_next = soup.select_one(
#                     'a.pagination__next[aria-disabled="true"]'
#                 )

#                 if not disabled_next:
#                     next_page_url = next_button["href"]

#             return page_hrefs, next_page_url

#         except Exception as e:
#             logger.error(f"Ошибка при обработке {url}: {str(e)}")
#             return [], None

#     def process_page(url):
#         """
#         Обрабатывает одну страницу каталога и извлекает ссылки на товары.

#         Args:
#             url (str): URL страницы категории
#         """
#         try:
#             page_hrefs, next_page_url = extract_product_links(url)

#             # Добавляем найденные ссылки на товары в общий список
#             if page_hrefs:
#                 with all_hrefs_lock:
#                     all_hrefs.extend(page_hrefs)
#                     logger.info(f"Найдено {len(page_hrefs)} ссылок на странице {url}")

#             # Добавляем следующую страницу в список для обработки
#             if next_page_url:
#                 with pagination_lock:
#                     pagination_urls.append(next_page_url)
#         except Exception as e:
#             logger.error(f"Ошибка при обработке страницы {url}: {str(e)}")

#     # Начинаем с первой страницы
#     logger.info(f"Запуск сбора ссылок с использованием {threads} потоков")

#     # Добавляем начальный URL в список страниц пагинации
#     pagination_urls.append(base_url)
#     processed_urls = set()

#     # Цикл продолжается, пока есть необработанные URL страниц пагинации
#     with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
#         while pagination_urls:
#             # Извлекаем URL для обработки (максимум threads URL за раз)
#             batch_urls = []
#             with pagination_lock:
#                 while pagination_urls and len(batch_urls) < threads:
#                     url = pagination_urls.pop(0)
#                     if url not in processed_urls:
#                         batch_urls.append(url)
#                         processed_urls.add(url)

#             if not batch_urls:
#                 break

#             # Запускаем задачи на обработку в пуле потоков
#             futures = [executor.submit(process_page, url) for url in batch_urls]

#             # Ждем завершения всех задач в текущем пакете
#             concurrent.futures.wait(futures)

#             # Сохраняем промежуточные результаты каждые 1000 ссылок
#             with all_hrefs_lock:
#                 current_count = len(all_hrefs)
#                 if current_count > 0 and current_count % 1000 == 0:
#                     temp_df = pd.DataFrame(all_hrefs, columns=["href"])
#                     temp_df.to_csv(f"all_urls_count_{current_count}.csv", index=False)
#                     logger.info(
#                         f"Промежуточное сохранение: {current_count} ссылок в all_urls_count_{current_count}.csv"
#                     )

#     # Удаляем дубликаты перед сохранением
#     unique_hrefs = list(set(all_hrefs))

#     # Сохраняем в CSV с помощью pandas
#     df = pd.DataFrame(unique_hrefs, columns=["href"])
#     df.to_csv("all_urls.csv", index=False)

#     logger.info(
#         f"Собрано {len(unique_hrefs)} уникальных ссылок и сохранено в all_urls.csv"
#     )
#     return unique_hrefs


def get_pagination_th(threads=20):
    """
    Функция для сбора всех ссылок на товары с использованием многопоточности.

    Args:
        threads (int): Количество потоков для параллельной обработки страниц пагинации

    Returns:
        list: Список всех собранных URL товаров
    """

    # Заголовки из curl-запроса

    cookies = {
        "cpt": "%5Ecpt_guid%3D1c6d329e-e67f-4633-b620-4c2f3bb2144f%5Ecpt_prvd%3Drecaptcha_v2%5E",
        "cbfm9f711": "0-0-0-0-0",
        "cbft9f711": "0-0-0-0-0",
        "cbfcl9f711": "no-touch,global-header,ghw,ghw--loaded,gh-header,gh-btt-button,icon-btn,gh-a11y-skip-button,gh-a11y-skip-button__link,gh-header__main,gh-logo,widgets-placeholder,gh-module-with-target,grid-cntr,pgHeading,stsMsg,stsMsg-errCtr,r3,c,rd-br,r3_t,r3_c,r3_cm,po,stsMsg-errBgr,stsMsg-msgInfo,b,g-hdn,stsMsg-txt,stsMsg-errTxtStyle,stsMsg-boldfont,stsMsg-npd,r3_bl,pgCenter,target-icaptcha-slot,g-recaptcha-response,captcha-not-rendered-msg-div,global-footer,wrap,gh-footer,gf-small-links,gf-small-links__link,gf-legal,legal-link,gf-privacy-choises,adBanner,ad,ads,adsbox,doubleclick,ad-placement,ad-placeholder,adbadge,BannerAd,gadget-csm,g-recaptcha-bubble-arrow",
        "ebay": "%5Ejs%3D1%5Esbf%3D%23000000%5E",
        "s": "CgAD4ACBoD7oXNzI2YTY5MjYxOTYwYTU0OGMyODU2ZDAwZmZiNmMwYWXXg5sO",
        "ak_bmsc": "E133A1AA3D388D7A0B4B4F8720BC9144~000000000000000000000000000000~YAAQRDYQYIRDAUuWAQAAEY9IeBsDwUd6KQpWc+rAS6+h5iqB0Cbkdj/sHQICFk5GXzqiOg34Nj6wY879LyVG7MPHghLNRbiDdoez9XdNqL6/3R7B2L7pFDclpUGAdsCj4H1Dfcp7cvJof3u5/DukfpWhK9mfYCzr/8oVhvbIm6hljKf5/nGyMArsdO0cK3Ihmv64QcdEcQ/Tf1EEqlSSK1l0gKxd7w7Y018Yi2VRX1TwgLxEqpnnPoK7meb/ftXP4B4n3w7/+H+hg4E1ZBYDL+LxNmfTF/ibrgVJQ/l4l3XhFIqMQKUw8kKfvPWc/zLDLknWsQcYhyECo3LPS3Yq4Ce6zTDcN5WoFHX6AgF7hHvHl2A9V1wdgqEL/Vu3vl10FkZQFvTp6g==",
        "__uzma": "c711b6ea-749f-4089-8b2a-b0911d6b8378",
        "__uzmb": "1745774743",
        "__uzme": "0350",
        "totp": "1745774744599.wYEOgK1fk0NnsUqPvGLyQdjk2KYm66b/3cyZ9c/G6qoZWs4pfcd2sAtzCWf3UBQGPddzZllwRtGtFuqh2xRg5w==.FsWOPAFQ8gZCpoviBh8GEiMWoZiT9ni1fy59Lis9mYI",
        "__uzmc": "183311367154",
        "__uzmd": "1745774749",
        "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736318203576075-913e4e8907d7f988418",
        "bm_sv": "E56D2805941827717B38CB01850D2411~YAAQRDYQYD1jAUuWAQAAF0JJeBubM6LQLpkiMSdl+2gwnh9yl1QDvuQgpRWpi2rNJ/yHvZ3a9tS6rnK5iN+g6uf9dGOVi4HTL8jbrhHytazIVXgN7UxoGBGGLgBw/9miRfqFLHy+9LI4iOdHJf2b4Ianp3ohnuSsGyLKpT2Iv+u1mELpABUiRDJvjSjQxiG2yWT+p7y+ytx7lTJb1rZYVtXzr8pWqA00MeMxDCZm5lfs3VJD6Plr8+BioaBk+w==~1",
        "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bd0cfc5^kms/in6bd0cfc5^pbf/%230000e400e0000000800000000069ef9c45^u1f/Bohdan6bd0cfc5^bl/DEen-US6bd0cfc5^",
        "nonsession": "BAQAAAZZay1gcAAaAADMABGnvnEUsUE9MAMoAIGvQz8U3MjZhNjkyNjE5NjBhNTQ4YzI4NTZkMDBmZmI2YzBhZQDLAAJoDm/NMjW8RuYqahgTYsCvv7GdfcgmCHMiRA**",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.google.com/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-full-version": '"135.0.7049.96"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    # Базовый URL и шаблон для пагинации
    base_url = "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?Items%2520Included=ABS%2520Accumulator&mag=1&rt=nc"
    page_template = "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?Items%2520Included=ABS%2520Accumulator&_pgn={}&mag=1&rt=nc"

    # Список для хранения всех ссылок на товары
    all_hrefs = []
    all_hrefs_lock = threading.Lock()

    # Счетчик обработанных страниц
    processed_pages = {"count": 0}
    processed_lock = threading.Lock()

    # Множество обработанных URL для избежания дублирования
    processed_urls = set()
    processed_urls_lock = threading.Lock()

    # Очередь для URL страниц
    url_queue = queue.Queue()

    # Флаг для завершения работы
    is_finished = {"value": False}

    def is_page_processed(url):
        """Проверяет, был ли URL уже обработан"""
        with processed_urls_lock:
            return url in processed_urls

    def mark_page_processed(url):
        """Отмечает URL как обработанный"""
        with processed_urls_lock:
            processed_urls.add(url)

    def get_page_and_links(url):
        """
        Извлекает ссылки на товары и ссылку на следующую страницу
        """
        try:
            # Случайная задержка для защиты от блокировки
            time.sleep(random.uniform(0.1, 0.3))

            response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            page_links = []

            # Ищем структурированные данные JSON-LD
            json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

            # Обрабатываем каждый блок JSON-LD
            for script in json_ld_scripts:
                try:
                    # Извлекаем JSON-данные из тега script
                    json_data = json.loads(script.string)

                    # Проверяем, есть ли данные о товарах
                    if (
                        "about" in json_data
                        and "offers" in json_data["about"]
                        and "itemOffered" in json_data["about"]["offers"]
                    ):
                        # Извлекаем список товаров
                        items = json_data["about"]["offers"]["itemOffered"]

                        # Перебираем товары и извлекаем URL
                        for item in items:
                            if "url" in item:
                                # Очищаем URL от параметров отслеживания
                                item_url = item["url"]
                                if "?" in item_url:
                                    clean_url = item_url.split("?")[0]
                                    page_links.append(clean_url)
                                else:
                                    page_links.append(item_url)
                except json.JSONDecodeError:
                    continue

            # Если из JSON-LD не удалось получить товары, пробуем обычные способы
            if not page_links:
                # Ищем основной блок с товарами
                main_section = soup.find("section", {"class": "brw-river"})

                if main_section:
                    # Пробуем разные селекторы для поиска ссылок на товары
                    items = []

                    # Стратегия 1: Стандартные ссылки товаров
                    items = main_section.select("a.s-item__link")

                    # Стратегия 2: Ссылки в информационных блоках
                    if not items:
                        items = main_section.select("div.s-item__info a")

                    # Стратегия 3: Ссылки в карточках товаров
                    if not items:
                        items = main_section.select(
                            "li.brwrvr__item-card a.bsig__title__wrapper"
                        )

                    # Стратегия 4: Поиск span с классом bsig__title и получение родительской ссылки
                    if not items:
                        title_spans = main_section.select("span.bsig__title")
                        items = [
                            span.parent
                            for span in title_spans
                            if span.parent.name == "a"
                        ]

                    # Собираем все найденные ссылки
                    for item in items:
                        if "href" in item.attrs:
                            page_links.append(item["href"])

            # Проверяем наличие следующей страницы
            next_page_url = None
            next_button = soup.select_one("a.pagination__next")

            # ИСПРАВЛЕНИЕ: Проверяем наличие общего количества товаров
            total_items_text = None
            total_items_elem = soup.select_one(".srp-controls__count-heading")
            if total_items_elem:
                total_items_text = total_items_elem.get_text(strip=True)
                # Извлекаем число из текста (например, из "3,414 results")
                import re

                match = re.search(r"([\d,]+)", total_items_text)
                if match:
                    try:
                        total_items = int(match.group(1).replace(",", ""))
                        # Вычисляем ожидаемое количество страниц (60 товаров на страницу)
                        expected_pages = (total_items + 59) // 60  # округление вверх
                        logger.info(
                            f"Найдено {total_items} товаров, ожидается {expected_pages} страниц"
                        )
                    except ValueError:
                        pass

            # Проверяем, что кнопка существует, имеет атрибут href и не отключена
            if next_button and "href" in next_button.attrs:
                disabled_next = soup.select_one(
                    'a.pagination__next[aria-disabled="true"]'
                )

                if not disabled_next:
                    next_page_url = next_button["href"]

            # ИСПРАВЛЕНИЕ: Если не нашли ссылок на этой странице, но это не последняя страница
            # на основе общего количества товаров, пробуем продолжить
            if not page_links and next_page_url is None:
                # Извлекаем номер страницы из URL
                page_num_match = re.search(r"_pgn=(\d+)", url)
                if page_num_match:
                    current_page = int(page_num_match.group(1))
                    # Если текущая страница меньше ожидаемого количества, пробуем перейти на следующую
                    if "expected_pages" in locals() and current_page < expected_pages:
                        next_page_url = page_template.format(current_page + 1)
                        logger.warning(
                            f"Не найдено товаров на странице {current_page}, но продолжаем на страницу {current_page + 1}"
                        )

            return page_links, next_page_url

        except Exception as e:
            logger.error(f"Ошибка при обработке {url}: {str(e)}")
            return [], None

    def worker():
        """
        Функция рабочего потока для обработки URL из очереди
        """
        while not is_finished["value"]:
            try:
                # Получаем URL из очереди (ждем не более 1 секунды)
                try:
                    url = url_queue.get(timeout=1)
                except queue.Empty:
                    # Даже если очередь пуста, нужно подождать, возможно другие потоки еще обрабатывают страницы
                    # и добавят новые URL в очередь
                    time.sleep(0.5)  # Небольшая пауза перед повторной проверкой
                    continue  # Продолжаем цикл, не завершая работу потока

                # Проверяем, не обрабатывался ли URL уже
                if is_page_processed(url):
                    url_queue.task_done()
                    continue

                # Отмечаем URL как обработанный
                mark_page_processed(url)

                # Увеличиваем счетчик обработанных страниц
                with processed_lock:
                    processed_pages["count"] += 1
                    current_page = processed_pages["count"]

                # Получаем ссылки на товары и следующую страницу
                page_links, next_page_url = get_page_and_links(url)

                # Добавляем ссылки на товары в общий список
                with all_hrefs_lock:
                    all_hrefs.extend(page_links)
                    logger.info(
                        f"[Поток {threading.current_thread().name}] Найдено {len(page_links)} ссылок на странице {current_page} ({url})"
                    )

                # Проверяем, является ли эта страница последней
                is_last_page = next_page_url is None

                # Если это последняя страница, логируем это
                if is_last_page:
                    logger.info(
                        f"[Поток {threading.current_thread().name}] Достигнута последняя страница: {url}"
                    )

                # Если есть следующая страница, добавляем ее в очередь
                if next_page_url and not is_page_processed(next_page_url):
                    url_queue.put(next_page_url)

                # Сохраняем промежуточные результаты
                with all_hrefs_lock:
                    if len(all_hrefs) > 0 and len(all_hrefs) % 1000 == 0:
                        temp_df = pd.DataFrame(all_hrefs, columns=["href"])
                        temp_file = f"all_urls_count_{len(all_hrefs)}.csv"
                        temp_df.to_csv(temp_file, index=False)
                        logger.info(
                            f"Промежуточное сохранение: {len(all_hrefs)} ссылок в {temp_file}"
                        )

                # Отмечаем задачу как выполненную
                url_queue.task_done()

            except Exception as e:
                logger.error(f"Ошибка в рабочем потоке: {str(e)}")

    # ВАЖНО: Предварительно заполняем очередь первыми N страницами
    # Это позволит всем потокам сразу начать работу
    logger.info(f"Предварительное заполнение очереди первыми {threads} страницами...")

    # Добавляем первую страницу
    url_queue.put(base_url)

    # Добавляем страницы с пагинацией 2, 3, ..., threads
    for page_num in range(2, threads + 1):
        page_url = page_template.format(page_num)
        url_queue.put(page_url)

    # Запускаем рабочие потоки
    logger.info(f"Запуск сбора ссылок с использованием {threads} потоков")
    worker_threads = []
    for i in range(threads):
        t = threading.Thread(target=worker, name=f"Worker-{i+1}")
        t.daemon = True
        t.start()
        worker_threads.append(t)

    # Ждем, пока не обнаружена последняя страница и очередь не опустеет
    try:
        last_count = 0
        consecutive_equal_count = 0
        max_equal_count = 6  # Увеличим до 30 секунд (6 проверок по 5 секунд)
        expected_pages = 0  # Ожидаемое количество страниц

        # Проверяем, есть ли информация о товарах в исходном URL
        initial_links, _ = get_page_and_links(base_url)

        while not is_finished["value"]:
            # Проверка каждые 5 секунд
            time.sleep(5)

            with processed_lock:
                current_count = processed_pages["count"]

            # Проверяем, изменилось ли количество обработанных страниц
            if current_count == last_count:
                consecutive_equal_count += 1
            else:
                consecutive_equal_count = 0
                last_count = current_count

            # Проверяем, что мы действительно достигли ожидаемого количества страниц
            should_finish = False
            if expected_pages > 0 and current_count >= expected_pages:
                logger.info(
                    f"Достигнуто ожидаемое количество страниц ({current_count}/{expected_pages}). Завершаем работу."
                )
                should_finish = True

            # Если количество обработанных страниц не меняется в течение долгого времени
            # и очередь пуста, значит работа завершена
            elif consecutive_equal_count >= max_equal_count and url_queue.empty():
                logger.info(
                    f"Количество страниц не изменилось за {max_equal_count * 5} секунд, очередь пуста. Завершаем работу."
                )
                should_finish = True

            if should_finish:
                # Проверяем, что количество обработанных страниц соответствует ожидаемому
                if (
                    expected_pages > 0 and current_count < expected_pages - 1
                ):  # Допускаем погрешность в 1 страницу
                    logger.warning(
                        f"Внимание: обработано только {current_count} из {expected_pages} страниц!"
                    )
                    # Добавляем недостающие страницы в очередь
                    for page_num in range(current_count + 1, expected_pages + 1):
                        page_url = page_template.format(page_num)
                        if not is_page_processed(page_url):
                            url_queue.put(page_url)
                            logger.info(
                                f"Добавлена пропущенная страница {page_num} в очередь"
                            )
                    continue  # Продолжаем работу, не завершаем
                else:
                    is_finished["value"] = True

            # Выводим статус для мониторинга
            with all_hrefs_lock:
                logger.info(
                    f"Прогресс: {current_count} страниц обработано, {len(all_hrefs)} ссылок найдено, {url_queue.qsize()} URL в очереди"
                )

    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
        is_finished["value"] = True

    # Ждем завершения всех потоков
    for t in worker_threads:
        t.join(timeout=2)

    # Удаляем дубликаты перед сохранением
    unique_hrefs = list(set(all_hrefs))

    # Сохраняем в CSV с помощью pandas
    df = pd.DataFrame(unique_hrefs, columns=["href"])
    df.to_csv("all_urls.csv", index=False)

    logger.info(
        f"Собрано {len(unique_hrefs)} уникальных ссылок и сохранено в all_urls.csv"
    )
    logger.info(f"Обработано {processed_pages['count']} страниц")

    return unique_hrefs


def get_product():

    # Заголовки из curl-запроса
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-full-version": '"135.0.7049.96"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    # Куки из curl-запроса
    cookies = {
        "__uzma": "97357116-b531-48ea-a787-9a1cdbc0d2a3",
        "__uzmb": "1737571173",
        "__uzme": "0889",
        "__ssds": "2",
        "__ssuzjsr2": "a9be0cd8e",
        "__uzmaj2": "f52997a6-1322-426e-8b54-c2c2eac61cf7",
        "__uzmbj2": "1737571182",
        "cid": "Qwjcj8NLrZa4OA91%23169442320",
        "shs": "BAQAAAZRXz2gmAAaAAVUAD2mwKzcyMjQyMjM4Mjg5MDAzLDLKGm6oHxSYJNWSOKNvMcNNo6deng**",
        "shui-messages-KYC_ALERT-viewsLeft": "999993",
        "ebaysid": "BAQAAAZRXz2gmAAaAA/oDQWuVKtBleUpyWlhraU9pSnphWFJsTG1saFppNXphV2R1WVhSMWNtVXVhMlY1Y0dGcGNpSXNJblpsY2lJNk1UTXNJbUZzWnlJNklsSlROVEV5SW4wLmV5SnBjM01pT2lKSlFVWlRUMEZKUkVWT1ZDSXNJbk4xWWlJNklqUm5aWGszYjNwdmRHVnRJaXdpWlhod0lqb3hOelF4T0RZMk9ETTJMQ0p1WW1ZaU9qRTNOREU0TmpVNU16WXNJbWxoZENJNk1UYzBNVGcyTlRrek5pd2lhblJwSWpvaU16azNaams1WXpFdE5HTTRZaTAwWWpKaExUa3daakV0TVRNelpHSTFNak0wWlRKbUlpd2ljMlZ6YzJsdmJsUnZhMlZ1VW1WbVpYSmxibU5sSWpvaWRsNHhMakVqYVY0eEkzQmVNeU55WGpFalpsNHdJMGxlTXlOMFhsVnNOSGhOUmpneFQydEdRMUZVVWtKTmFrSkNVbFJOZUU1RVJrZFNSVmt4VDBSb1ExSnFhekpSYTFKRFRWUnJNVkpVVVhsWWVrWm1UVk5PUmxocVNUSk5RVDA5SWl3aWMyVnpjMmx2Ymtsa0lqb2lPR0ZrTVdZeVlXUXhPVEl3WVdFM01qZzRZelprTnpnMlptWmpaV1UzT1RZaWZRLlB6WWtiNGJZWndOalJMbW81TXprVFBLWUNER1A0UllmSmE3a3BackFyUHhxX0h5TWpjUGtsWmFaZlExVjlEc3RjRUJEVTZPbUFTRzMwcTZoMVpDa3U0SEZOaTVNLU1OSTdhYmxtMkRBdDdnRGZ1VW5BMy1PckVEaUFqLTZmeTRXRjV3N1Q3eHNmbTZQYUJCUWFFTXRZZmRuYk5iZ1VnTk0yYTJ6OHpWNm05VjF0cURXeGY2QkpHX3paOTJaMnRsYl9NWS1ZMkFjVHZhdjI4Wk4zUTRmeGRWUDBRbUloUEdHZS1fMy1GVGNBM1JtUlFUQ3ByV09yNjFJS3c3cFplaFNGQksxODRTTXdjYWFqbWpvanBJZ0VQUjE0dGFCclFUeTlHdkRXblp2YU1RZW45cXN2ZFNTTHUwNUlwREdtdjE4ZFZUbVZtRENJRzBMUG5NdUNHbVdrd8QyyucYciLIbBojCo8LK3++Sy8x",
        "__uzmlj2": "G9FAAxnDuMKptEcAzxYkJIGvwaFLJ25rRkt6/3IP/jM=",
        "cpt": "%5Ecpt_prvd%3Dhcaptcha%5E",
        "__deba": "Wed3akqZJHwtM1z8M732L6ii3bqHZuzpiBZB3tGbaQbTPrlh8SVw389_7KVXBGqwXR8UW1J2_XMwSXzXGqPFGBpfL_bTa09RToxbD82BSPFB4sx0wK9nLHnUrJtlsixT0HRcCVsfcKIPRCZzSv4Rgw==",
        "__uzmcj2": "541718282825",
        "__uzmdj2": "1745310345",
        "__uzmfj2": "7f600038e61fac-f753-483f-8618-80f320552cd617375711825237739162974-e2ffbe8e527097c082",
        "ds1": "ats/1745310956857",
        "ns1": "BAQAAAZZay1gcAAaAAKUADGnoiG0xMzQ0MDY3NjMvMDvpPZJlkVUgx4l3N2CqNEQAeekN5Q**",
        "s": "CgAD4ACBoC2jPNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjBnFkGC",
        "ak_bmsc": "C2ECD7D77F71821EE513B7B3B2480630~000000000000000000000000000000~YAAQBUx1aAAKEUuWAQAAESyGaRuW9aZ0ekXKkZzsI0kyGf0qouioE7XHR+OXUAPSznIfHKImsFIMTBd1xIIGTho9s7UgT7KXQygQKmt6oHMjS3pL/FXkRYlr/5qxj5EJt/CM+OcIPGzOAeIz1BXiGPHNcFZ6XGQUwqYWxnagmoJh0bBIa4TKOycl13Y/dVv6DBCJlir3eHy7QQ+8Jo69/OA0OxJalZM7spn8e6pULNEe8Gre4sgu4n3e+/+KgLpEnhyfUQCx9iidyooUaFtpa0ERpQ+x4f4UF6wDVNztzEDUr64Foj36k6m6sKnRnfz3h5AYThYMhrpiWz4emz8h+S9cfMEbahTLbtU+A48vbBotjWRN1ecJ/YhsaODxD+06Qw/Ppy2ivJo=",
        "ebay": "%5Ejs%3D1%5EsfLMD%3D0%5Esin%3Din%5Esbf%3D%2300000004%5E",
        "__uzmc": "2378932286496",
        "__uzmd": "1745530440",
        "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736317959267058-150c914f21eedb01322",
        "totp": "1745530442106.iKVpBvoQ4A9rdCj5AxmsfGvdDoUrnJ5aeWFfjbtTpUSYsoJQpHWP+cj1En6KNPh8xOWRTXWVSdbYGvdqABqRqA==.rT765YSD8240_-ElUr6mQTVlLWGQPBQxu6oJx1gJKDg",
        "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bcd154b^kms/in6bcd154b^pbf/%230000e400e0000000800000000069ebe1cb^u1f/Bohdan6bcd154b^bl/DEen-US6bcd154b^",
        "nonsession": "CgADKACBrzRVLNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjAAywABaAq1UzQMPWZF",
        "bm_sv": "4412198FB9F945B4A1004A4BC7D99614~YAAQFkx1aIUHxyOWAQAAete4aRuU5vduaJOn4pgjq6EVDHga/DIIqDYbJ7gNTlr+NaByhQco0ZV3ZhO5oZDWMV6jpT7D5uoukWumggLYbu+8RCXeVYVvHjaoNLiBNG/WxbQZAG5sijqhc9Ap9T5/GmoqVNIpSe2bQNnhHWyZBUlkXPYsikwka2eNCt1ux7nG1B8wMY4/gOlEquX3YvTY4bCOg+VDpsLkJa4o0pduncsGr+8X/kWXxSgZRr2wgIs=~1",
    }

    # Файл для хранения маппинга
    mapping_file = html_directory / "url_mapping.csv"

    # Создаем файл с маппингом хешей к оригинальным URL
    url_mapping = []

    # Читаем CSV-файл
    try:
        df = pd.read_csv("all_urls.csv")
    except FileNotFoundError:
        logger.error("Файл all_urls.csv не найден!")
        return

    total_urls = len(df)
    processed = 0

    # Проходим по каждой ссылке
    for url in df["href"]:
        # Создаем MD5-хеш URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}.html"
        output_html_file = html_directory / filename

        # Добавляем в маппинг
        url_mapping.append({"hash": url_hash, "url": url})

        # Проверяем, не скачан ли уже файл
        if output_html_file.exists():
            logger.info(f"Файл {filename} уже существует, пропускаем")
            processed += 1
            continue

        logger.info(f"Загружаем {url} в {filename}... ({processed}/{total_urls})")

        try:
            # Выполняем запрос
            response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()

            # Сохраняем HTML в файл
            output_html_file.write_text(response.text, encoding="utf-8")

            logger.info(f"Сохранено в {filename}")

            # Сохраняем маппинг после каждых 100 файлов
            if processed % 100 == 0 and processed > 0:
                mapping_df = pd.DataFrame(url_mapping)
                mapping_df.to_csv(mapping_file, index=False)
                logger.info(
                    f"Промежуточное сохранение маппинга: {processed}/{total_urls}"
                )

        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {str(e)}")

        processed += 1

        # Пауза между запросами с рандомизацией для избежания блокировки
        time.sleep(random.uniform(1.5, 3.0))

    # Сохраняем итоговый маппинг
    mapping_df = pd.DataFrame(url_mapping)
    mapping_df.to_csv(mapping_file, index=False)

    logger.info(f"Загрузка завершена! Обработано {processed} из {total_urls} URL")


def get_product_th(threads=10):
    """
    Загружает страницы товаров в параллельном режиме.

    Args:
        threads (int): Количество потоков для параллельной загрузки. По умолчанию 10.
    """

    # Заголовки из curl-запроса
    # Заголовки из curl-запроса
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-full-version": '"135.0.7049.96"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    # Куки из curl-запроса
    cookies = {
        "__uzma": "97357116-b531-48ea-a787-9a1cdbc0d2a3",
        "__uzmb": "1737571173",
        "__uzme": "0889",
        "__ssds": "2",
        "__ssuzjsr2": "a9be0cd8e",
        "__uzmaj2": "f52997a6-1322-426e-8b54-c2c2eac61cf7",
        "__uzmbj2": "1737571182",
        "cid": "Qwjcj8NLrZa4OA91%23169442320",
        "shs": "BAQAAAZRXz2gmAAaAAVUAD2mwKzcyMjQyMjM4Mjg5MDAzLDLKGm6oHxSYJNWSOKNvMcNNo6deng**",
        "shui-messages-KYC_ALERT-viewsLeft": "999993",
        "ebaysid": "BAQAAAZRXz2gmAAaAA/oDQWuVKtBleUpyWlhraU9pSnphWFJsTG1saFppNXphV2R1WVhSMWNtVXVhMlY1Y0dGcGNpSXNJblpsY2lJNk1UTXNJbUZzWnlJNklsSlROVEV5SW4wLmV5SnBjM01pT2lKSlFVWlRUMEZKUkVWT1ZDSXNJbk4xWWlJNklqUm5aWGszYjNwdmRHVnRJaXdpWlhod0lqb3hOelF4T0RZMk9ETTJMQ0p1WW1ZaU9qRTNOREU0TmpVNU16WXNJbWxoZENJNk1UYzBNVGcyTlRrek5pd2lhblJwSWpvaU16azNaams1WXpFdE5HTTRZaTAwWWpKaExUa3daakV0TVRNelpHSTFNak0wWlRKbUlpd2ljMlZ6YzJsdmJsUnZhMlZ1VW1WbVpYSmxibU5sSWpvaWRsNHhMakVqYVY0eEkzQmVNeU55WGpFalpsNHdJMGxlTXlOMFhsVnNOSGhOUmpneFQydEdRMUZVVWtKTmFrSkNVbFJOZUU1RVJrZFNSVmt4VDBSb1ExSnFhekpSYTFKRFRWUnJNVkpVVVhsWWVrWm1UVk5PUmxocVNUSk5RVDA5SWl3aWMyVnpjMmx2Ymtsa0lqb2lPR0ZrTVdZeVlXUXhPVEl3WVdFM01qZzRZelprTnpnMlptWmpaV1UzT1RZaWZRLlB6WWtiNGJZWndOalJMbW81TXprVFBLWUNER1A0UllmSmE3a3BackFyUHhxX0h5TWpjUGtsWmFaZlExVjlEc3RjRUJEVTZPbUFTRzMwcTZoMVpDa3U0SEZOaTVNLU1OSTdhYmxtMkRBdDdnRGZ1VW5BMy1PckVEaUFqLTZmeTRXRjV3N1Q3eHNmbTZQYUJCUWFFTXRZZmRuYk5iZ1VnTk0yYTJ6OHpWNm05VjF0cURXeGY2QkpHX3paOTJaMnRsYl9NWS1ZMkFjVHZhdjI4Wk4zUTRmeGRWUDBRbUloUEdHZS1fMy1GVGNBM1JtUlFUQ3ByV09yNjFJS3c3cFplaFNGQksxODRTTXdjYWFqbWpvanBJZ0VQUjE0dGFCclFUeTlHdkRXblp2YU1RZW45cXN2ZFNTTHUwNUlwREdtdjE4ZFZUbVZtRENJRzBMUG5NdUNHbVdrd8QyyucYciLIbBojCo8LK3++Sy8x",
        "__uzmlj2": "G9FAAxnDuMKptEcAzxYkJIGvwaFLJ25rRkt6/3IP/jM=",
        "cpt": "%5Ecpt_prvd%3Dhcaptcha%5E",
        "__deba": "Wed3akqZJHwtM1z8M732L6ii3bqHZuzpiBZB3tGbaQbTPrlh8SVw389_7KVXBGqwXR8UW1J2_XMwSXzXGqPFGBpfL_bTa09RToxbD82BSPFB4sx0wK9nLHnUrJtlsixT0HRcCVsfcKIPRCZzSv4Rgw==",
        "__uzmcj2": "541718282825",
        "__uzmdj2": "1745310345",
        "__uzmfj2": "7f600038e61fac-f753-483f-8618-80f320552cd617375711825237739162974-e2ffbe8e527097c082",
        "ds1": "ats/1745310956857",
        "ns1": "BAQAAAZZay1gcAAaAAKUADGnoiG0xMzQ0MDY3NjMvMDvpPZJlkVUgx4l3N2CqNEQAeekN5Q**",
        "s": "CgAD4ACBoC2jPNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjBnFkGC",
        "ak_bmsc": "C2ECD7D77F71821EE513B7B3B2480630~000000000000000000000000000000~YAAQBUx1aAAKEUuWAQAAESyGaRuW9aZ0ekXKkZzsI0kyGf0qouioE7XHR+OXUAPSznIfHKImsFIMTBd1xIIGTho9s7UgT7KXQygQKmt6oHMjS3pL/FXkRYlr/5qxj5EJt/CM+OcIPGzOAeIz1BXiGPHNcFZ6XGQUwqYWxnagmoJh0bBIa4TKOycl13Y/dVv6DBCJlir3eHy7QQ+8Jo69/OA0OxJalZM7spn8e6pULNEe8Gre4sgu4n3e+/+KgLpEnhyfUQCx9iidyooUaFtpa0ERpQ+x4f4UF6wDVNztzEDUr64Foj36k6m6sKnRnfz3h5AYThYMhrpiWz4emz8h+S9cfMEbahTLbtU+A48vbBotjWRN1ecJ/YhsaODxD+06Qw/Ppy2ivJo=",
        "ebay": "%5Ejs%3D1%5EsfLMD%3D0%5Esin%3Din%5Esbf%3D%2300000004%5E",
        "__uzmc": "2378932286496",
        "__uzmd": "1745530440",
        "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736317959267058-150c914f21eedb01322",
        "totp": "1745530442106.iKVpBvoQ4A9rdCj5AxmsfGvdDoUrnJ5aeWFfjbtTpUSYsoJQpHWP+cj1En6KNPh8xOWRTXWVSdbYGvdqABqRqA==.rT765YSD8240_-ElUr6mQTVlLWGQPBQxu6oJx1gJKDg",
        "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bcd154b^kms/in6bcd154b^pbf/%230000e400e0000000800000000069ebe1cb^u1f/Bohdan6bcd154b^bl/DEen-US6bcd154b^",
        "nonsession": "CgADKACBrzRVLNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjAAywABaAq1UzQMPWZF",
        "bm_sv": "4412198FB9F945B4A1004A4BC7D99614~YAAQFkx1aIUHxyOWAQAAete4aRuU5vduaJOn4pgjq6EVDHga/DIIqDYbJ7gNTlr+NaByhQco0ZV3ZhO5oZDWMV6jpT7D5uoukWumggLYbu+8RCXeVYVvHjaoNLiBNG/WxbQZAG5sijqhc9Ap9T5/GmoqVNIpSe2bQNnhHWyZBUlkXPYsikwka2eNCt1ux7nG1B8wMY4/gOlEquX3YvTY4bCOg+VDpsLkJa4o0pduncsGr+8X/kWXxSgZRr2wgIs=~1",
    }

    # Создаем директорию для сохранения HTML-файлов, если она не существует

    # Файл для хранения маппинга
    mapping_file = html_directory / "url_mapping.csv"
    file_name = "all_urls.csv"
    output_csv_path = data_directory / file_name
    # Читаем CSV-файл
    try:
        df = pd.read_csv(output_csv_path)
    except FileNotFoundError:
        logger.error("Файл all_urls.csv не найден!")
        return

    total_urls = len(df)
    logger.info(f"Всего найдено {total_urls} URL для загрузки")

    # Словарь для маппинга
    url_mapping = []

    # Блокировка для безопасного добавления в url_mapping и логирования
    mapping_lock = Lock()
    log_lock = Lock()

    # Счетчик обработанных URL
    processed_counter = {"count": 0}
    counter_lock = Lock()

    # Определяем функцию для обработки одного URL
    def process_url(url):
        try:
            # Создаем MD5-хеш URL
            url_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{url_hash}.html"
            output_html_file = html_directory / filename

            # Добавляем в маппинг
            with mapping_lock:
                url_mapping.append({"hash": url_hash, "url": url})

            # Проверяем, не скачан ли уже файл
            if output_html_file.exists():
                with log_lock:
                    pass
                    # logger.debug(f"Файл {filename} уже существует, пропускаем")
                return True  # URL уже обработан

            # Выполняем запрос
            # response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            src = make_request(url, headers=headers, cookies=cookies)
            # Сохраняем HTML в файл
            output_html_file.write_text(src, encoding="utf-8")

            with log_lock:
                logger.info(f"Сохранено в {filename}")

            # Увеличиваем счетчик обработанных URL
            with counter_lock:
                processed_counter["count"] += 1
                count = processed_counter["count"]

                # Периодически сохраняем маппинг
                if count % 100 == 0:
                    with mapping_lock:
                        mapping_df = pd.DataFrame(url_mapping)
                        mapping_df.to_csv(mapping_file, index=False)
                    logger.info(
                        f"Промежуточное сохранение маппинга: {count}/{total_urls}"
                    )

            return True

        except Exception as e:
            with log_lock:
                logger.error(f"Ошибка при загрузке {url}: {str(e)}")
            return False

    # Запускаем многопоточную обработку
    start_time = time.time()
    logger.info(f"Запуск загрузки в {threads} потоков")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(process_url, df["href"]))

    # Сохраняем итоговый маппинг
    mapping_df = pd.DataFrame(url_mapping)
    mapping_df.to_csv(mapping_file, index=False)

    end_time = time.time()
    total_time = end_time - start_time
    success_count = sum(1 for r in results if r)

    logger.info(
        f"Загрузка завершена! Успешно обработано {success_count} из {total_urls} URL"
    )
    logger.info(f"Затраченное время: {total_time:.2f} секунд")

    return success_count


def get_breadcrumbList(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            # Получаем текст скрипта и проверяем его наличие
            script_text = script.string
            if not script_text or not script_text.strip():
                continue

            # Проверим, что это скрипт JSON-LD
            if "application/ld+json" not in script.get("type", ""):
                continue
            json_data = json.loads(script_text)
            # Проверяем, является ли это продуктом
            if isinstance(json_data, dict):
                # Проверяем тип - может быть строкой или списком типов
                product_type = json_data.get("@type")
                is_product = False

                if isinstance(product_type, str) and product_type == "BreadcrumbList":
                    is_product = True
                elif (
                    isinstance(product_type, list) and "BreadcrumbList" in product_type
                ):
                    is_product = True

                if is_product:
                    item_list = json_data.get("itemListElement", [])[-1]
                    name_category = item_list.get("name", "")
                    return name_category
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке скрипта: {str(e)}")


def scrap_html():

    # Список для хранения данных
    data = []
    # Множество для хранения всех уникальных ключей характеристик
    spec_keys = set()

    # Проходим по всем HTML-файлам в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

            try:
                soup = BeautifulSoup(content, "lxml")

                # Инициализируем словарь для данных
                product_data = {"filename": html_file.name}
                breadcrumb = get_breadcrumbList(soup)
                product_data["category"] = breadcrumb

                # 1. Извлекаем URL из <meta property="og:url">
                url_meta = soup.find("meta", {"property": "og:url"})
                product_data["url"] = url_meta.get("content", "") if url_meta else ""

                title_tag = soup.find("div", {"data-testid": "x-item-title"})
                product_data["title"] = (
                    title_tag.find("span").get_text(strip=True)
                    if title_tag and title_tag.find("span")
                    else ""
                )
                # 2. Извлекаем цену из <div class="x-price-primary">
                price_div = soup.find("div", {"class": "x-price-primary"})
                if price_div:
                    price_text = price_div.find(
                        "span", {"class": "ux-textspans"}
                    ).get_text(strip=True)
                    # Извлекаем числовое значение (например, "US $1,450.00" -> "1450.00")
                    price = "".join(
                        filter(lambda x: x.isdigit() or x == ".", price_text)
                    )
                    product_data["price"] = price
                else:
                    product_data["price"] = ""

                # 3. Извлекаем изображения (до 3) из <div class="ux-image-carousel-item image-treatment image">
                images = []
                image_divs = soup.find_all(
                    "div", {"class": "ux-image-carousel-item image-treatment image"}
                )
                for div in image_divs[:3]:  # Ограничиваем до 3 изображений
                    img = div.find("img")
                    if img:
                        src = img.get("data-zoom-src")
                        if src:
                            images.append(src)
                product_data["image_1"] = images[0] if len(images) > 0 else ""
                product_data["image_2"] = images[1] if len(images) > 1 else ""
                product_data["image_3"] = images[2] if len(images) > 2 else ""

                # 4. Извлекаем состояние товара
                condition_div = soup.find("div", {"class": "vim x-item-condition"})
                if condition_div:
                    condition_text = condition_div.find(
                        "span", {"data-testid": "ux-textual-display"}
                    )
                    product_data["condition"] = (
                        condition_text.get_text(strip=True) if condition_text else ""
                    )
                else:
                    product_data["condition"] = ""

                # 5. Извлекаем информацию о возврате
                returns_div = soup.find("div", {"data-testid": "x-returns-minview"})
                if not returns_div:
                    # Если не нашли по data-testid, пробуем поискать по классу как запасной вариант
                    returns_div = soup.find("div", {"class": "vim x-returns-minview"})

                if returns_div:
                    # Ищем все элементы с текстом внутри блока возвратов
                    returns_text = returns_div.find(
                        "div", {"class": "ux-labels-values__values-content"}
                    )
                    if returns_text:
                        # Собираем весь текст из дочерних элементов, соединяя пробелом
                        # (вместо запятой, чтобы текст читался более естественно)
                        returns_parts = []
                        for child in returns_text.find_all(["span", "button"]):
                            text = child.get_text(strip=True)
                            if text:
                                returns_parts.append(text)

                        # Соединяем все части текста
                        product_data["returns"] = " ".join(returns_parts)
                    else:
                        product_data["returns"] = ""
                else:
                    product_data["returns"] = ""
                # 6-7. Извлекаем информацию о доставке (Shipping и Delivery)
                shipping_container = soup.find(
                    "div", {"data-testid": "d-shipping-minview"}
                )
                if not shipping_container:
                    # Резервный поиск по классу
                    shipping_container = soup.find(
                        "div", {"class": "vim d-shipping-minview"}
                    )

                if shipping_container:
                    # Ищем Shipping внутри контейнера
                    shipping_block = shipping_container.find(
                        "div",
                        {
                            "data-testid": "ux-labels-values",
                            "class": lambda c: c and "ux-labels-values--shipping" in c,
                        },
                    )
                    if shipping_block:
                        shipping_content = shipping_block.find(
                            "div", {"class": "ux-labels-values__values-content"}
                        )
                        if shipping_content:
                            # Обрабатываем первую строку с ценой и методом доставки
                            first_line_parts = []
                            for span in shipping_content.select(
                                "div:first-child > span.ux-textspans"
                            ):
                                text = span.get_text(strip=True)
                                if text and not text.startswith("See details"):
                                    first_line_parts.append(text)

                            # Обрабатываем вторую строку с информацией о местоположении
                            location_text = ""
                            location_span = shipping_content.select_one(
                                "div:nth-child(2) > span.ux-textspans--SECONDARY"
                            )
                            if location_span:
                                location_text = location_span.get_text(strip=True)

                            # Собираем всю информацию о доставке
                            shipping_info = []
                            if first_line_parts:
                                shipping_info.append(" ".join(first_line_parts))
                            if location_text:
                                shipping_info.append(location_text)

                            # Ищем информацию о комбинированной доставке
                            combined_shipping = shipping_container.find(
                                "span",
                                string=lambda s: s and "Save on combined shipping" in s,
                            )
                            if combined_shipping:
                                shipping_info.append("Save on combined shipping")

                            product_data["shipping"] = ", ".join(shipping_info)
                        else:
                            product_data["shipping"] = ""
                    else:
                        product_data["shipping"] = ""

                    # Обработка информации о доставке (Delivery)
                    delivery_block = shipping_container.find(
                        "div", {"class": "ux-labels-values--deliverto"}
                    )

                    if delivery_block:
                        delivery_content_div = delivery_block.find(
                            "div", {"class": "ux-labels-values__values-content"}
                        )
                        if delivery_content_div:
                            delivery_info = []

                            # Первая строка - даты доставки
                            first_div = delivery_content_div.find("div")

                            if first_div:
                                delivery_text = ""

                                # Ищем основной текст и выделенные даты
                                main_spans = first_div.find_all(
                                    "span", {"class": "ux-textspans"}, recursive=False
                                )

                                # Собираем текст и даты
                                for span in main_spans:
                                    # Исключаем span-элементы, содержащие информационный всплывающий блок
                                    if "ux-textspans__custom-view" not in span.get(
                                        "class", []
                                    ) and not span.has_attr("role"):
                                        delivery_text += span.get_text(strip=True) + " "

                                if delivery_text.strip():
                                    delivery_info.append(delivery_text.strip())

                            # Вторая строка - примечание о сроках
                            second_div = (
                                delivery_content_div.find_all("div")[1]
                                if len(delivery_content_div.find_all("div")) > 1
                                else None
                            )
                            if second_div:
                                notes = []
                                for span in second_div.find_all(
                                    "span",
                                    {
                                        "class": lambda c: c
                                        and "ux-textspans--SECONDARY" in c
                                    },
                                ):
                                    notes.append(span.get_text(strip=True))

                                if notes:
                                    delivery_info.append(" ".join(notes))

                            # Третья строка - информация об отправке
                            third_div = (
                                delivery_content_div.find_all("div")[2]
                                if len(delivery_content_div.find_all("div")) > 2
                                else None
                            )
                            if third_div:
                                shipping_info = []

                                # Собираем текст из всех span элементов
                                for span in third_div.find_all(
                                    "span",
                                    {
                                        "class": lambda c: c
                                        and "ux-textspans--SECONDARY" in c
                                    },
                                ):
                                    shipping_info.append(span.get_text(strip=True))

                                # Собираем текст из всех ссылок
                                for link in third_div.find_all("a"):
                                    span = link.find(
                                        "span",
                                        {
                                            "class": lambda c: c
                                            and "ux-textspans--SECONDARY" in c
                                        },
                                    )
                                    if span:
                                        shipping_info.append(span.get_text(strip=True))

                                if shipping_info:
                                    delivery_info.append(" ".join(shipping_info))

                            # Собираем всю информацию в одну строку с разделителями
                            product_data["delivery"] = ", ".join(delivery_info)
                        else:
                            product_data["delivery"] = ""
                    else:
                        product_data["delivery"] = ""
                else:
                    product_data["shipping"] = ""
                    product_data["delivery"] = ""
                # 8. Извлекаем характеристики
                specifications = {}

                # Метод 1: Извлечение из x-prp-product-details (первый формат)
                specs_div = soup.find("div", {"class": "x-prp-product-details"})

                if specs_div:
                    spec_rows = specs_div.find_all(
                        "div", {"class": "x-prp-product-details_row"}
                    )
                    for row in spec_rows:
                        cols = row.find_all(
                            "div", {"class": "x-prp-product-details_col"}
                        )
                        for col in cols:
                            name = col.find(
                                "span", {"class": "x-prp-product-details_name"}
                            )
                            value = col.find(
                                "span", {"class": "x-prp-product-details_value"}
                            )
                            if name and value:
                                spec_name = name.get_text(strip=True)
                                spec_value = value.get_text(strip=True)
                                specifications[spec_name] = spec_value
                                # Добавляем ключ в множество всех ключей
                                spec_keys.add(spec_name)

                # Метод 2: Извлечение из vim x-about-this-item (второй формат)
                if not specifications:
                    about_item_div = soup.find(
                        "div", {"class": "vim x-about-this-item"}
                    )

                    if about_item_div:
                        spec_items = about_item_div.find_all(
                            "dl", {"class": "ux-labels-values"}
                        )

                        for item in spec_items:
                            # Находим название характеристики
                            name_elem = item.find(
                                "dt", {"class": "ux-labels-values__labels"}
                            )
                            if not name_elem:
                                continue

                            spec_name = name_elem.get_text(strip=True)

                            # Находим значение характеристики
                            value_elem = item.find(
                                "dd", {"class": "ux-labels-values__values"}
                            )
                            if not value_elem:
                                continue

                            # Ищем первый div с текстом внутри значения
                            value_content = value_elem.find(
                                "div", {"class": "ux-labels-values__values-content"}
                            )
                            if not value_content:
                                continue

                            # Извлекаем только основной текст
                            first_div = value_content.find("div")
                            if not first_div:
                                continue

                            # Обрабатываем обычный текст
                            if first_div.find(
                                "span",
                                {"class": "ux-expandable-textual-display-block-inline"},
                            ):
                                # Если есть кнопка Read more, получаем только первую часть текста
                                text_span = first_div.find(
                                    "span", {"data-testid": "text"}
                                )
                                if text_span:
                                    spec_value = text_span.get_text(strip=True)
                                else:
                                    # Если нет span с data-testid="text", берем весь текст блока
                                    spec_value = first_div.get_text(strip=True).split(
                                        "Read more"
                                    )[0]
                            else:
                                # Обычный текст, берем только текст из первого div
                                spec_value = first_div.get_text(strip=True)

                            # Очищаем значение от служебных текстов
                            if "Read more" in spec_value:
                                spec_value = spec_value.split("Read more")[0]
                            if "Read Less" in spec_value:
                                spec_value = spec_value.split("Read Less")[0]

                            # Удаляем возможные скрытые тексты
                            spec_value = re.sub(
                                r"opens in a new window or tab", "", spec_value
                            )
                            spec_value = re.sub(
                                r"about the seller notes", "", spec_value
                            )
                            spec_value = re.sub(r"Read moreRead Less", "", spec_value)

                            # Убираем лишние кавычки в начале и конце
                            spec_value = spec_value.strip('"')

                            # Сохраняем в словарь
                            specifications[spec_name] = spec_value
                            # Добавляем ключ в множество всех ключей
                            spec_keys.add(spec_name)

                # Сохраняем характеристики как JSON-строку
                product_data["specifications"] = json.dumps(
                    specifications, ensure_ascii=False
                )

                # Добавляем характеристики как отдельные поля в product_data
                for key, value in specifications.items():
                    product_data[key] = value

                # Добавляем данные в список
                data.append(product_data)

            except Exception as e:
                logger.error(f"Ошибка при обработке {html_file.name}: {str(e)}")
                data.append(
                    {
                        "filename": html_file.name,
                        "title": "",
                        "url": "",
                        "price": "",
                        "image_1": "",
                        "image_2": "",
                        "image_3": "",
                        "condition": "",
                        "returns": "",
                        "shipping": "",
                        "delivery": "",
                    }
                )

    # Создаем DataFrame с учетом всех возможных ключей характеристик
    # Базовые колонки, которые есть у всех товаров
    base_columns = [
        "filename",
        "title",
        "category",
        "url",
        "price",
        "image_1",
        "image_2",
        "image_3",
        "condition",
        "returns",
        "shipping",
        "delivery",
    ]
    # del product_data["specifications"]
    # Добавляем все уникальные ключи характеристик как отдельные колонки
    all_columns = base_columns + sorted(spec_keys)

    # Преобразуем данные в DataFrame, заполняя отсутствующие колонки пустыми строками
    # и обрабатывая переносы строк
    df_data = []
    for item in data:
        row = {}
        for col in all_columns:
            value = item.get(col, "")
            # Заменяем переносы строк на пробелы или другой символ
            if isinstance(value, str):
                value = value.replace("\n", " ").replace("\r", "")
            row[col] = value
        df_data.append(row)

    df = pd.DataFrame(df_data, columns=all_columns)

    # Используем quoting=csv.QUOTE_ALL, чтобы все поля были в кавычках
    # и escapechar для экранирования специальных символов
    import csv

    df.to_csv(
        "product_details.csv",
        index=False,
        encoding="utf-8",
        sep=";",
        quoting=csv.QUOTE_ALL,
        escapechar="\\",
        doublequote=True,
        quotechar='"',
    )

    logger.info(
        f"Обработано {len(data)} файлов, данные сохранены в product_details.csv"
    )


if __name__ == "__main__":

    get_pagination(200)
    # get_pagination_th(20)
    # get_product()
    get_product_th(20)
    # scrap_html()
