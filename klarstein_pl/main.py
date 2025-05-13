import json
from pathlib import Path

# import pandas as pd
# import requests
from bs4 import BeautifulSoup
from config.logger import logger

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
    # Ищем все теги <script> с атрибутом type="application/json"
    script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    # Фильтруем теги, где содержимое начинается с "__listing_StoreState"
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
    logger.info(json.dumps(product_data, indent=4, ensure_ascii=False))


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
            "name": name,
            "sku": sku,
            "price": price,
            "images": images,
        }

    # Обработка itemListElement
    itemListElement = json_data_breadcrumb.get("itemListElement", [])
    all_items = []
    for item in itemListElement[:-1]:  # Срез [:-1] сохранен, предполагая, что он нужен
        if isinstance(item, dict):
            all_items.append(item.get("name"))
    product_data["breadcrumbs"] = all_items
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
            accordion_data.append({"title": title, "description": content})

    # Добавление данных в словарь
    product_data["accordions"] = accordion_data

    # Логирование результата
    # logger.info(json.dumps(product_data, indent=4, ensure_ascii=False))
    return product_data


if __name__ == "__main__":
    scrap_html_file()
