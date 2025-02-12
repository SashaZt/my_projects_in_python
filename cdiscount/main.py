import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"
img_directory = current_directory / "img"
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
img_directory.mkdir(parents=True, exist_ok=True)

output_json_file = data_directory / "output.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"


logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def scrap_html_page(html_file):
    with html_file.open(encoding="utf-8") as file:
        content = file.read()

    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(content, "lxml")
    scripts = soup.find_all("script", type="application/ld+json")
    combined_data = {"BreadcrumbList": [], "Product": []}
    # Extract only required fields from BreadcrumbList
    for script in scripts:
        json_content = json.loads(script.string)
        if json_content.get("@type") == "BreadcrumbList":
            logger.debug("Found BreadcrumbList: {}", json_content)
            filtered_breadcrumbs = []
            for item in json_content.get("itemListElement", []):
                filtered_breadcrumbs.append(
                    {
                        "position": item.get("position"),
                        "@id": item.get("item", {}).get("@id"),
                        "name": item.get("item", {}).get("name"),
                    }
                )
            combined_data["BreadcrumbList"].append(
                {"@type": "BreadcrumbList", "itemListElement": filtered_breadcrumbs}
            )
        elif json_content.get("@type") == "Product":
            filtered_product = {
                "brand": json_content.get("brand", {}).get("name"),
                "description": json_content.get("description"),
                "gtin": json_content.get("gtin"),
                "availability": json_content.get("offers", {}).get("availability"),
                "itemCondition": json_content.get("offers", {}).get("itemCondition"),
                "price": json_content.get("offers", {}).get("price"),
                "priceCurrency": json_content.get("offers", {}).get("priceCurrency"),
                "priceValidUntil": json_content.get("offers", {}).get(
                    "priceValidUntil"
                ),
                "url": json_content.get("offers", {}).get("url"),
                "productID": json_content.get("productID"),
                "color": json_content.get("color"),
                "category": json_content.get("category"),
                "sku": json_content.get("sku"),
                "name": json_content.get("name"),
                "image": json_content.get("image"),
            }
            combined_data["Product"].append(filtered_product)

    # Save combined data to JSON file
    with output_json_file.open("w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    html_file = (
        html_directory
        / "Poupon Poupée bébé 12 pouces intéractive silicone Doll nouveau-né enfant Mignonne Jouet playmate Cadeau-A1 - Cdiscount Jeux - Jouets.html"
    )
    scrap_html_page(html_file)
