import asyncio
import csv
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import openpyxl
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from PIL import Image

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
page_path = os.path.join(temp_path, "page")
html_path = os.path.join(temp_path, "html")
json_path = os.path.join(temp_path, "json")
img_path = os.path.join(temp_path, "img")


# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(page_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)
cookies = {
    "sbjs_migrations": "1418474375998%3D1",
    "sbjs_current_add": "fd%3D2025-01-26%2007%3A21%3A41%7C%7C%7Cep%3Dhttps%3A%2F%2Fkik-tuning.com.ua%2F%7C%7C%7Crf%3D%28none%29",
    "sbjs_first_add": "fd%3D2025-01-26%2007%3A21%3A41%7C%7C%7Cep%3Dhttps%3A%2F%2Fkik-tuning.com.ua%2F%7C%7C%7Crf%3D%28none%29",
    "sbjs_current": "typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29",
    "sbjs_first": "typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29",
    "sbjs_udata": "vst%3D3%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F131.0.0.0%20Safari%2F537.36",
    "woocommerce_recently_viewed": "2692",
    "sbjs_session": "pgs%3D3%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fkik-tuning.com.ua%2Fproduct%2Fkapot-bmw-5-f10-f11%2F",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://kik-tuning.com.ua/sitemap_index.xml",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def get_xml():

    # Ссылки на файлы Sitemap
    sitemaps = [
        "https://kik-tuning.com.ua/product-sitemap2.xml",
        "https://kik-tuning.com.ua/product-sitemap.xml",
    ]

    # Список для хранения URL
    product_urls = []

    for sitemap in sitemaps:
        # Скачиваем XML
        response = requests.get(sitemap, cookies=cookies, headers=headers, timeout=30)
        if response.status_code == 200:
            # Парсим XML
            root = ET.fromstring(response.content)
            # Извлекаем URL из тегов <loc>
            for url in root.findall(
                ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
            ):
                loc = url.text
                # Фильтруем только нужные ссылки
                if loc and "https://kik-tuning.com.ua/product/" in loc:
                    product_urls.append(loc)
        else:
            print(f"Не удалось загрузить {sitemap}. Код ответа: {response.status_code}")

    # Создаем DataFrame и сохраняем в CSV
    df = pd.DataFrame(product_urls, columns=["url"])
    df.to_csv("urls.csv", index=False, encoding="utf-8")

    print("Ссылки успешно сохранены в urls.csv")


def main():
    urls = []
    with open("urls.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for url in urls:
            filename_json = os.path.join(
                json_path, f"data_{hashlib.md5(url.encode()).hexdigest()}.json"
            )
            if not os.path.exists(filename_json):
                futures.append(executor.submit(parse_url, url, headers, filename_json))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def parse_url(url, headers, filename_json):
    src = fetch(url, headers)
    soup = BeautifulSoup(src, "lxml")
    json_data = parsing(soup)
    if json_data and not os.path.exists(filename_json):
        with open(filename_json, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
    return json_data


def fetch(url, headers):
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parsing(soup):
    # product_json = extract_product(soup)
    # if product_json is None:
    #     return None
    # brand_product, category_product, breadcrumb = extract_data_breadcrumb(soup)

    # name_product = product_json.get("name")
    # image_product = product_json.get("image")
    # url_product = product_json.get("url")
    # sku_product = product_json.get("sku")
    # price_product = product_json.get("offers", {}).get("price")
    brand_product = ""
    category_product = ""
    breadcrumb = ""
    product_name = ""
    product_url = ""
    product_image = ""
    product_sku = ""
    product_price = ""

    # Парсинг HTML с помощью BeautifulSoup
    script_tag = soup.find_all("script", type="application/ld+json")

    if len(script_tag) > 1:  # Проверяем, есть ли хотя бы два таких тега
        # Парсинг JSON
        second_script = script_tag[1].string  # Берем содержимое второго тега
        json_data = json.loads(second_script)
        if "@graph" in json_data:
            for item in json_data["@graph"]:
                # Извлечение данных из BreadcrumbList
                if item.get("@type") == "BreadcrumbList":
                    for element in item.get("itemListElement", []):
                        position = element.get("position")
                        name = element["item"].get("name", "")
                        if position == 2:
                            brand_product = name
                        elif position == 3:
                            category_product = name
                        elif position == 4:
                            breadcrumb = name

                # Извлечение данных о продукте
                if item.get("@type") == "Product":
                    product_name = item.get("name", "")
                    product_url = item.get("url", "")
                    product_image = item.get("image", "")
                    product_sku = item.get("sku", "")
                    if "offers" in item:
                        offers = (
                            item["offers"][0]
                            if isinstance(item["offers"], list)
                            else item["offers"]
                        )
                        product_price = offers.get("priceSpecification", [{}])[0].get(
                            "price", ""
                        )
    all_data = {
        "breadcrumb": breadcrumb,
        "brand_product": brand_product,
        "category_product": category_product,
        "image_product": product_image,
        "sku_product": product_sku,
        "price_product": product_price,
        "name_product": product_name,
        "url_product": product_url,
    }
    return all_data


def read_json_files():
    all_data = []
    for filename in os.listdir(json_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_path, filename)
            with open(file_path, "r", encoding="utf-8") as json_file:
                try:
                    data = json.load(json_file)
                    all_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Ошибка при чтении файла {filename}: {e}")
    return all_data


async def parsing_page():
    all_datas = read_json_files()
    # Преобразуем словарь обратно в список
    # unique_all_datas = list(all_datas.values())

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Сортировка по указанным колонкам
    df = df.sort_values(by=["breadcrumb", "brand_product", "category_product"])

    # Создаем новый Workbook
    wb = Workbook()
    ws = wb.active

    # Записываем заголовки
    for col_num, column_title in enumerate(df.columns, 1):
        ws.cell(row=1, column=col_num, value=column_title)

    # Записываем данные и вставляем изображения
    for row_num, row_data in enumerate(df.itertuples(index=False), 2):
        for col_num, cell_value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=cell_value)

            # Если это колонка с изображениями, вставляем изображение
            if col_num == df.columns.get_loc("image_product") + 1:
                image_url = cell_value
                try:
                    image_filename = os.path.join(
                        img_path, f"{row_num}.jpg"
                    )  # Изменим на .jpg
                    webp_filename = os.path.join(
                        img_path, f"{row_num}.webp"
                    )  # Временный файл для WebP

                    if not os.path.exists(image_filename):
                        print(
                            f"Загрузка изображения: {image_url}"
                        )  # Отладочное сообщение
                        image_data = requests.get(
                            image_url, headers=headers, timeout=30
                        ).content

                        # Сохраняем как WebP, даже если оно такое
                        with open(webp_filename, "wb") as img_file:
                            img_file.write(image_data)

                        # Конвертируем WebP в JPEG
                        with Image.open(webp_filename) as img:
                            img.convert("RGB").save(image_filename, "JPEG")

                        os.remove(webp_filename)  # Удаляем временный WebP файл

                    image = openpyxl.drawing.image.Image(image_filename)
                    image.width = 250  # Ширина изображения
                    image.height = 250  # Высота изображения
                    ws.add_image(image, cell.coordinate)
                    ws.row_dimensions[row_num].height = (
                        image.height
                    )  # Установка высоты строки
                except Exception as e:
                    print(f"Ошибка при загрузке изображения {image_url}: {e}")

    # Сохраняем файл
    output_file = "output.xlsx"
    wb.save(output_file)

    print(f"Файл сохранен как {output_file}")


if __name__ == "__main__":
    get_xml()
    main()
    asyncio.run(parsing_page())
