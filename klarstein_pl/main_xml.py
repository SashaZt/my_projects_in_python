import json
import re
import xml.dom.minidom
from pathlib import Path
from xml.etree import ElementTree as ET

from config.logger import logger
from main_db import loader

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "easy.html"


# Полный обновленный код для main_xml.py
def create_xml(data, output_file):
    """
    Создает YML файл для Prom.ua с полной поддержкой обязательных полей
    Поддерживает как старую структуру данных, так и новую YML-структуру
    """

    # Определяем тип структуры данных
    if "shop_info" in data and "offers" in data:
        # Новая YML структура
        return create_xml_from_yml_structure(data, output_file)
    # else:
    #     # Старая структура - конвертируем в новую
    #     yml_data = convert_old_to_yml_structure(data)
    #     return create_xml_from_yml_structure(yml_data, output_file)


# # Обновляем функцию конвертации, чтобы model использовал правильный язык
# def convert_old_to_yml_structure(old_data):
#     """
#     Конвертирует старую структуру данных в новую YML структуру
#     ПОЛЬСКИЙ СОХРАНЯЕТСЯ ТОЛЬКО ДЛЯ ПЕРЕВОДА, В XML НЕ ПОПАДАЕТ
#     """
#     # Извлекаем данные из старой структуры
#     product = old_data.get("product", {})
#     descriptions = old_data.get("description_pl", [])
#     breadcrumbs = old_data.get("breadcrumbs_pl", [])

#     # Генерируем категории из breadcrumbs
#     categories = []
#     parent_id = None
#     for idx, category_name in enumerate(breadcrumbs, 1):
#         category = {
#             "id": idx,
#             "name_pl": category_name,  # польский - только для БД и перевода
#             "name": category_name,  # русский - заполнится после перевода
#             "name_ua": category_name,  # украинский - заполнится после перевода
#         }
#         if parent_id:
#             category["parentId"] = parent_id
#         categories.append(category)
#         parent_id = idx

#     # # Если нет breadcrumbs, создаем дефолтную категорию
#     # if not categories:
#     #     categories.append(
#     #         {
#     #             "id": 1,
#     #             "name_pl": "Produkty",  # только для БД
#     #             "name": "Товары",  # русский
#     #             "name_ua": "Товари",  # украинский
#     #         }
#     #     )

#     # Извлекаем размеры и вес
#     dimensions = extract_dimensions_from_descriptions(descriptions)

#     # Определяем ID последней категории
#     category_id = len(categories) if categories else 1

#     # Формируем offer
#     offer = {
#         "id": product.get("sku", ""),
#         "available": "true",
#         "price": product.get("price", "0"),
#         "currencyId": "UAH",
#         "categoryId": str(category_id),
#         # Названия товара
#         "name_pl": product.get("name_pl", ""),  # польский - только для БД и перевода
#         "name": product.get("name", ""),  # русский - заполнится после перевода
#         "name_ua": product.get("name_ua", ""),  # украинский - заполнится после перевода
#         "vendor": "Klarstein",
#         "country_of_origin": "Германия",
#         # Модель тоже будет переводиться
#         "pictures": product.get("images", []),
#         # Описания
#         "description_pl": descriptions,  # польский - только для БД и перевода
#         "description": [],  # русский - заполнится после перевода
#         "description_ua": [],  # украинский - заполнится после перевода
#         "dimensions": dimensions,
#     }

#     # Формируем YML структуру
#     yml_structure = {
#         "shop_info": {
#             "name": "Klarstein Ukraine",
#             "company": "Klarstein Shop",
#             "url": "https://klarstein.ua",
#         },
#         "categories": categories,
#         "offers": [offer],
#     }

#     return yml_structure


def extract_dimensions_from_descriptions(descriptions):
    """
    Извлекает размеры и вес из описаний (старая логика)
    """
    dimensions = {}

    for accordion in descriptions:
        if (
            "wymiary" in accordion.get("title_pl", "").lower()
            or "techniczne" in accordion.get("title_pl", "").lower()
        ):
            tech_desc = accordion.get("description_pl", "")

            # Поиск размеров (ширина x высота x глубина)
            dimensions_match = re.search(
                r"wymiary: ok\. (\d+) x (\d+) x (\d+) cm", tech_desc, re.IGNORECASE
            )
            if dimensions_match:
                dimensions["width"] = dimensions_match.group(1)
                dimensions["height"] = dimensions_match.group(2)
                dimensions["length"] = dimensions_match.group(3)

            # Поиск веса
            weight_match = re.search(
                r"waga: ok\. ([\d,]+) kg", tech_desc, re.IGNORECASE
            )
            if weight_match:
                dimensions["weight"] = weight_match.group(1).replace(",", ".")

            break

    return dimensions


# def create_xml_from_yml_structure(yml_data, output_file):
#     """
#     Создает XML из YML структуры с полной поддержкой обязательных полей
#     ИСПРАВЛЕНО: Правильная обработка переведенных данных
#     """

#     # Создание корневого элемента
#     root = ET.Element("yml_catalog")
#     root.set("date", "2025-06-02 12:00")

#     shop = ET.SubElement(root, "shop")

#     # === ОБЯЗАТЕЛЬНЫЕ ЭЛЕМЕНТЫ МАГАЗИНА ===

#     shop_info = yml_data.get("shop_info", {})

#     # 1. Название магазина (обязательно)
#     name = ET.SubElement(shop, "name")
#     name.text = shop_info.get("name", "Klarstein Ukraine")

#     # 2. Компания (обязательно)
#     company = ET.SubElement(shop, "company")
#     company.text = shop_info.get("company", "Klarstein Shop")

#     # 3. URL сайта (обязательно)
#     url = ET.SubElement(shop, "url")
#     url.text = shop_info.get("url", "https://klarstein.ua")

#     # 4. Валюты (обязательно)
#     currencies = ET.SubElement(shop, "currencies")
#     currency = ET.SubElement(currencies, "currency", id="UAH", rate="1")

#     # 5. Категории (обязательно)
#     categories_element = ET.SubElement(shop, "categories")
#     for category in yml_data.get("categories", []):
#         cat_attrs = {"id": str(category["id"])}
#         if "parentId" in category:
#             cat_attrs["parentId"] = str(category["parentId"])

#         category_element = ET.SubElement(categories_element, "category", **cat_attrs)

#         # ИСПРАВЛЕНО: Приоритет украинский -> русский (БЕЗ польского)
#         category_name = category.get("name_ua") or category.get("name", "")
#         category_element.text = category_name

#     # 6. Блок товаров (обязательно)
#     offers = ET.SubElement(shop, "offers")

#     # Создание товаров
#     descriptions_for_cdata = []
#     for offer_data in yml_data.get("offers", []):
#         create_offer_element(offers, offer_data)
#         descriptions_for_cdata.append(offer_data)

#     # Создание XML строки
#     xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

#     # Заменяем плейсхолдеры на CDATA содержимое
#     xml_str = replace_description_placeholders(xml_str, descriptions_for_cdata)

#     # Форматирование XML
#     dom = xml.dom.minidom.parseString(xml_str)
#     pretty_xml = dom.toprettyxml(indent="  ")

#     # Добавление правильной декларации XML с DOCTYPE
#     pretty_xml = format_final_xml(pretty_xml)

#     # Запись в файл
#     with open(output_file, "w", encoding="utf-8") as file:
#         file.write(pretty_xml)


#     logger.info(f"YML файл создан: {output_file}")
#     return pretty_xml
def create_xml_from_yml_structure(yml_data, output_file):
    """
    Создает XML из YML структуры с полной поддержкой обязательных полей
    ИСПРАВЛЕНО: Правильная обработка дерева категорий
    """

    # Создание корневого элемента
    root = ET.Element("yml_catalog")
    root.set("date", "2025-06-02 12:00")

    shop = ET.SubElement(root, "shop")

    # === ОБЯЗАТЕЛЬНЫЕ ЭЛЕМЕНТЫ МАГАЗИНА ===

    shop_info = yml_data.get("shop_info", {})

    # 1. Название магазина (обязательно)
    name = ET.SubElement(shop, "name")
    name.text = shop_info.get("name", "Klarstein Ukraine")

    # 2. Компания (обязательно)
    company = ET.SubElement(shop, "company")
    company.text = shop_info.get("company", "Klarstein Shop")

    # 3. URL сайта (обязательно)
    url = ET.SubElement(shop, "url")
    url.text = shop_info.get("url", "https://klarstein.ua")

    # 4. Валюты (обязательно)
    currencies = ET.SubElement(shop, "currencies")
    currency = ET.SubElement(currencies, "currency", id="UAH", rate="1")

    # 5. Категории (обязательно) - ИСПРАВЛЕНО
    categories_element = ET.SubElement(shop, "categories")

    # Сортируем категории: сначала родительские (без parent_id), потом дочерние
    categories = yml_data.get("categories", [])
    categories_sorted = sorted(
        categories,
        key=lambda x: (
            x.get("parent_id")
            is not None,  # Сначала родительские (False), потом дочерние (True)
            x.get("parent_id") or 0,  # Сортировка по parent_id
            x.get("category_id", 0),  # Сортировка по id
        ),
    )

    for category in categories_sorted:
        cat_attrs = {"id": str(category["category_id"])}

        # Добавляем parentId только если он есть и не равен None
        parent_id = category.get("parent_id")
        if parent_id is not None:
            cat_attrs["parentId"] = str(parent_id)

        category_element = ET.SubElement(categories_element, "category", **cat_attrs)

        # ИСПРАВЛЕНО: Приоритет украинский -> русский (БЕЗ польского)
        category_name = category.get("name_ua") or category.get("name", "Категория")
        category_element.text = category_name

    # 6. Блок товаров (обязательно)
    offers = ET.SubElement(shop, "offers")

    # Создание товаров
    descriptions_for_cdata = []
    for offer_data in yml_data.get("offers", []):
        create_offer_element(offers, offer_data)
        descriptions_for_cdata.append(offer_data)

    # Создание XML строки
    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

    # Заменяем плейсхолдеры на CDATA содержимое
    xml_str = replace_description_placeholders(xml_str, descriptions_for_cdata)

    # Форматирование XML
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Добавление правильной декларации XML с DOCTYPE
    pretty_xml = format_final_xml(pretty_xml)

    # Запись в файл
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(pretty_xml)

    logger.info(f"YML файл создан: {output_file}")
    return pretty_xml


def create_offer_element(offers_parent, offer_data):
    """
    Создает элемент offer с полным соблюдением обязательных полей и их порядка
    ИСПРАВЛЕНО: Правильное использование quantity из БД
    """
    # === ОБЯЗАТЕЛЬНЫЕ АТРИБУТЫ OFFER ===
    offer_attrs = {
        "id": offer_data.get("id", ""),
        "available": offer_data.get("available", "true"),
        "selling_type": offer_data.get("selling_type", "u"),
    }

    # Добавляем группировку для вариантов товаров
    if offer_data.get("group_id"):
        offer_attrs["group_id"] = offer_data["group_id"]

    offer = ET.SubElement(offers_parent, "offer", **offer_attrs)

    # === ОБЯЗАТЕЛЬНЫЕ ЭЛЕМЕНТЫ В ПРАВИЛЬНОМ ПОРЯДКЕ ===

    # 1. Цена (обязательно)
    price = ET.SubElement(offer, "price")
    price.text = str(offer_data.get("price"))

    # Оптовые цены в структуре prices с quantity из БД
    price_opt1 = offer_data.get("price_opt1")
    quantity1 = offer_data.get("quantity1")
    price_opt2 = offer_data.get("price_opt2")
    quantity2 = offer_data.get("quantity2")
    logger.info(price_opt1)
    logger.info(price_opt2)
    logger.info(quantity1)
    logger.info(quantity2)
    # Проверяем, есть ли хотя бы одна оптовая цена
    has_opt_prices = False

    # Проверяем первую оптовую цену
    if price_opt1 and str(price_opt1).strip() and float(str(price_opt1)) > 0:
        has_opt_prices = True

    # Проверяем вторую оптовую цену
    if price_opt2 and str(price_opt2).strip() and float(str(price_opt2)) > 0:
        has_opt_prices = True

    # Создаем элемент prices только если есть оптовые цены
    if has_opt_prices:
        prices = ET.SubElement(offer, "prices")

        # Добавляем первую оптовую цену, если она есть
        if price_opt1 and str(price_opt1).strip() and float(str(price_opt1)) > 0:
            price_elem1 = ET.SubElement(prices, "price")
            value1 = ET.SubElement(price_elem1, "value")
            value1.text = str(price_opt1)
            quantity_elem1 = ET.SubElement(price_elem1, "quantity")
            quantity_elem1.text = str(quantity1) if quantity1 else "1"

        # Добавляем вторую оптовую цену, если она есть
        if price_opt2 and str(price_opt2).strip() and float(str(price_opt2)) > 0:
            price_elem2 = ET.SubElement(prices, "price")
            value2 = ET.SubElement(price_elem2, "value")
            value2.text = str(price_opt2)
            quantity_elem2 = ET.SubElement(price_elem2, "quantity")
            quantity_elem2.text = str(quantity2) if quantity2 else "1"
    # 2. Валюта (обязательно)
    currencyId = ET.SubElement(offer, "currencyId")
    currencyId.text = offer_data.get("currencyId", "UAH")
    # Скидка
    discount = ET.SubElement(offer, "discount")
    discount.text = offer_data.get("discount", "")

    # 3. Категория (обязательно)
    categoryId = ET.SubElement(offer, "categoryId")
    categoryId.text = str(offer_data.get("categoryId"))

    # 4. Название товара (обязательно)
    # ИСПРАВЛЕНО: Приоритет украинский -> русский
    name = ET.SubElement(offer, "name")
    product_name = offer_data.get("name", "")
    name.text = product_name
    name_ua = ET.SubElement(offer, "name_ua")
    product_name_ua = offer_data.get("name_ua", "")
    name_ua.text = product_name_ua

    # === ДОПОЛНИТЕЛЬНЫЕ РЕКОМЕНДУЕМЫЕ ПОЛЯ ===

    # Производитель
    if offer_data.get("vendor"):
        vendor = ET.SubElement(offer, "vendor")
        vendor.text = offer_data["vendor"]

    # Артикул
    if offer_data.get("vendorCode") is not None:
        vendor_code = ET.SubElement(offer, "vendorCode")
        vendor_code.text = str(offer_data["vendorCode"])

    # Страна производитель
    if offer_data.get("country_of_origin"):
        country_of_origin = ET.SubElement(offer, "country_of_origin")
        country_of_origin.text = offer_data["country_of_origin"]

    # Ключевые слова - используем переведенные (украинский -> русский)
    keywords_ua = offer_data.get("keywords_ua")
    if keywords_ua:
        keywords_elem_ua = ET.SubElement(offer, "keywords_ua")
        keywords_elem_ua.text = keywords_ua
    keywords = offer_data.get("keywords")
    if keywords:
        keywords_elem = ET.SubElement(offer, "keywords")
        keywords_elem.text = keywords

    # Изображения
    pictures = offer_data.get("pictures", offer_data.get("images", []))
    for img_url in pictures:
        if img_url:  # Проверяем, что URL не пустой
            picture = ET.SubElement(offer, "picture")
            picture.text = img_url

    # Описание на русском (с placeholder для CDATA)
    description = ET.SubElement(offer, "description")
    description.text = "DESCRIPTION_PLACEHOLDER_RU"

    # Описание на украинском (с placeholder для CDATA)
    description_ua = ET.SubElement(offer, "description_ua")
    description_ua.text = "DESCRIPTION_PLACEHOLDER_UA"

    # Размеры и вес
    add_dimensions_to_offer(offer, offer_data.get("dimensions", {}))

    # Характеристики (параметры)
    add_params_to_offer(offer, offer_data.get("params", {}))

    return offer


def add_dimensions_to_offer(offer_element, dimensions_data):
    """
    Добавляет размеры и вес к товару
    """
    if not dimensions_data:
        return

    dimensions = ET.SubElement(offer_element, "dimensions")

    # Вес
    if dimensions_data.get("weight"):
        weight_elem = ET.SubElement(dimensions, "weight", unit="кг")
        weight_elem.text = str(dimensions_data["weight"])

    # Ширина
    if dimensions_data.get("width"):
        width_elem = ET.SubElement(dimensions, "width", unit="см")
        width_elem.text = str(dimensions_data["width"])

    # Высота
    if dimensions_data.get("height"):
        height_elem = ET.SubElement(dimensions, "height", unit="см")
        height_elem.text = str(dimensions_data["height"])

    # Длина/глубина
    if dimensions_data.get("length"):
        length_elem = ET.SubElement(dimensions, "length", unit="см")
        length_elem.text = str(dimensions_data["length"])


def add_params_to_offer(offer_element, params_data):
    """
    Добавляет характеристики товара
    """
    for param_name, param_value in params_data.items():
        if param_value:  # Добавляем только непустые значения
            param = ET.SubElement(offer_element, "param", name=param_name)
            param.text = str(param_value)


def replace_description_placeholders(xml_str, offers_data):
    """
    Заменяет плейсхолдеры описаний на CDATA содержимое
    ИСПРАВЛЕНО: Поддержка обоих языков
    """
    for offer_data in offers_data:
        # Получаем описания для обоих языков
        description_ru = offer_data.get("description", "")
        description_ua = offer_data.get("description_ua", "")

        # Заменяем placeholder для русского описания
        xml_str = xml_str.replace(
            "<description>DESCRIPTION_PLACEHOLDER_RU</description>",
            f"<description><![CDATA[{description_ru}]]></description>",
            1,  # Заменяем только первое вхождение
        )

        # Заменяем placeholder для украинского описания
        xml_str = xml_str.replace(
            "<description_ua>DESCRIPTION_PLACEHOLDER_UA</description_ua>",
            f"<description_ua><![CDATA[{description_ua}]]></description_ua>",
            1,  # Заменяем только первое вхождение
        )

    return xml_str


def format_final_xml(pretty_xml):
    """
    Форматирует финальный XML с правильными декларациями
    """
    # Добавляем DOCTYPE если его нет
    if "<!DOCTYPE" not in pretty_xml:
        lines = pretty_xml.split("\n")
        # Находим строку с xml declaration
        xml_decl_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("<?xml"):
                xml_decl_index = i
                break

        # Вставляем DOCTYPE после xml declaration
        lines.insert(xml_decl_index + 1, '<!DOCTYPE yml_catalog SYSTEM "shops.dtd">')
        pretty_xml = "\n".join(lines)

    # Убираем лишние пустые строки
    lines = pretty_xml.split("\n")
    cleaned_lines = []
    for line in lines:
        if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# def create_xml_from_products_list(products_list, output_file):
#     """
#     Создает XML из списка товаров, полученных из БД
#     """
#     if not products_list:
#         logger.warning("Нет товаров для создания XML")
#         return None

#     # Получаем уникальные категории из товаров
#     categories_dict = {}

#     for product in products_list:
#         category_id = product.get("category_id")
#         if category_id and category_id not in categories_dict:
#             # Создаем базовую структуру категории
#             categories_dict[category_id] = {
#                 "id": category_id,
#                 "name": "Категория",  # Базовое название
#                 "name_ua": "Категорія",
#             }

#     # Преобразуем словарь категорий в список
#     categories_list = list(categories_dict.values())

#     # Формируем YML структуру
#     yml_structure = {
#         "shop_info": {
#             "name": "Klarstein Ukraine",
#             "company": "Klarstein UA",
#             "url": "https://klarstein.ua",
#         },
#         "categories": categories_list,
#         "offers": [],
#     }

#     # Преобразуем каждый товар в offer
#     for product in products_list:
#         offer = {
#             "id": product.get("product_id", ""),
#             "available": "true" if product.get("available") else "false",
#             "selling_type": product.get("selling_type", "u"),
#             "price": str(product.get("price", "0")),
#             "price_opt1": str(product.get("price_opt1", "0")),
#             "price_opt2": str(product.get("price_opt2", "0")),
#             "quantity1": str(product.get("quantity1", "0")),
#             "quantity2": str(product.get("quantity2", "0")),
#             "discount": str(product.get("discount")),
#             "currencyId": product.get("currency_id", "UAH"),
#             "categoryId": str(product.get("category_id", 1)),
#             # Названия товара
#             "name": product.get("name", ""),
#             "name_ua": product.get("name_ua", ""),
#             # Дополнительные поля
#             "vendor": product.get("vendor", "Klarstein"),
#             "vendorCode": product.get("vendor_code"),
#             "country_of_origin": product.get("country_of_origin", "Германия"),
#             "keywords": product.get("keywords", ""),
#             "keywords_ua": product.get("keywords_ua", ""),
#             # Изображения
#             "pictures": product.get("images", []),
#             # Описания
#             "description": product.get("description", ""),
#             "description_ua": product.get("description_ua", ""),
#             # Размеры
#             "dimensions": {
#                 "width": product.get("width"),
#                 "height": product.get("height"),
#                 "length": product.get("length"),
#                 "weight": product.get("weight"),
#             },
#         }

#         # Убираем пустые размеры
#         offer["dimensions"] = {
#             k: v for k, v in offer["dimensions"].items() if v is not None
#         }

#         yml_structure["offers"].append(offer)

#     # Создаем XML
#     return create_xml_from_yml_structure(yml_structure, output_file)


def create_xml_from_products_list(products_list, output_file):
    """
    Создает XML из списка товаров, полученных из БД
    ИСПРАВЛЕНО: Правильная загрузка дерева категорий
    """
    if not products_list:
        logger.warning("Нет товаров для создания XML")
        return None

    # ИСПРАВЛЕНО: Загружаем ВСЕ категории из БД для построения дерева
    categories_list = loader.get_all_categories()  # Нужно добавить эту функцию в loader

    if not categories_list:
        logger.warning("Нет категорий в БД")
        # Создаем дефолтную категорию
        categories_list = [
            {"category_id": 1, "parent_id": None, "name": "Товары", "name_ua": "Товари"}
        ]

    # Формируем YML структуру
    yml_structure = {
        "shop_info": {
            "name": "Klarstein Ukraine",
            "company": "Klarstein UA",
            "url": "https://klarstein.ua",
        },
        "categories": categories_list,  # Передаем полный список категорий
        "offers": [],
    }

    # Преобразуем каждый товар в offer
    for product in products_list:
        offer = {
            "id": product.get("product_id", ""),
            "available": "true" if product.get("available") else "false",
            "selling_type": product.get("selling_type", "u"),
            "price": str(product.get("price", "0")),
            "price_opt1": str(product.get("price_opt1", "0")),
            "price_opt2": str(product.get("price_opt2", "0")),
            "quantity1": str(product.get("quantity1", "1")),
            "quantity2": str(product.get("quantity2", "1")),
            "discount": str(product.get("discount", "")),
            "currencyId": product.get("currency_id", "UAH"),
            "categoryId": str(product.get("category_id", 1)),
            # Названия товара
            "name": product.get("name", ""),
            "name_ua": product.get("name_ua", ""),
            # Дополнительные поля
            "vendor": product.get("vendor", "Klarstein"),
            "vendorCode": product.get("vendor_code"),
            "country_of_origin": product.get("country_of_origin", "Германия"),
            "keywords": product.get("keywords", ""),
            "keywords_ua": product.get("keywords_ua", ""),
            # Изображения
            "pictures": product.get("images", []),
            # Описания
            "description": product.get("description", ""),
            "description_ua": product.get("description_ua", ""),
            # Размеры
            "dimensions": {
                "width": product.get("width"),
                "height": product.get("height"),
                "length": product.get("length"),
                "weight": product.get("weight"),
            },
        }

        # Убираем пустые размеры
        offer["dimensions"] = {
            k: v for k, v in offer["dimensions"].items() if v is not None
        }

        yml_structure["offers"].append(offer)

    # Создаем XML
    return create_xml_from_yml_structure(yml_structure, output_file)


def export_products_to_xml():
    """Экспортирует товары в XML и помечает их как выгруженные"""
    try:
        # Получаем товары для экспорта
        products = loader.get_products_for_export()
        # logger.info(products)
        # exit()
        if not products:
            logger.info("Нет товаров для экспорта в XML")
            return False

        logger.info(f"Найдено {len(products)} товаров для экспорта")

        # Создаем XML из списка товаров
        xml_result = create_xml_from_products_list(products, "export_output.xml")

        if xml_result:
            # Помечаем товары как выгруженные
            product_ids = [product["product_id"] for product in products]
            success = loader.mark_as_exported(product_ids)

            if success:
                logger.info(
                    f"XML создан успешно. {len(product_ids)} товаров помечены как выгруженные"
                )
                return True
            else:
                logger.error("Ошибка при пометке товаров как выгруженные")
                return False
        else:
            logger.error("Ошибка создания XML")
            return False

    except Exception as e:
        logger.error(f"Ошибка экспорта товаров в XML: {e}")
        return False


if __name__ == "__main__":
    success = export_products_to_xml()

    if success:
        logger.info("Экспорт товаров в XML завершен успешно")
    else:
        logger.error("Экспорт товаров в XML завершен с ошибками")
