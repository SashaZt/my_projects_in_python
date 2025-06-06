import hashlib
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config.logger import logger

current_dir = Path.cwd()
temp_dir = current_dir / "temp"
xml_dir = temp_dir / "xml"
data_dir = temp_dir / "data"
json_dir = temp_dir / "json"
log_dir = current_dir / "log"
html_dir = temp_dir / "html"

log_dir.mkdir(parents=True, exist_ok=True)
json_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)
xml_dir.mkdir(parents=True, exist_ok=True)
html_dir.mkdir(parents=True, exist_ok=True)

log_file_path = log_dir / "log_message.log"
start_xml_path = xml_dir / "sitemap.xml"
output_csv_file = data_dir / "output.csv"
output_json_file = data_dir / "output.json"

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}


def make_response(url):
    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )
    if response.status_code == 200:
        return response
    else:
        logger.error(f"Ошибка при запросе по {url} Статус {response.status_code}")
        return None


def download_start_xml():
    """
    Скачиваем основной sitemap.xml
    """
    url = "https://www.ikea.com/sitemaps/sitemap.xml"
    response = make_response(url)
    if response is not None:
        # Сохранение содержимого в файл
        with open(start_xml_path, "wb") as file:
            file.write(response.content)


def parse_start_xml():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    download_start_xml()
    target = "https://www.ikea.com/sitemaps/prod-pl-PL_"
    try:
        # Парсим XML файл
        tree = ET.parse(start_xml_path)
        root = tree.getroot()

        # Определяем пространство имен (namespace), если оно есть
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Ищем все теги <url> и извлекаем <loc>
        matching_urls = [
            url.text
            for url in root.findall(".//sitemap:loc", namespace)
            if url.text and target in url.text
        ]
        return matching_urls

    except FileNotFoundError:
        return []


def download_all_xml():
    """
    Скачиваем
    """
    urls = parse_start_xml()
    for url in urls:

        # Извлечение имени файла из URL с помощью Path
        file_name = Path(urlparse(url).path).name  # Извлекает 'prod-pl-PL_6.xml'
        file_path = xml_dir / file_name  # Формируем полный путь с помощью /
        if file_path.exists():
            logger.info(f"Файл {file_name} уже существует")
            continue

        response = make_response(url)  # Проверка успешности запроса
        # Сохранение содержимого в файл
        with open(file_path, "wb") as file:
            file.write(response.content)

    parse_all_sitemap_urls()


def parse_all_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_dir.glob("prod*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")
    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)


def format_product_code(url):
    # Извлекаем цифры из конца URL с помощью регулярного выражения
    match = re.search(r"(\d+)$", url.rstrip("/"))
    if match:
        code = match.group(1)
        # Форматируем код: первые 3 цифры, затем 3 цифры, затем 2 цифры
        if len(code) == 8:
            return f"{code[:3]}.{code[3:6]}.{code[6:]}"
    return None


def main_th():
    """
    Скачивание товаров
    """
    urls = []

    df = pd.read_csv(output_csv_file, encoding="utf-8")
    urls = df["url"].tolist()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for url in urls[:1]:
            file_name = format_product_code(url)
            output_html_file = html_dir / f"{file_name}.html"
            if not output_html_file.exists():
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def get_html(url, html_file):
    response = make_response(url)
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(response.text)
    logger.info(html_file)


def pars_htmls():
    logger.info("Собираем данные со страниц html")

    html_files = list(html_dir.glob("*.html"))
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files:
        # Имя без раширения
        file_name = html_file.stem
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        product = soup.find("script", attrs={"id": "pip-range-json-ld"})
        json_string = product.string
        all_data = scrap_json(json_string)

        json_breadcrumblist = soup.find("script", attrs={"type": "application/ld+json"})
        product_breadcrumblist = json_breadcrumblist.string
        category_path = extract_category_path(product_breadcrumblist)
        all_data["category_path"] = category_path
        file_path = json_dir / f"{file_name}.json"
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)


def scrap_json(json_string):
    json_data = None
    # Убеждаемся, что содержимое не None
    if json_string:
        try:
            # Парсим строку как JSON
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON: {e}")
    availability = json_data.get("offers", {}).get("availability", "").split("/")[-1]
    if availability == "InStock":
        active = True
    else:
        active = False
    images = json_data.get("image", [])
    transformed_images = transform_images(images)
    descriptions = json_data.get("description", "")
    reviews = json_data.get("review", [])
    transformed_reviews = transform_reviews(reviews)
    reviews_rating = transform_reviews_rating(reviews)
    product = {
        "success": True,
        "id": json_data.get("sku", ""),  # SKU как уникальный идентификатор
        "title": json_data.get("name", ""),  # Название на польском
        "url": json_data.get("url", ""),  # URL продукта
        "active": active,
        "same_offers_id": None,
        "same_offers_count": 0,
        "buyers": 0,
        "buyers_this_offer": 0,
        "rating": float(
            json_data.get("aggregateRating", {}).get("ratingValue", 0)
        ),  # Средний рейтинг
        "reviews_count": int(
            json_data.get("aggregateRating", {}).get("reviewCount", 0)
        ),  # Количество отзывов
        "reviews_with_text_count": 0,
        "availableQuantity": 0,
        "price": float(json_data.get("offers", {}).get("price", 0)),  # Цена
        "price_with_delivery": 0.0,
        "currency": json_data.get("offers", {}).get("priceCurrency", ""),  # Валюта
        "delivery_price": 0.0,
        "delivery_period": None,
        "delivery_options": [],
        "seller_id": 0,
        "seller_login": None,
        "seller_rating": 0.0,
        "specifications": {
            "Parametry": {
                "Stan": "",
                "Faktura": "",
                "Rodzaj": "",
                "Waga produktu z opakowaniem jednostkowym": "",
                "EAN (GTIN)": "",
                "Marka": json_data.get("brand", {}).get("name", ""),  # Бренд
                "Typ": "",
                "Parametry": "",
            }
        },
        "description": {
            "sections": [{"items": [{"type": "TEXT", "content": descriptions}]}]
        },
        "images": transformed_images,  # Список URL изображений
        "reviews": transformed_reviews,  # Список отзывов
        "reviews_rating": reviews_rating,  # Список отзывов
    }
    # logger.info(json.dumps(product))
    return product


def transform_images(images):
    """
    Подготовка фото под формат шаблона
    """
    return [
        {"original": url, "thumbnail": "", "embeded": "", "alt": ""} for url in images
    ]


def extract_category_path(json_data):
    """
    Подготовка категорий под формат шаблона
    """
    category_path = []
    json_data = json.loads(json_data)
    items = json_data.get("itemListElement", [])
    for item in items[1:]:  # Пропускаем первый элемент
        url = item.get("item", "")
        # Извлекаем id из последней части URL
        match = re.search(r"/([^/]+)-([^/]+)/?$", url)
        category_id = ""
        if match:
            # Берем последнюю часть после дефиса
            category_id = match.group(2)

        category_path.append(
            {"id": category_id, "name": item.get("name", ""), "url": url}
        )

    return category_path


def transform_reviews(reviews):
    return [
        {
            "text": review.get("reviewBody", ""),
            "score": review.get("reviewRating", {}).get("ratingValue", ""),
            "date": None,
        }
        for review in reviews
    ]


def transform_reviews_rating(reviews):
    # Инициализируем словарь для подсчёта оценок
    rating_counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    # Подсчитываем количество отзывов для каждой оценки
    total_ratings = 0
    sum_ratings = 0
    for review in reviews:
        rating = str(review.get("reviewRating", {}).get("ratingValue", 0))
        if rating in rating_counts:
            rating_counts[rating] += 1
            total_ratings += 1
            sum_ratings += int(rating)

    # Вычисляем среднюю оценку
    average_rating = sum_ratings / total_ratings if total_ratings > 0 else 0

    # Добавляем среднюю оценку в результат
    result = {
        "rating_counts": rating_counts,
        "average_rating": round(average_rating, 1),
    }
    logger.info(result)
    return result


if __name__ == "__main__":
    # download_all_xml()
    # main_th()
    pars_htmls()
    # main_loop()
    # download_start_xml()
    # parse_all_sitemap_urls()
