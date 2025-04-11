import json
import csv
import os
from pathlib import Path
from typing import Any, Dict
import pandas as pd
import requests
from urllib.parse import urlparse

from extractor import ProductDataExtractor
from image_utils import download_product_images
from json_utils import create_product_database, save_json_data
from main_get_html import get_html, scrap_page
from logger import logger

# Пути к директориям
current_directory = Path.cwd()
html_directory = current_directory / "html"
csv_directory = current_directory / "csv"
json_directory = current_directory / "json"
images_directory = current_directory / "images"
output_database = current_directory / "product_database.json"

# Создаем нужные директории
html_directory.mkdir(exist_ok=True)
json_directory.mkdir(exist_ok=True)
images_directory.mkdir(exist_ok=True)
csv_directory.mkdir(exist_ok=True)
cookies = {
    "PHPSESSID": "veilud4s6c3a6eae33ncp3m222",
    "user_id": "5b387233db63876c1540ef24c9b1aacd",
    "cc_cookie": "%7B%22categories%22%3A%5B%22necessary%22%2C%22functionality%22%2C%22analytics%22%2C%22marketing%22%5D%2C%22revision%22%3A0%2C%22data%22%3Anull%2C%22consentTimestamp%22%3A%222025-04-07T11%3A32%3A21.849Z%22%2C%22consentId%22%3A%22d27c5c74-1482-479b-a878-a4ee2a6dba3b%22%2C%22services%22%3A%7B%22necessary%22%3A%5B%5D%2C%22functionality%22%3A%5B%5D%2C%22analytics%22%3A%5B%5D%2C%22marketing%22%3A%5B%5D%7D%2C%22lastConsentTimestamp%22%3A%222025-04-07T11%3A32%3A21.849Z%22%2C%22expirationTime%22%3A1759750341849%7D",
    "session": "mzl6kWsidKIbqO%2B4XsA4ui83%2BSNgV5Kf2UjrppYitmmXHM%2B%2F4m%2F4YELGdcxIgz4cQKmfLfWylBGJOtmG7KENYPzIn3oYp%2FbahxaTAdPevNL2yNupajluOZ2O5R21b6faa%2Fcu601vMcxF%2B0evQW9PrspL0GhJNUuyd9PVk6lRFcY54DQD3j8Qxw8hJ%2BJw%2BnREeZyC6QMtVN9o313JRFONR8C9OPdoBjJjpt8E%2BgtUubvNxCncaAY55oh%2FS%2FbGgDJH6Lxx%2Fnv04Gprw49675h47U7fJSzmdY36Hefclc5X%2BFvGrcoH8vec6pgLFWpyX2yurxfb5hdk6yrZk4uMJ13TVPrpW7LyihwEbEvJy59DaLNg6lXRS4qtZhkpqR1V0IJhuQSqaokNW6uzB0wR4ujJTgkD0JfqRpEcdYHdzOrSxhE%3D",
    "hl": "en",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "referer": "https://www.jubana.lt/en/starters/starter-parts",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}


def process_html_file(html_content: str) -> Dict[str, Any]:
    """
    Обрабатывает HTML файл и извлекает структурированные данные

    Args:
        html_content (str): Содержимое HTML файла

    Returns:
        dict: Структурированные данные о продукте
    """
    try:
        extractor = ProductDataExtractor()
        extractor.parse_html(html_content)
        result = extractor.extract_all_data()
        return result
    except Exception as e:
        logger.error(f"Ошибка при обработке HTML файла: {e}")
        return {}


def process_html_to_json():
    """Обрабатывает все HTML файлы из вложенных директорий и сохраняет данные в JSON"""
    # Получаем список всех поддиректорий
    subdirectories = [d for d in html_directory.iterdir() if d.is_dir()]
    logger.info(f"Найдено {len(subdirectories)} поддиректорий.")

    if not subdirectories:
        logger.warning("Поддиректории не найдены, проверяя файлы в корневой директории")
        html_files = list(html_directory.glob("*.html"))
        if html_files:
            process_directory_files(html_directory, json_directory)
        return

    for subdir in subdirectories:
        subdir_name = subdir.name
        logger.info(f"Обрабатываю поддиректорию: {subdir_name}")

        # Создаем директорию для JSON файлов этой категории если её нет
        category_json_dir = json_directory / subdir_name
        category_json_dir.mkdir(exist_ok=True, parents=True)

        # Обрабатываем все HTML файлы в текущей поддиректории
        process_directory_files(subdir, category_json_dir, category=subdir_name)


def process_directory_files(directory, output_dir, category=None):
    """
    Обрабатывает все HTML файлы в указанной директории

    Args:
        directory (Path): Директория с HTML файлами
        output_dir (Path): Директория для сохранения JSON файлов
        category (str, optional): Имя категории (поддиректории)
    """
    html_files = list(directory.glob("*.html"))
    logger.info(f"Найдено {len(html_files)} HTML файлов в директории {directory}.")

    for html_file in html_files:
        try:
            logger.info(f"Обработка файла: {html_file}")

            # Создаем имя для выходного JSON файла
            output_json_file = output_dir / f"{html_file.stem}.json"

            # Читаем HTML файл
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            # Обрабатываем HTML и извлекаем данные
            product_data = process_html_file(content)

            # Добавляем категорию к данным продукта, если она предоставлена
            if category and product_data:
                product_data["category"] = category

            # Проверяем, есть ли данные для сохранения
            if not product_data:
                logger.warning(f"Не удалось извлечь данные из {html_file}")
                continue

            # Сохраняем результат в JSON файл
            if save_json_data(product_data, output_json_file):
                logger.info(f"Данные сохранены в {output_json_file}")
            else:
                logger.error(f"Не удалось сохранить данные в {output_json_file}")

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file}: {e}", exc_info=True)


def download_images_for_products():
    """Скачивает изображения для всех продуктов из JSON файлов во всех категориях"""
    # Получаем список поддиректорий (категорий)
    categories = [d for d in json_directory.iterdir() if d.is_dir()]
    logger.info(f"Найдено {len(categories)} категорий для обработки.")

    if not categories:
        # Если нет поддиректорий, проверяем файлы в основной директории
        json_files = list(json_directory.glob("*.json"))
        if json_files:
            process_json_files_in_directory(json_directory, None)
        return

    # Обрабатываем каждую категорию
    for category_dir in categories:
        category_name = category_dir.name
        logger.info(f"Обработка категории: {category_name}")

        # Получаем все JSON файлы в этой категории
        json_files = list(category_dir.glob("*.json"))

        if not json_files:
            logger.warning(f"В категории {category_name} не найдено JSON файлов")
            continue

        # Обрабатываем файлы в этой категории
        process_json_files_in_directory(category_dir, category_name)


def process_json_files_in_directory(directory, category_name):
    """Обрабатывает JSON файлы в указанной директории"""
    json_files = list(directory.glob("*.json"))
    logger.info(f"Найдено {len(json_files)} JSON файлов в директории {directory}")

    for json_file in json_files:
        try:
            # Читаем JSON файл
            with open(json_file, "r", encoding="utf-8") as file:
                product_data = json.load(file)

            # Проверяем, есть ли изображения в данных
            if "images" not in product_data or not product_data["images"]:
                logger.warning(f"Нет информации об изображениях в {json_file}")
                continue

            # Получаем модель продукта для именования файлов
            # Если модели нет, используем имя файла без расширения
            model = product_data.get("model", json_file.stem)

            # Создаем директорию для изображений в соответствующей категории
            if category_name:
                product_images_dir = images_directory / category_name
            else:
                product_images_dir = images_directory

            product_images_dir.mkdir(exist_ok=True, parents=True)

            # Получаем список URL изображений
            image_urls = product_data["images"].split(",")

            # Скачиваем изображения
            downloaded_files = []

            for idx, img_url in enumerate(image_urls):
                img_url = img_url.strip()
                if not img_url:
                    continue

                # Проверяем, является ли URL относительным
                if not img_url.startswith(("http://", "https://")):
                    # Для относительных URL нужно добавить базовый URL сайта
                    base_url = "https://www.jubana.lt"
                    if not img_url.startswith("/"):
                        img_url = "/" + img_url
                    img_url = base_url + img_url

                # Получаем расширение файла из URL
                path_parts = urlparse(img_url).path.split("/")
                if "." in path_parts[-1]:
                    ext = path_parts[-1].split(".")[-1]
                    if "?" in ext:  # Удаляем параметры запроса из расширения
                        ext = ext.split("?")[0]
                else:
                    ext = "jpg"  # По умолчанию jpg

                # Формируем имя файла
                filename = f"{model}_{idx+1}.{ext}"
                file_path = product_images_dir / filename

                # Проверяем, существует ли файл
                if file_path.exists():
                    downloaded_files.append(str(file_path))
                    continue

                # Скачиваем изображение
                try:
                    response = requests.get(
                        img_url,
                        cookies=cookies,
                        headers=headers,
                        timeout=30,
                        stream=True,
                    )
                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        downloaded_files.append(str(file_path))
                        logger.info(f"Скачано изображение: {file_path}")
                    else:
                        logger.warning(
                            f"Не удалось скачать изображение {img_url}. Код ответа: {response.status_code}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при скачивании изображения {img_url}: {e}")

            logger.info(
                f"Для продукта {model} в категории {category_name or 'основной'} "
                f"скачано {len(downloaded_files)} изображений"
            )

            # Обновляем информацию об изображениях в JSON - без префикса "images\"
            product_data["downloaded_images"] = []
            for f in downloaded_files:
                path = Path(f)
                # Получаем путь, начиная с имени категории (без "images\")
                relative_path = path.relative_to(images_directory)
                product_data["downloaded_images"].append(str(relative_path))

            # Сохраняем обновленные данные
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(product_data, file, ensure_ascii=False, indent=4)

            logger.info(f"Обновлена информация о скачанных изображениях в {json_file}")

        except Exception as e:
            logger.error(
                f"Ошибка при скачивании изображений для {json_file}: {e}", exc_info=True
            )


def create_database():
    """Создает общую базу данных из всех JSON файлов"""
    logger.info("Создание общей базы данных продуктов...")
    create_product_database(json_directory, output_database)
    logger.info(f"База данных создана: {output_database}")


def main():
    """Основная функция для запуска всего процесса"""
    logger.info("Запуск обработки...")
    all_data = {
        "categories": [
            {
                "name": "Starters_12V",
                "url": "https://www.jubana.lt/en/starters/starters-12v",
            },
            {
                "name": "Starters_24V",
                "url": "https://www.jubana.lt/en/starters/starters-24v",
            },
            {
                "name": "Starter_parts",
                "url": "https://www.jubana.lt/en/starters/starter-parts",
            },
            {
                "name": "Alternators_14V",
                "url": "https://www.jubana.lt/en/alternators/alternators-14v",
            },
            {
                "name": "Alternator_parts",
                "url": "https://www.jubana.lt/en/alternators/alternator-parts",
            },
            {
                "name": "Alternators_28V",
                "url": "https://www.jubana.lt/en/alternators/alternators-28v",
            },
        ]
    }
    # # Скачивание HTML файлов page
    # for category in all_data["categories"]:
    #     category_name = category["name"]
    #     url = category["url"]
    #     logger.info(f"Скачивание HTML для категории: {category_name}")
    #     get_html_page(category_name, url)
    #     time.sleep(5)

    ## Собираем ссылки на страницы продуктов
    # for category in all_data["categories"]:
    #     category_name = category["name"]
    #     output_csv_file = csv_directory / f"{category_name}.csv"
    #     urls = scrap_page(category_name)
    #     url_data = pd.DataFrame(urls, columns=["url"])
    #     url_data.to_csv(output_csv_file, index=False)

    ##Скачивание HTML файлов для продуктов
    # for category in all_data["categories"]:
    #     category_name = category["name"]
    #     output_csv_file = csv_directory / f"{category_name}.csv"
    #     with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             get_html(category_name, row["url"])

    # Шаг 1: Обработка HTML файлов и создание JSON
    # process_html_to_json()

    # # Шаг 2: Скачивание изображений
    download_images_for_products()

    # # # Шаг 3: Создание общей базы данных
    # # create_database()

    # logger.info("Обработка завершена.")


if __name__ == "__main__":
    main()
