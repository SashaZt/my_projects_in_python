import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Получаем абсолютный путь к родительской директории
BASE_DIR = Path(__file__).parent.parent
# Добавляем родительскую директорию в sys.path
sys.path.append(str(BASE_DIR))

# Теперь можно импортировать из родительской директории
from config.logger import logger

name_site = "kytary.pl"
config_directory = BASE_DIR / "config"
json_data_directory = BASE_DIR / "json_data"
html_directory = BASE_DIR / "html_pages" / name_site
output_file = json_data_directory / f"{name_site}.json"


def extract_product_data(data):

    title = data.find("meta", attrs={"itemprop": "name"})
    if title is not None:
        title = title.get("content").strip()
    else:
        logger.warning("Тег с названием не найден")
        title = None
    price = data.find("div", attrs={"class": "price"})
    if price is not None:
        price = price.text.strip()
    else:
        logger.warning("Тег с ценой не найден")
        price = None
    # Извлечение артикулов
    sku = data.find("meta", attrs={"itemprop": "sku"})
    if sku is not None:
        sku = sku.get("content")
    else:
        logger.warning("Тег с артикулом не найден")
        sku = None

    availability = data.find("div", attrs={"class": "pdpwst"})
    if availability:
        availability = availability.text.strip()
    else:
        logger.warning("Тег с доступностью не найден")
        availability = None

    all_data = {
        "title": title,
        "price": price,
        "article_number": sku,
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
