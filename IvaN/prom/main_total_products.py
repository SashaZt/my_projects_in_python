import concurrent.futures
import csv
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

import requests
from config.logger import logger
from requests.exceptions import HTTPError, RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

# Настройка директорий
current_directory = Path.cwd()
json_products_directory = current_directory / "json_products"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
json_products_directory.mkdir(parents=True, exist_ok=True)
proxy_file = config_directory / "proxy.json"
companies_file = config_directory / "result.json"
proxy_list = []

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://prom.ua",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://prom.ua/c2718447-magazin-tovarov-evropy.html",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "x-apollo-operation-name": "CompanyFiltersQuery",
    "x-forwarded-proto": "https",
    "x-language": "ru",
    "x-requested-with": "XMLHttpRequest",
}


def load_companies(file_path):
    """Load the list of companies from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading companies file: {e}")
        return []


def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if proxy_file.exists():
            with open(proxy_file, "r") as f:
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
    retry=retry_if_exception_type((RequestException, json.JSONDecodeError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
)
def process_company(company):
    """Обработка одной компании с применением случайного прокси"""
    company_id = company["companyId"]
    company_slug = company["companySlug"]

    logger.info(f"Обработка компании: {company_id} ({company_slug})")

    try:
        # Получаем случайный прокси для этого запроса
        proxies = get_random_proxy()

        # Вызываем функцию get_json с прокси
        get_json_with_proxy(company_id, company_slug, proxies)

        return company_id
    except Exception as e:
        logger.error(f"Ошибка при обработке компании {company_id}: {e}")
        raise


def parse_review_date(review_data):
    """Extract the year from the review date."""
    try:
        date_created = review_data.get("dateCreated")
        if date_created:
            return datetime.fromisoformat(date_created).year
        return None
    except (ValueError, TypeError):
        return None


def get_json_with_proxy(company_id, company_slug, proxies):
    """Получение JSON с использованием прокси"""
    json_data = {
        "operationName": "CompanyFiltersQuery",
        "variables": {
            "regionId": None,
            "params": {
                "company_id": company_id,
                "company_name": company_slug,
                "binary_filters": [],
            },
            "company_id": company_id,
        },
        "query": "query CompanyFiltersQuery($company_id: Int!, $params: Any, $sort: String, $regionId: Int = null, $subdomain: String = null) {\n  listing: companyListing(\n    company_id: $company_id\n    params: $params\n    sort: $sort\n    region: {id: $regionId, subdomain: $subdomain}\n  ) {\n    filters {\n      ...FiltersFragment\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FiltersFragment on ListingFilters {\n  total\n  priceChartFilter {\n    ...PriceFilterFragment\n    __typename\n  }\n  binaryFilters {\n    ...PromoBinaryFilterFragment\n    __typename\n  }\n  attributeFilters {\n    ...AttributeFilterFragment\n    __typename\n  }\n  categoryFilter {\n    ...AttributeFilterFragment\n    __typename\n  }\n  productGroupFilter {\n    ...AttributeFilterFragment\n    __typename\n  }\n  deliveryFilter {\n    ...DeliveryFilterFragment\n    __typename\n  }\n  colorFilter {\n    ...AttributeFilterFragment\n    __typename\n  }\n  promoFilter {\n    ...ItemPromoFilterFragment\n    __typename\n  }\n  regionFilter {\n    ...RegionFilterFragment\n    __typename\n  }\n  regionDeliveryFilter {\n    ...RegionFilterFragment\n    __typename\n  }\n  opinionsFilter {\n    ...ProductOpinionsFilterFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceFilterFragment on PriceChartFilter {\n  measureUnit\n  values\n  __typename\n}\n\nfragment PromoBinaryFilterFragment on Filter {\n  name\n  values {\n    selected\n    value\n    count\n    title\n    icon\n    darkIcon\n    displayType\n    image {\n      src\n      srcDark\n      width\n      height\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AttributeFilterFragment on AttributeFilter {\n  name\n  title\n  type\n  min\n  max\n  measureUnit\n  values {\n    position\n    positionInPreview\n    selected\n    value\n    count\n    title\n    position\n    parent\n    used_count\n    colorHex\n    __typename\n  }\n  __typename\n}\n\nfragment DeliveryFilterFragment on Filter {\n  name\n  values {\n    selected\n    value\n    count\n    title\n    __typename\n  }\n  __typename\n}\n\nfragment ProductOpinionsFilterFragment on Filter {\n  name\n  title\n  values {\n    selected\n    value\n    count\n    title\n    __typename\n  }\n  __typename\n}\n\nfragment ItemPromoFilterFragment on Filter {\n  name\n  values {\n    selected\n    value\n    count\n    title\n    icon\n    darkIcon\n    __typename\n  }\n  __typename\n}\n\nfragment RegionFilterFragment on Filter {\n  title\n  name\n  values {\n    selected\n    value\n    count\n    title\n    groupName\n    __typename\n  }\n  __typename\n}",
    }

    file_path = json_products_directory / f"products_{company_id}_{company_slug}.json"

    if file_path.exists():
        logger.info(f"Пропуск существующего файла: {file_path}")
        return

    # Добавляем задержку для избежания блокировки
    time.sleep(random.uniform(1, 3))

    # Используем прокси для запроса
    response = requests.post(
        "https://prom.ua/graphql",
        headers=headers,
        json=json_data,
        proxies=proxies,  # Используем переданный прокси
        timeout=30,
    )

    response.raise_for_status()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)

    logger.info(f"Сохранены данные для компании {company_id} ({company_slug})")


def process_companies(companies, max_workers=10):
    """Многопоточная обработка компаний"""
    results = []

    logger.info(f"Запуск обработки {len(companies)} компаний в {max_workers} потоков")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи на выполнение
        futures = [executor.submit(process_company, company) for company in companies]

        # Обрабатываем результаты по мере их завершения
        for future in concurrent.futures.as_completed(futures):
            try:
                company_id = future.result()
                results.append(company_id)
                logger.info(f"Завершена обработка компании {company_id}")
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")

    return results


def main():
    # Define paths

    # Загружаем прокси
    load_proxies()

    # Если нет прокси, выходим
    if not proxy_list:
        logger.error("Нет доступных прокси, выход из программы")
        return

    # Load companies
    companies = load_companies(companies_file)
    if not companies:
        logger.error(
            "Компании не найдены или произошла ошибка при загрузке файла компаний"
        )
        return

    logger.info(f"Начинаем обрабатывать {len(companies)} компаний")
    processed = process_companies(companies, max_workers=10)
    logger.info(f"Завершено {len(processed)} компаний")


if __name__ == "__main__":
    main()
