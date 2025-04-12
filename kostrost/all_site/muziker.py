import json
from pathlib import Path

from bs4 import BeautifulSoup
from config.logger import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
html_directory = current_directory / "html_pages" / "www.muziker.pl"


def extract_product_data(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        title = product_json.get("name")
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

        all_data = {
            "title": title,
            "price": offer_price,
            "article_number": sku,
            "availability": "availability",
        }
        return all_data
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
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML
        soup = BeautifulSoup(content, "lxml")
        scripts = soup.find_all("script", type="application/ld+json")

        if not scripts:
            logger.warning(
                f"В файле {html_file.name} не найдено скриптов с типом application/ld+json"
            )
            continue
        availability = None
        # Флаг для отслеживания, был ли найден продукт
        availability_tag = soup.find("div", class_="stock-status-detail")
        if availability_tag:
            availability = availability_tag.text.strip().split("\n")[0].strip()
        else:
            logger.warning("Тег с доступностью не найден для другого сайта")
        # Перебираем все скрипты JSON-LD
        for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                script_text = script.string
                if not script_text or not script_text.strip():
                    continue
                # Очищаем JSON от проблемных символов

                # Парсим JSON
                json_data = json.loads(script_text)

                # Проверяем, является ли это продуктом
                if isinstance(json_data, dict) and json_data.get("@type") == "Product":

                    # Извлекаем данные основного продукта
                    main_product = extract_product_data(json_data)
                    if main_product:
                        main_product["availability"] = availability
                        all_data.append(main_product)

                    break
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                # Или можно использовать print:
                logger.info(f"Ошибка парсинга JSON: {e}")
        else:
            logger.error("Product JSON не найден.")

    # Сохраняем данные в JSON
    if all_data:
        output_file = current_directory / "muziker_data.json"
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Данные сохранены в {output_file}")

    return all_data


if __name__ == "__main__":
    parsed_data = pars_htmls()
    logger.info(f"Обработано файлов: {len(parsed_data)}")
