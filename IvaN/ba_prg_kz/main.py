import json
import queue
import random
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

# Настройки
MAX_RETRIES = 10  # Максимальное количество повторных попыток
RETRY_DELAY = 5  # Пауза между повторными попытками в секундах

current_directory = Path.cwd()
json_directory = current_directory / "json"
data_directory = current_directory / "data"
log_directory = current_directory / "log"
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

input_csv_file = data_directory / "output.csv"
log_file_path = log_directory / "log_message.log"
proxy_file = data_directory / "proxy.txt"  # Путь к файлу с прокси

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# Предполагаем, что headers определены где-то в вашем коде
headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "origin": "https://ba.prg.kz",
    "priority": "u=1, i",
    "referer": "https://ba.prg.kz/",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

# Глобальный список прокси (будет доступен всем потокам)
ALL_PROXIES = []


# Функция для загрузки прокси из файла
def load_proxies():
    if not proxy_file.exists():
        logger.warning(
            f"Файл с прокси {proxy_file} не найден, используем локальное соединение"
        )
        return []

    try:
        with open(proxy_file, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]

        logger.info(f"Загружено {len(proxies)} прокси из файла")
        return proxies
    except Exception as e:
        logger.error(f"Ошибка при чтении файла с прокси: {str(e)}")
        return []


# Функция для получения случайного прокси из списка
def get_random_proxy():
    if not ALL_PROXIES:
        return None
    return random.choice(ALL_PROXIES)


# Функция для чтения ID компаний из CSV файла
def read_companies_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["bin"].tolist()


# Функция получения и сохранения JSON данных с использованием прокси
def get_json(id_company, q):
    file_name = json_directory / f"{id_company}.json"

    # Если файл уже существует, пропускаем
    if file_name.exists():
        logger.warning(f"Файл для ID {id_company} уже существует, пропускаем")
        q.task_done()
        return

    retry_count = 0

    while retry_count < MAX_RETRIES:
        # Для каждой попытки выбираем случайный прокси
        proxy = get_random_proxy()
        proxies = None

        if proxy:
            proxies = {"http": proxy, "https": proxy}
            logger.debug(
                f"Используем случайный прокси {proxy} для ID {id_company} (попытка {retry_count+1})"
            )

        try:
            params = {
                "id": id_company,
                "lang": "ru",
            }

            response = requests.get(
                "https://apiba.prgapp.kz/CompanyFullInfo",
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=30,
            )

            # Проверяем статус ответа
            if response.status_code == 200:
                try:
                    data = response.json()
                    with open(file_name, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    if proxy:
                        logger.info(
                            f"Успешно сохранен файл для ID {id_company} (прокси: {proxy})"
                        )
                    else:
                        logger.info(
                            f"Успешно сохранен файл для ID {id_company} (без прокси)"
                        )
                    q.task_done()
                    return
                except ValueError:
                    logger.error(f"Ошибка: ответ для ID {id_company} не содержит JSON")
            else:
                if proxy:
                    logger.error(
                        f"Ошибка для ID {id_company}: статус {response.status_code} (прокси: {proxy})"
                    )
                else:
                    logger.error(
                        f"Ошибка для ID {id_company}: статус {response.status_code} (без прокси)"
                    )

            # Если ответ не 200 или произошла ошибка парсинга JSON
            retry_count += 1
            logger.warning(
                f"Попытка {retry_count}/{MAX_RETRIES} для ID {id_company}, пауза {RETRY_DELAY} сек."
            )
            time.sleep(RETRY_DELAY)

        except requests.exceptions.RequestException as e:
            if proxy:
                logger.error(
                    f"Ошибка запроса для ID {id_company} (прокси: {proxy}): {str(e)}"
                )
            else:
                logger.error(
                    f"Ошибка запроса для ID {id_company} (без прокси): {str(e)}"
                )

            retry_count += 1
            logger.error(
                f"Попытка {retry_count}/{MAX_RETRIES} для ID {id_company}, пауза {RETRY_DELAY} сек."
            )
            time.sleep(RETRY_DELAY)

    logger.warning(f"Исчерпаны все попытки для ID {id_company}")
    q.task_done()


# Функция для работы потока
def worker(q, thread_id):
    logger.info(f"Запущен поток {thread_id}")

    while True:
        id_company = q.get()
        if id_company is None:  # Сигнал для завершения потока
            q.task_done()
            break
        get_json(id_company, q)


# Основная функция
def process_companies(num_threads=5):
    # Загружаем прокси в глобальный список
    global ALL_PROXIES
    ALL_PROXIES = load_proxies()

    if ALL_PROXIES:
        logger.info(f"Будет использовано {len(ALL_PROXIES)} разных прокси для запросов")
    else:
        logger.info("Прокси не найдены, будем использовать локальное соединение")

    # Получаем список ID компаний
    company_ids = read_companies_from_csv(input_csv_file)
    logger.info(f"Загружено {len(company_ids)} ID компаний")

    # Создаем очередь и потоки
    q = queue.Queue()
    threads = []

    # Запускаем рабочие потоки
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(q, i))
        t.daemon = True
        t.start()
        threads.append(t)

    # Добавляем ID компаний в очередь
    for id_company in company_ids:
        q.put(id_company)

    # Дожидаемся завершения обработки очереди
    q.join()

    # Останавливаем потоки
    for i in range(num_threads):
        q.put(None)

    # Дожидаемся завершения всех потоков
    for t in threads:
        t.join()

    logger.info("Обработка завершена!")


# Пример использования
if __name__ == "__main__":
    num_threads = 50  # Укажите желаемое количество потоков

    process_companies(num_threads)
