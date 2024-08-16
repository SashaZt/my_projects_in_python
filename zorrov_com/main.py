import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import csv
from selectolax.parser import HTMLParser
import aiofiles
import asyncio
from configuration.logger_setup import logger
from datetime import datetime

# Получаем текущую директорию
current_directory = Path.cwd()
temp_path = current_directory / "temp"
html_path = temp_path / "html"
xml_directory = Path("xml")

# Создание директории, если она не существует
temp_path.mkdir(parents=True, exist_ok=True)
html_path.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(exist_ok=True)
#

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}


def download_and_parse_main_xml():

    main_url = "https://zorrov.com/image_sitemap.xml"
    # Скачиваем основной файл
    response = requests.get(main_url, headers=headers)

    if response.status_code == 200:
        # Парсим основной XML-файл
        root = ET.fromstring(response.content)

        # Обходим все элементы <loc>
        for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            file_url = loc.text
            if file_url:
                # Извлекаем имя файла из URL и скачиваем его
                file_name = Path(file_url).name
                save_path = xml_directory / file_name
                download_xml(file_url, save_path)
    else:
        print(f"Ошибка при скачивании основного файла: {response.status_code}")


def download_xml(url: str, save_path: Path):
    response = requests.get(url)

    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен: {save_path}")
    else:
        logger.error(f"Ошибка при скачивании файла {url}: {response.status_code}")


def parse_xml_files():
    output_csv = Path("urls.csv")
    all_loc_urls = []

    for xml_file in xml_directory.glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if loc is not None:
                all_loc_urls.append(loc.text)

    # Сохраняем все URL в CSV-файл
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["url"])
        for url in all_loc_urls:
            writer.writerow([url])


# Асинхронная функция для парсинга одного файла
async def parse_html_file(file_path: Path):
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        html_content = await file.read()

    parser = HTMLParser(html_content)

    # Извлечение текста из <h1> с классом "h2"
    h1_element = parser.css_first("h1.h2")
    title = (
        h1_element.text(strip=True)
        if h1_element
        else logger.error("Заголовок не найден")
    )

    # Извлечение текста из <p> с классом "supplementary-text supplementary-text--size--big"
    p_element = parser.css_first("p.supplementary-text.supplementary-text--size--big")
    article_number = (
        p_element.text(strip=True).replace("Артикул:", "")
        if p_element
        else logger.error("Артикул не найден")
    )
    # Извлечение текста из <div class="static-content">
    # Находим все элементы <div class="static-content">
    static_content_elements = parser.css("div.static-content")
    static_content = "Статический контент не найден"

    for element in static_content_elements:
        # Проверяем, содержит ли элемент текст "Оплата:"
        if "Оплата:" in element.text():
            # Логируем найденный контент
            # Забираем весь текст из первого подходящего элемента
            static_content = element.text(strip=True)
            break

    description_elements = parser.css_first(
        "div.static-content.static-content--theme--dark"
    )
    if description_elements:
        description = description_elements.text(strip=True)
        description = description.replace("Zorrov", "")
    else:
        logger.error("Артикул не найден")
        description = ""

    # Находим таблицу с классом "product-specifications"
    table = parser.css_first("table.product-specifications")

    if not table:
        return {}

    # Словарь для хранения данных
    specifications = {}

    # Находим все строки <tr> в таблице
    rows = table.css("tr")

    for row in rows:
        # Извлекаем все ячейки <td> в строке
        cells = row.css("td")

        # Если в строке две ячейки, добавляем их в словарь
        if len(cells) == 2:
            key = cells[0].text(strip=True)
            value = cells[1].text(strip=True)
            # Добавляем данные в словарь
            specifications[key] = value
    # Находим таблицу с классом "product-specifications"
    image_product_element = parser.css_first("a.js-photoswipe-link")

    if image_product_element:
        image_product = image_product_element.attributes.get("href")
        image_product = f"https://zorrov.com{image_product}"
    else:
        image_product = None  # Или любое другое значение по умолчанию

        # Теперь href_value содержит значение атрибута href, если элемент был найден
    price_element = parser.css_first("span.price__current")

    if price_element:
        price = price_element.text(strip=True)
    else:
        price_element = parser.css_first("span.price__prev")
        price = price_element.text(strip=True)

        # Теперь price_value содержит текстовое значение "230"

    return (
        title,
        article_number,
        static_content,
        description,
        specifications,
        image_product,
        price,
    )


# Асинхронная функция для парсинга всех файлов в папке
async def parse_all_html_files():
    tasks = []

    for html_file in html_path.glob("*.html"):
        tasks.append(parse_html_file(html_file))

    results = await asyncio.gather(*tasks)
    all_datas = []
    for (
        title,
        article_number,
        static_content,
        description,
        specifications,
        image_product,
        price,
    ) in results[:2]:
        all_data = {
            "title": title,
            "article_number": article_number,
            "static_content": static_content,
            "description": description,
            "image_product": image_product,
            "price": price,
            "specifications": specifications,
        }
        all_datas.append(all_data)
    logger.info(all_datas)
    # Генерация XML-файла
    # create_xml(all_datas)


def create_item_element(product_data):
    item = ET.Element("item", id=product_data["article_number"], available="true")

    # Добавляем основные поля
    ET.SubElement(item, "url").text = "Ссылка на товар"  # Пример ссылки на товар
    ET.SubElement(item, "price").text = product_data["price"]
    ET.SubElement(item, "categoryId").text = "26"  # Пример категории
    ET.SubElement(item, "name").text = product_data["title"]
    ET.SubElement(item, "description").text = product_data["description"]
    ET.SubElement(item, "model").text = product_data[
        "article_number"
    ]  # Используем артикул как модель
    # ET.SubElement(item, "upc").text = "4969"  # Пример UPC кода
    # ET.SubElement(item, "quantity").text = "1314"  # Пример количества на складе
    # ET.SubElement(item, "vendor").text = "Feron"  # Пример производителя
    ET.SubElement(item, "vendorCode").text = product_data["article_number"]
    ET.SubElement(item, "image").text = product_data["image_product"]

    # Добавляем параметры (specifications)
    for key, value in product_data["specifications"].items():
        param = ET.SubElement(item, "param")
        param.set("name", key)
        param.text = value

    return item


def create_xml(data):
    price = ET.Element("price", date=datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Общая информация о магазине
    ET.SubElement(price, "name").text = "Мой магазин"
    ET.SubElement(price, "company").text = "Моя компания"
    ET.SubElement(price, "url").text = "Тут ссылка на мой магазин"
    ET.SubElement(price, "currency", code="UAH", rate="1")

    # Категории
    categories = ET.SubElement(price, "categories")
    ET.SubElement(categories, "category", id="17", parentId="139").text = (
        "Чохли для телефонів"
    )

    # Добавляем товары
    items = ET.SubElement(price, "items")
    for product_data in data:
        item_element = create_item_element(product_data)
        items.append(item_element)

    tree = ET.ElementTree(price)
    tree.write("output.xml", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    # download_and_parse_main_xml()
    # parse_xml_files()
    asyncio.run(parse_all_html_files())
