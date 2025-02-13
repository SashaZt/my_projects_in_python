import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def parse_html():
    extracted_data = []

    # Loop through HTML files
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "lxml")

        # Извлекаем и парсим данные
        parsed_description = parse_description(soup)
        # parsed_description = None
        data_breadcrumb, data_product, review_data = extract_json_blocks(soup)
        quantity = extract_quantity_sold(soup)
        images = extract_image_links(soup)
        specifications = extract_item_specifics(soup)
        identifiers = extract_product_identifiers(soup)
        features = extract_product_key_features(soup)
        data_product["quantity"] = quantity
        all_data = {
            "category_path": data_breadcrumb,
            "data_product": data_product,
            "review_data": review_data,
            "images": images,
            "description": parsed_description,
            "specifications": specifications,
            "identifiers": identifiers,
            "features": features,
        }
        extracted_data.append(all_data)

    with open("extracted_data.json", "w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, indent=4, ensure_ascii=False)


def extract_json_blocks(soup):
    data_breadcrumb = None  # Инициализируем для хранения BreadcrumbList
    data_product = None  # Инициализируем для хранения Product
    review_data = None  # Инициализируем для хранения Product

    # Находим все теги <script> с типом application/ld+json
    for script_tag in soup.find_all("script", type="application/ld+json"):
        try:
            # Преобразуем содержимое тега в JSON
            json_data = json.loads(script_tag.string.strip())

            # Проверяем, является ли JSON объектом (dict)
            if isinstance(json_data, dict):
                # Если это BreadcrumbList, обрабатываем через соответствующую функцию
                if json_data.get("@type") == "BreadcrumbList":
                    data_breadcrumb = process_breadcrumb(json_data)
                # Если это Product, обрабатываем через соответствующую функцию
                elif json_data.get("@type") == "Product":
                    data_product, review_data = process_product(json_data)

        except json.JSONDecodeError:
            # Пропускаем некорректный JSON
            continue

    return data_breadcrumb, data_product, review_data


def process_breadcrumb(breadcrumb_json):
    breadcrumb_data = []
    for item in breadcrumb_json.get("itemListElement", []):
        breadcrumb_data.append(
            {"name": item.get("name", ""), "url": item.get("item", "")}
        )
    return breadcrumb_data


def process_product(product_json):
    product_data = []

    all_data_product = {
        "name": product_json.get("name", ""),
        "image": product_json.get("image", ""),
        "brand": product_json.get("brand", {}).get("name", ""),
        "price": safe_to_float(product_json.get("offers", {}).get("price", "")),
        "currency": product_json.get("offers", {}).get("priceCurrency", ""),
        "rating": safe_to_float(
            product_json.get("aggregateRating", {}).get("ratingValue", "")
        ),
        "reviews_count": safe_to_float(
            product_json.get("aggregateRating", {}).get("ratingCount", "")
        ),
        "gtin13": (
            int(product_json.get("gtin13", ""))
            if product_json.get("gtin13", "").isdigit()
            else None
        ),
        "color": product_json.get("color", ""),
        "model": product_json.get("model", ""),
    }
    product_data.append(all_data_product)

    review_data = []
    for review in product_json.get("review", []):
        all_data_review = {
            "type": "Review",
            "product_name": product_json.get("name", ""),
            "review_title": review.get("name", ""),
            "author": review.get("author", {}).get("name", ""),
            "rating": safe_to_float(
                review.get("reviewRating", {}).get("ratingValue", "")
            ),
            "review_text": review.get("reviewBody", ""),
            "date": review.get("datePublished", ""),
        }
        review_data.append(all_data_review)
    return all_data_product, review_data


def safe_to_float(value):
    # Если значение уже int или float, возвращаем его
    if isinstance(value, (int, float)):
        return value

    # Если это строка, пробуем преобразовать в число
    if isinstance(value, str):
        try:
            num = float(value)
            # Проверяем, является ли число целым
            if num.is_integer():
                return int(num)
            return num
        except ValueError:
            return None  # Возвращаем None, если не получилось преобразовать

    return None  # Если это не число и не строка, возвращаем None


def extract_quantity_sold(soup):
    # Найти div с id="qtyAvailability"
    qty_div = soup.find("div", id="qtyAvailability")

    available_count = None

    if qty_div:
        # Найти все <span> внутри div
        span_tags = qty_div.find_all("span")

        for span in span_tags:
            text = span.get_text(strip=True).lower()

            if "available" in text:
                number_str = text.split()[0].replace(",", "")
                try:
                    available_count = int(number_str)
                    return available_count
                except ValueError:
                    pass

    return None


def extract_image_links(soup):
    images = []

    # Находим все элементы с классами для изображений
    image_items = soup.find_all(
        "div", class_="ux-image-carousel-item image-treatment image"
    )
    active_image_items = soup.find_all(
        "div", class_="ux-image-carousel-item image-treatment active image"
    )

    # Объединяем списки, чтобы обработать оба типа изображений
    all_image_items = image_items + active_image_items

    for item in all_image_items:
        # Находим тег <img> внутри элемента
        img_tag = item.find("img")
        if img_tag:
            # Извлекаем оригинальную ссылку, миниатюру и альтернативный текст
            original = img_tag.get("data-zoom-src") or img_tag.get("src", "")
            thumbnail = (
                original.replace("s-l1600", "s-l400")
                if "s-l1600" in original
                else original
            )
            alt_text = img_tag.get("alt", "")

            # Добавляем в список
            images.append(
                {"original": original, "thumbnail": thumbnail, "alt": alt_text}
            )

    # Удаляем дубликаты
    return remove_duplicate_images(images)


def remove_duplicate_images(images):
    seen = set()
    unique_images = []

    for image in images:
        original_url = image.get("original")  # Уникальный ключ
        if original_url not in seen:
            seen.add(original_url)
            unique_images.append(image)

    return unique_images


def fetch_description_page(url):
    """
    Выполняет HTTP-запрос к указанному URL и возвращает HTML-контент.
    """
    try:
        cookies = {
            "ak_bmsc": "86595A80EDDC4C245FE3CA4B6C9DC389~000000000000000000000000000000~YAAQHvlVaOrec2WUAQAAC5qpjxpRSQTujxqcOkQdpgq2A/xdPVAUhELU5nuj+x21ClmTbb9u/ZZSawpOKkBkhsGACap6TpQqUidMY5mOvubXYaJe0Z2tWuoG6mrZdlkzaJYE+DhxEb+5AKnjn0FgJcZIU5lDJIJK2wHKXzQ9yYXlJM9OxlPzMsvpoBlDG11ALgDiUjqkJBL1NIjsFrITRCyW/IGquHAbp/sqEF9feBKSozZ/ne3vW4K3TvCDGHdEs608mqkWp+zsouyaBIysnuMcYVPPv80JrlIxJ5btGha81siLLkmMM8KxB4xOMOmXmxC7mMJ0xp49lKeSBo82WQugEhUHLVfMMGaFgRn7OhTKmNYzhk5gXO5k3D2U5QzRrBM1byLlMw==",
            "dp1": "bbl/DE6b53ba04^",
            "nonsession": "BAQAAAZRXz2gmAAaAADMABWlyhoQ2MDMyMwDKACBrU7oEOGZhYzQ5YjMxOTQwYWI0ZWUxYzU2NTZkZmZmZjRmZjcAywABZ5FaDDHyaEn6peczjYUVle2rSscJumdmyg**",
            "s": "CgAD4ACBnkqSEOGZhYzQ5YjMxOTQwYWI0ZWUxYzU2NTZkZmZmZjRmZjf9oqgH",
            "ebay": "%5Esbf%3D%23000000%5E",
            "bm_sv": "676922604F4B8252541665EAEFAF4620~YAAQHvlVaAtAdGWUAQAA6NqsjxoNXn9Lf2OmOT5N6eX6SkWecJJP0dRnvrclccNDXmK//uGe3F4gVNamBFS58HP3CvRsbKIZeCO+hCRcMtFgIxQacjTktVtBTJZ1+Q8dQW2AeiSZCVjMFEXE7PYQDv1CUZk7LX63m02U/SsVkLncGO1+Tv2UQLqrHIlyuK+CenZapB0OIOHX4hUFCPlIbp9NubB8OSRlGdlD0cQioHImiRmMV+0DcPhIPtCWfeBml12hsGBy3w==~1",
        }

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 'Cookie': 'ak_bmsc=86595A80EDDC4C245FE3CA4B6C9DC389~000000000000000000000000000000~YAAQHvlVaOrec2WUAQAAC5qpjxpRSQTujxqcOkQdpgq2A/xdPVAUhELU5nuj+x21ClmTbb9u/ZZSawpOKkBkhsGACap6TpQqUidMY5mOvubXYaJe0Z2tWuoG6mrZdlkzaJYE+DhxEb+5AKnjn0FgJcZIU5lDJIJK2wHKXzQ9yYXlJM9OxlPzMsvpoBlDG11ALgDiUjqkJBL1NIjsFrITRCyW/IGquHAbp/sqEF9feBKSozZ/ne3vW4K3TvCDGHdEs608mqkWp+zsouyaBIysnuMcYVPPv80JrlIxJ5btGha81siLLkmMM8KxB4xOMOmXmxC7mMJ0xp49lKeSBo82WQugEhUHLVfMMGaFgRn7OhTKmNYzhk5gXO5k3D2U5QzRrBM1byLlMw==; dp1=bbl/DE6b53ba04^; nonsession=BAQAAAZRXz2gmAAaAADMABWlyhoQ2MDMyMwDKACBrU7oEOGZhYzQ5YjMxOTQwYWI0ZWUxYzU2NTZkZmZmZjRmZjcAywABZ5FaDDHyaEn6peczjYUVle2rSscJumdmyg**; s=CgAD4ACBnkqSEOGZhYzQ5YjMxOTQwYWI0ZWUxYzU2NTZkZmZmZjRmZjf9oqgH; ebay=%5Esbf%3D%23000000%5E; bm_sv=676922604F4B8252541665EAEFAF4620~YAAQHvlVaAtAdGWUAQAA6NqsjxoNXn9Lf2OmOT5N6eX6SkWecJJP0dRnvrclccNDXmK//uGe3F4gVNamBFS58HP3CvRsbKIZeCO+hCRcMtFgIxQacjTktVtBTJZ1+Q8dQW2AeiSZCVjMFEXE7PYQDv1CUZk7LX63m02U/SsVkLncGO1+Tv2UQLqrHIlyuK+CenZapB0OIOHX4hUFCPlIbp9NubB8OSRlGdlD0cQioHImiRmMV+0DcPhIPtCWfeBml12hsGBy3w==~1',
            "DNT": "1",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-full-version": '"131.0.6778.265"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"19.0.0"',
        }

        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()  # Проверка на успешный запрос
        return response.text  # Возвращаем HTML-контент страницы
    except requests.RequestException as e:
        print(f"Ошибка при запросе URL {url}: {e}")
        return None


def parse_description(soup):
    """
    Парсит HTML-контент и извлекает все теги h1, h2, p, b, ul, li, img.
    Возвращает объединённую строку из этих тегов.
    """
    url = extract_iframe_url(soup)
    html_content = fetch_description_page(url)

    if not html_content:
        return ""

    # Парсим HTML-контент
    soup = BeautifulSoup(html_content, "lxml")

    # Находим все нужные теги
    tags = soup.find_all(["h1", "h2", "p", "b", "ul", "li", "img"])

    # Преобразуем все теги в строки и объединяем их через join
    return "".join(str(tag) for tag in tags)


def extract_iframe_url(soup):
    """
    Извлекает URL из атрибута src тега <iframe> и обрезает его до знака '?'.
    """
    # Находим тег <iframe> с id="desc_ifr"
    iframe_tag = soup.find("iframe", id="desc_ifr")
    if not iframe_tag:
        return None  # Если iframe не найден

    # Извлекаем значение атрибута src
    src_url = iframe_tag.get("src")
    if not src_url:
        return None  # Если src отсутствует

    # Обрезаем URL до знака '?'
    base_url = src_url.split("?")[0]
    return base_url


def extract_item_specifics(soup):
    """
    Извлекает данные из структуры <dl> -> <dt> и <dd>.
    Возвращает данные в виде словаря.
    """

    # Находим все теги <dl>
    specifics = {}
    for dl_tag in soup.find_all("dl", class_="ux-labels-values"):
        # Извлекаем текст из <dt> (заголовок) и <dd> (значение)
        dt_tag = dl_tag.find("dt")
        dd_tag = dl_tag.find("dd")
        if dt_tag and dd_tag:
            title = dt_tag.get_text(strip=True)
            value = dd_tag.get_text(strip=True)
            specifics[title] = value

    return specifics


def extract_section_data(soup, section_class):
    """
    Универсальная функция для извлечения данных из секции.
    :param soup: объект BeautifulSoup
    :param section_class: класс секции для поиска
    :return: словарь с данными секции
    """
    # Находим указанную секцию
    section = soup.find("div", class_=section_class)
    if not section:
        return {}

    # Результирующий словарь
    section_data = {}

    # Ищем все элементы 'ux-labels-values' внутри секции
    for item in section.find_all("div", class_="ux-labels-values"):
        # Извлекаем название и значение
        label_div = item.find("div", class_="ux-labels-values__labels")
        value_div = item.find("div", class_="ux-labels-values__values")
        if label_div and value_div:
            label = label_div.get_text(strip=True)
            value = value_div.get_text(strip=True)
            section_data[label] = value

    return section_data


def extract_product_identifiers(soup):
    """
    Извлекает данные из секции 'Product Identifiers'.
    """
    return extract_section_data(
        soup, "ux-layout-section-evo ux-layout-section--productIdentifiers"
    )


def extract_product_key_features(soup):
    """
    Извлекает данные из секции 'Product Key Features'.
    """
    return extract_section_data(
        soup, "ux-layout-section-evo ux-layout-section--productKeyFeatures"
    )


if __name__ == "__main__":
    parse_html()
