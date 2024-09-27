import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import requests
import random
import csv


# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
file_proxy = configuration_directory / "roman.txt"


cookies = {
    "G_ENABLED_IDPS": "google",
    "PHPSESSID": "qrv15skogbamtogk5kb75t09l9",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def load_proxies():
    # Загрузка списка прокси из файла
    with open(file_proxy, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


# Функция для чтения файла и запуска многопоточности
def process_infox_file(max_workers):
    proxies = load_proxies()  # Загружаем список всех прокси

    successful_urls = get_successful_urls(csv_file_successful)
    urls_df = pd.read_csv(output_csv_file)

    # Создаем прогресс-бар
    total_urls = len(urls_df)
    progress_bar = tqdm(
        total=total_urls,
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )

    # Запускаем многопоточность
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_and_save_html, url, successful_urls, proxies)
            for url in urls_df["identifier"]
        ]

        for future in as_completed(futures):
            try:
                future.result()  # Получаем результат выполнения задачи
            except Exception as e:
                logger.error(f"Error occurred: {e}")
            finally:
                # Обновляем прогресс-бар по завершении каждой задачи
                progress_bar.update(1)

    # Закрываем прогресс-бар
    progress_bar.close()
    logger.info("Все запросы выполнены.")


# Функция для запроса и сохранения HTML
def fetch_and_save_html(identifier, successful_urls, proxies):
    if identifier in successful_urls:
        logger.info(f"| Компания уже была обработана, пропускаем. |")
        return

    try:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}

        base_url = "https://www.ua-region.com.ua"
        url = f"{base_url}/{identifier}"

        # Отправляем запрос
        response = requests.get(
            url,
            proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )

        # Проверяем статус ответа
        if response.status_code == 200:
            # Формируем путь для сохранения файла
            file_path = html_files_directory / f"{identifier}.html"
            # Сохраняем HTML в файл
            file_path.write_text(response.text, encoding="utf-8")
            successful_urls.add(identifier)
            write_to_csv(identifier, csv_file_successful)

        else:
            logger.error(
                f"Ошибка: не удалось получить данные для {identifier}. Статус: {response.status_code}"
            )

    except Exception as e:
        logger.error(f"Произошла ошибка при обработке {identifier}: {e}")


def write_to_csv(data, filename):
    # Проверяем, существует ли файл и является ли он пустым
    file_path = Path(filename)
    if not file_path.exists() or file_path.stat().st_size == 0:
        # Если файл не существует или пуст, добавляем заголовок
        with open(filename, "a", encoding="utf-8") as f:
            f.write("identifier\n")  # Добавляем заголовок

    # Записываем данные
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


if __name__ == "__main__":
    max_workers = 20
    process_infox_file(max_workers)
