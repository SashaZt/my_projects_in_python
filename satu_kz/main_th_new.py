import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
json_directory = current_directory / "json"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
json_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_csv = data_directory / "output.csv"
file_proxy = configuration_directory / "roman.txt"


def p_c_h_j():
    # Прокси-сервер
    proxy = {
        "http": "http://5.79.73.131:13010",
        "https": "http://5.79.73.131:13010",
    }

    # Cookies и Headers
    cookies = {
        "cid": "270153821938440617613145839967091521916",
        "evoauth": "wb5cdecf4c4de459a88a9719d6d85a4d7",
        "timezone_offset": "120",
        "last_search_term": "",
        "user_tracker": "694b374bcae0b670fdef32ed66ce6fb6485f88ae|193.24.221.34|2024-11-30",
        "auth": "5c18ac9a4f6cb3bec14c7df31bbd6ea00f0cacbd",
        "csrf_token": "b0dc3533afe24266b9f754e83dbb165d",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://satu.kz",
        "priority": "u=1, i",
        "referer": "https://satu.kz/c672063-internet-magazin-itmagkz.html",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-forwarded-proto": "https",
        "x-language": "ru",
        "x-requested-with": "XMLHttpRequest",
    }

    json_data = {
        "operationName": "CompanyContactsQuery",
        "variables": {
            "withGroupManagerPhones": False,
            "withWorkingHoursWarning": False,
            "getProductDetails": False,
            "company_id": "company_id",
            "groupId": -1,
            "productId": -1,
        },
        "query": "query CompanyContactsQuery($company_id: Int!, $groupId: Int!, $productId: Long!, $withGroupManagerPhones: Boolean = false, $withWorkingHoursWarning: Boolean = false, $getProductDetails: Boolean = false) {\n  context {\n    context_meta\n    currentRegionId\n    recaptchaToken\n    __typename\n  }\n  company(id: $company_id) {\n    ...CompanyWorkingHoursFragment @include(if: $withWorkingHoursWarning)\n    ...CompanyRatingFragment\n    id\n    name\n    contactPerson\n    contactEmail\n    phones {\n      id\n      description\n      number\n      __typename\n    }\n    addressText\n    isChatVisible\n    mainLogoUrl(width: 100, height: 50)\n    slug\n    isOneClickOrderAllowed\n    isOrderableInCatalog\n    isPackageCPA\n    addressMapDescription\n    region {\n      id\n      __typename\n    }\n    geoCoordinates {\n      id\n      latitude\n      longtitude\n      __typename\n    }\n    branches {\n      id\n      name\n      phones\n      address {\n        region_id\n        country_id\n        city\n        zipCode\n        street\n        regionText\n        __typename\n      }\n      __typename\n    }\n    webSiteUrl\n    site {\n      id\n      isDisabled\n      __typename\n    }\n    operationType\n    __typename\n  }\n  productGroup(id: $groupId) @include(if: $withGroupManagerPhones) {\n    id\n    managerPhones {\n      id\n      number\n      __typename\n    }\n    __typename\n  }\n  product(id: $productId) @include(if: $getProductDetails) {\n    id\n    name\n    image(width: 60, height: 60)\n    price\n    signed_id\n    discountedPrice\n    priceCurrencyLocalized\n    buyButtonDisplayType\n    regions {\n      id\n      name\n      isCity\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CompanyWorkingHoursFragment on Company {\n  id\n  isWorkingNow\n  isOrderableInCatalog\n  scheduleSettings {\n    id\n    currentDayCaption\n    __typename\n  }\n  scheduleDays {\n    id\n    name\n    dayType\n    hasBreak\n    workTimeRangeStart\n    workTimeRangeEnd\n    breakTimeRangeStart\n    breakTimeRangeEnd\n    __typename\n  }\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  __typename\n}",
    }
    return proxy, cookies, headers, json_data


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Функция для загрузки JSON
def fetch_json(
    proxies, company, proxy, cookies, headers, json_data, unique_companies, lock
):
    output_json_file = json_directory / f"{company}.json"
    json_data["variables"]["company_id"] = company
    proxys = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxys, "https": proxys}
    try:
        response = requests.post(
            "https://satu.kz/graphql",
            cookies=cookies,
            proxies=proxies_dict,
            headers=headers,
            json=json_data,
            timeout=60,
        )
        if response.status_code == 200:
            response_data = response.json()
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("data", {}).get("company") is not None:
                    # Добавляем компанию в список уникальных с использованием lock

                    with open(output_json_file, "w", encoding="utf-8") as f:
                        json.dump(response_data, f, ensure_ascii=False, indent=4)
                    # logger.info(f"JSON сохранен: {output_json_file}")
                else:
                    with lock:
                        unique_companies.add(company)

        else:
            pass
            # logger.warning(f"Ошибка ответа {response.status_code} для {company}")
    except requests.exceptions.Timeout:
        pass
        # logger.error(f"Тайм-аут при обработке {company}")
    except requests.exceptions.RequestException as e:
        pass
        # logger.error(f"Ошибка запроса для {company}: {e}")


# Функция для чтения файла уникальных компаний
def read_unique_companies(file_path):
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()


# Функция для получения ID из имён файлов JSON
def get_ids_from_json_files(json_dir):
    ids = set()
    for file in json_dir.glob("*.json"):
        try:
            # Извлекаем ID из имени файла (без расширения)
            ids.add(file.stem)
        except Exception as e:
            logger.warning(f"Ошибка обработки файла {file}: {e}")
    return ids


# Основной запуск с очередями и ThreadPoolExecutor
if __name__ == "__main__":
    total_records = 835001  # Общее количество записей
    total_records = 200001  # Общее количество записей
    start_record = 100001
    batch_size = 10000  # Размер одной партии
    max_workers = 50  # Количество одновременно работающих потоков

    unique_companies_file = data_directory / "unique_companies.csv"
    count = 0
    while True:
        for batch_start in range(start_record, total_records, batch_size):
            proxies = load_proxies()  # Загружаем список всех прокси

            batch_end = min(batch_start + batch_size, total_records)
            all_id = list(range(batch_start, batch_end))

            start_time_now = datetime.now()
            start_time = start_time_now.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"Начало обработки партии: {batch_start}-{batch_end - 1} в {start_time}"
            )

            proxy, cookies, headers, json_data = p_c_h_j()

            # Загрузка уже существующих уникальных компаний
            processed_companies = read_unique_companies(unique_companies_file)

            # Загрузка ID из JSON файлов
            json_ids = get_ids_from_json_files(json_directory)
            logger.info(f"Найдено {len(json_ids)} ID в папке JSON.")
            # Объединение уникальных компаний и ID из JSON файлов
            all_unique_items = list(processed_companies | json_ids)

            # Исключаем ID из processed_companies и json_ids
            all_id = [
                company_id
                for company_id in all_id
                if str(company_id) not in processed_companies
                and str(company_id) not in json_ids
            ]

            logger.info(f"Проверка в этом пуле {len(all_id)}")

            # Проверка на количество элементов в all_id
            if len(all_id) < 10:
                logger.info(
                    f"Партия {batch_start}-{batch_end - 1} уже обработана или слишком мала (менее 10 элементов). Пропуск."
                )
                continue

            unique_companies = set()
            lock = threading.Lock()  # Для защиты доступа к unique_companies

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_id = {
                    executor.submit(
                        fetch_json,
                        proxies,
                        company_id,
                        proxy,
                        cookies,
                        headers,
                        json_data,
                        unique_companies,
                        lock,
                    ): company_id
                    for company_id in all_id
                }

                for future in as_completed(future_to_id):
                    company_id = future_to_id[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Ошибка при обработке ID {company_id}: {e}")

            # Сохранение уникальных компаний в CSV (добавляем новые компании)
            with open(unique_companies_file, "a", encoding="utf-8") as f:
                for company in unique_companies:
                    if company not in processed_companies:  # Проверка на уникальность
                        f.write(f"{company}\n")
        count += 1
        logger.info(f"Круг {count}")
        # logger.info(
        #     f"Уникальные компании из партии {batch_start}-{batch_end - 1} сохранены в {unique_companies_file}"
        # )

        # # Рассчитываем длительность
        # end_time_now = datetime.now()
        # end_time = end_time_now.strftime("%Y-%m-%d %H:%M:%S")
        # duration = (end_time_now - start_time_now).total_seconds()
        # logger.info(
        #     f"Партия {batch_start}-{batch_end - 1} завершена в {end_time}. Длительность: {duration:.2f} секунд."
        # )
