import concurrent.futures
import csv
import json
import os
import random
import time
from pathlib import Path
from threading import Lock

import requests
from logger import logger
from requests.exceptions import HTTPError, RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

# Настройка директорий
current_directory = Path.cwd()
json_directory = current_directory / "json"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
proxy_file = config_directory / "proxy.json"

# Файл для сохранения прогресса обработки
PROGRESS_FILE = current_directory / "check.csv"
BATCH_SIZE = 100  # Размер пакета для сохранения прогресса

# Заголовки запроса
headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://prom.ua",
    "priority": "u=1, i",
    "referer": "https://prom.ua/c2810486-nicegarden.html",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "x-apollo-operation-name": "CompanyContactsQuery",
    "x-forwarded-proto": "https",
    "x-language": "ru",
    "x-requested-with": "XMLHttpRequest",
}

# Глобальные переменные
proxy_list = []
processed_ids = set()  # Множество для хранения уже обработанных ID
progress_lock = Lock()  # Блокировка для защиты от одновременной записи в CSV-файл
NUM_THREADS = 10  # Количество потоков


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


def load_processed_ids():
    """
    Загружает список уже обработанных ID из CSV-файла
    """
    global processed_ids
    if not PROGRESS_FILE.exists():
        return

    try:
        with open(PROGRESS_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            # Пропускаем заголовок, если он есть
            header = next(reader, None)
            if header and header[0] != "id":
                # Если первая строка не заголовок, то это ID
                processed_ids.add(int(header[0]))

            # Читаем остальные ID
            for row in reader:
                if row and row[0].isdigit():
                    processed_ids.add(int(row[0]))

        logger.info(
            f"Загружено {len(processed_ids)} обработанных ID из {PROGRESS_FILE}"
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке обработанных ID: {str(e)}")


def save_batch_progress(ids_batch):
    """
    Сохраняет пакет обработанных ID в CSV-файл
    """
    with progress_lock:
        try:
            file_exists = PROGRESS_FILE.exists()

            with open(PROGRESS_FILE, "a", newline="") as file:
                writer = csv.writer(file)

                # Записываем заголовок, если файл новый
                if not file_exists:
                    writer.writerow(["id"])

                # Записываем каждый ID из пакета
                for company_id in ids_batch:
                    writer.writerow([company_id])

            logger.info(f"Сохранен пакет из {len(ids_batch)} обработанных ID")
        except Exception as e:
            logger.error(f"Ошибка при сохранении прогресса: {str(e)}")


@retry(
    stop=stop_after_attempt(5),  # Максимум 5 попыток
    wait=wait_fixed(5),  # Задержка 5 секунд между попытками
    retry=retry_if_exception_type(
        (HTTPError, RequestException)
    ),  # Повторять при ошибках
)
def get_json(company_id):
    """
    Запрос данных компании по её ID с использованием случайного прокси
    """
    # Проверяем, был ли ID уже обработан
    if company_id in processed_ids:
        return None

    # Проверяем, существует ли уже файл для этой компании
    file_name = json_directory / f"company_id_{company_id}.json"
    if file_name.exists():
        return company_id  # Возвращаем ID как обработанный

    # Получаем случайный прокси для запроса
    proxy = get_random_proxy()

    json_data = {
        "operationName": "CompanyContactsQuery",
        "variables": {
            "withGroupManagerPhones": False,
            "withWorkingHoursWarning": False,
            "getProductDetails": False,
            "company_id": company_id,
            "groupId": -1,
            "productId": -1,
        },
        "query": "query CompanyContactsQuery($company_id: Int!, $groupId: Int!, $productId: Long!, $withGroupManagerPhones: Boolean = false, $withWorkingHoursWarning: Boolean = false, $getProductDetails: Boolean = false) {\n  context {\n    context_meta\n    currentRegionId\n    recaptchaToken\n    __typename\n  }\n  company(id: $company_id) {\n    ...CompanyWorkingHoursFragment @include(if: $withWorkingHoursWarning)\n    ...CompanyRatingFragment\n    id\n    name\n    contactPerson\n    contactEmail\n    phones {\n      id\n      description\n      number\n      __typename\n    }\n    addressText\n    isChatVisible\n    mainLogoUrl(width: 100, height: 50)\n    slug\n    isOneClickOrderAllowed\n    isOrderableInCatalog\n    isPackageCPA\n    addressMapDescription\n    region {\n      id\n      __typename\n    }\n    geoCoordinates {\n      id\n      latitude\n      longtitude\n      __typename\n    }\n    branches {\n      id\n      name\n      phones\n      address {\n        region_id\n        country_id\n        city\n        zipCode\n        street\n        regionText\n        __typename\n      }\n      __typename\n    }\n    webSiteUrl\n    site {\n      id\n      isDisabled\n      __typename\n    }\n    operationType\n    __typename\n  }\n  productGroup(id: $groupId) @include(if: $withGroupManagerPhones) {\n    id\n    managerPhones {\n      id\n      number\n      __typename\n    }\n    __typename\n  }\n  product(id: $productId) @include(if: $getProductDetails) {\n    id\n    name\n    image(width: 60, height: 60)\n    price\n    signed_id\n    discountedPrice\n    priceCurrencyLocalized\n    buyButtonDisplayType\n    regions {\n      id\n      name\n      isCity\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CompanyWorkingHoursFragment on Company {\n  id\n  isWorkingNow\n  isOrderableInCatalog\n  scheduleSettings {\n    id\n    currentDayCaption\n    __typename\n  }\n  scheduleDays {\n    id\n    name\n    dayType\n    hasBreak\n    workTimeRangeStart\n    workTimeRangeEnd\n    breakTimeRangeStart\n    breakTimeRangeEnd\n    __typename\n  }\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  deliveryStats {\n    id\n    deliverySpeed\n    __typename\n  }\n  __typename\n}",
    }

    try:
        response = requests.post(
            "https://prom.ua/graphql",
            headers=headers,
            json=json_data,
            proxies=proxy,
            timeout=30,
        )

        # Проверка на ошибки HTTP-запроса
        response.raise_for_status()

        # Обработка JSON
        data = response.json()

        # Проверяем наличие данных компании
        company = data.get("data", {}).get("company", {})

        # Сохраняем данные только если компания существует
        if company:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(
                f"Успешно получены данные для компании ID: {company_id}, прокси: {proxy['http'] if proxy else 'нет'}"
            )
        # else:
        #     logger.info(f"Компания ID: {company_id} не существует или недоступна")

        # Добавляем небольшую случайную задержку для снижения нагрузки на сервер
        time.sleep(random.uniform(0.2, 1.0))

        return company_id  # Возвращаем ID как обработанный

    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON для компании ID: {company_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при запросе данных компании ID: {company_id}: {str(e)}")
        raise  # Перебрасываем исключение для работы retry


def process_range(start_id, end_id, thread_id):
    """
    Обрабатывает диапазон company_id и сохраняет прогресс пакетами
    """
    batch = []  # Временный список для накопления обработанных ID

    for company_id in range(start_id, end_id + 1):
        try:
            # Обрабатываем запрос и получаем ID, если он был успешно обработан
            processed_id = get_json(company_id)

            if processed_id:
                batch.append(processed_id)

                # Когда накопили достаточное количество ID, сохраняем их
                if len(batch) >= BATCH_SIZE:
                    save_batch_progress(batch)
                    # Обновляем глобальное множество обработанных ID
                    with progress_lock:
                        processed_ids.update(batch)
                    batch = []  # Очищаем пакет

        except Exception as e:
            logger.error(
                f"Не удалось обработать компанию ID: {company_id} после всех попыток: {str(e)}"
            )

    # Сохраняем оставшиеся ID, если они есть
    if batch:
        save_batch_progress(batch)
        with progress_lock:
            processed_ids.update(batch)

    # logger.info(f"Поток {thread_id} завершил обработку диапазона {start_id}-{end_id}")


def main():
    """
    Основная функция для запуска многопоточной обработки
    """
    # Загружаем прокси сервера
    load_proxies()

    # Загружаем уже обработанные ID
    load_processed_ids()

    # Определяем диапазон ID компаний для обработки
    start_id = 1
    end_id = 4000000

    # Количество компаний для обработки
    total_companies = end_id - start_id + 1

    # Разделение работы между потоками
    companies_per_thread = total_companies // NUM_THREADS

    # Создаем список задач для каждого потока
    tasks = []
    for i in range(NUM_THREADS):
        thread_start = start_id + i * companies_per_thread
        thread_end = thread_start + companies_per_thread - 1

        # Для последнего потока берем все оставшиеся компании
        if i == NUM_THREADS - 1:
            thread_end = end_id

        tasks.append((thread_start, thread_end, i))

    # Запускаем пул потоков
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Создаем список задач и передаем каждую в executor
        futures = [
            executor.submit(process_range, start, end, thread_id)
            for start, end, thread_id in tasks
        ]

        # Ожидаем завершения всех задач
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Ошибка в потоке выполнения: {str(e)}")

    logger.info("Обработка завершена.")


if __name__ == "__main__":
    main()
