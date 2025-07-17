#client/scrap.py
import json
import math
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from main_db import loader
from translation import translate_text

from config import Config, logger, paths


class CategoriesManager:
    """Менеджер для управления уникальными категориями с правильной иерархией"""

    def __init__(self):
        # Основной реестр: {уникальный_ключ: category_data}
        self.categories_registry = {}
        # Маппинг имени на ID для быстрого поиска: {name_pl: category_id}
        self.name_to_id = {}
        # Маппинг полного пути на ID: {"Małe AGD" -> "Małe AGD > Kostkarki do lodu": category_id}
        self.path_to_id = {}
        self.next_id = 1

    def _get_category_path(self, breadcrumbs_pl, index):
        """Создает уникальный путь для категории"""
        return " > ".join(breadcrumbs_pl[: index + 1])

    def add_breadcrumbs(self, breadcrumbs_pl):
        """
        Добавляет цепочку breadcrumbs и возвращает ID последней категории
        ИСПРАВЛЕНО: правильная обработка иерархии без дубликатов
        """
        if not breadcrumbs_pl:
            return 1  # Дефолтная категория

        current_parent_id = None
        last_category_id = None

        # Проходим по каждому уровню breadcrumbs
        for i, category_name_pl in enumerate(breadcrumbs_pl):
            # Создаем уникальный путь для этой категории
            category_path = self._get_category_path(breadcrumbs_pl, i)

            # Проверяем, существует ли категория по полному пути
            if category_path in self.path_to_id:
                # Категория уже существует
                category_id = self.path_to_id[category_path]
                last_category_id = category_id
                current_parent_id = category_id
                logger.debug(
                    f"Найдена существующая категория: {category_path} (ID: {category_id})"
                )
            else:
                # Создаем новую категорию
                logger.info(
                    f"Создаем новую категорию: {category_name_pl} (путь: {category_path})"
                )

                # Переводим название
                russian, ukrainian = translate_text(category_name_pl)

                new_category = {
                    "id": self.next_id,
                    "name": russian,
                    "name_pl": category_name_pl,
                    "name_ua": ukrainian,
                    "path": category_path,  # Сохраняем полный путь для отладки
                }

                # Добавляем parentId если есть родитель
                if current_parent_id:
                    new_category["parentId"] = current_parent_id

                # Регистрируем категорию
                unique_key = f"id_{self.next_id}"
                self.categories_registry[unique_key] = new_category
                self.path_to_id[category_path] = self.next_id

                # Также ведем простой маппинг имени на ID (для последней категории с таким именем)
                self.name_to_id[category_name_pl] = self.next_id

                last_category_id = self.next_id
                current_parent_id = self.next_id
                self.next_id += 1

                logger.info(
                    f"Категория создана: {category_name_pl} -> ID: {current_parent_id}"
                )

        return last_category_id

    def get_all_categories(self):
        """Возвращает все уникальные категории в виде списка"""
        categories = list(self.categories_registry.values())

        # Сортируем: сначала родительские (без parentId), потом дочерние
        categories_sorted = sorted(
            categories,
            key=lambda x: (
                "parentId" in x,  # Сначала без parentId (родительские)
                x.get("parentId", 0),  # Потом по parentId
                x["id"],  # Потом по id
            ),
        )

        logger.info(f"Возвращаем {len(categories_sorted)} уникальных категорий")
        return categories_sorted

    def get_category_id_by_name_pl(self, name_pl):
        """Возвращает ID категории по польскому названию"""
        return self.name_to_id.get(name_pl, 1)  # Дефолтная категория

    def get_category_id_by_path(self, breadcrumbs_pl):
        """Возвращает ID категории по полному пути"""
        if not breadcrumbs_pl:
            return 1

        full_path = " > ".join(breadcrumbs_pl)
        return self.path_to_id.get(full_path, 1)

    def print_debug_info(self):
        """Отладочная информация о категориях"""
        logger.info("=== ОТЛАДКА КАТЕГОРИЙ ===")
        logger.info(f"Всего категорий: {len(self.categories_registry)}")

        for key, category in self.categories_registry.items():
            parent_info = (
                f" (родитель: {category['parentId']})"
                if "parentId" in category
                else " (корневая)"
            )
            logger.info(f"ID {category['id']}: {category['name_pl']}{parent_info}")

        logger.info("=== ПУТИ КАТЕГОРИЙ ===")
        for path, cat_id in self.path_to_id.items():
            logger.info(f"'{path}' -> ID: {cat_id}")


categories_manager = CategoriesManager()
config = Config.load()

def scrap_html_file():
    """ИСПРАВЛЕННАЯ версия - корректное управление категориями"""
    global categories_manager

    all_products = []
    html_files = list(paths.html.glob("*.html"))

    logger.info(f"Найдено {len(html_files)} HTML файлов для обработки")

    # # ЭТАП 1: Сначала собираем ВСЕ категории из всех файлов
    logger.info("=== ЭТАП 1: Сбор всех категорий ===")

    for html_file in html_files:
        logger.info(f"Сканируем категории в файле: {html_file.name}")

        try:
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            soup = BeautifulSoup(content, "lxml")
            script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

            # Ищем breadcrumbs
            breadcrumb_script = None
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if json_data.get("@type") == "BreadcrumbList":
                        breadcrumb_script = json_data
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

            if breadcrumb_script:
                # Извлекаем breadcrumbs
                itemListElement = breadcrumb_script.get("itemListElement", [])
                breadcrumbs_pl = []
                for item in itemListElement[:-1]:
                    if isinstance(item, dict):
                        breadcrumbs_pl.append(item.get("name"))

                if breadcrumbs_pl:
                    # ВАЖНО: Регистрируем категории, но пока не обрабатываем товары
                    categories_manager.add_breadcrumbs(breadcrumbs_pl)
                    logger.info(
                        f"Зарегистрированы категории: {' > '.join(breadcrumbs_pl)}"
                    )

        except Exception as e:
            logger.error(f"Ошибка сканирования категорий в файле {html_file.name}: {e}")
            continue

    # Выводим отладочную информацию о собранных категориях
    categories_manager.print_debug_info()

    # ЭТАП 2: Теперь обрабатываем товары с уже готовыми категориями
    logger.info("=== ЭТАП 2: Обработка товаров ===")

    for html_file in html_files:
        logger.info(f"Обрабатываем товар в файле: {html_file.name}")

        try:
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            soup = BeautifulSoup(content, "lxml")
            script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

            # Ищем данные товара и breadcrumbs
            breadcrumb_script = None
            product_script = None
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if (
                        json_data.get("@type") == "BreadcrumbList"
                        and not breadcrumb_script
                    ):
                        breadcrumb_script = json_data
                    elif json_data.get("@type") == "Product" and not product_script:
                        product_script = json_data

                    if breadcrumb_script and product_script:
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

            if not product_script or not breadcrumb_script:
                logger.warning(
                    f"Не найдены необходимые данные в файле {html_file.name}"
                )
                continue

            # Получаем данные продукта
            product_data = scrap_json_product(product_script, breadcrumb_script)
            product_data_description = scrap_html_product(soup)

            # Объединяем данные
            product_data.update(product_data_description)

            # ВАЖНО: Определяем category_id по полному пути breadcrumbs
            breadcrumbs_pl = product_data.get("breadcrumbs_pl", [])
            if breadcrumbs_pl:
                category_id = categories_manager.get_category_id_by_path(breadcrumbs_pl)
            else:
                category_id = 1

            # Добавляем ID категории к данным товара
            product_data["category_id"] = category_id

            logger.info(
                f"Товар: {product_data.get('product', {}).get('sku', 'unknown')}"
            )
            logger.info(f"Путь категорий: {' > '.join(breadcrumbs_pl)}")
            logger.info(f"Назначен category_id: {category_id}")

            all_products.append(product_data)

        except Exception as e:
            logger.error(f"Ошибка обработки файла {html_file.name}: {e}")
            continue

    if not all_products:
        logger.error("Не удалось обработать ни одного товара")
        return False

    # Формируем финальную YML структуру со всеми товарами
    yml_structure = {
        "shop_info": {
            "name": "Klarstein Ukraine",
            "company": "Klarstein UA",
            "url": "https://klarstein.ua",
        },
        "categories": categories_manager.get_all_categories(),  # Все уникальные категории
        "offers": [],
    }

    # Генерируем offers для всех товаров
    for product_data in all_products:
        offer = generate_offer_with_category_id(product_data)
        yml_structure["offers"].append(offer)

    # Сохраняем результат
    with open("result_all_products.json", "w", encoding="utf-8") as f:
        json.dump(yml_structure, f, ensure_ascii=False, indent=4)

    logger.info("=== ФИНАЛЬНАЯ СТАТИСТИКА ===")
    logger.info(f"Обработано товаров: {len(all_products)}")
    logger.info(f"Уникальных категорий: {len(yml_structure['categories'])}")

    # Показываем финальную структуру категорий
    logger.info("=== ФИНАЛЬНЫЕ КАТЕГОРИИ ===")
    for cat in yml_structure["categories"]:
        parent_info = (
            f" (родитель: {cat['parentId']})" if "parentId" in cat else " (корневая)"
        )

    with open("result_all_products.json", "r", encoding="utf-8") as f:
        yml_structure = json.load(f)
    # Загружаем в БД
    success = loader.load_data_to_db(yml_structure)



def generate_offer_with_category_id(raw_data):
    """
    ИСПРАВЛЕННАЯ версия - использует правильный category_id из данных
    """
    product = raw_data.get("product", {})
    description_pl = raw_data.get("description_pl", [])
    images = product.get("images", [])

    # Извлекаем размеры и вес
    dimensions = extract_dimensions_and_weight(description_pl)

    # Безопасное получение ширины
    try:
        weight = float(dimensions.get("weight") or 0)
        if weight <= 0:  # Если ширина 0 или отрицательная
            weight = config.client.shipping.default_weight_kg
    except (ValueError, TypeError):
        weight = config.client.shipping.default_weight_kg

    # Безопасное получение цены
    try:
        price = float(product.get("price", "0"))
    except (ValueError, TypeError):
        price = 0.0

    prise_result = calculate_prices(price, weight)

    category_id = raw_data.get("category_id", 1)

    # Определяем категории для ключевых слов
    categories = raw_data.get("breadcrumbs_pl", [])
    keywords_pl = ", ".join(categories)

    # Формируем готовое HTML описание из польских данных
    description, description_ua, description_pl = generate_complete_description_html(
        description_pl, images
    )

    name_pl = product.get("name_pl", "")
    name_russian, name_ukrainian = translate_text(name_pl)
    keywords, keywords_ua = translate_text(keywords_pl)

    # Основная структура offer
    offer = {
        # Обязательные атрибуты
        "id": product.get("sku", ""),
        "available": "true",
        "selling_type": "u",
        # Обязательные элементы
        "price": prise_result["price_retail"],
        "price_opt1": prise_result["price_opt1"],
        "price_opt2": prise_result["price_opt2"],
        "quantity1": prise_result["quantity1"],
        "quantity2": prise_result["quantity2"],
        "discount": 0,
        "currencyId": "UAH",
        "categoryId": str(category_id),  # ИСПРАВЛЕНО: используем правильный ID
        # Название товара
        "name": name_russian,
        "name_pl": name_pl,
        "name_ua": name_ukrainian,
        # Дополнительные поля
        "vendor": "Klarstein",
        "vendorCode": generate_10_digit_number(),
        "country_of_origin": "Германия",
        "keywords_pl": keywords_pl,
        "keywords": keywords,
        "keywords_ua": keywords_ua,
        "model": "",
        # Изображения
        "pictures": product.get("images", []),
        # Готовые HTML описания для всех языков
        "description": description,
        "description_pl": description_pl,
        "description_ua": description_ua,
        # Размеры и вес
        "dimensions": dimensions,
    }

    return offer


def scrap_json_product(json_data_product, json_data_breadcrumb):
    """Извлекаем базовые данные продукта"""
    product_data = {}

    # Получение данных из json_data_product
    name = json_data_product.get("name")
    sku = json_data_product.get("sku")
    price = json_data_product.get("offers", {}).get("price")
    images = json_data_product.get("image", [])

    # Проверка на наличие ключевых данных и добавление в словарь
    if name and sku:
        product_data["product"] = {
            "name_pl": name,
            "sku": f"Kla{sku}",
            "price": price,
            "images": images,
        }

    # Обработка breadcrumbs для категорий
    itemListElement = json_data_breadcrumb.get("itemListElement", [])
    all_items = []
    for item in itemListElement[:-1]:  # Исключаем последний элемент (сам товар)
        if isinstance(item, dict):
            all_items.append(item.get("name"))
    product_data["breadcrumbs_pl"] = all_items

    return product_data


def scrap_html_product(soup):
    """Извлекаем данные описания из HTML"""
    product_data = {}

    # Поиск всех элементов accordion__item
    accordion_items = soup.find_all("div", attrs={"class": "accordion__item"})
    accordion_data = []

    # Обработка всех элементов, кроме последних двух
    for item in accordion_items[:-1]:
        # Извлечение заголовка
        title_div = item.find("div", attrs={"class": "accordion__title"})
        title = (
            title_div.find("h2").get_text(strip=True)
            if title_div and title_div.find("h2")
            else ""
        )

        # Извлечение содержимого
        content_div = item.find("div", attrs={"class": "accordion__content"})
        if content_div:
            content = content_div.decode_contents()
        else:
            content = ""

        # Добавление в список, если есть заголовок
        if title:
            accordion_data.append({"title_pl": title, "description_pl": content})

    product_data["description_pl"] = accordion_data
    return product_data


def generate_10_digit_number():
    return random.randint(1000000000, 9999999999)


def generate_complete_description_html(descriptions, images):
    """
    Генерирует полное HTML описание с изображениями
    Точно как в оригинальном коде
    """
    description_text = ""
    description_text_ua = ""
    description_text_pl = ""
    for i, accordion in enumerate(descriptions):
        # Добавляем заголовок и содержимое
        title_pl = accordion.get("title_pl", "")
        content_pl = accordion.get("description_pl", "")

        title, title_ua = translate_text(title_pl)
        content, content_ua = translate_text(content_pl)

        description_text_pl += f"<h2>{title_pl}</h2>\n{content_pl}\n"
        description_text += f"<h2>{title}</h2>\n{content}\n"
        description_text_ua += f"<h2>{title_ua}</h2>\n{content_ua}\n"

        # После каждого блока, кроме последнего, добавляем фото
        if i < len(images) and i < len(descriptions) - 1:
            description_text += f'<p><img src="{images[i]}" alt="Product image"></p>\n'
        # После каждого блока, кроме последнего, добавляем фото
        if i < len(images) and i < len(descriptions) - 1:
            description_text_ua += (
                f'<p><img src="{images[i]}" alt="Product image"></p>\n'
            )
        if i < len(images) and i < len(descriptions) - 1:
            description_text_pl += (
                f'<p><img src="{images[i]}" alt="Product image"></p>\n'
            )

    return description_text, description_text_ua, description_text_pl


def calculate_prices(
    supplier_price: float,
    weight: float,
) -> Dict[str, Any]:
    """
    Рассчитывает цены с наценками на основе правил ценообразования

    Args:
        supplier_price: Цена поставщика (в EUR/PLN)
        currency_rate: Курс валюты к UAH
        weight: Вес товара в кг
        shipping_cost_per_kg: Стоимость доставки за кг в UAH
        markup_rules: Правила наценки
        rounding_precision: Точность округления

    Returns:
        Словарь с рассчитанными ценами и правилом
    """
    # Правила расчета наценки markup_rules берется из config.json
    markup_rules = config.client.price_rules.markup_rules
    # ОТЛАДКА: проверяем что загрузилось
    # logger.info(f"DEBUG: markup_rules type: {type(markup_rules)}")
    # logger.info(f"DEBUG: markup_rules length: {len(markup_rules) if markup_rules else 'None'}")
    # if markup_rules:
    #     logger.info(f"DEBUG: first rule: {markup_rules[0]}")
    #     logger.info(f"DEBUG: last rule: {markup_rules[-1]}")

    # Округление rounding_precision берется из config.json
    rounding_precision = config.client.price_rules.rounding_precision

    # Курс Злотых pln_to_uah
    pln_to_uah = config.client.exchange_rates.pln_to_uah

    # Цена доставки берется cost_per_kg_uah с config.json
    cost_per_kg_uah = config.client.shipping.cost_per_kg_uah

    # Цена поставщика supplier_price * Курс Злотых pln_to_uah
    base_price_uah = supplier_price * pln_to_uah

    # Вес товара  weight от поставщика  * Стоимость доставка cost_per_kg_uah
    shipping_cost = weight * cost_per_kg_uah

    # Ищем подходящие правило для цены в гривнах base_price_uah
    markup_rule = find_markup_rule(base_price_uah, markup_rules)

    # Коеэфициенты для разных цен
    retail = markup_rule["retail"]
    opt1 = markup_rule["opt1"]
    opt2 = markup_rule["opt2"]

    retail_price = round((base_price_uah * retail) + shipping_cost, rounding_precision)
    opt1_price = round((base_price_uah * opt1) + shipping_cost, rounding_precision)
    opt2_price = round((base_price_uah * opt2) + shipping_cost, rounding_precision)

    # logger.info(f"Стоимость доставки за 1кг {cost_per_kg_uah}")
    # logger.info(f"Курс Злотых {pln_to_uah}")
    # logger.info(f"Цена поставщика {supplier_price}")
    # logger.info(f"Цена в гривнах {base_price_uah}")
    # logger.info(f"Цена retail_price {retail_price}")
    # logger.info(f"Цена opt1_price {opt1_price}")
    # logger.info(f"Цена opt2_price {opt2_price}")

    all_data = {
        # Рассчитанные цены
        "price_retail": retail_price,
        "price_opt1": opt1_price,
        "price_opt2": opt2_price,
        # Количества для оптовых цен
        "quantity1": markup_rule["quantity1"],
        "quantity2": markup_rule["quantity2"],
    }
    # logger.info(all_data)
    return all_data


def find_markup_rule(
    price: float, markup_rules: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Находит подходящее правило наценки для указанной цены

    Args:
        price: Цена для поиска правила
        markup_rules: Список правил наценки

    Returns:
        Подходящее правило или None
    """
    logger.info(f"Поиск правила для цены: {price}")
    
    # Сортируем правила по min для безопасности
    sorted_rules = sorted(markup_rules, key=lambda x: x["min"])
    
    # Проходим по всем правилам
    for i, rule in enumerate(sorted_rules):
        # logger.info(f"Проверяем правило {i+1}: {rule['min']} <= {price} < {rule['max']}")
        
        # Для последнего правила используем >= вместо <
        if i == len(sorted_rules) - 1:
            if price >= rule["min"]:
                logger.info(f"Выбрано последнее правило: {rule}")
                return rule
        else:
            # Для остальных правил используем строгое сравнение
            if rule["min"] <= price < rule["max"]:
                logger.info(f"Выбрано правило {i+1}: {rule}")
                return rule
    
    # Если цена меньше минимального диапазона, берем первое правило
    if price < sorted_rules[0]["min"]:
        logger.warning(f"Цена {price} меньше минимального диапазона, используем первое правило")
        return sorted_rules[0]
    
    # Если ничего не найдено, берем последнее правило как fallback
    logger.warning(f"Не найдено правило для цены {price}, используем последнее правило")
    return sorted_rules[-1]



#     return dimensions
def extract_dimensions_and_weight(descriptions):
    """
    Извлекает размеры и вес из технических характеристик
    Ищет во всех блоках описания, чтобы найти все 4 параметра
    """
    dimensions = {"width": None, "height": None, "length": None, "weight": None}

    # Объединяем все описания в один текст для поиска
    all_text = ""
    for desc in descriptions:
        title = desc.get("title_pl", "")
        description = desc.get("description_pl", "")
        all_text += f" {title} {description}"

    # Различные паттерны для поиска размеров
    dimension_patterns = [
        # Стандартный формат: wymiary: ok. X x Y x Z cm
        r"wymiary:\s*ok\.\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm",
        # Формат: wymiary: X x Y x Z cm
        r"wymiary:\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm",
        # Формат с указанием координат: (szer. x wys. x gł.)
        r"(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm\s*\([^)]*szer[^)]*wys[^)]*gł[^)]*\)",
        # Формат с указанием координат: (wys. x szer. x gł.)
        r"(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm\s*\([^)]*wys[^)]*szer[^)]*gł[^)]*\)",
        # Формат с указанием координат: (dł. x szer. x wys.)
        r"(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm\s*\([^)]*dł[^)]*szer[^)]*wys[^)]*\)",
    ]

    # Поиск размеров по всем паттернам
    for pattern in dimension_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            dim1, dim2, dim3 = match.groups()

            # Определяем порядок размеров по контексту
            context = match.group(0).lower()

            if "szer" in context and "wys" in context and "gł" in context:
                # Формат (szer. x wys. x gł.) - ширина x высота x глубина
                if context.find("szer") < context.find("wys") < context.find("gł"):
                    dimensions["width"] = dim1.replace(",", ".")
                    dimensions["height"] = dim2.replace(",", ".")
                    dimensions["length"] = dim3.replace(",", ".")
                # Формат (wys. x szer. x gł.) - высота x ширина x глубина
                elif context.find("wys") < context.find("szer") < context.find("gł"):
                    dimensions["height"] = dim1.replace(",", ".")
                    dimensions["width"] = dim2.replace(",", ".")
                    dimensions["length"] = dim3.replace(",", ".")
            elif "dł" in context and "szer" in context:
                # Формат (dł. x szer. x wys.) - длина x ширина x высота
                if context.find("dł") < context.find("szer") < context.find("wys"):
                    dimensions["length"] = dim1.replace(",", ".")
                    dimensions["width"] = dim2.replace(",", ".")
                    dimensions["height"] = dim3.replace(",", ".")
            else:
                # Стандартный порядок без явного указания - предполагаем ширина x высота x длина
                dimensions["width"] = dim1.replace(",", ".")
                dimensions["height"] = dim2.replace(",", ".")
                dimensions["length"] = dim3.replace(",", ".")
            break

    # Дополнительные паттерны для отдельных размеров
    if not all([dimensions["width"], dimensions["height"], dimensions["length"]]):
        # Поиск отдельных размеров
        separate_patterns = {
            "width": [
                r"szerokość:\s*(\d+(?:,\d+)?)\s*cm",
                r"szer\.?\s*(\d+(?:,\d+)?)\s*cm",
            ],
            "height": [
                r"wysokość:\s*(\d+(?:,\d+)?)\s*cm",
                r"wys\.?\s*(\d+(?:,\d+)?)\s*cm",
            ],
            "length": [
                r"długość:\s*(\d+(?:,\d+)?)\s*cm",
                r"głębokość:\s*(\d+(?:,\d+)?)\s*cm",
                r"dł\.?\s*(\d+(?:,\d+)?)\s*cm",
                r"gł\.?\s*(\d+(?:,\d+)?)\s*cm",
            ],
        }

        for dim_type, patterns in separate_patterns.items():
            if not dimensions[dim_type]:
                for pattern in patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        dimensions[dim_type] = match.group(1).replace(",", ".")
                        break

    # Поиск веса
    weight_patterns = [
        r"waga:\s*ok\.\s*([\d,]+)\s*kg",
        r"waga:\s*([\d,]+)\s*kg",
        r"masa:\s*([\d,]+)\s*kg",
        r"ciężar:\s*([\d,]+)\s*kg",
    ]

    for pattern in weight_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            dimensions["weight"] = match.group(1).replace(",", ".")
            break

    # Поиск размеров внутренних/внешних (для раковин, холодильников и т.д.)
    if not all([dimensions["width"], dimensions["height"], dimensions["length"]]):
        internal_external_patterns = [
            r"wymiary\s+wewnętrzne:\s*ok\.\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)",
            r"wymiary\s+zewnętrzne:\s*ok\.\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)",
        ]

        for pattern in internal_external_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match and not dimensions["width"]:
                dimensions["width"] = match.group(1).replace(",", ".")
                dimensions["length"] = match.group(2).replace(",", ".")
                break

    # Если нашли только 2 размера, попробуем найти третий
    if (
        sum(
            1
            for v in [dimensions["width"], dimensions["height"], dimensions["length"]]
            if v
        )
        == 2
    ):
        missing_dim_patterns = [
            r"grubość:\s*(\d+(?:,\d+)?)\s*(?:mm|cm)",
            r"wysokość:\s*(\d+(?:,\d+)?)\s*cm",
        ]

        for pattern in missing_dim_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", ".")
                # Если это толщина в мм, конвертируем в см
                if "mm" in match.group(0).lower():
                    value = str(float(value) / 10)

                # Присваиваем недостающему размеру
                if not dimensions["height"]:
                    dimensions["height"] = value
                elif not dimensions["length"]:
                    dimensions["length"] = value
                elif not dimensions["width"]:
                    dimensions["width"] = value
                break

    return dimensions


def add_translations(yml_data, translations):
    """
    Добавляет переводы в структуру YML
    """
    # Добавляем переводы категорий
    if "categories" in translations:
        for i, cat_translation in enumerate(translations["categories"]):
            if i < len(yml_data["categories"]):
                # Обновляем русский и украинский переводы
                if "name" in cat_translation:
                    yml_data["categories"][i]["name"] = cat_translation["name"]
                if "name_ua" in cat_translation:
                    yml_data["categories"][i]["name_ua"] = cat_translation["name_ua"]

    # Добавляем переводы товаров
    if "offers" in translations:
        for i, offer_translation in enumerate(translations["offers"]):
            if i < len(yml_data["offers"]):
                # Обновляем названия
                if "name" in offer_translation:
                    yml_data["offers"][i]["name"] = offer_translation["name"]
                if "name_ua" in offer_translation:
                    yml_data["offers"][i]["name_ua"] = offer_translation["name_ua"]

                # Обновляем описания
                if "description" in offer_translation:
                    yml_data["offers"][i]["description"] = offer_translation[
                        "description"
                    ]
                if "description_ua" in offer_translation:
                    yml_data["offers"][i]["description_ua"] = offer_translation[
                        "description_ua"
                    ]

    return yml_data
