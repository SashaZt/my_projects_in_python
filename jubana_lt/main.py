import json
import csv
import os
from pathlib import Path
from typing import Any, Dict
import pandas as pd
# Импорт нужных модулей
from extractor import ProductDataExtractor
from image_utils import download_product_images
from json_utils import create_product_database, save_json_data
from main_get_html import get_html,scrap_page
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
    """Обрабатывает все HTML файлы и сохраняет данные в JSON"""
    html_files = list(html_directory.glob("*.html"))
    logger.info(f"Найдено {len(html_files)} HTML файлов.")

    for html_file in html_files:
        try:
            logger.info(f"Обработка файла: {html_file}")

            # Создаем имя для выходного JSON файла
            output_json_file = json_directory / f"{html_file.stem}.json"

            # Читаем HTML файл
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            # Обрабатываем HTML и извлекаем данные
            product_data = process_html_file(content)

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
            logger.error(f"Ошибка при обработке файла {html_file}: {e}")


def download_images_for_products():
    """Скачивает изображения для всех продуктов из JSON файлов"""
    json_files = list(json_directory.glob("*.json"))
    logger.info(f"Найдено {len(json_files)} JSON файлов для скачивания изображений.")

    for json_file in json_files:
        try:
            # Читаем JSON файл
            with open(json_file, "r", encoding="utf-8") as file:
                product_data = json.load(file)

            # Проверяем, есть ли изображения в данных
            if "images" not in product_data:
                logger.warning(f"Нет информации об изображениях в {json_file}")
                continue

            # Получаем ID продукта для именования файлов
            product_id = (
                product_data.get("product_id")
                or product_data.get("sku")
                or product_data.get("model")
                or json_file.stem
            )

            # Создаем директорию для изображений конкретного продукта
            product_images_dir = images_directory / str(product_id)
            product_images_dir.mkdir(exist_ok=True)

            # Скачиваем изображения
            image_info = product_data["images"]
            downloaded_files = download_product_images(
                image_info, product_images_dir, product_id
            )

            logger.info(
                f"Для продукта {product_id} скачано {len(downloaded_files)} изображений"
            )

            # Обновляем информацию об изображениях в JSON
            product_data["downloaded_images"] = [
                str(Path(f).relative_to(current_directory)) for f in downloaded_files
            ]

            # Сохраняем обновленные данные
            save_json_data(product_data, json_file)
            logger.info(f"Обновлена информация о скачанных изображениях в {json_file}")

        except Exception as e:
            logger.error(f"Ошибка при скачивании изображений для {json_file}: {e}")


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
    for category in all_data["categories"]:
        category_name = category["name"]
        output_csv_file = csv_directory / f"{category_name}.csv"
        with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                get_html(category_name, row["url"])
    
    
    # # Шаг 1: Обработка HTML файлов и создание JSON
    # process_html_to_json()

    # # Шаг 2: Скачивание изображений
    # download_images_for_products()

    # # # Шаг 3: Создание общей базы данных
    # # create_database()

    # logger.info("Обработка завершена.")


if __name__ == "__main__":
    main()
