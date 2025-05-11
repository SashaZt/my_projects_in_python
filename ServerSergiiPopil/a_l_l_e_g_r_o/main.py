import asyncio
import json
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config.logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "easy.html"


def scrap_html():

    with open("Delphi.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Ищем все теги <script> с атрибутом type="application/json"
    script_tags = soup.find_all("script", attrs={"type": "application/json"})

    # Фильтруем теги, где содержимое начинается с "__listing_StoreState"
    for script in script_tags:
        if script.string and script.string.strip().startswith('{"__listing_StoreState'):
            json_content = script.string.strip()

            json_data = json.loads(json_content)

            # Записываем JSON в файл
            with open("Delphi.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)


def scrap_json():
    def extract_number(text):
        if text is None:
            return 0
        number = ""
        for char in text:
            if char.isdigit():
                number += char
            elif number:
                break  # Прерываем, как только найдена первая последовательность цифр
        return int(number) if number else 0

    # Чтение JSON-файла
    with open("Delphi.json", "r", encoding="utf-8") as f:
        delphi_data = json.load(f)

    # Функция для преобразования товара
    def convert_product(delphi_product):
        product = {}

        # Извлечение указанных полей
        product["offerId"] = int(delphi_product.get("offerId", None))
        product["url"] = delphi_product.get("url", None)
        product["title"] = delphi_product.get("title", {}).get("text", None)
        price_value = (
            delphi_product.get("price", {}).get("mainPrice", {}).get("amount", None)
        )
        product["price"] = float(price_value) if price_value is not None else None

        delivery_price = (
            delphi_product.get("shipping", {}).get("lowest", {}).get("amount", None)
        )
        product["delivery_price"] = (
            float(delivery_price) if delivery_price is not None else None
        )

        price_with_delivery = (
            delphi_product.get("shipping", {})
            .get("itemWithDelivery", {})
            .get("amount", None)
        )
        product["price_with_delivery"] = (
            float(price_with_delivery) if price_with_delivery is not None else None
        )

        product["delivery_period"] = (
            delphi_product.get("shipping", {})
            .get("summary", {})
            .get("labels", [{}])[0]
            .get("text", None)
        )
        product["same_offers_id"] = delphi_product.get("eventData", {}).get(
            "product_id", None
        )
        product["same_offers_count"] = delphi_product.get("productOffersCount", 0)
        product["buyers"] = extract_number(
            delphi_product.get("productPopularity", {}).get("label", None)
        )
        rating = (
            delphi_product.get("productReview", {})
            .get("rating", {})
            .get("average", None)
        )
        product["rating"] = float(rating) if rating is not None else None
        product["reviews_count"] = (
            delphi_product.get("productReview", {}).get("rating", {}).get("count", 0)
        )

        # Преобразование parameters в specifications
        specifications = {"short_preview": True, "Parametry": {}}
        for param in delphi_product.get("parameters", []):
            param_name = param.get("name", "")
            param_values = param.get("values", [])
            if param_name and param_values:
                specifications["Parametry"][param_name] = param_values[0]
        product["specifications"] = specifications

        # Преобразование photos (берем small и заменяем s64 на original)
        product["images"] = [
            photo.get("small", "").replace("s64", "original")
            for photo in delphi_product.get("photos", [])
        ]

        return product

    # Извлечение товаров
    products = []
    elements = (
        delphi_data.get("__listing_StoreState", {}).get("items", {}).get("elements", [])
    )
    for element in elements:
        if element.get("type") == "product":
            product = convert_product(element)
            products.append(product)

    # Формирование итогового JSON
    output_data = {
        "success": True,
        "totalCount": len(products),
        "totalSameOffersCount": sum(p["same_offers_count"] for p in products),
        "lastAvailablePage": 1,
        "products": products,
    }

    # Сохранение результата
    with open("extracted_products_tz.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(
        f"Извлечено {len(products)} товаров. Результат сохранен в extracted_products_tz.json"
    )


def get_scrapi():

    # Твой API-ключ от ScraperAPI
    API_KEY = "6c54502fd688c7ce737f1c650444884a"

    # Настройка прокси с параметром ultra_premium=true
    proxies = {
        "http": f"http://scraperapi.ultra_premium=true:{API_KEY}@proxy-server.scraperapi.com:8001",
        "https": f"http://scraperapi.ultra_premium=true:{API_KEY}@proxy-server.scraperapi.com:8001",
    }
    # proxies = {
    #     "http": "http://5.79.73.131:13010",
    #     "https": "http://5.79.73.131:13010",
    # }

    # Целевой URL, который ты хочешь скрапить
    target_url = "https://allegro.pl/kategoria/hamulce-tarczowe-zestawy-tarcze-klocki-zaciski-250407?producent-czesci=Delphi&pasuje-do-marka=Honda&pasuje-do-model=ACCORD%20VII%20(CL%2C%20CN)%20(2003.01%20-%202012.09)"  # Замени на нужный URL
    count = 1
    while True:
        try:
            # Отправка GET-запроса через прокси ScraperAPI
            response = requests.get(
                target_url, proxies=proxies, verify=False, timeout=70
            )

            if response.status_code == 200:
                # Сохранение HTML-страницы целиком

                with open(output_html_file, "w", encoding="utf-8") as file:
                    file.write(response.text)
                logger.info(f"Сохранили файл {output_html_file} с попытки {count}")
                break
            else:
                logger.info(f"Попытка {count}")
                count += 1
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
