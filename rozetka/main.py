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


# Загрузка данных из CSV
df = pd.read_csv("products.csv")

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

# Добавление категорий из конфига
categories = ET.SubElement(shop, "categories")
for cat in shop_config.get("categories", []):
    category = ET.SubElement(categories, "category")
    category.set("id", cat.get("id"))
    if "rz_id" in cat:
        category.set("rz_id", cat.get("rz_id"))
    category.text = cat.get("name")

# Добавление товаров
offers = ET.SubElement(shop, "offers")

# Остальной код без изменений...
# ...

# Сохраняем XML в файл
with open("rozetka_export.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print("XML файл для Rozetka успешно создан!")
