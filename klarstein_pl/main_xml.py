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

    name.text = data["product"]["name_pl"]

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
    model.text = data["product"]["name_pl"]

    # Категория
    categoryId = ET.SubElement(offer, "categoryId")
    categoryId.text = "1"  # ID категории

    # Изображения
    for img_url in data["product"]["images"]:
        picture = ET.SubElement(offer, "picture")
        picture.text = img_url

    # Описание: включаем все аккордеоны и вставляем изображения между ними
    description_text = ""
    for i, accordion in enumerate(data["description_pl"]):
        # Добавляем заголовок и содержимое
        description_text += (
            f"<h2>{accordion['title_pl']}</h2>\n{accordion['description_pl']}\n"
        )

        # После каждого блока, кроме последнего, добавляем фото
        if i < len(data["product"]["images"]) and i < len(data["description_pl"]) - 1:
            description_text += f'<p><img src="{data["product"]["images"][i]}" alt="Product image"></p>\n'

    description = ET.SubElement(offer, "description_pl")
    description.text = "DESCRIPTION_PLACEHOLDER"

    # Обработка размеров и веса из технического блока
    for accordion in data["description_pl"]:
        if accordion["title_pl"] == "Wymiary i szczegóły techniczne":
            tech_desc = accordion["description_pl"]

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
