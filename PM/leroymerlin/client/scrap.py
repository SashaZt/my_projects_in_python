import json
from pathlib import Path

from bs4 import BeautifulSoup

from config import logger, paths


def extract_product_data(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        # logger.info(json.dumps(product_json))
        product_name = product_json.get("name")
        product_url = product_json.get("url")
        sku = product_json.get("sku")
        image = product_json.get("image")
        description = product_json.get("description")
        brand = product_json.get("brand", {})
        del brand["@type"]
        aggregateRating = product_json.get("aggregateRating", {})
        del aggregateRating["@type"]

        # Создаем итоговый словарь с данными продукта
        data_json = {
            "product_name": product_name,
            "product_url": product_url,
            "sku": sku,
            "image": [image],
            "description": description,
            "brand": brand,
            "aggregateRating": aggregateRating,
        }

        return data_json
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def extract_offers(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        # logger.info(json.dumps(product_json))
        priceCurrency = product_json.get("priceCurrency", None)
        price = product_json.get("price", None)

        # Создаем итоговый словарь с данными продукта
        data_json = {"product_name": priceCurrency, "product_url": price}

        return data_json
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def scrap_htmls():
    # Список для хранения данных
    all_data = []
    # Проверяем наличие HTML-файлов
    html_files = list(paths.html.glob("*.html"))
    # Проходим по всем HTML-файлам в папке
    for html_file in html_files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        try:
            # Инициализируем как список, а не словарь
            product_data = []
            offers_data = {}

            soup = BeautifulSoup(content, "lxml")
            # Находим все скрипты с типом application/json
            scripts = soup.find_all("script", type="application/json")

            if not scripts:
                logger.warning(
                    f"В файле {html_file.name} не найдено скриптов с типом application/json"
                )
                continue

            for script in scripts:
                script_text = script.string
                if not script_text or not script_text.strip():
                    continue

                # Парсим JSON
                json_data = json.loads(script_text)

                # Проверяем, является ли это продуктом
                if isinstance(json_data, dict) and json_data.get("@type") == "Product":
                    # Извлекаем данные основного продукта
                    main_product = extract_product_data(json_data)
                    if main_product:
                        product_data.append(main_product)

                if isinstance(json_data, dict) and json_data.get("@type") == "Offer":
                    all_offers = extract_offers(json_data)
                    if all_offers:
                        offers_data.update(all_offers)

            # Объединяем данные продукта с данными предложений
            if product_data:
                # Если есть данные о ценах, добавляем их к каждому продукту
                for product in product_data:
                    if offers_data:
                        product.update(offers_data)

                all_data.extend(product_data)

        except Exception as e:
            logger.error(f"Ошибка при обработке {html_file.name}: {str(e)}")

    # Логируем финальные данные
    logger.info(json.dumps(all_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    scrap_htmls()
