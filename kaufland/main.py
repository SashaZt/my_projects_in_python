# Рабочий код для парсинга с html файлов

import json
import re
import sys
from pathlib import Path

from loguru import logger

current_directory = Path.cwd()
log_directory = current_directory / "log"
json_directory = current_directory / "json"
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

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


def extract_script_content(file_path):
    """
    Извлекает содержимое скрипта с APP_SHELL_SSR_STATE из HTML файла

    Args:
        file_path (str): Путь к файлу HTML или содержимое HTML

    Returns:
        str: Содержимое скрипта
    """
    try:
        # Проверяем, является ли input файлом или строкой HTML
        if file_path.endswith(".html") or file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        else:
            content = file_path

        # Найти JavaScript в тегах script
        pattern = r'<script>(window\["APP_SHELL_SSR_STATE_@mf\\u002Fpdp-frontend"\].*?)<\/script>'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1)
        else:
            return None
    except Exception as e:
        logger.warning(f"Ошибка при обработке ввода: {e}")
        return None


def extract_image_hashes(script_content):
    """
    Извлекает хеши изображений из скрипта

    Args:
        script_content (str): Содержимое JavaScript

    Returns:
        list: Список хешей изображений
    """
    # Ищем последовательность параметров в вызове функции
    end_pattern = r"\}\((.*?)\)\);$"
    match = re.search(end_pattern, script_content)
    if not match:
        return []

    # Получаем строку с параметрами
    params_str = match.group(1)

    # Извлекаем только хеши (строки из 32 символов в шестнадцатеричном формате)
    hash_pattern = r'"([a-f0-9]{32})"'
    hash_matches = re.finditer(hash_pattern, params_str)

    hashes = [
        f"https://media.cdn.kaufland.de/product-images/1024x1024/{match.group(1)}.webp"
        for match in hash_matches
    ]
    return hashes


def parse_js_assignment(js_code):
    """
    Парсит JavaScript-выражение присваивания и извлекает данные

    Args:
        js_code (str): JavaScript-код с выражением присваивания

    Returns:
        dict: Структурированные данные из JavaScript-объекта
    """
    # Извлечь IIFE (Immediately Invoked Function Expression)
    iife_pattern = r'window\["APP_SHELL_SSR_STATE_@mf\\u002Fpdp-frontend"\] = \(function\((.*?)\)\{(.*?)return (.*?)\}\((.*?)\)\);'
    match = re.search(iife_pattern, js_code, re.DOTALL)

    if not match:
        return None

    # Получить параметры, тело функции, возвращаемый объект и переданные аргументы
    parameters = match.group(1).split(",")
    function_body = match.group(2)
    return_object = match.group(3)
    args = match.group(4).split(",")

    # Создать отображение аргументов на параметры
    param_map = {}
    for i, param in enumerate(parameters):
        if i < len(args):
            param_map[param.strip()] = args[i].strip()

    # Извлечь определения переменных из тела функции
    var_defs = {}
    var_pattern = r"B\.(\w+)=(.*?);"
    var_matches = re.finditer(var_pattern, function_body)

    for var_match in var_matches:
        var_name = var_match.group(1)
        var_value = var_match.group(2)

        # Попробовать преобразовать значение
        try:
            # Преобразовать числа
            if var_value.replace(".", "", 1).isdigit():
                var_defs[var_name] = (
                    float(var_value) if "." in var_value else int(var_value)
                )
            # Обработать ссылки на параметры
            elif var_value in param_map:
                var_defs[var_name] = param_map[var_value]
            else:
                var_defs[var_name] = var_value
        except:
            var_defs[var_name] = var_value

    # Извлечение полной структуры данных товара
    product_info = {
        # Базовая информация из переменных
        "offerNetPrice": var_defs.get("offerNetPrice"),
        "sellerId": var_defs.get("sellerId"),
        "offerId": var_defs.get("offerId"),
        "categoryId": var_defs.get("categoryId"),
        "itemId": var_defs.get("itemId"),
        "isDirectSales": var_defs.get("isDirectSales"),
    }

    # Расширенное извлечение данных из return_object
    try:
        # Основная информация о товаре
        title_pattern = r'title:"([^"]+)"'
        title_match = re.search(title_pattern, return_object)
        if title_match:
            product_info["title"] = title_match.group(1)

        # Цена
        price_pattern = r"price:([\d.]+)"
        price_match = re.search(price_pattern, return_object)
        if price_match:
            product_info["price"] = float(price_match.group(1))

        # Валюта
        currency_pattern = r'currency:"([^"]+)"'
        currency_match = re.search(currency_pattern, return_object)
        if currency_match:
            product_info["currency"] = currency_match.group(1)

        # Описание продукта
        description_pattern = r'descriptionHtml:"([^"]+)"'
        description_match = re.search(description_pattern, return_object)
        if description_match:
            product_info["description"] = (
                description_match.group(1)
                .replace("\\u003C", "<")
                .replace("\\u003E", ">")
                .replace("\\u002F", "/")
            )

        # Информация о доставке
        delivery_date_pattern = r'datePhrase:"([^"]+)"'
        delivery_date_match = re.search(delivery_date_pattern, return_object)
        if delivery_date_match:
            product_info["deliveryDate"] = delivery_date_match.group(1)

        delivery_time_pattern = r'deliveryTime:"([^"]+)"'
        delivery_time_match = re.search(delivery_time_pattern, return_object)
        if delivery_time_match:
            product_info["deliveryTime"] = delivery_time_match.group(1)

        # Информация о категории
        main_category_title_pattern = r"mainCategoryTitle:([^,}]+)"
        main_category_title_match = re.search(
            main_category_title_pattern, return_object
        )
        if main_category_title_match:
            # Очистить значение от возможных ссылок на параметры
            cat_title = main_category_title_match.group(1).strip()
            if cat_title in param_map:
                product_info["mainCategoryTitle"] = param_map[cat_title].strip('"')
            else:
                product_info["mainCategoryTitle"] = cat_title.strip('"')

        # URL товара
        path_pattern = r'virtualProductPath:"([^"]+)"'
        path_match = re.search(path_pattern, return_object)
        if path_match:
            product_info["productPath"] = path_match.group(1).replace("\\u002F", "/")

        # Производитель
        manufacturer_pattern = r"name:([^,}]+),logoUrl:"
        manufacturer_match = re.search(manufacturer_pattern, return_object)
        if manufacturer_match:
            manufacturer = manufacturer_match.group(1).strip()
            if manufacturer in param_map:
                product_info["manufacturer"] = param_map[manufacturer].strip('"')
            else:
                product_info["manufacturer"] = manufacturer.strip('"')

        # EAN и другие атрибуты
        ean_pattern = r'EAN",values:\[\{text:"([^"]+)"\}\]'
        ean_match = re.search(ean_pattern, return_object)
        if ean_match:
            product_info["ean"] = ean_match.group(1)
        else:
            # Альтернативный поиск EAN
            alt_ean_pattern = (
                r'"0\d{12,13}"'  # EAN обычно начинается с 0 и содержит 13-14 цифр
            )
            alt_ean_match = re.search(alt_ean_pattern, return_object)
            if alt_ean_match:
                product_info["ean"] = alt_ean_match.group(0).strip('"')

        # Информация о продавце
        seller_name_pattern = r'name:"([^"]+)",legalData:'
        seller_name_match = re.search(seller_name_pattern, return_object)
        if seller_name_match:
            product_info["sellerName"] = seller_name_match.group(1)

        shop_link_pattern = r'shopLink:"([^"]+)"'
        shop_link_match = re.search(shop_link_pattern, return_object)
        if shop_link_match:
            product_info["shopLink"] = shop_link_match.group(1).replace("\\u002F", "/")

        # Срок возврата
        return_period_pattern = r'returnPeriod:"([^"]+)"'
        return_period_match = re.search(return_period_pattern, return_object)
        if return_period_match:
            product_info["returnPeriod"] = return_period_match.group(1)

        # Доступное количество
        amount_left_pattern = r"amountLeft:(\d+),"
        amount_left_match = re.search(amount_left_pattern, return_object)
        if amount_left_match:
            product_info["amountLeft"] = int(amount_left_match.group(1))

        # Хлебные крошки
        breadcrumb_pattern = r'\{id:(\d+),title:"([^"]+)",name:"([^"]+)",url:"([^"]+)"'
        breadcrumb_matches = re.finditer(breadcrumb_pattern, return_object)
        breadcrumbs = []
        for match in breadcrumb_matches:
            breadcrumbs.append(
                {
                    "id": match.group(1),
                    "title": match.group(2),
                    "name": match.group(3),
                    "url": match.group(4).replace("\\u002F", "/"),
                }
            )
        product_info["breadcrumbs"] = breadcrumbs

        # Ответственные лица (например, информация о компании)
        responsible_pattern = r'name:"([^"]+)",address:"([^"]+)",email:"([^"]+)"'
        responsible_match = re.search(responsible_pattern, return_object)
        if responsible_match:
            product_info["responsiblePeople"] = {
                "name": responsible_match.group(1),
                "address": responsible_match.group(2).replace("\\n", "\n"),
                "email": responsible_match.group(3),
            }

        # Рейтинг и количество отзывов
        reviews_pattern = r"numberOfReviews:(\d+),numberOfStars:(\d+)"
        reviews_match = re.search(reviews_pattern, return_object)
        if reviews_match:
            product_info["reviews"] = {
                "count": int(reviews_match.group(1)),
                "stars": int(reviews_match.group(2)),
            }

        # Информация о доставке
        country_pattern = r'country:"([^"]+)",countryISO:"([^"]+)"'
        country_match = re.search(country_pattern, return_object)
        if country_match:
            product_info["deliveryCountry"] = {
                "name": country_match.group(1),
                "iso": country_match.group(2),
            }

        # Диапазон времени доставки
        delivery_range_pattern = r'min:"([^"]+)",max:"([^"]+)"'
        delivery_range_match = re.search(delivery_range_pattern, return_object)
        if delivery_range_match:
            product_info["deliveryTimeRange"] = {
                "min": delivery_range_match.group(1),
                "max": delivery_range_match.group(2),
            }

    except Exception as e:
        logger.warning(f"Ошибка при извлечении данных из объекта: {e}")

    return product_info


def extract_product_data(input_content, output_file=None):
    """
    Извлекает данные о товаре из HTML файла или строки HTML и опционально сохраняет в JSON

    Args:
        input_content (str): Путь к HTML файлу или строка с HTML содержимым
        output_file (str, optional): Путь для сохранения результатов в JSON

    Returns:
        dict: Данные о товаре
    """
    # Извлечь скрипт
    script_content = extract_script_content(input_content)

    if not script_content:
        logger.warning("Скрипт не найден в содержимом.")
        return None

    # Разобрать данные
    product_data = parse_js_assignment(script_content)
    # Добавляем извлечение хешей изображений из параметров IIFE
    direct_image_hashes = extract_image_hashes(script_content)
    if direct_image_hashes:
        product_data["directImageHashes"] = direct_image_hashes
    if not product_data:
        logger.warning("Не удалось разобрать данные из скрипта.")
        return None
    # Сохранить результат в JSON, если указан output_file
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Данные сохранены в {output_file}")

    return product_data


def parse_to_custom_structure(input_file):
    """
    Парсит HTML файл и сохраняет данные в заданной структуре JSON

    Args:
        input_file (str): Путь к HTML файлу
        output_file (str, optional): Путь для сохранения результатов в JSON. По умолчанию "product.json"

    Returns:
        dict: Данные о товаре в заданной структуре
    """
    # Получаем данные из существующей функции
    product_data = extract_product_data(input_file)

    if not product_data:
        logger.warning("Не удалось получить данные о товаре")
        return None
    ean = product_data.get("ean", "")
    # Создаем структуру согласно требованию
    custom_structure = {
        "ean": [product_data.get("ean", "")],
        "attributes": {
            "title": [product_data.get("title", "")],
            "manufacturer": [product_data.get("manufacturer", "")],
            "category": [product_data.get("mainCategoryTitle", "")],
            "description": [product_data.get("description", "")],
            "picture": [],
        },
    }

    # Добавляем URL изображений, если они доступны
    if "directImageHashes" in product_data and product_data["directImageHashes"]:
        custom_structure["attributes"]["picture"] = product_data["directImageHashes"]

    json_file = json_directory / f"{ean}.json"
    # Сохраняем результат в JSON файл
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(custom_structure, f, ensure_ascii=False, indent=4)

    logger.info(f"Данные в кастомной структуре сохранены в {json_file}")

    return custom_structure


# Пример использования
if __name__ == "__main__":
    input_file = "product.html"  # Путь к HTML файлу
    output_file = "product_data.json"  # Путь для сохранения результатов

    # Полнеый парсер htmlфайла
    # product_data = extract_product_data(input_file, output_file)

    ## Готовит специальный файл для выгрузки через API
    parse_to_custom_structure(input_file)
