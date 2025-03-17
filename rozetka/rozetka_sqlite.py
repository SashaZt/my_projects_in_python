import json
import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

# Константы для файлов
INPUT_XML_FILE = "export_crm.xml"
CONFIG_FILE = "shop_config.json"
DB_FILE = "rozetka.db"
OUTPUT_XML_FILE = "rozetka_export.xml"


def extract_data_from_xml(xml_file=INPUT_XML_FILE):
    """
    Извлекает данные из XML файла Rozetka и возвращает структурированные данные

    Args:
        xml_file (str): Путь к XML файлу Rozetka

    Returns:
        dict: Словарь с данными из XML или None в случае ошибки
    """
    print(f"Извлечение данных из XML файла: {xml_file}")

    # Проверяем существование файла
    if not os.path.exists(xml_file):
        print(f"Ошибка: файл XML {xml_file} не найден")
        return None

    try:
        # Парсим XML файл
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Получаем элементы shop
        shop = root.find("shop")
        if shop is None:
            print("Ошибка: элемент 'shop' не найден в XML")
            return None

        # Извлекаем информацию о магазине
        shop_info = {
            "name": shop.find("name").text if shop.find("name") is not None else "",
            "company": (
                shop.find("company").text if shop.find("company") is not None else ""
            ),
            "url": shop.find("url").text if shop.find("url") is not None else "",
        }

        # Извлекаем валюты
        currencies = {}
        currencies_elem = shop.find("currencies")
        if currencies_elem is not None:
            for currency in currencies_elem.findall("currency"):
                currency_id = currency.get("id")
                currency_rate = currency.get("rate")
                currencies[currency_id] = currency_rate

        # Извлекаем категории
        categories = []
        categories_elem = shop.find("categories")
        if categories_elem is not None:
            for category in categories_elem.findall("category"):
                categories.append(
                    {
                        "id": category.get("id"),
                        "name": category.text if category.text else "",
                        "rz_id": category.get("rz_id"),
                    }
                )

        # Извлекаем товары
        products = []
        offers = shop.find("offers")
        if offers is not None:
            for offer in offers.findall("offer"):
                product = {
                    "id": offer.get("id"),
                    "available": offer.get("available", "true").lower(),
                    "images": [],
                    "params": [],
                }

                # Извлекаем основные данные товара
                for child in offer:
                    if child.tag == "picture":
                        product["images"].append(
                            child.text.strip() if child.text else ""
                        )
                    elif child.tag == "param":
                        # Обрабатываем параметры
                        param_name = child.get("name", "")
                        param_id = child.get("paramid")
                        value_id = child.get("valueid")

                        # Обрабатываем значение параметра, учитывая CDATA
                        param_value = child.text
                        if param_value and "<![CDATA[" in param_value:
                            cdata_match = re.search(
                                r"<!\[CDATA\[(.*?)\]\]>", param_value, re.DOTALL
                            )
                            param_value = (
                                cdata_match.group(1) if cdata_match else param_value
                            )

                        product["params"].append(
                            {
                                "name": param_name,
                                "value": param_value,
                                "paramid": param_id,
                                "valueid": value_id,
                            }
                        )
                    elif child.tag in ["description", "description_ua"]:
                        # Обрабатываем описания с CDATA
                        text = child.text
                        if text and "<![CDATA[" in text:
                            cdata_match = re.search(
                                r"<!\[CDATA\[(.*?)\]\]>", text, re.DOTALL
                            )
                            product[child.tag] = (
                                cdata_match.group(1) if cdata_match else text
                            )
                        else:
                            product[child.tag] = text
                    else:
                        # Остальные элементы (price, name, etc.)
                        product[child.tag] = child.text

                products.append(product)

        # Формируем и возвращаем результат
        return {
            "shop_info": shop_info,
            "currencies": currencies,
            "categories": categories,
            "products": products,
        }

    except Exception as e:
        print(f"Ошибка при обработке XML: {e}")
        return None


def import_to_sqlite(xml_data=None, config_file=CONFIG_FILE, db_file=DB_FILE):
    """
    Импортирует данные в SQLite базу данных

    Args:
        xml_data (dict): Данные из XML (если None, будут извлечены из файла)
        config_file (str): Путь к JSON-файлу с настройками магазина
        db_file (str): Путь для сохранения базы данных

    Returns:
        bool: True если успешно, иначе False
    """
    print(f"Импорт данных в базу данных: {db_file}")

    # Если данные не переданы, извлекаем их из XML
    if xml_data is None:
        xml_data = extract_data_from_xml()
        if xml_data is None:
            return False

    # Загружаем конфигурацию магазина
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            shop_config = json.load(f)
    else:
        print(f"Ошибка: файл конфигурации {config_file} не найден")
        return False

    # Удаляем файл базы данных, если он существует
    if os.path.exists(db_file):
        os.remove(db_file)

    # Создаем подключение к базе данных
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Создаем таблицы
    cursor.execute(
        """
    CREATE TABLE shop_info (
        name TEXT,
        company TEXT,
        url TEXT,
        vendor TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE currencies (
        id TEXT PRIMARY KEY,
        rate TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE categories (
        id TEXT PRIMARY KEY,
        name TEXT,
        rz_id TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE products (
        id TEXT PRIMARY KEY,
        available TEXT,
        price REAL,
        price_old REAL,
        price_promo REAL,
        stock_quantity INTEGER,
        currencyId TEXT,
        categoryId TEXT,
        vendorCode TEXT,
        article TEXT,
        vendor TEXT,
        barcode TEXT,
        name TEXT,
        name_ua TEXT,
        description TEXT,
        description_ua TEXT,
        url TEXT,
        FOREIGN KEY (categoryId) REFERENCES categories(id),
        FOREIGN KEY (currencyId) REFERENCES currencies(id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE product_images (
        product_id TEXT,
        image_url TEXT,
        position INTEGER,
        PRIMARY KEY (product_id, position),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE product_params (
        product_id TEXT,
        name TEXT,
        value TEXT,
        paramid TEXT,
        valueid TEXT,
        PRIMARY KEY (product_id, name),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """
    )

    # Добавляем информацию о магазине
    cursor.execute(
        "INSERT INTO shop_info (name, company, url, vendor) VALUES (?, ?, ?, ?)",
        (
            shop_config.get("name", ""),
            shop_config.get("company", ""),
            shop_config.get("url", ""),
            shop_config.get("vendor", ""),
        ),
    )

    # Добавляем валюты
    for currency_id, rate in shop_config.get("currencies", {}).items():
        cursor.execute(
            "INSERT INTO currencies (id, rate) VALUES (?, ?)", (currency_id, rate)
        )

    # Добавляем категории
    for category in shop_config.get("categories", []):
        cursor.execute(
            "INSERT INTO categories (id, name, rz_id) VALUES (?, ?, ?)",
            (
                category.get("id", ""),
                category.get("name", ""),
                category.get("rz_id", None),
            ),
        )

    # Получаем список доступных категорий
    cursor.execute("SELECT id FROM categories")
    available_category_ids = [row[0] for row in cursor.fetchall()]

    # Получаем глобальное значение vendor из shop_config
    default_vendor = shop_config.get("vendor", "")

    # Добавляем товары
    added_products = 0
    skipped_products = 0

    for product in xml_data["products"]:
        # Проверяем, есть ли товар в нужной категории
        category_id = product.get("categoryId")
        if category_id not in available_category_ids:
            skipped_products += 1
            continue

        # Используем vendor из товара, если есть, иначе из настроек магазина
        vendor = product.get("vendor", default_vendor)

        # Преобразуем некоторые поля
        price = float(product.get("price", 0))
        price_old = (
            float(product.get("price_old", 0)) if "price_old" in product else None
        )
        price_promo = (
            float(product.get("price_promo", 0)) if "price_promo" in product else None
        )

        stock_quantity = 0
        if "stock_quantity" in product:
            stock_quantity = int(float(product["stock_quantity"]))
        elif "quantity_in_stock" in product:
            stock_quantity = int(float(product["quantity_in_stock"]))

        # Вставляем основные данные товара
        cursor.execute(
            """
        INSERT INTO products (
            id, available, price, price_old, price_promo, stock_quantity,
            currencyId, categoryId, vendorCode, article, vendor, barcode,
            name, name_ua, description, description_ua, url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                product["id"],
                product["available"],
                price,
                price_old,
                price_promo,
                stock_quantity,
                product.get("currencyId", "UAH"),
                category_id,
                product.get("vendorCode"),
                product.get("article"),
                vendor,
                product.get("barcode"),
                product.get("name"),
                product.get("name_ua"),
                product.get("description"),
                product.get("description_ua"),
                product.get("url"),
            ),
        )

        # Добавляем изображения
        for position, image_url in enumerate(product["images"], 1):
            cursor.execute(
                """
            INSERT INTO product_images (product_id, image_url, position)
            VALUES (?, ?, ?)
            """,
                (product["id"], image_url, position),
            )

        # Добавляем параметры
        for param in product["params"]:
            cursor.execute(
                """
            INSERT INTO product_params (product_id, name, value, paramid, valueid)
            VALUES (?, ?, ?, ?, ?)
            """,
                (
                    product["id"],
                    param["name"],
                    param["value"],
                    param.get("paramid"),
                    param.get("valueid"),
                ),
            )

        added_products += 1

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

    print(
        f"База данных успешно создана. Добавлено {added_products} товаров, пропущено {skipped_products} товаров."
    )
    return True


def export_to_xml(db_file=DB_FILE, output_file=OUTPUT_XML_FILE):
    """
    Экспортирует данные из SQLite в XML формат Rozetka

    Args:
        db_file (str): Путь к базе данных SQLite
        output_file (str): Путь для сохранения XML файла

    Returns:
        bool: True если успешно, иначе False
    """
    print(f"Экспорт данных из {db_file} в {output_file}...")

    # Проверяем существование файла базы данных
    if not os.path.exists(db_file):
        print(f"Ошибка: файл базы данных {db_file} не найден")
        return False

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Чтобы получать результаты запросов в виде словарей
    cursor = conn.cursor()

    # Создаем корневой элемент XML
    root = ET.Element("yml_catalog")
    root.set("date", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Создаем элемент shop
    shop = ET.SubElement(root, "shop")

    # Добавляем информацию о магазине
    cursor.execute("SELECT * FROM shop_info LIMIT 1")
    shop_info = cursor.fetchone()
    if shop_info:
        ET.SubElement(shop, "name").text = shop_info["name"]
        ET.SubElement(shop, "company").text = shop_info["company"]
        if shop_info["url"]:
            ET.SubElement(shop, "url").text = shop_info["url"]

    # Добавляем валюты
    currencies = ET.SubElement(shop, "currencies")
    cursor.execute("SELECT * FROM currencies")
    for currency in cursor.fetchall():
        currency_elem = ET.SubElement(currencies, "currency")
        currency_elem.set("id", currency["id"])
        currency_elem.set("rate", currency["rate"])

    # Добавляем категории
    categories = ET.SubElement(shop, "categories")
    cursor.execute("SELECT * FROM categories")
    for category in cursor.fetchall():
        category_elem = ET.SubElement(categories, "category")
        category_elem.set("id", category["id"])
        if category["rz_id"]:
            category_elem.set("rz_id", category["rz_id"])
        category_elem.text = category["name"]

    # Добавляем товары
    offers = ET.SubElement(shop, "offers")
    cursor.execute("SELECT * FROM products")
    product_rows = cursor.fetchall()

    for product in product_rows:
        offer = ET.SubElement(offers, "offer")
        offer.set("id", product["id"])
        offer.set("available", product["available"])

        # Добавляем основные элементы
        ET.SubElement(offer, "price").text = str(product["price"])

        if product["price_old"]:
            ET.SubElement(offer, "price_old").text = str(product["price_old"])

        if product["price_promo"]:
            ET.SubElement(offer, "price_promo").text = str(product["price_promo"])

        ET.SubElement(offer, "stock_quantity").text = str(product["stock_quantity"])
        ET.SubElement(offer, "currencyId").text = product["currencyId"]
        ET.SubElement(offer, "categoryId").text = product["categoryId"]

        # Добавляем изображения
        cursor.execute(
            "SELECT * FROM product_images WHERE product_id = ? ORDER BY position",
            (product["id"],),
        )
        for image in cursor.fetchall():
            ET.SubElement(offer, "picture").text = image["image_url"]

        # Добавляем другие элементы
        if product["name"]:
            ET.SubElement(offer, "name").text = product["name"]

        if product["name_ua"]:
            ET.SubElement(offer, "name_ua").text = product["name_ua"]

        if product["article"]:
            ET.SubElement(offer, "article").text = product["article"]

        if product["vendorCode"]:
            ET.SubElement(offer, "vendorCode").text = product["vendorCode"]

        if product["vendor"]:
            ET.SubElement(offer, "vendor").text = product["vendor"]

        # Добавляем описания с CDATA
        if product["description"]:
            description = ET.SubElement(offer, "description")
            description.text = f"<![CDATA[{product['description']}]]>"

        if product["description_ua"]:
            description_ua = ET.SubElement(offer, "description_ua")
            description_ua.text = f"<![CDATA[{product['description_ua']}]]>"

        if product["url"]:
            ET.SubElement(offer, "url").text = product["url"]

        # Добавляем баркод, если есть
        if product["barcode"]:
            ET.SubElement(offer, "barcode").text = product["barcode"]

        # Добавляем параметры товара
        cursor.execute(
            "SELECT * FROM product_params WHERE product_id = ?", (product["id"],)
        )
        for param_row in cursor.fetchall():
            param = ET.SubElement(offer, "param")
            param.set("name", param_row["name"])

            if param_row["paramid"]:
                param.set("paramid", param_row["paramid"])

            if param_row["valueid"]:
                param.set("valueid", param_row["valueid"])

            # Проверяем, нужно ли обернуть значение в CDATA
            param_value = param_row["value"]
            if param_value and ("<br>" in param_value or "<" in param_value):
                param.text = f"<![CDATA[{param_value}]]>"
            else:
                param.text = param_value

    # Преобразуем XML в строку
    rough_string = ET.tostring(root, "utf-8")

    # Обрабатываем CDATA секции (ElementTree не поддерживает CDATA напрямую)
    rough_string = rough_string.decode("utf-8")
    rough_string = re.sub(
        r"&lt;!\[CDATA\[(.*?)\]\]&gt;", r"<![CDATA[\1]]>", rough_string, flags=re.DOTALL
    )

    # Создаем красиво отформатированный XML
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")

    # Удаляем лишние пустые строки
    pretty_xml = re.sub(r"\n\s*\n", "\n", pretty_xml)

    # Сохраняем XML в файл
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    # Закрываем соединение с базой данных
    conn.close()

    print(f"XML файл успешно создан: {output_file}")
    print(f"Добавлено {len(product_rows)} товаров")
    return True


def process_all():
    """
    Выполняет весь процесс: извлечение данных из XML,
    импорт в SQLite и экспорт в XML Rozetka
    """
    print("=== Шаг 1: Извлечение данных из XML ===")
    xml_data = extract_data_from_xml()
    if xml_data is None:
        print("Ошибка: не удалось извлечь данные из XML")
        return False

    print("\n=== Шаг 2: Импорт данных в SQLite ===")
    if not import_to_sqlite(xml_data):
        print("Ошибка: не удалось импортировать данные в SQLite")
        return False

    print("\n=== Шаг 3: Экспорт данных в XML ===")
    if not export_to_xml():
        print("Ошибка: не удалось экспортировать данные в XML")
        return False

    print("\nПроцесс успешно завершен!")
    return True


# Основной исполняемый код
if __name__ == "__main__":
    # Можно запустить отдельные функции или весь процесс

    # Опция 1: Выполнить весь процесс
    # process_all()

    # Опция 2: Выполнить отдельные шаги
    # xml_data = extract_data_from_xml()
    # import_to_sqlite()
    export_to_xml()
