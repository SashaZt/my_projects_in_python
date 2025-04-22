# /utils/xml_utils.py
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Set

from config.logger import logger
from utils.csv_utils import write_csv


def parse_sitemap_index(xml_file: Path) -> List[str]:
    """Парсит основной файл sitemap-index.xml."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_links = [loc.text for loc in root.findall("ns:sitemap/ns:loc", namespace)]
    logger.info(f"Найдено {len(sitemap_links)} ссылок на sitemap файлы")
    return sitemap_links


def parse_product_urls(xml_file: Path) -> List[str]:
    """Извлекает ссылки на продукты из XML файла."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    product_urls = [loc.text for loc in root.findall("ns:url/ns:loc", namespace)]
    return product_urls


def process_xml_files(input_dir: Path, output_csv: Path) -> None:
    """Обрабатывает XML файлы и сохраняет уникальные URL в CSV."""
    product_urls = set()  # Используем set для уникальных URL
    xml_files = list(input_dir.glob("*.xml"))
    total_files = len(xml_files)

    for idx, xml_file in enumerate(xml_files, 1):
        try:
            urls = parse_product_urls(xml_file)
            product_urls.update(urls)
            logger.info(f"Обработан файл {xml_file.name} ({idx}/{total_files})")
        except Exception as e:
            logger.error(f"Ошибка при обработке {xml_file.name}: {e}")

    write_csv(output_csv, list(product_urls))
    logger.info(f"Всего найдено {len(product_urls)} уникальных URL")
