import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

# Получаем абсолютный путь к родительской директории
BASE_DIR = Path(__file__).parent.parent
# Добавляем родительскую директорию в sys.path
sys.path.append(str(BASE_DIR))

# Теперь можно импортировать из родительской директории
from config.logger import logger

name_site = "www.musiccenter.com.pl"
config_directory = BASE_DIR / "config"
json_data_directory = BASE_DIR / "json_data"
html_directory = BASE_DIR / "html_pages" / name_site
output_file = json_data_directory / f"{name_site}.json"


def extract_product_data(data):

    title = data.find("h1", attrs={"class": "h1"})
    title = title.text.strip()
    price = data.find("span", attrs={"class": "current-price-value"})
    if price:
        price = price.get("content")
    else:
        logger.warning("Тег с ценой не найден")
        price = None
    article_number = data.find("div", attrs={"class": "product-codes"})
    if article_number:
        article_number = (
            article_number.find("ul")
            .find("li")
            .text.replace("Kod produktu: [", "")
            .replace("]", "")
            .strip()
        )
    else:
        logger.warning("Тег с артикулом не найден")
        article_number = None

    availability = None
    # Флаг для отслеживания, был ли найден продукт
    availability_tag = data.find(
        "div", class_="product-more-info js-product-add-to-cart"
    )
    if availability_tag:
        availability = availability_tag.find("div", class_="i-item i-1").text.strip()

    all_data = {
        "title": title,
        "price": price,
        "article_number": article_number,
        "availability": availability,
    }
    return all_data


def pars_htmls():
    # logger.info(f"Обрабатываем директорию: {html_directory}")
    all_data = []

    # Проверяем наличие HTML-файлов
    html_files = list(html_directory.glob("*.html"))

    # Обрабатываем каждый HTML-файл
    for html_file in html_files:
        try:
            with html_file.open(encoding="utf-8") as file:
                content = file.read()

            # Парсим HTML
            soup = BeautifulSoup(content, "lxml")
            result = extract_product_data(soup)

            if result:
                # logger.info(json.dumps(result, ensure_ascii=False, indent=4))
                all_data.append(result)
            else:
                logger.warning(f"Не удалось извлечь данные из {html_file.name}")

        except UnicodeDecodeError as e:
            logger.error(f"Ошибка кодировки в файле {html_file.name}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")

    # Сохраняем данные в JSON
    if all_data:

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        # logger.info(f"Данные сохранены в {output_file}")

    return all_data


if __name__ == "__main__":
    parsed_data = pars_htmls()
    # logger.info(f"Обработано файлов: {len(parsed_data)}")
