import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from configuration.logger_setup import logger

# Получаем текущую директорию
current_directory = Path.cwd()
# Определяем путь к XML файлу и CSV файлу
xml_sitemap = current_directory / "sitemap_products_1.xml"
output_csv = current_directory / "output.csv"


def xml_to_csv(xml_file: Path, csv_file: Path):
    # Чтение XML файла
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Префикс пространства имен
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлекаем все теги <loc> и записываем их в список
    urls = [loc.text for loc in root.findall("ns:url/ns:loc", ns)]

    # Создаем DataFrame с помощью pandas
    df = pd.DataFrame(urls, columns=["url"])

    # Сохраняем DataFrame в CSV файл
    df.to_csv(csv_file, index=False, encoding="utf-8")


# Вызываем функцию для записи в csv
xml_to_csv(xml_sitemap, output_csv)
