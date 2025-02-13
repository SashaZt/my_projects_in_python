import concurrent.futures
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger

# Замените пути на актуальные
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
output_csv_file_img = data_directory / "output_img.csv"
output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"


def extract_image_filename(image_url):
    match = re.search(r"/(\d{4})/(\d{2})/([^/]+)\.png$", image_url)
    if match:
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"
    return "unknown_filename"


def save_urls_product(filename, urls):
    """Сохраняет список URL-ов в CSV."""
    pd.DataFrame({"image_url": urls}).to_csv(filename, index=False)


def process_html_file(html_file):
    """Обрабатывает один HTML-файл и извлекает данные."""
    with html_file.open(encoding="utf-8") as file:
        content = file.read()
    logger.info(f"Processing {html_file.name}")
    soup = BeautifulSoup(content, "lxml")
    name_tag = soup.find("h1", attrs={"class": "product_title entry-title"})
    name = name_tag.text.strip() if name_tag else None
    img_tag = soup.find("meta", attrs={"property": "og:image"})
    image_url = img_tag.get("content") if img_tag else None
    if not image_url:
        return None, None
    image_filename = extract_image_filename(image_url)
    description = None
    description_tag = soup.find("div", attrs={"id": "tab-description"})
    if description_tag:
        text_parts = description_tag.text.split("Данная деталь", 1)
        description = (
            "Данная деталь" + text_parts[1].strip() if len(text_parts) > 1 else None
        )
    data_product = {
        "name": name,
        "description": description,
        "image_filename": image_filename,
    }
    return data_product, image_url


def parsing_page(num_threads=50):
    """Парсит HTML-файлы с использованием многопоточности."""
    all_data = []
    all_img_urls = []
    html_files = list(html_directory.glob("*.html"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = executor.map(process_html_file, html_files)

    for data_product, image_url in results:
        if data_product:
            all_data.append(data_product)
        if image_url:
            all_img_urls.append(image_url)

    save_urls_product(output_csv_file_img, all_img_urls)
    df = pd.DataFrame(all_data)
    df.to_excel(output_xlsx_file, index=False)


# Запуск с 8 потоками
if __name__ == "__main__":
    parsing_page(num_threads=50)
