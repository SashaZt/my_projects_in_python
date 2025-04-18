import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Получаем абсолютный путь к родительской директории
BASE_DIR = Path(__file__).parent.parent
# Добавляем родительскую директорию в sys.path
sys.path.append(str(BASE_DIR))

# Теперь можно импортировать из родительской директории
from config.logger import logger

name_site = "www.gear4music.pl"
config_directory = BASE_DIR / "config"
json_data_directory = BASE_DIR / "json_data"
html_directory = BASE_DIR / "html_pages" / name_site
output_file = json_data_directory / f"{name_site}.json"


def extract_product_data(products_json):
    try:
        product_json = products_json.get("@graph", [])[1]

        # Если product_json - строка, парсим её как JSON
        if isinstance(product_json, str):
            product_json = json.loads(product_json)

        title = product_json.get("name", None)
        if title:
            # Заменяем множественные пробелы на одиночный и убираем пробелы в начале/конце
            title = re.sub(r"\s+", " ", title).strip()
        sku = product_json.get("productID")

        # Извлекаем данные из offers
        offers = product_json.get("offers", {})

        # Обработка случая, когда offers может быть списком
        if isinstance(offers, list) and offers:
            offers = offers[0]

        # Пробуем получить цену разными способами
        offer_price = None
        if isinstance(offers, dict):
            if "price" in offers:
                offer_price = offers.get("price")

        # Форматируем цену, если она найдена
        if offer_price:
            offer_price = str(offer_price).replace(".", ",")
        # Обработка доступности
        availability = offers.get("availability", "").replace("http://schema.org/", "")
        schema_terms = r"(InStock|OutOfStock)"  # Шаблон для поиска
        all_availability = {
            "InStock": "Towar dostępny",
            "OutOfStock": "Towar niedostępny",
        }

        # Поиск значений доступности
        matches = re.findall(schema_terms, availability or "")
        result_availability = None
        if matches:
            last_term = matches[-1]
            result_availability = all_availability.get(last_term, None)

        all_data = {
            "title": title,
            "price": offer_price,
            "article_number": sku,
            "availability": result_availability,
        }
        return all_data

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при парсинге JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def pars_htmls():
    logger.info(f"Обрабатываем директорию: {html_directory}")
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
            scripts = soup.find("script", type="application/ld+json")
            # Перебираем все скрипты JSON-LD
            # for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                # Извлекаем данные основного продукта
                main_product = extract_product_data(json.loads(scripts.string))
                if main_product:
                    logger.info(json.dumps(main_product, ensure_ascii=False, indent=4))

                    all_data.append(main_product)

            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")

        except UnicodeDecodeError as e:
            logger.error(f"Ошибка кодировки в файле {html_file.name}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")

    # Сохраняем данные в JSON
    if all_data:

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Данные сохранены в {output_file}")

    return all_data


if __name__ == "__main__":
    parsed_data = pars_htmls()
    logger.info(f"Обработано файлов: {len(parsed_data)}")
