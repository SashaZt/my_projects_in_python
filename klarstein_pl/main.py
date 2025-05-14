import json
import xml.dom.minidom
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from config.logger import logger
from lxml import etree as ET

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "easy.html"


def scrap_html_file():

    with open("111.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    # Проходим по всем тегам
    breadcrumb_script = None
    product_script = None
    for script in script_tags:

        try:
            # Парсим содержимое тега как JSON
            json_data = json.loads(script.string)

            # Проверяем @type
            if json_data.get("@type") == "BreadcrumbList" and not breadcrumb_script:
                breadcrumb_script = json_data
            elif json_data.get("@type") == "Product" and not product_script:
                product_script = json_data

            # Если оба найдены, можно прервать цикл
            if breadcrumb_script and product_script:
                break
        except (json.JSONDecodeError, TypeError):
            # Пропускаем, если содержимое не является валидным JSON
            continue
    # logger.info(json.dumps(product_script, indent=4, ensure_ascii=False))
    product_data = scrap_json_product(product_script, breadcrumb_script)
    product_data_description = scrap_html_product(soup)
    product_data.update(product_data_description)
    # logger.info(json.dumps(product_data, indent=4, ensure_ascii=False))
    with open("file_name.json", "w", encoding="utf-8") as f:
        json.dump(product_data, f, ensure_ascii=False, indent=4)
    create_xml(product_data, "output.xml")


def scrap_json_product(json_data_product, json_data_breadcrumb):
    # Извлекаем нужные данные из JSON
    # Инициализация product_data как словаря
    product_data = {}

    # Получение данных из json_data_product
    name = json_data_product.get("name")
    sku = json_data_product.get("sku")
    price = json_data_product.get("offers", {}).get("price")
    images = json_data_product.get("image", [])

    # Проверка на наличие ключевых данных и добавление в словарь
    if name and sku:  # Проверка, чтобы не добавлять пустые данные
        product_data["product"] = {
            "name_pl": name,
            "sku": f"Kla1{sku}",
            "price": price,
            "images": images,
        }

    # Обработка itemListElement
    itemListElement = json_data_breadcrumb.get("itemListElement", [])
    all_items = []
    for item in itemListElement[:-1]:  # Срез [:-1] сохранен, предполагая, что он нужен
        if isinstance(item, dict):
            all_items.append(item.get("name"))
    product_data["breadcrumbs_pl"] = all_items
    # logger.info(json.dumps(product_data, indent=4, ensure_ascii=False))
    return product_data


def scrap_html_product(soup):
    # Инициализация словаря для результата
    product_data = {}

    # Поиск всех элементов accordion__item
    accordion_items = soup.find_all("div", class_="accordion__item")

    # Список для хранения данных об аккордеонах
    accordion_data = []

    # Обработка всех элементов, кроме последних двух
    for item in accordion_items[:-2]:
        # Извлечение заголовка
        title_div = item.find("div", class_="accordion__title")
        title = (
            title_div.find("h2").get_text(strip=True)
            if title_div and title_div.find("h2")
            else ""
        )

        # Извлечение содержимого
        content_div = item.find("div", class_="accordion__content")
        if content_div:
            # Извлекаем все дочерние элементы content_div и преобразуем в строку
            content = "".join(
                str(child).strip()
                for child in content_div.children
                if str(child).strip()
            )
        else:
            content = ""

        # Добавление в список, если есть заголовок
        if title:
            accordion_data.append({"title_pl": title, "description_pl": content})

    # Добавление данных в словарь
    product_data["description_pl"] = accordion_data

    # Логирование результата
    # logger.info(json.dumps(product_data, indent=4, ensure_ascii=False))
    return product_data


# Чтение JSON-файла
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def create_xml(data, output_file):
    # Создание корневого элемента
    root = ET.Element("yml_catalog")
    root.set("date", "2025-05-13 12:00")

    shop = ET.SubElement(root, "shop")

    # Обязательные элементы магазина
    name = ET.SubElement(shop, "name")
    name.text = "Klarstein"

    company = ET.SubElement(shop, "company")
    company.text = "Klarstein Shop"

    url = ET.SubElement(shop, "url")
    url.text = "https://klarstein.ua"

    currencies = ET.SubElement(shop, "currencies")
    currency = ET.SubElement(currencies, "currency", id="UAH", rate="1")

    # Блок товаров
    offers = ET.SubElement(shop, "offers")

    # Создание элемента товара
    offer = ET.SubElement(
        offers,
        "offer",
        id=data["product"]["sku"],
        available="true",
        selling_type="u",
    )

    # Название товара
    name = ET.SubElement(offer, "name")
    name.text = data["product"]["name"]

    # Цена
    price = ET.SubElement(offer, "price")
    price.text = data["product"]["price"]

    # Валюта
    currencyId = ET.SubElement(offer, "currencyId")
    currencyId.text = "UAH"

    # Производитель
    vendor = ET.SubElement(offer, "vendor")
    vendor.text = "Klarstein"

    # Страна производитель
    country_of_origin = ET.SubElement(offer, "country_of_origin")
    country_of_origin.text = "Германия"

    # Модель
    model = ET.SubElement(offer, "model")
    model.text = data["product"]["name"]

    # Категория
    categoryId = ET.SubElement(offer, "categoryId")
    categoryId.text = "1"  # ID категории

    # Изображения
    for img_url in data["product"]["images"]:
        picture = ET.SubElement(offer, "picture")
        picture.text = img_url

    # Описание: включаем все аккордеоны и вставляем изображения между ними
    description_text = ""
    for i, accordion in enumerate(data["description"]):
        # Добавляем заголовок и содержимое
        description_text += (
            f"<h2>{accordion['title']}</h2>\n{accordion['description']}\n"
        )

        # После каждого блока, кроме последнего, добавляем фото
        if i < len(data["product"]["images"]) and i < len(data["description"]) - 1:
            description_text += f'<p><img src="{data["product"]["images"][i]}" alt="Product image"></p>\n'

    description = ET.SubElement(offer, "description")
    description.text = "DESCRIPTION_PLACEHOLDER"

    # Обработка размеров и веса из технического блока
    for accordion in data["description"]:
        if accordion["title"] == "Wymiary i szczegóły techniczne":
            tech_desc = accordion["description"]

            # Извлечение габаритов и веса
            width = None
            height = None
            length = None
            weight = None

            # Поиск размеров
            import re

            # Ищем габариты (ширина x высота x глубина)
            # Пример: Wymiary: ok. 48 x 129 x 60 cm (SxWxG)
            dimensions_match = re.search(
                r"Wymiary: ok\. (\d+) x (\d+) x (\d+) cm", tech_desc
            )
            if dimensions_match:
                width = dimensions_match.group(1)  # ширина
                height = dimensions_match.group(2)  # высота
                length = dimensions_match.group(3)  # глубина/длина

            # Ищем вес
            # Пример: Waga: ok. 46 kg
            weight_match = re.search(r"Waga: ok\. (\d+) kg", tech_desc)
            if weight_match:
                weight = weight_match.group(1)

            # Добавляем блок с размерами если нашли хотя бы часть данных
            if any([width, height, length, weight]):
                dimensions = ET.SubElement(offer, "dimensions")

                if weight:
                    weight_elem = ET.SubElement(dimensions, "weight", unit="кг")
                    weight_elem.text = weight

                if width:
                    width_elem = ET.SubElement(dimensions, "width", unit="см")
                    width_elem.text = width

                if height:
                    height_elem = ET.SubElement(dimensions, "height", unit="см")
                    height_elem.text = height

                if length:
                    length_elem = ET.SubElement(dimensions, "length", unit="см")
                    length_elem.text = length

    # Создание XML строки
    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

    # Заменяем плейсхолдер на CDATA содержимое
    xml_str = xml_str.replace(
        "<description>DESCRIPTION_PLACEHOLDER</description>",
        f"<description><![CDATA[{description_text}]]></description>",
    )

    # Форматирование XML
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Добавление декларации XML
    pretty_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + pretty_xml[pretty_xml.find("<yml_catalog") :]
    )

    # Запись в файл
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(pretty_xml)

    return pretty_xml


if __name__ == "__main__":
    scrap_html_file()
