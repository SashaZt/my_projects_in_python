import json
import random
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from main_db import loader
from translation import translate_text

from config import Config, logger, paths

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "easy.html"

file_name = "10035233"


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


# def scrap_html_file():
#     all_data = []
#     html_files = list(html_directory.glob("*.html"))
#     for html_file in html_files:
#         with open(f"{file_name}.html", "r", encoding="utf-8") as file:
#             content = file.read()
#         soup = BeautifulSoup(content, "lxml")
#         script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

#         # Проходим по всем тегам
#         breadcrumb_script = None
#         product_script = None
#         for script in script_tags:
#             try:
#                 # Парсим содержимое тега как JSON
#                 json_data = json.loads(script.string)

#                 # Проверяем @type
#                 if json_data.get("@type") == "BreadcrumbList" and not breadcrumb_script:
#                     breadcrumb_script = json_data
#                 elif json_data.get("@type") == "Product" and not product_script:
#                     product_script = json_data

#                 # Если оба найдены, можно прервать цикл
#                 if breadcrumb_script and product_script:
#                     break
#             except (json.JSONDecodeError, TypeError):
#                 # Пропускаем, если содержимое не является валидным JSON
#                 continue

#         # Получаем данные продукта
#         product_data = scrap_json_product(product_script, breadcrumb_script)
#         product_data_description = scrap_html_product(soup)

#         # Объединяем данные
#         product_data.update(product_data_description)
#         all_data.append(product_data)
#         # Преобразуем в структуру для YML
#         yml_structure = transform_to_yml_structure(product_data)

#     # Сохраняем в JSON с правильной структурой
#     with open("result.json", "w", encoding="utf-8") as f:
#         json.dump(yml_structure, f, ensure_ascii=False, indent=4)

#     success = loader.load_data_to_db(yml_structure)

#     if success:
#         logger.info(f"Товар {file_name} успешно загружен в БД")
#     else:
#         logger.error(f"Ошибка загрузки товара {file_name} в БД")


# #     return success
# def scrap_html_file():
#     """ИСПРАВЛЕННАЯ версия - обрабатывает множество HTML файлов"""
#     global categories_manager

#     all_products = []
#     html_files = list(html_directory.glob("*.html"))

#     logger.info(f"Найдено {len(html_files)} HTML файлов для обработки")

#     for html_file in html_files:
#         logger.info(f"Обрабатываем файл: {html_file.name}")

#         try:
#             with open(html_file, "r", encoding="utf-8") as file:
#                 content = file.read()

#             soup = BeautifulSoup(content, "lxml")
#             script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

#             # Проходим по всем тегам
#             breadcrumb_script = None
#             product_script = None
#             for script in script_tags:
#                 try:
#                     # Парсим содержимое тега как JSON
#                     json_data = json.loads(script.string)

#                     # Проверяем @type
#                     if (
#                         json_data.get("@type") == "BreadcrumbList"
#                         and not breadcrumb_script
#                     ):
#                         breadcrumb_script = json_data
#                     elif json_data.get("@type") == "Product" and not product_script:
#                         product_script = json_data

#                     # Если оба найдены, можно прервать цикл
#                     if breadcrumb_script and product_script:
#                         break
#                 except (json.JSONDecodeError, TypeError):
#                     # Пропускаем, если содержимое не является валидным JSON
#                     continue

#             if not product_script or not breadcrumb_script:
#                 logger.warning(
#                     f"Не найдены необходимые данные в файле {html_file.name}"
#                 )
#                 continue

#             # Получаем данные продукта
#             product_data = scrap_json_product(product_script, breadcrumb_script)
#             product_data_description = scrap_html_product(soup)

#             # Объединяем данные
#             product_data.update(product_data_description)

#             # ВАЖНО: Регистрируем категории из этого товара
#             breadcrumbs_pl = product_data.get("breadcrumbs_pl", [])
#             category_id = categories_manager.add_breadcrumbs(breadcrumbs_pl)

#             # Добавляем ID категории к данным товара
#             product_data["category_id"] = category_id
#             logger.info(product_data)
#             exit()
#             all_products.append(product_data)

#         except Exception as e:
#             logger.error(f"Ошибка обработки файла {html_file.name}: {e}")
#             continue

#     if not all_products:
#         logger.error("Не удалось обработать ни одного товара")
#         return False

#     # Формируем финальную YML структуру со всеми товарами
#     yml_structure = {
#         "shop_info": {
#             "name": "Klarstein Ukraine",
#             "company": "Klarstein UA",
#             "url": "https://klarstein.ua",
#         },
#         "categories": categories_manager.get_all_categories(),  # Все уникальные категории
#         "offers": [],
#     }

#     # Генерируем offers для всех товаров
#     for product_data in all_products:
#         offer = generate_offer_with_category_id(product_data)
#         yml_structure["offers"].append(offer)

#     # Сохраняем результат
#     with open("result_all_products.json", "w", encoding="utf-8") as f:
#         json.dump(yml_structure, f, ensure_ascii=False, indent=4)

# with open("result_all_products.json", "r", encoding="utf-8") as f:
#     yml_structure = json.load(f)
#     # Загружаем в БД
#     success = loader.load_data_to_db(yml_structure)

#     if success:
#         logger.info(
#             f"Успешно загружено {len(all_products)} товаров и {len(yml_structure['categories'])} уникальных категорий в БД"
#         )
#     else:
#         logger.error("Ошибка загрузки данных в БД")


#     # return success
def scrap_html_file():
    """ИСПРАВЛЕННАЯ версия - корректное управление категориями"""
    # global categories_manager

    # all_products = []
    # html_files = list(html_directory.glob("*.html"))

    # logger.info(f"Найдено {len(html_files)} HTML файлов для обработки")

    # # ЭТАП 1: Сначала собираем ВСЕ категории из всех файлов
    # logger.info("=== ЭТАП 1: Сбор всех категорий ===")

    # for html_file in html_files:
    #     logger.info(f"Сканируем категории в файле: {html_file.name}")

    #     try:
    #         with open(html_file, "r", encoding="utf-8") as file:
    #             content = file.read()

    #         soup = BeautifulSoup(content, "lxml")
    #         script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

    #         # Ищем breadcrumbs
    #         breadcrumb_script = None
    #         for script in script_tags:
    #             try:
    #                 json_data = json.loads(script.string)
    #                 if json_data.get("@type") == "BreadcrumbList":
    #                     breadcrumb_script = json_data
    #                     break
    #             except (json.JSONDecodeError, TypeError):
    #                 continue

    #         if breadcrumb_script:
    #             # Извлекаем breadcrumbs
    #             itemListElement = breadcrumb_script.get("itemListElement", [])
    #             breadcrumbs_pl = []
    #             for item in itemListElement[
    #                 :-1
    #             ]:  # Исключаем последний элемент (сам товар)
    #                 if isinstance(item, dict):
    #                     breadcrumbs_pl.append(item.get("name"))

    #             if breadcrumbs_pl:
    #                 # ВАЖНО: Регистрируем категории, но пока не обрабатываем товары
    #                 categories_manager.add_breadcrumbs(breadcrumbs_pl)
    #                 logger.info(
    #                     f"Зарегистрированы категории: {' > '.join(breadcrumbs_pl)}"
    #                 )

    #     except Exception as e:
    #         logger.error(f"Ошибка сканирования категорий в файле {html_file.name}: {e}")
    #         continue

    # # Выводим отладочную информацию о собранных категориях
    # categories_manager.print_debug_info()

    # # ЭТАП 2: Теперь обрабатываем товары с уже готовыми категориями
    # logger.info("=== ЭТАП 2: Обработка товаров ===")

    # for html_file in html_files:
    #     logger.info(f"Обрабатываем товар в файле: {html_file.name}")

    #     try:
    #         with open(html_file, "r", encoding="utf-8") as file:
    #             content = file.read()

    #         soup = BeautifulSoup(content, "lxml")
    #         script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

    #         # Ищем данные товара и breadcrumbs
    #         breadcrumb_script = None
    #         product_script = None
    #         for script in script_tags:
    #             try:
    #                 json_data = json.loads(script.string)
    #                 if (
    #                     json_data.get("@type") == "BreadcrumbList"
    #                     and not breadcrumb_script
    #                 ):
    #                     breadcrumb_script = json_data
    #                 elif json_data.get("@type") == "Product" and not product_script:
    #                     product_script = json_data

    #                 if breadcrumb_script and product_script:
    #                     break
    #             except (json.JSONDecodeError, TypeError):
    #                 continue

    #         if not product_script or not breadcrumb_script:
    #             logger.warning(
    #                 f"Не найдены необходимые данные в файле {html_file.name}"
    #             )
    #             continue

    #         # Получаем данные продукта
    #         product_data = scrap_json_product(product_script, breadcrumb_script)
    #         product_data_description = scrap_html_product(soup)

    #         # Объединяем данные
    #         product_data.update(product_data_description)

    #         # ВАЖНО: Определяем category_id по полному пути breadcrumbs
    #         breadcrumbs_pl = product_data.get("breadcrumbs_pl", [])
    #         if breadcrumbs_pl:
    #             category_id = categories_manager.get_category_id_by_path(breadcrumbs_pl)
    #         else:
    #             category_id = 1

    #         # Добавляем ID категории к данным товара
    #         product_data["category_id"] = category_id

    #         logger.info(
    #             f"Товар: {product_data.get('product', {}).get('sku', 'unknown')}"
    #         )
    #         logger.info(f"Путь категорий: {' > '.join(breadcrumbs_pl)}")
    #         logger.info(f"Назначен category_id: {category_id}")

    #         all_products.append(product_data)

    #     except Exception as e:
    #         logger.error(f"Ошибка обработки файла {html_file.name}: {e}")
    #         continue

    # if not all_products:
    #     logger.error("Не удалось обработать ни одного товара")
    #     return False

    # # Формируем финальную YML структуру со всеми товарами
    # yml_structure = {
    #     "shop_info": {
    #         "name": "Klarstein Ukraine",
    #         "company": "Klarstein UA",
    #         "url": "https://klarstein.ua",
    #     },
    #     "categories": categories_manager.get_all_categories(),  # Все уникальные категории
    #     "offers": [],
    # }

    # # Генерируем offers для всех товаров
    # for product_data in all_products:
    #     offer = generate_offer_with_category_id(product_data)
    #     yml_structure["offers"].append(offer)

    # # Сохраняем результат
    # with open("result_all_products.json", "w", encoding="utf-8") as f:
    #     json.dump(yml_structure, f, ensure_ascii=False, indent=4)

    # logger.info("=== ФИНАЛЬНАЯ СТАТИСТИКА ===")
    # logger.info(f"Обработано товаров: {len(all_products)}")
    # logger.info(f"Уникальных категорий: {len(yml_structure['categories'])}")

    # # Показываем финальную структуру категорий
    # logger.info("=== ФИНАЛЬНЫЕ КАТЕГОРИИ ===")
    # for cat in yml_structure["categories"]:
    #     parent_info = (
    #         f" (родитель: {cat['parentId']})" if "parentId" in cat else " (корневая)"
    #     )
    #     logger.info(f"ID {cat['id']}: {cat['name_pl']}{parent_info}")
    with open("result_all_products.json", "r", encoding="utf-8") as f:
        yml_structure = json.load(f)
    # Загружаем в БД
    success = loader.load_data_to_db(yml_structure)

    # if success:
    #     logger.info(
    #         f"Успешно загружено {len(all_products)} товаров и {len(yml_structure['categories'])} уникальных категорий в БД"
    #     )
    # else:
    #     logger.error("Ошибка загрузки данных в БД")

    # return success


# def generate_offer_with_category_id(raw_data):
#     """
#     ИСПРАВЛЕННАЯ версия - использует уже определенный category_id
#     """
#     product = raw_data.get("product", {})
#     description_pl = raw_data.get("description_pl", [])
#     images = product.get("images", [])

#     # Извлекаем размеры и вес
#     dimensions = extract_dimensions_and_weight(description_pl)

#     # Определяем категорию товара (последняя в breadcrumbs)
#     categories = raw_data.get("breadcrumbs_pl", [])

#     keywords_pl = ", ".join(categories)

#     category_id = len(categories) if categories else 1

#     # Формируем готовое HTML описание из польских данных
#     description, description_ua, description_pl = generate_complete_description_html(
#         description_pl, images
#     )

#     name_pl = product.get("name_pl", "")
#     name_russian, name_ukrainian = translate_text(name_pl)

#     keywords, keywords_ua = translate_text(keywords_pl)

#     # Основная структура offer
#     offer = {
#         # Обязательные атрибуты
#         "id": product.get("sku", ""),
#         "available": "true",
#         "selling_type": "u",
#         # Обязательные элементы
#         "price": product.get("price", "0"),
#         "price_opt1": "",
#         "price_opt2": "",
#         "quantity1": "",
#         "quantity2": "",
#         "discount": "",
#         "currencyId": "UAH",
#         "categoryId": str(category_id),
#         # Название товара
#         "name": name_russian,  # русский - пока копируем, потом переведем
#         "name_pl": name_pl,  # польский - исходный
#         "name_ua": name_ukrainian,  # украинский - заполнится после перевода
#         # Дополнительные поля
#         "vendor": "Klarstein",
#         "vendorCode": generate_10_digit_number(),
#         "country_of_origin": "Германия",
#         "keywords_pl": keywords_pl,
#         "keywords": keywords,
#         "keywords_ua": keywords_ua,
#         "model": "",
#         # Изображения
#         "pictures": product.get("images", []),
#         # Готовые HTML описания для всех языков
#         "description": description,  # русский - пока польский HTML, потом переведем
#         "description_pl": description_pl,  # польский - готовый HTML
#         "description_ua": description_ua,  # украинский - заполнится после перевода
#         # Размеры и вес
#         "dimensions": dimensions,
#     }

#     return offer


def generate_offer_with_category_id(raw_data):
    """
    ИСПРАВЛЕННАЯ версия - использует правильный category_id из данных
    """
    product = raw_data.get("product", {})
    description_pl = raw_data.get("description_pl", [])
    images = product.get("images", [])

    # Извлекаем размеры и вес
    dimensions = extract_dimensions_and_weight(description_pl)

    # ИСПРАВЛЕНО: Используем category_id, который уже определен правильно
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
        "price": product.get("price", "0"),
        "price_opt1": "",
        "price_opt2": "",
        "quantity1": "",
        "quantity2": "",
        "discount": "",
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


def extract_dimensions_and_weight(descriptions):
    """
    Извлекает размеры и вес из технических характеристик
    """
    dimensions = {}

    for desc in descriptions:
        if (
            "wymiary" in desc.get("title_pl", "").lower()
            or "techniczne" in desc.get("title_pl", "").lower()
        ):
            tech_desc = desc.get("description_pl", "")

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


if __name__ == "__main__":
    scrap_html_file()
