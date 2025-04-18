# excel_scraper/site/abixmusic.pl.py
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

name_site = "abixmusic.pl"
config_directory = BASE_DIR / "config"
json_data_directory = BASE_DIR / "json_data"
json_data_directory.mkdir(parents=True, exist_ok=True)
html_directory = BASE_DIR / "html_pages" / name_site
output_file = json_data_directory / f"{name_site}.json"


def extract_product_data(product_json):
    try:
        # Если product_json - строка, парсим её как JSON
        if isinstance(product_json, str):
            product_json = json.loads(product_json)

        # Проверяем, что product_json - словарь
        if not isinstance(product_json, dict):
            raise ValueError("product_json должен быть словарем или строкой JSON")

        title = product_json.get("name", None)
        sku = product_json.get("sku")

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
        # availability = offers.get("availability", "").replace("http://schema.org/", "")
        # logger.info(f"Доступность: {availability}")
        # schema_terms = r"(InStock|OutOfStock)"  # Шаблон для поиска
        # all_availability = {
        #     "InStock": "Towar dostępny",
        #     "OutOfStock": "Towar niedostępny",
        # }

        # # Поиск значений доступности
        # matches = re.findall(schema_terms, availability or "")
        # result_availability = None
        # if matches:
        #     last_term = matches[-1]
        #     result_availability = all_availability.get(last_term, None)

        all_data = {
            "title": title,
            "price": offer_price,
            "article_number": sku,
            "availability": "availability",
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
            scripts = soup.find_all("script", type="application/ld+json")[-1]
            # Перебираем все скрипты JSON-LD
            # for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                script_text = scripts.string
                # Извлекаем данные основного продукта
                main_product = extract_product_data(script_text)
                availability_description = soup.find(
                    "div", attrs={"id": "projector_status_description"}
                )
                if availability_description:
                    availability_description = availability_description.text.strip()
                    main_product["availability"] = availability_description
                else:
                    availability_label = soup.find(
                        "strong", attrs={"id": "projector_delivery_label"}
                    ).text.strip()
                    if availability_label == "Wysyłka":
                        availability_label = "Zamów do 14:00"
                        main_product["availability"] = availability_label
                if main_product:
                    # main_product["availability"] = availability_label
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
