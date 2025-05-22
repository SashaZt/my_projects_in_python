import concurrent.futures
import hashlib
import json
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
from requests.exceptions import HTTPError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)

config_file = config_directory / "config.json"

cookies = {
    "__uzma": "48f63d0a-8f14-443b-8715-fcdba0ef603b",
    "__uzmb": "1728902698",
    "__uzme": "0335",
    "__uzmc": "256671941755",
    "__uzmd": "1742639115",
    "__uzmf": "7f600064f0eb3a-c548-42ca-b2b7-28f9559755a4172890269899113736416513-2a38b34a491a6dcd19",
    "AMP_MKTG_f93443b04c": "JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE",
    "AMP_f93443b04c": "JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI1NWQ1NmQxMi1mOThiLTQ5MGEtYTUzMi00ZjEyZThiZTJkMGYlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzQyNjM5MTE3MDMyJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc0MjYzOTExNzA1NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==",
    "dp1": "bbl/UA6ba0f710^",
    "nonsession": "BAQAAAZRXz2gmAAaAADMABWm/w5AyMTAwMADKACBroPcQOGFhMTk4MGYxOTIwYTZmMTZlM2QyZjUwZmZiNTE4YTYAywABZ96XGDbYNiX16bk46kVFvzpbH3uSlWh5Iw**",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
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


# Декоратор для повторных попыток
# Декоратор для повторных попыток
@retry(
    stop=stop_after_attempt(10),  # Максимум 10 попыток
    wait=wait_fixed(10),  # Задержка 10 секунд между попытками
    retry=retry_if_exception_type(HTTPError),  # Повторять при HTTPError
)
def make_request(url, params=None):
    """
    Выполняет HTTP-запрос с автоматическими повторными попытками при ошибках.
    """
    # Получаем случайный прокси
    proxies = get_random_proxy()
    logger.info(proxies)
    response = requests.get(
        url,
        proxies=proxies,
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=30,
    )
    response.raise_for_status()  # Вызывает HTTPError, если статус не 200

    return response.text


def get_pagination(max_pages=None):
    """
    Функция для сбора ссылок с пагинацией с заданным максимальным количеством страниц

    Args:
        max_pages (int, optional): Максимальное количество страниц для обхода.
                                   None означает без ограничений.

    Returns:
        list: Список собранных ссылок
    """
    # Список для хранения всех href
    all_hrefs = []
    load_proxies()

    def scrape_page(url, params):
        try:
            src = make_request(url, params=params)
            soup = BeautifulSoup(src, "lxml")

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
                                # Очищаем URL от параметров отслеживания, если необходимо
                                item_url = item["url"]
                                if "?" in item_url:
                                    url = item_url.split("?")[0]
                                    all_hrefs.append(url)
                                else:
                                    all_hrefs.append(item_url)

                                # logger.debug(
                                #     f"Найден товар из JSON-LD: {item.get('name', 'Без имени')} - {item_url}"
                                # )
                except json.JSONDecodeError:
                    logger.warning("Не удалось разобрать JSON-LD")
                    continue

            # Если из JSON-LD не удалось получить товары, пробуем обычные способы
            if not all_hrefs:
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
                            all_hrefs.append(item["href"])

            # Проверяем наличие следующей страницы
            next_button = soup.select_one("a.pagination__next")

            # Проверяем, что кнопка существует, имеет атрибут href и не отключена
            if next_button and "href" in next_button.attrs:
                disabled_next = soup.select_one(
                    'a.pagination__next[aria-disabled="true"]'
                )

                if not disabled_next:
                    logger.info(
                        f"Найдена ссылка на следующую страницу: {next_button['href']}"
                    )
                    return next_button["href"]

            # Если мы на странице 167 и не нашли кнопку Next, проверяем наличие ссылки на страницу 168
            if params and "_pgn" in params and params["_pgn"] == 167:
                # Ищем прямые ссылки на страницу 168
                page_links = soup.select("a.pagination__item")
                for link in page_links:
                    if link.text.strip() == "168" and "href" in link.attrs:
                        logger.info(
                            f"Найдена прямая ссылка на страницу 168: {link['href']}"
                        )
                        return link["href"]

                logger.info("Принудительно переходим к странице 168")
                # Если не нашли прямую ссылку, но мы на странице 167, возвращаем тот же URL
                # В цикле будет автоматически создан параметр _pgn=168
                return url

            return None
        except Exception as e:
            logger.error(f"Ошибка при обработке {url}: {str(e)}")
            return None

    # Начинаем с первой страницы
    current_url = (
        "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684"
    )
    page_count = 1
    all_brands = [
        "1",
        "1&1",
        "A.B.S.",
        "AB Components",
        "ABS",
        "ABS Private Brand",
        "ACDelco",
        "ACDelco (OE)",
        "Acura",
        "ADVICS",
        "Aftermarket Products",
        "Aisin",
        "Alfa Romeo",
        "Alto",
        "American Motors",
        "AM General",
        "Areyourshop",
        "ASTON MARTIN",
        "ATE",
        "ATE/Premium One",
        "ATI",
        "ATS",
        "Audi",
        "Autopower",
        "Autozone",
        "Bendix",
        "Bentley",
        "BMW",
        "Bosch",
        "Brembo",
        "Buick",
        "Cadillac",
        "CAR",
        "Cherokee",
        "Chevrolet",
        "Chrysler",
        "Citroën",
        "Cooper",
        "Corsa",
        "Corvette",
        "Cruiser",
        "Cummins",
        "Custom",
        "Daewoo",
        "Dart",
        "Delco",
        "Delphi",
        "DENSO",
        "Dodge",
        "Dragon",
        "Ducati",
        "Edge",
        "EVO",
        "Factory/OEM",
        "Factory Spec",
        "Ferrari",
        "Fiat",
        "Fomoco",
        "Ford",
        "Ford Performance",
        "Fusion",
        "FWD",
        "FWD Front Wheel Drive",
        "Galaxy",
        "General Motors",
        "Genesis",
        "GM",
        "GMC",
        "Haldex",
        "Hella",
        "Honda",
        "Hummer",
        "Hyundai",
        "Infiniti",
        "Jaguar",
        "Jeep",
        "Kia",
        "Lamborghini",
        "Land Rover",
        "Legacy",
        "Lexus",
        "Lincoln",
        "Mando",
        "Maserati",
        "Maxima",
        "MaXpeedingRods",
        "Mazda",
        "Mazdaspeed",
        "McLaren",
        "Mercedes-Benz",
        "Mercury",
        "Merkur",
        "Mini",
        "Mitsubishi",
        "Mitsuboshi",
        "Mopar",
        "Mustang",
        "Nissan",
        "Nissin",
        "OE+",
        "OE Brand",
        "OEM",
        "Oldsmobile",
        "Opel",
        "Pathfinder",
        "Peugeot",
        "Pilot",
        "Plymouth",
        "Pontiac",
        "Porsche",
        "Promaster",
        "Ram",
        "Range Rover",
        "Renault",
        "Rogue",
        "Rolls-Royce",
        "Rover",
        "Saab",
        "Saturn",
        "Scion",
        "Shark",
        "Škoda",
        "Smart",
        "Speedmotor",
        "Standard",
        "Subaru",
        "Suburban",
        "Suburban Manufacturing",
        "Sumitomo",
        "Suzuki",
        "Tesla",
        "Toyota",
        "Triumph",
        "TRW",
        "URO",
        "VAG",
        "Vauxhall",
        "Visteon",
        "Volkswagen",
        "Volvo",
        "WABCO",
        "Western Star",
        "Yamaha",
        "Yukon",
        "Unbranded",
        "Not Specified",
    ]
    # Начальные параметры для первой страницы
    params = {
        "Brand": "Audi",
        "Items%20Included": "ABS%20Pump",
        "LH_ItemCondition": "1000",
        "mag": "1",
        "rt": "nc",
    }
    conditions = ["1000", "2500", "3000"]
    for brand in all_brands:
        logger.info(f"Обработка бренда: {brand}")
        params["Brand"] = brand
        for condition in conditions:
            params["LH_ItemCondition"] = condition
            logger.info(f"Обработка состояния: {condition}")

            while current_url:
                # Проверяем максимальное количество страниц
                # if max_pages is not None and page_count > max_pages:
                #     logger.info(f"Достигнуто максимальное количество страниц: {max_pages}")
                #     break

                logger.info(f"Обработка страницы {page_count}...")

                # Для всех страниц, кроме первой, добавляем параметр пагинации
                if page_count > 1:
                    params["_pgn"] = page_count

                # Обрабатываем текущую страницу
                next_url = scrape_page(current_url, params)

                # Сохраняем промежуточные результаты каждые 10 страниц
                if page_count % 10 == 0:
                    temp_df = pd.DataFrame(all_hrefs, columns=["href"])
                    file_name_temp = f"all_urls_page_{page_count}.csv"
                    output_temp_csv_path = data_directory / file_name_temp
                    temp_df.to_csv(output_temp_csv_path, index=False)
                    logger.info(
                        f"Промежуточное сохранение: {len(all_hrefs)} ссылок в all_urls_page_{page_count}.csv"
                    )

                # Если есть следующий URL, продолжаем, иначе завершаем
                if next_url:
                    current_url = next_url
                    page_count += 1

                    # Пауза между запросами с небольшой рандомизацией
                    delay = random.uniform(1.8, 3.2)
                    logger.info(f"Пауза перед следующим запросом: {delay:.2f} сек")
                    time.sleep(delay)
                else:
                    logger.info("Достигнут конец пагинации")
                    break

            # Сохраняем в CSV с помощью pandas
            file_name = "all_urls.csv"
            output_csv_path = data_directory / file_name
            df = pd.DataFrame(all_hrefs, columns=["href"])
            df.to_csv(output_csv_path, index=False)

            logger.info(f"Собрано {len(all_hrefs)} ссылок и сохранено в all_urls.csv")
            get_product_th(all_hrefs, 40)
            # return all_hrefs


def get_product_th(urls, threads=10):
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
    # file_name = "all_urls.csv"
    # output_csv_path = data_directory / file_name
    # Читаем CSV-файл
    # try:
    #     df = pd.read_csv(output_csv_path)
    # except FileNotFoundError:
    #     logger.error("Файл all_urls.csv не найден!")
    #     return

    # total_urls = len(df)
    # logger.info(f"Всего найдено {total_urls} URL для загрузки")

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
                    logger.debug(f"Файл {filename} уже существует, пропускаем")
                return True  # URL уже обработан

            # Выполняем запрос
            # response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            src = make_request(url)
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
        results = list(executor.map(process_url, urls))  # df["href"])

    # Сохраняем итоговый маппинг
    mapping_df = pd.DataFrame(url_mapping)
    mapping_df.to_csv(mapping_file, index=False)

    end_time = time.time()
    total_time = end_time - start_time
    success_count = sum(1 for r in results if r)

    # logger.info(
    #     f"Загрузка завершена! Успешно обработано {success_count} из {total_urls} URL"
    # )
    logger.info(f"Затраченное время: {total_time:.2f} секунд")

    return success_count



if __name__ == "__main__":
    # get_pagination()
    # get_pagination_th(20)
    # get_product()
    # get_product_th(20)

