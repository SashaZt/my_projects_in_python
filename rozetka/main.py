import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

import pandas as pd


# Функция для создания узла с CDATA содержимым
def create_cdata_element(parent, tag, text):
    element = ET.SubElement(parent, tag)
    element.text = f"<![CDATA[{text}]]>"
    return element


# Загрузка настроек магазина из конфигурационного файла
def load_shop_config(config_file="shop_config.json"):
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Значения по умолчанию
        return {
            "name": "Название магазина",
            "company": "Название компании",
            "url": "https://www.example.com/",
            "currencies": {"UAH": "1", "USD": "36.6", "EUR": "37.9"},
            "categories": [{"id": "1", "name": "Название категории"}],
        }


# Загрузка данных из CSV с указанием разделителя ";"
try:
    df = pd.read_csv("products.csv", sep=";")
    print(f"CSV успешно загружен, найдено {len(df)} товаров")
except Exception as e:
    print(f"Ошибка при загрузке CSV: {e}")
    # Попробуем с другим разделителем, если первый не сработал
    try:
        df = pd.read_csv("products.csv", sep=",")
        print(f"CSV успешно загружен с разделителем ',', найдено {len(df)} товаров")
    except Exception as e2:
        print(f"Ошибка при загрузке CSV с другим разделителем: {e2}")
        exit(1)

# Загрузка настроек магазина
shop_config = load_shop_config()

# Создание корневого элемента XML
root = ET.Element("yml_catalog")
root.set("date", datetime.now().strftime("%Y-%m-%d %H:%M"))

# Создание элемента shop и добавление информации из конфига
shop = ET.SubElement(root, "shop")
ET.SubElement(shop, "name").text = shop_config.get("name")
ET.SubElement(shop, "company").text = shop_config.get("company")
ET.SubElement(shop, "url").text = shop_config.get("url")

# Добавление валют из конфига
currencies = ET.SubElement(shop, "currencies")
for currency_id, rate in shop_config.get("currencies", {}).items():
    currency = ET.SubElement(currencies, "currency")
    currency.set("id", currency_id)
    currency.set("rate", rate)

# Загружаем категории из CSV файла, если они есть
categories_file = "categories.csv"
if os.path.exists(categories_file):
    try:
        categories_df = pd.read_csv(categories_file, sep=";")
        print(f"Загружено {len(categories_df)} категорий из CSV")
    except:
        categories_df = pd.read_csv(categories_file, sep=",")
        print(f"Загружено {len(categories_df)} категорий из CSV с разделителем ','")

    # Добавление категорий из CSV
    categories = ET.SubElement(shop, "categories")
    for _, row in categories_df.iterrows():
        category = ET.SubElement(categories, "category")
        category.set("id", str(row["id"]))
        if "rz_id" in row and not pd.isna(row["rz_id"]):
            category.set("rz_id", str(row["rz_id"]))
        category.text = row["name"]
else:
    # Добавление категорий из конфига, если CSV файл не найден
    categories = ET.SubElement(shop, "categories")
    for cat in shop_config.get("categories", []):
        category = ET.SubElement(categories, "category")
        category.set("id", str(cat.get("id")))
        if "rz_id" in cat:
            category.set("rz_id", str(cat.get("rz_id")))
        category.text = cat.get("name")

# Добавление товаров
offers = ET.SubElement(shop, "offers")

# Создание товаров из DataFrame
for _, row in df.iterrows():
    offer = ET.SubElement(offers, "offer")
    offer.set("id", str(row["id"]))
    offer.set("available", str(row["available"]).lower())

    # Добавляем основные элементы
    ET.SubElement(offer, "price").text = str(row["price"])

    if "price_old" in row and not pd.isna(row["price_old"]):
        ET.SubElement(offer, "price_old").text = str(row["price_old"])
    elif "oldprice" in row and not pd.isna(row["oldprice"]):
        ET.SubElement(offer, "price_old").text = str(row["oldprice"])

    if "price_promo" in row and not pd.isna(row["price_promo"]):
        ET.SubElement(offer, "price_promo").text = str(row["price_promo"])

    # Обрабатываем количество товара
    stock_field = None
    if "stock_quantity" in row and not pd.isna(row["stock_quantity"]):
        stock_field = "stock_quantity"
    elif "quantity_in_stock" in row and not pd.isna(row["quantity_in_stock"]):
        stock_field = "quantity_in_stock"

    if stock_field:
        ET.SubElement(offer, "stock_quantity").text = str(row[stock_field])

    # Добавляем обязательные поля
    if "currencyId" in row and not pd.isna(row["currencyId"]):
        ET.SubElement(offer, "currencyId").text = str(row["currencyId"])

    if "categoryId" in row and not pd.isna(row["categoryId"]):
        ET.SubElement(offer, "categoryId").text = str(row["categoryId"])

    # Добавляем изображения
    for i in range(1, 16):  # максимум 15 изображений
        pic_col = f"picture{i}"
        if pic_col in row and not pd.isna(row[pic_col]):
            ET.SubElement(offer, "picture").text = str(row[pic_col]).strip()

    # Добавляем название, артикул и производителя
    if "name" in row and not pd.isna(row["name"]):
        ET.SubElement(offer, "name").text = str(row["name"])

    if "name_ua" in row and not pd.isna(row["name_ua"]):
        ET.SubElement(offer, "name_ua").text = str(row["name_ua"])

    if "article" in row and not pd.isna(row["article"]):
        ET.SubElement(offer, "article").text = str(row["article"])

    if "vendorCode" in row and not pd.isna(row["vendorCode"]):
        ET.SubElement(offer, "vendorCode").text = str(row["vendorCode"])

    if "vendor" in row and not pd.isna(row["vendor"]):
        ET.SubElement(offer, "vendor").text = str(row["vendor"])

    # Добавляем описания с CDATA
    if "description" in row and not pd.isna(row["description"]):
        create_cdata_element(offer, "description", str(row["description"]))

    if "description_ua" in row and not pd.isna(row["description_ua"]):
        create_cdata_element(offer, "description_ua", str(row["description_ua"]))

    # Добавляем URL и баркод если есть
    if "url" in row and not pd.isna(row["url"]):
        ET.SubElement(offer, "url").text = str(row["url"])

    if "barcode" in row and not pd.isna(row["barcode"]):
        ET.SubElement(offer, "barcode").text = str(
            int(row["barcode"]) if not pd.isna(row["barcode"]) else ""
        )

    # Добавляем параметры товара
    param_index = 1
    while True:
        name_col = f"param_name{param_index}"
        value_col = f"param_value{param_index}"

        if name_col not in row or pd.isna(row[name_col]):
            break

        param = ET.SubElement(offer, "param")
        param.set("name", str(row[name_col]))

        # Добавляем paramid и valueid, если есть
        paramid_col = f"param_paramid{param_index}"
        if paramid_col in row and not pd.isna(row[paramid_col]):
            param.set("paramid", str(row[paramid_col]))

        valueid_col = f"param_valueid{param_index}"
        if valueid_col in row and not pd.isna(row[valueid_col]):
            param.set("valueid", str(row[valueid_col]))

        # Проверяем, нужно ли обернуть значение в CDATA
        param_value = str(row[value_col]) if not pd.isna(row[value_col]) else ""
        if "<br>" in param_value or "<" in param_value:
            create_cdata_element(param, "", param_value)
        else:
            param.text = param_value

        param_index += 1

# Преобразуем XML в строку с красивым форматированием
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
with open("rozetka_export.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print("XML файл для Rozetka успешно создан!")
