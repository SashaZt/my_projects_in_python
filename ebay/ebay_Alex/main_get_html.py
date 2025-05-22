import concurrent.futures
import hashlib
import json
import random
import time
from pathlib import Path
from threading import Lock
from urllib.parse import quote, quote_plus, urlencode

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from requests.exceptions import HTTPError
from scrap import scrap_online
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

# Инициализация директорий
current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
html_directory = current_directory / "html"
progress_directory = current_directory / "progress"
temp_directory = current_directory / "temp"
json_directory = temp_directory / "json"
html_directory = temp_directory / "html"
config_directory = current_directory / "config"
temp_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)


config_file = config_directory / "config.json"

# Заголовки HTTP-запросов
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


# Глобальный список прокси
proxy_list = []


def encode_ebay_special_chars(value):
    """
    Специальная функция кодирования для eBay, которая обрабатывает особые символы
    так же, как это делает браузер на eBay.

    Args:
        value (str): Исходная строка

    Returns:
        str: Закодированная строка для eBay
    """
    # Предварительно заменяем специальные символы как на eBay
    replacements = {
        ".": "%252E",  # Точка кодируется как %252E в eBay
        "/": "%252F",  # Слэш кодируется как %252F в eBay
        "&": "%2526",  # Амперсанд кодируется особым образом
        "+": "%252B",  # Плюс кодируется особым образом
        "(": "%2528",  # Скобки кодируются особым образом
        ")": "%2529",  # Скобки кодируются особым образом
    }

    # Применяем замены
    for char, replacement in replacements.items():
        value = value.replace(char, replacement)

    # Заменяем пробелы на %2520 (двойное кодирование пробела в eBay)
    value = value.replace(" ", "%2520")

    return value


def create_ebay_url(base_url, params, ebay_order=None):
    """
    Создает URL для eBay, точно соответствующий формату браузера.

    Args:
        base_url (str): Базовый URL без параметров
        params (dict): Словарь параметров запроса

    Returns:
        str: Точно сформированный URL в формате eBay
    """
    # Стандартный порядок параметров в eBay
    ebay_order = ["LH_ItemCondition", "Items Included", "Brand", "mag", "_pgn"]

    # Преобразуем параметры в формат eBay
    encoded_pairs = []

    for key in ebay_order:
        if key in params:
            # Кодируем ключи и значения в стиле eBay
            if key == "Items Included":
                encoded_key = "Items%2520Included"
            else:
                encoded_key = key

            value = params[key]

            # Кодируем значения с пробелами и специальными символами
            if isinstance(value, str):
                # Заменяем пробелы на %2520
                encoded_value = value.replace(" ", "%2520")

                # Заменяем специальные символы
                encoded_value = encoded_value.replace(".", "%252E")
                encoded_value = encoded_value.replace("/", "%252F")
                encoded_value = encoded_value.replace("&", "%2526")
                encoded_value = encoded_value.replace("+", "%252B")
                encoded_value = encoded_value.replace("(", "%2528")
                encoded_value = encoded_value.replace(")", "%2529")
            else:
                # Для числовых значений просто преобразуем в строку
                encoded_value = str(value)

            encoded_pairs.append(f"{encoded_key}={encoded_value}")

    # Добавляем оставшиеся параметры, которых нет в стандартном порядке
    for key, value in params.items():
        if key not in ebay_order:
            # Кодируем значения с пробелами и специальными символами
            if isinstance(value, str):
                # Заменяем пробелы на %2520
                encoded_value = value.replace(" ", "%2520")

                # Заменяем специальные символы
                encoded_value = encoded_value.replace(".", "%252E")
                encoded_value = encoded_value.replace("/", "%252F")
                encoded_value = encoded_value.replace("&", "%2526")
                encoded_value = encoded_value.replace("+", "%252B")
                encoded_value = encoded_value.replace("(", "%2528")
                encoded_value = encoded_value.replace(")", "%2529")
            else:
                # Для числовых значений просто преобразуем в строку
                encoded_value = str(value)

            encoded_pairs.append(f"{key}={encoded_value}")

    # Соединяем параметры в строку запроса
    query_string = "&".join(encoded_pairs)

    # Формируем полный URL
    full_url = f"{base_url}?{query_string}"
    return full_url


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
@retry(
    stop=stop_after_attempt(10),  # Максимум 10 попыток
    wait=wait_fixed(10),  # Задержка 10 секунд между попытками
    retry=retry_if_exception_type(HTTPError),  # Повторять при HTTPError
)
def make_request(url):
    """
    Выполняет HTTP-запрос с автоматическими повторными попытками при ошибках.
    """
    # Получаем случайный прокси
    proxies = get_random_proxy()
    # proxies = {
    #     "http": "http://5.79.73.131:13010",
    #     "https": "http://5.79.73.131:13010",
    # }
    response = requests.get(
        url,
        proxies=proxies,
        headers=headers,
        timeout=10,
        verify=False,
    )
    response.raise_for_status()  # Вызывает HTTPError, если статус не 200

    return response.text


# Декоратор для повторных попыток
@retry(
    stop=stop_after_attempt(10),  # Максимум 10 попыток
    wait=wait_fixed(10),  # Задержка 10 секунд между попытками
    retry=retry_if_exception_type(HTTPError),  # Повторять при HTTPError
)
def make_request_one_html(url):
    """
    Выполняет HTTP-запрос с автоматическими повторными попытками при ошибках.
    """
    proxies = {
        "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
        "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
    }
    proxies = get_random_proxy()
    response = requests.get(
        url,
        proxies=proxies,
        headers=headers,
        timeout=10,
        verify=False,
    )
    response.raise_for_status()  # Вызывает HTTPError, если статус не 200

    return response.text


def load_progress():
    """
    Загружает информацию о прогрессе скрапинга
    """
    progress_file = progress_directory / "scraping_progress.json"

    if progress_file.exists():
        try:
            with open(progress_file, "r") as f:
                progress = json.load(f)
                logger.info("Загружена информация о прогрессе")
                return progress
        except Exception as e:
            logger.error(f"Ошибка при загрузке прогресса: {str(e)}")

    # Возвращаем начальный прогресс
    return {
        "completed_brands": [],
        "current_brand": None,
        "completed_conditions": [],
        "current_condition": None,
        "current_page": 1,
        "completed_urls": [],
    }


def save_progress(progress):
    """
    Сохраняет информацию о прогрессе скрапинга
    """
    progress_file = progress_directory / "scraping_progress.json"

    try:
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=4)
        # logger.info("Сохранена информация о прогрессе")
    except Exception as e:
        logger.error(f"Ошибка при сохранении прогресса: {str(e)}")


def merge_collected_urls():
    """
    Объединяет все CSV-файлы с URL в один файл
    """
    csv_files = list(data_directory.glob("urls_*.csv"))

    if not csv_files:
        logger.warning("Не найдены CSV-файлы с URL")
        return pd.DataFrame(columns=["href"])

    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file}: {str(e)}")

    if not dfs:
        return pd.DataFrame(columns=["href"])

    # Объединяем все DataFrame и удаляем дубликаты
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates()

    # Сохраняем объединенный файл
    output_file = data_directory / "all_urls_combined.csv"
    combined_df.to_csv(output_file, index=False)

    logger.info(f"Объединено {len(combined_df)} уникальных URL в {output_file}")
    return combined_df


def scrape_page(url, params=None):
    """
    Обрабатывает одну страницу и извлекает ссылки на товары

    Args:
        url (str): Базовый URL страницы
        params (dict): Параметры запроса

    Returns:
        tuple: (next_url, page_hrefs) - URL следующей страницы и список найденных ссылок
    """
    page_hrefs = []

    try:
        # Создаем полный URL с параметрами
        if params:
            full_url = create_ebay_url(url, params)
        else:
            full_url = url

        logger.info(f"Запрашиваем: {full_url}")

        # Выполняем запрос
        src = make_request(full_url)
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
                                cleaned_url = item_url.split("?")[0]
                                page_hrefs.append(cleaned_url)
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

                # Собираем все найденные ссылки
                for item in items:
                    if "href" in item.attrs:
                        page_hrefs.append(item["href"])

        # Проверяем наличие следующей страницы
        next_button = soup.select_one("a.pagination__next")

        # Проверяем, что кнопка существует, имеет атрибут href и не отключена
        if next_button and "href" in next_button.attrs:
            disabled_next = soup.select_one('a.pagination__next[aria-disabled="true"]')

            if not disabled_next:
                next_url = next_button["href"]
                logger.info(f"Найдена ссылка на следующую страницу: {next_url}")
                return next_url, page_hrefs

        return None, page_hrefs
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {str(e)}")
        return None, []


def run_scraper(max_pages=None, threads=20, resume=True):
    """
    Основная функция для запуска скрапера, который сразу скачивает страницы товаров
    после обработки каждой страницы пагинации.

    Args:
        max_pages (int, optional): Максимальное количество страниц для каждой комбинации
        threads (int): Количество потоков для скачивания страниц товаров
        resume (bool): Продолжить с последнего сохраненного прогресса
    """
    # Загружаем прокси
    load_proxies()

    # Загружаем прогресс, если нужно
    progress = (
        load_progress()
        if resume
        else {
            "completed_brands": [],
            "current_brand": None,
            "completed_conditions": [],
            "current_condition": None,
            "completed_price_ranges": [],
            "current_price_range": None,
            "current_page": 1,
            "completed_urls": [],
        }
    )

    # Базовый URL (без параметров)
    base_url = "https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?rt=nc&mag=1&Items%2520Included=ABS%2520Accumulator"

    # Список брендов (сокращен для примера, используйте полный список)
    all_brands = [
        # "1",
        # "1&1",
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

    # Условия товаров
    conditions = ["1000", "2500", "3000"]

    # Диапазоны цен
    price_ranges = [
        {"name": "low", "params": {"_udhi": "75"}},  # До 75 долларов
        {
            "name": "medium",
            "params": {"_udlo": "75", "_udhi": "150"},
        },  # От 75 до 150 долларов
        {"name": "high", "params": {"_udlo": "150"}},  # От 150 долларов и выше
    ]

    # Пропускаем уже обработанные бренды
    if progress["completed_brands"]:
        logger.info(
            f"Пропускаем {len(progress['completed_brands'])} обработанных брендов"
        )
        all_brands = [
            brand for brand in all_brands if brand not in progress["completed_brands"]
        ]

    # Если есть текущий бренд, начинаем с него
    if progress["current_brand"] and progress["current_brand"] in all_brands:
        start_index = all_brands.index(progress["current_brand"])
        all_brands = all_brands[start_index:]
        logger.info(f"Начинаем с бренда: {progress['current_brand']}")

    # Общий счетчик обработанных URL и страниц
    total_processed_urls = 0
    total_processed_pages = 0

    # Перебираем бренды
    for brand in all_brands:
        logger.info(f"Обработка бренда: {brand}")
        progress["current_brand"] = brand

        # Пропускаем уже обработанные условия для текущего бренда
        current_conditions = conditions
        if brand == progress["current_brand"] and progress["completed_conditions"]:
            logger.info(
                f"Пропускаем {len(progress['completed_conditions'])} обработанных условий"
            )
            current_conditions = [
                c for c in conditions if c not in progress["completed_conditions"]
            ]

        # Сбрасываем список обработанных условий для нового бренда
        if brand != progress["current_brand"]:
            progress["completed_conditions"] = []

        # Перебираем условия
        for condition in current_conditions:
            logger.info(f"Обработка состояния: {condition}")
            progress["current_condition"] = condition

            # Пропускаем уже обработанные ценовые диапазоны для текущего условия
            current_price_ranges = price_ranges
            if (
                brand == progress["current_brand"]
                and condition == progress["current_condition"]
                and progress.get("completed_price_ranges")
            ):
                logger.info(
                    f"Пропускаем {len(progress['completed_price_ranges'])} обработанных ценовых диапазонов"
                )
                current_price_ranges = [
                    pr
                    for pr in price_ranges
                    if pr["name"] not in progress["completed_price_ranges"]
                ]

            # Сбрасываем список обработанных ценовых диапазонов для нового условия
            if condition != progress["current_condition"]:
                progress["completed_price_ranges"] = []

            # Перебираем ценовые диапазоны
            for price_range in current_price_ranges:
                logger.info(f"Обработка ценового диапазона: {price_range['name']}")
                progress["current_price_range"] = price_range["name"]

                # Базовые параметры запроса
                params = {
                    "Brand": brand,
                    "Items Included": "ABS Pump",  # Используем пробелы вместо %20
                    "LH_ItemCondition": condition,
                    "mag": "1",
                }

                # Добавляем параметры ценового диапазона
                params.update(price_range["params"])

                # Устанавливаем начальную страницу
                current_page = 1
                if (
                    brand == progress["current_brand"]
                    and condition == progress["current_condition"]
                    and price_range["name"] == progress["current_price_range"]
                ):
                    current_page = progress["current_page"]
                    logger.info(f"Начинаем с страницы {current_page}")
                else:
                    progress["current_page"] = 1

                # Для всех страниц, кроме первой, добавляем параметр пагинации
                if current_page > 1:
                    params["_pgn"] = str(current_page)

                # Цикл по страницам
                next_url = None
                while True:
                    # Проверяем ограничение по максимальному количеству страниц
                    if max_pages is not None and current_page > max_pages:
                        logger.info(
                            f"Достигнуто максимальное количество страниц ({max_pages})"
                        )
                        break

                    logger.info(f"Обработка страницы {current_page}...")

                    # На первой странице или при использовании программной навигации используем параметры
                    if next_url is None:
                        # Обрабатываем текущую страницу и получаем URL товаров
                        next_url, page_hrefs = scrape_page(base_url, params)
                    else:
                        # Если есть прямая ссылка на следующую страницу, используем её
                        next_url, page_hrefs = scrape_page(next_url)

                    # Увеличиваем счетчик обработанных страниц
                    total_processed_pages += 1

                    # Если на странице нашлись товары, сразу скачиваем их
                    if page_hrefs:
                        logger.info(
                            f"Найдено {len(page_hrefs)} ссылок на странице {current_page}. Начинаем загрузку..."
                        )
                        brand_safe = brand.replace("/", "_")
                        price_range_name = price_range["name"]

                        # Сохраняем URL для отчетности с указанием ценового диапазона
                        urls_df = pd.DataFrame(page_hrefs, columns=["href"])
                        file_name = f"urls_{brand_safe}_{condition}_{price_range_name}_page_{current_page}.csv"
                        output_path = data_directory / file_name
                        urls_df.to_csv(output_path, index=False)

                        # Запускаем многопоточную загрузку страниц товаров
                        success_count = get_product_th(page_hrefs, threads=threads)

                        # Добавляем успешно загруженные URL в список завершенных
                        progress["completed_urls"].extend(page_hrefs)

                        # Увеличиваем общий счетчик
                        total_processed_urls += success_count

                        logger.info(
                            f"Загружено {success_count}/{len(page_hrefs)} товаров со страницы {current_page}"
                        )
                        logger.info(
                            f"Всего обработано: {total_processed_urls} товаров, {total_processed_pages} страниц"
                        )
                    else:
                        logger.info(f"На странице {current_page} не найдено товаров")

                    # Сохраняем прогресс
                    progress["current_page"] = current_page
                    # save_progress(progress)

                    # Если есть следующий URL, продолжаем, иначе завершаем
                    if next_url:
                        current_page += 1

                        # Обновляем параметр страницы для программной навигации
                        if "_pgn" in params:
                            params["_pgn"] = str(current_page)
                        elif current_page > 1:
                            params["_pgn"] = str(current_page)

                        # Пауза между запросами с небольшой рандомизацией
                        delay = random.uniform(1.8, 3.2)
                        logger.info(f"Пауза перед следующим запросом: {delay:.2f} сек")
                        # time.sleep(delay)
                    else:
                        logger.info("Достигнут конец пагинации для текущей комбинации")
                        break

                # Отмечаем ценовой диапазон как обработанный
                if "completed_price_ranges" not in progress:
                    progress["completed_price_ranges"] = []
                progress["completed_price_ranges"].append(price_range["name"])
                progress["current_page"] = 1
                # save_progress(progress)

                logger.info(
                    f"Завершена обработка комбинации {brand}/{condition}/{price_range['name']}"
                )

            # Отмечаем условие как обработанное
            progress["completed_conditions"].append(condition)
            progress["completed_price_ranges"] = []
            progress["current_page"] = 1
            # save_progress(progress)

            logger.info(f"Завершена обработка комбинации {brand}/{condition}")

        # Отмечаем бренд как обработанный
        progress["completed_brands"].append(brand)
        progress["completed_conditions"] = []
        progress["completed_price_ranges"] = []
        # save_progress(progress)

        logger.info(f"Завершена обработка бренда {brand}")

    logger.info(
        f"Скрапинг завершен. Обработано {total_processed_urls} товаров на {total_processed_pages} страницах."
    )

    # Объединяем все собранные URL для итогового отчета
    all_csv_files = list(data_directory.glob("urls_*.csv"))
    all_urls = []

    for file in all_csv_files:
        try:
            df = pd.read_csv(file)
            all_urls.extend(df["href"].tolist())
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file}: {str(e)}")

    # Удаляем дубликаты
    unique_urls = list(set(all_urls))

    # Сохраняем итоговый отчет
    final_df = pd.DataFrame(unique_urls, columns=["href"])
    final_path = data_directory / "all_urls_final.csv"
    final_df.to_csv(final_path, index=False)

    logger.info(f"Создан итоговый отчет с {len(unique_urls)} уникальными URL")

    return unique_urls


def get_product_th(urls, threads=10):
    """
    Загружает страницы товаров в параллельном режиме.

    Args:
        urls (list): Список URL для загрузки
        threads (int): Количество потоков для параллельной загрузки. По умолчанию 10.

    Returns:
        int: Количество успешно загруженных страниц
    """
    # Проверяем список URL
    if not urls:
        logger.warning("Список URL пуст")
        return 0

    total_urls = len(urls)
    logger.info(f"Начинаем загрузку {total_urls} страниц товаров")

    # Файл для хранения маппинга
    mapping_file = html_directory / "url_mapping.csv"

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
            src = make_request_one_html(url)
            logger.info(f"файл {output_html_file}")
            # Сохраняем HTML в файл
            output_html_file.write_text(src, encoding="utf-8")
            result = scrap_online(src)
            if result:
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
        results = list(executor.map(process_url, urls))

    # Сохраняем итоговый маппинг
    mapping_df = pd.DataFrame(url_mapping)
    mapping_df.to_csv(mapping_file, index=False)

    end_time = time.time()
    total_time = end_time - start_time
    success_count = sum(1 for r in results if r)

    logger.info(f"Загрузка завершена: {success_count}/{total_urls} успешно")
    logger.info(f"Затраченное время: {total_time:.2f} секунд")

    return success_count


def main(max_pages=None, threads=20, resume=True):
    """
    Основная функция для запуска процесса скрапинга

    Args:
        max_pages (int, optional): Максимальное количество страниц для каждой комбинации
        threads (int): Количество потоков для скачивания страниц товаров
        resume (bool): Продолжить с прошлого места
    """
    # Шаг 1: Запускаем сбор ссылок с пагинацией
    logger.info("=== Шаг 1: Сбор URL товаров ===")
    all_urls = run_scraper(max_pages=max_pages, resume=resume)

    # # Шаг 2: Если URL не собраны, пытаемся объединить существующие файлы
    # if not all_urls:
    #     logger.info("URL не были собраны, объединяем существующие файлы")
    #     df = merge_collected_urls()
    #     if not df.empty:
    #         all_urls = df["href"].tolist()

    # # Шаг 3: Скачиваем страницы товаров в многопоточном режиме
    # if all_urls:
    #     logger.info(f"=== Шаг 2: Скачивание {len(all_urls)} страниц товаров .===")
    #     success_count = get_product_th(all_urls, threads=threads)
    #     logger.info(f"Скачивание завершено: {success_count}/{len(all_urls)} успешно")
    # else:
    #     logger.warning("Нет URL для скачивания")


if __name__ == "__main__":
    # Пример запуска полного процесса
    while True:
        main(threads=20)
