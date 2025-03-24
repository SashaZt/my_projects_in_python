import html
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
output_html_file = html_directory / "output.html"
output_json_file = html_directory / "output.json"

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


def extract_json_from_tag(html_content):
    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")

    # Находим элемент с id="product-details"
    product_div = soup.find("div", id="product-details")

    if product_div and "data-product" in product_div.attrs:
        # Получаем значение атрибута data-product
        data_product = product_div["data-product"]

        # Раскодируем HTML-сущности (например, &quot; -> ")
        decoded_data = html.unescape(data_product)

        try:
            # Преобразуем строку в JSON-объект
            json_data = json.loads(decoded_data)
            return json_data
        except json.JSONDecodeError as e:
            return f"Ошибка при парсинге JSON: {e}"
    else:
        return "Элемент с id='product-details' или атрибут 'data-product' не найден"


# Чтение содержимого HTML-файла
with open(output_html_file, "r", encoding="utf-8") as file:
    html_content = file.read()

# Извлечение JSON
result = extract_json_from_tag(html_content)

# Вывод результата
if isinstance(result, dict):
    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(output_json_file)
else:
    print(result)
