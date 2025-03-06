import json
import re
import sys
import traceback
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def clean_html(html_text):
    """Очищает HTML-разметку и возвращает чистый текст"""
    text = re.sub(r"\u003C\u002F?[^>]+\u003E", "", html_text)  # Удаляем HTML теги
    text = unescape(text)  # Преобразуем HTML-сущности
    return text.strip()


def extract_breadcrumb(script_content):
    """Извлекает хлебные крошки с полной структурой данных"""
    breadcrumb = []
    breadcrumb_pattern = r"breadcrumb:\[(.*?)\]"
    match = re.search(breadcrumb_pattern, script_content, re.DOTALL)

    if match:
        items = match.group(1)
        # Разбиваем на отдельные элементы
        item_sections = items.split("},{")

        for section in item_sections:
            # Очищаем от лишних скобок в начале/конце
            section = section.strip("{").strip("}")
            item = {}

            # Извлекаем все поля
            # ID (опционально)
            id_match = re.search(r"id:([^,]+)", section)
            if id_match:
                id_value = id_match.group(1)
                try:
                    item["id"] = int(id_value)
                except ValueError:
                    item["id"] = id_value

            # Name
            name_match = re.search(r'name:"([^"]+)"', section)
            if name_match:
                item["name"] = name_match.group(1)

            # Title
            title_match = re.search(r'title:"([^"]+)"', section)
            if title_match:
                item["title"] = title_match.group(1)

            # URL
            url_match = re.search(r'url:"([^"]+)"', section)
            if url_match:
                item["url"] = url_match.group(1).replace("\\u002F", "/")

            # isMasked
            masked_match = re.search(r"isMasked:([a-zA-Z])", section)
            if masked_match:
                item["isMasked"] = masked_match.group(1)

            if item:  # Добавляем только если удалось извлечь хотя бы одно поле
                breadcrumb.append(item)

    return breadcrumb


def extract_description(script_content):
    """Извлекает описание продукта"""
    desc_pattern = r'descriptionHtml:"([^"]+)"'
    match = re.search(desc_pattern, script_content)

    if not match:
        return {}

    html_content = (
        match.group(1)
        .replace("\\u003C", "<")
        .replace("\\u003E", ">")
        .replace("\\u002F", "/")
    )

    specs = {}
    dt_dd_pattern = r"<dt>([^<]+)</dt><dd>([^<]+)</dd>"
    for dt, dd in re.findall(dt_dd_pattern, html_content):
        key = clean_html(dt.strip(":"))
        value = clean_html(dd)
        specs[key] = value

    return {"specifications": specs}


def extract_attributes(script_content):
    """Извлекает атрибуты продукта с полной структурой"""
    # Ищем всю секцию атрибутов
    attr_section_pattern = r"attributes:{default:\[(.*?)\],highlighted:"
    section_match = re.search(attr_section_pattern, script_content, re.DOTALL)

    if not section_match:
        return {}

    attrs_section = section_match.group(1)
    attributes = []

    # Извлекаем каждый атрибут
    attr_pattern = r'{id:"([^"]+)",name:"([^"]+)",values:\[([^\]]*)\]'
    for attr_match in re.finditer(attr_pattern, attrs_section):
        attr_id = attr_match.group(1)
        attr_name = attr_match.group(2)
        values_text = attr_match.group(3)

        # Извлекаем значения
        values = []
        value_pattern = r'{text:"([^"]+)"(?:,link:"([^"]+)")?}'
        for value_match in re.finditer(value_pattern, values_text):
            value = {"text": value_match.group(1)}
            if value_match.group(2):
                value["link"] = value_match.group(2).replace("\\u002F", "/")
            values.append(value)

        # Пропускаем атрибуты с пустыми значениями
        if not values:
            continue

        # Получаем дополнительные флаги
        flags = {}
        flag_patterns = {
            "isCategoryRelevant": r"isCategoryRelevant:(true|false)",
            "isDefaultRelevant": r"isDefaultRelevant:(true|false)",
            "isPartOfRadioEquipmentAct": r"isPartOfRadioEquipmentAct:(true|false)",
        }

        for flag_name, pattern in flag_patterns.items():
            flag_match = re.search(pattern, attrs_section)
            if flag_match:
                flags[flag_name] = flag_match.group(1) == "true"

        attributes.append(
            {"id": attr_id, "name": attr_name, "values": values, "flags": flags}
        )

    return attributes


def extract_image_hashes(script_content):
    """Извлекает хеши изображений из скрипта"""
    # Ищем последнюю часть скрипта с параметрами функции
    end_pattern = r"\)\((.*?)\)\);$"
    match = re.search(end_pattern, script_content)
    if not match:
        return []

    # Получаем список параметров
    params = match.group(1).split(",")

    # Извлекаем только хеши (строки из 32 символов в шестнадцатеричном формате)
    hashes = []
    hash_pattern = r'"([a-f0-9]{32})"'

    for param in params:
        hash_match = re.search(hash_pattern, param)
        if hash_match:
            hashes.append(hash_match.group(1))

    return hashes


def extract_product_data(script_content):
    """Извлекает все данные о продукте"""
    product_data = {
        "id": None,
        "title": None,
        "manufacturer": None,
        "price": None,
        "currency": None,
        "breadcrumb": [],
        "description": {},
        "attributes": [],
        "reviews": {},
        "delivery": {},
        "image_hashes": [],  # Добавляем новое поле
    }

    # Базовая информация
    title_match = re.search(r'title:"([^"]+)"', script_content)
    if title_match:
        product_data["title"] = title_match.group(1)

    # Производитель
    manufacturer_pattern = r'"manufacturer".*?"text":"([^"]+)"'
    manufacturer_match = re.search(manufacturer_pattern, script_content)
    if manufacturer_match:
        product_data["manufacturer"] = manufacturer_match.group(1)

    # Цена и валюта
    price_match = re.search(r"B\.offerNetPrice=([\d.]+)", script_content)
    if price_match:
        product_data["price"] = float(price_match.group(1))
        product_data["currency"] = "EUR"

    # Хлебные крошки
    product_data["breadcrumb"] = extract_breadcrumb(script_content)

    # Описание и характеристики
    description_data = extract_description(script_content)
    product_data.update(description_data)

    # Атрибуты
    product_data["attributes"] = extract_attributes(script_content)

    # Информация о доставке
    delivery_pattern = r"delivery:{([^}]+)}"
    delivery_match = re.search(delivery_pattern, script_content)
    if delivery_match:
        delivery_text = delivery_match.group(1)
        delivery_info = {}
        for field in ["datePhrase", "deliveryTime"]:
            field_match = re.search(rf'{field}:"([^"]+)"', delivery_text)
            if field_match:
                delivery_info[field] = field_match.group(1)
        product_data["delivery"] = delivery_info

    # Информация об отзывах
    reviews_pattern = r"reviewMetaData:{numberOfReviews:(\d+),numberOfStars:([\d.]+)}"
    reviews_match = re.search(reviews_pattern, script_content)
    if reviews_match:
        product_data["reviews"] = {
            "count": int(reviews_match.group(1)),
            "rating": float(reviews_match.group(2)),
        }
    # Добавляем извлечение хешей изображений
    product_data["image_hashes"] = extract_image_hashes(script_content)
    return product_data


def extract_script_content(html_file_path):
    """
    Извлекает содержимое скрипта, содержащего 'APP_SHELL_SSR_STATE_@mf\u002Fpdp-frontend' из HTML-файла.

    Args:
        html_file_path (str): Путь к HTML-файлу

    Returns:
        str: Содержимое скрипта или None, если скрипт не найден
    """
    try:
        # Чтение HTML-файла
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Метод 1: Используем BeautifulSoup для извлечения всех скриптов
        soup = BeautifulSoup(html_content, "html.parser")
        scripts = soup.find_all("script")

        target_script = None
        target_pattern = r'window\["APP_SHELL_SSR_STATE_@mf\\u002Fpdp-frontend"\]'

        # Проверяем каждый скрипт на наличие целевого идентификатора
        for script in scripts:
            if script.string and re.search(target_pattern, script.string):
                target_script = script.string
                break

        # Метод 2: Если BeautifulSoup не нашел скрипт, используем регулярные выражения
        if target_script is None:
            pattern = r'<script[^>]*>(.*?window\["APP_SHELL_SSR_STATE_@mf\\u002Fpdp-frontend"\].*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                target_script = match.group(1)

        return target_script

    except Exception as e:
        print(f"Произошла ошибка при извлечении скрипта: {e}")
        return None


def main():
    try:
        logger.info("Читаем файл скрипта...")
        # with open("found_script.txt", "r", encoding="utf-8") as f:
        #     script_content = f.read()
        script_content = extract_script_content(
            "Astschere, Baumschere, Gartenschere, _ Kaufland.de.html"
        )
        product_data = extract_product_data(script_content)

        logger.info("\nСохраняем результат...")
        with open("product_data.json", "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        logger.info("Данные успешно извлечены и сохранены в 'product_data.json'")

        # Выводим основную информацию
        logger.info("\nОсновная информация о продукте:")
        logger.info(f"Название: {product_data['title']}")
        logger.info(f"Цена: {product_data['price']} {product_data['currency']}")

        if product_data["breadcrumb"]:
            logger.info("\nКатегории:")
            for item in product_data["breadcrumb"]:
                title = item.get("title") or item.get("name", "Без названия")
                logger.info(f"- {title}")

        if product_data.get("specifications"):
            logger.info("\nОсновные характеристики:")
            for key, value in list(product_data["specifications"].items())[:5]:
                logger.info(f"{key}: {value}")

        if product_data.get("attributes"):
            logger.info("\nАтрибуты:")
            for attr in product_data["attributes"][:5]:  # Показываем первые 5 атрибутов
                values_text = ", ".join(v["text"] for v in attr["values"])
                logger.info(f"{attr['name']}: {values_text}")

        if product_data.get("reviews"):
            logger.info(
                f"\nОтзывы: {product_data['reviews']['count']} шт., "
                f"рейтинг: {product_data['reviews']['rating']}"
            )

        if product_data.get("delivery"):
            logger.info(f"\nДоставка: {product_data['delivery'].get('datePhrase')}")

    except FileNotFoundError:
        logger.error("Ошибка: Не найден файл found_script.txt")
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
