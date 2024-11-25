import csv
import random
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.config_utils import (
    initialize_directories,
    load_environment_variables,
)
from configuration.logger_setup import logger

# Инициализация директорий
base_directory = Path.cwd()
directories = initialize_directories(base_directory)


# Загрузка переменных окружения
env_file = directories["config_dir"] / ".env"
env_vars = load_environment_variables(env_file)
time_a = int(env_vars["TIME_A"])
time_b = int(env_vars["TIME_B"])


def read_cities_from_csv(input_csv_file: str) -> List[str]:
    """Читает список URL из столбца 'url' CSV-файла.

    Args:
        input_csv_file (str): Путь к входному CSV-файлу.

    Returns:
        List[str]: Список URL-адресов из столбца 'url'.

    Raises:
        ValueError: Если файл не содержит столбца 'url'.
        FileNotFoundError: Если файл не найден.
    """
    try:
        with open(input_csv_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if "url" not in reader.fieldnames:
                raise ValueError("Входной файл не содержит столбца 'url'.")

            urls = [
                row["url"] for row in reader if row["url"]
            ]  # Считываем только непустые значения
            return urls

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {input_csv_file} не найден.")

    except ValueError as e:
        raise e


def read_urls_from_txt(input_txt_file: str) -> List[str]:
    """Читает список URL из текстового файла.

    Args:
        input_txt_file (str): Путь к входному текстовому файлу.

    Returns:
        List[str]: Список URL-адресов.

    Raises:
        FileNotFoundError: Если файл не найден.
        IOError: Если файл пустой или произошла ошибка при чтении.
    """
    try:
        with open(input_txt_file, "r", encoding="utf-8") as file:
            urls = [
                line.strip() for line in file if line.strip()
            ]  # Убираем пустые строки и лишние пробелы
            return urls

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {input_txt_file} не найден.")

    except IOError as e:
        raise IOError(f"Ошибка при чтении файла {input_txt_file}: {e}")


# Получение куки
def get_cookies(config_file: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Извлекает заголовки и куки из строки curl, хранящейся в указанном файле.

    Args:
        config_file (str): Путь к файлу, содержащему строку curl.

    Returns:
        Tuple[Dict[str, str], Dict[str, str]]:
            - headers (Dict[str, str]): Словарь заголовков.
            - cookies (Dict[str, str]): Словарь куки.

    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если файл не содержит корректную строку curl.
    """
    # Чтение строки curl из файла
    with open(config_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def get_html():
    """Скачивает данные по каждому сайту с учетом лимита и текущего прогресса.

    Args:
        limit_site (int): Лимит на количество сайтов для обработки за один запуск.
    """
    # Загружаем список сайтов и общее количество
    # sites = read_cities_from_csv(directories["csv_file"])
    sites = read_urls_from_txt(directories["txt_file"])
    # Получаем заголовки и куки
    headers, cookies = get_cookies(directories["config_file"])

    # Обработка выбранных сайтов
    for url in sites:
        url_id = url.rsplit("/", maxsplit=1)[-1]
        product_id = url.rsplit("/", maxsplit=2)[-2]

        file_page_file = directories["html_dir"] / f"{product_id}_{url_id}.html"
        if file_page_file.exists():
            continue
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_page_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            pause = random_pause(1, 3)


def random_pause(min_seconds: int = 30, max_seconds: int = 60) -> int:
    """Выполняет случайную паузу в заданном диапазоне.

    Args:
        min_seconds (int): Минимальная длительность паузы (целое число).
        max_seconds (int): Максимальная длительность паузы (целое число).

    Returns:
        int: Фактическая длительность паузы.
    """
    if min_seconds > max_seconds:
        raise ValueError("min_seconds не может быть больше max_seconds")

    pause_duration = random.randint(
        min_seconds, max_seconds
    )  # Используем randint для целых чисел
    logger.info(f"Пауза {pause_duration} секунд.")
    time.sleep(pause_duration)
    return pause_duration


def get_parsing():
    all_data = []
    for html_file in directories["html_dir"].glob("*.html"):
        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        name_product = None
        availability_product = None
        price_product = None
        sku_product = None
        try:
            name_product = soup.find("h1", attrs={"itemprop": "name"}).text
        except:
            continue
            name_product = None
        try:

            price_product = (
                soup.find("em", attrs={"class": "main-price"})
                .text.replace("€", "")
                .replace(".", ",")
            )
        except:
            price_product = None
        try:
            availability_product = soup.select_one(
                "div.product_cell.cell_2 > div > div > span.second"
            ).text
            if availability_product == "out of stock":
                availability_product = "Немає в наявності"
            else:
                availability_product = "В наявноті"
        except:
            availability_product = None
        try:

            sku_product = soup.select_one(
                "div.productdetails-more-details.clearfix > div > div.row.code > span"
            ).text
            sku_product = f"INT-{sku_product}"
        except:
            sku_product = None
        result = {
            "name_product": name_product,
            "price_product": price_product,
            "availability_product": availability_product,
            "sku_product": sku_product,
        }
        all_data.append(result)
    data_df = pd.DataFrame(all_data)

    # Сохраняем данные в новый Excel файл
    data_df.to_excel(directories["results_report"], index=False)


if __name__ == "__main__":
    # get_html()
    get_parsing()
