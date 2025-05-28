import json
import random
import threading
import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

import urllib3
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    ProxyError,
    RequestException,
    Timeout,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.exceptions import ProtocolError, ReadTimeoutError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from logger import logger

# Глобальные переменные
proxy_list = []
current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
html_directory = current_directory / "html"

# Создаем необходимые директории
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

config_file = config_directory / "config.json"

# Куки (добавьте свои если нужны)
cookies = {}

def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if config_file.exists():
            with open(config_file, "r", encoding='utf-8') as f:
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

def load_company_ids(csv_file_path: str) -> List[str]:
    """
    Загружает ID компаний из CSV файла
    """
    company_ids = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if 'id' in row and row['id'].strip():
                    company_ids.append(row['id'].strip())
        
        logger.info(f"Загружено {len(company_ids)} ID компаний из {csv_file_path}")
        return company_ids
    except Exception as e:
        logger.error(f"Ошибка при загрузке CSV файла: {str(e)}")
        return []

@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(
        multiplier=1, min=4, max=60
    ), 
    retry=(
        retry_if_exception_type(HTTPError)
        | retry_if_exception_type(ConnectionError)
        | retry_if_exception_type(Timeout)
        | retry_if_exception_type(ProxyError)
        | retry_if_exception_type(ProtocolError)
        | retry_if_exception_type(ReadTimeoutError)
        | retry_if_exception_type(OSError)
        | retry_if_exception_type(RequestException)
    ),
    before_sleep=before_sleep_log(logger, "WARNING")
)
def download_company_page(id_company: str) -> bool:
    """
    Скачивает страницу компании и сохраняет в HTML файл
    """
    try:
        # Проверяем, существует ли уже файл
        html_file_path = html_directory / f"{id_company}.html"
        if html_file_path.exists():
            logger.info(f"Файл {id_company}.html уже существует, пропускаем")
            return True

        # Получаем случайный прокси для этого потока
        proxies = get_random_proxy()
        thread_id = threading.current_thread().ident
        
        if proxies:
            logger.debug(f"Поток {thread_id}: Используем прокси для ID {id_company}")

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ru,en;q=0.9,uk;q=0.8',
            'cache-control': 'no-cache',
            'dnt': '1',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        }

        params = {
            'from': 'search',
        }

        url = f'https://opendatabot.ua/c/{id_company}'
        
        response = requests.get(
            url, 
            params=params, 
            cookies=cookies, 
            headers=headers,
            proxies=proxies,
            timeout=30,
            verify=False,
        )
        
        # Проверяем статус ответа
        if response.status_code == 200:
            # Сохраняем HTML в файл
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Успешно сохранен файл {id_company}.html (статус: {response.status_code})")
            return True
        else:
            # Если статус не 200, поднимаем исключение для повторной попытки
            logger.warning(f"Получен статус {response.status_code} для ID {id_company}")
            response.raise_for_status()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке ID {id_company}: {str(e)}")
        raise  # Перебрасываем исключение для retry декоратора

def process_companies_multithread(csv_file_path: str, max_workers: int = 5):
    """
    Обрабатывает компании в многопоточном режиме
    """
    # Загружаем прокси
    load_proxies()
    
    # Загружаем ID компаний из CSV
    company_ids = load_company_ids(csv_file_path)
    
    if not company_ids:
        logger.error("Не найдено ID компаний для обработки")
        return
    
    logger.info(f"Начинаем обработку {len(company_ids)} компаний с {max_workers} потоками")
    
    # Счетчики для статистики
    successful_downloads = 0
    failed_downloads = 0
    
    # Используем ThreadPoolExecutor для многопоточности
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи
        future_to_id = {
            executor.submit(download_company_page, company_id): company_id 
            for company_id in company_ids
        }
        
        # Обрабатываем результаты по мере завершения
        for future in as_completed(future_to_id):
            company_id = future_to_id[future]
            try:
                result = future.result()
                if result:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
            except Exception as e:
                logger.error(f"Окончательная ошибка для ID {company_id}: {str(e)}")
                failed_downloads += 1
    
    # Выводим статистику
    logger.info(f"Обработка завершена:")
    logger.info(f"Успешно обработано: {successful_downloads}")
    logger.info(f"Ошибок: {failed_downloads}")
    logger.info(f"Всего: {len(company_ids)}")

def main():
    """
    Главная функция с парсингом аргументов командной строки
    """
    parser = argparse.ArgumentParser(description='Скачивание страниц компаний с OpenDataBot')
    parser.add_argument('csv_file', help='Путь к CSV файлу с ID компаний')
    parser.add_argument('--threads', '-t', type=int, default=5, 
                       help='Количество потоков (по умолчанию: 5)')
    
    args = parser.parse_args()
    
    # Проверяем существование CSV файла
    if not Path(args.csv_file).exists():
        logger.error(f"CSV файл {args.csv_file} не найден")
        return
    
    # Запускаем обработку
    process_companies_multithread(args.csv_file, args.threads)

if __name__ == "__main__":
    while True:
        main()