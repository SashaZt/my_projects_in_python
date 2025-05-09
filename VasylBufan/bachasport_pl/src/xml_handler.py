# /src/xml_handler.py
import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from config.logger import logger

# Получаем текущую директорию и пути
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = data_directory / "xml"
results_directory = data_directory / "results"

# Создаем директории если они не существуют
for directory in [data_directory, xml_directory, results_directory]:
    directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам результатов
csv_output_file = results_directory / "products.csv"
json_output_file = results_directory / "products.json"


def parse_xml_file(xml_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Парсит XML файл продукта и извлекает из него данные.

    Args:
        xml_path (Union[str, Path]): Путь к XML файлу.

    Returns:
        Optional[Dict[str, Any]]: Словарь с данными продукта или None в случае ошибки.
    """
    try:
        xml_path = Path(xml_path) if isinstance(xml_path, str) else xml_path

        if not xml_path.exists():
            logger.error(f"XML файл не найден: {xml_path}")
            return None

        # Парсим XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Извлекаем данные из XML
        product_data = extract_product_data_from_xml(root)

        logger.info(f"Успешно обработан XML продукта: {xml_path.name}")
        return product_data
    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML файла {xml_path}: {e}")

        # Пробуем исправить XML и повторно распарсить
        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # Пытаемся исправить некоторые распространенные ошибки в XML
            fixed_xml = fix_invalid_xml(xml_content)

            # Парсим из исправленной строки
            root = ET.fromstring(fixed_xml)
            product_data = extract_product_data_from_xml(root)

            logger.info(f"Успешно обработан исправленный XML продукта: {xml_path.name}")
            return product_data
        except Exception as e2:
            logger.error(f"Не удалось исправить и распарсить XML {xml_path}: {e2}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при обработке XML файла {xml_path}: {e}")
        return None


def fix_invalid_xml(xml_content: str) -> str:
    """
    Пытается исправить некорректный XML.

    Args:
        xml_content (str): Исходный XML контент.

    Returns:
        str: Исправленный XML контент.
    """
    # Используем BeautifulSoup для исправления некорректного HTML/XML
    soup = BeautifulSoup(xml_content, "xml")

    # Преобразуем обратно в строку
    fixed_xml = str(soup)

    # Заменяем некорректные символы
    fixed_xml = re.sub(
        r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", fixed_xml
    )

    return fixed_xml


def extract_product_data_from_xml(root: ET.Element) -> Dict[str, Any]:
    """
    Извлекает данные продукта из корневого элемента XML.

    Args:
        root (ET.Element): Корневой элемент XML.

    Returns:
        Dict[str, Any]: Словарь с данными продукта.
    """
    product_data = {}

    try:
        # Извлекаем основные атрибуты продукта
        for elem in root.findall(".//*"):
            if elem.tag and elem.text:
                tag_name = elem.tag.strip()
                # Пропускаем вложенные элементы с своими подэлементами
                if len(elem) == 0:  # Элемент не имеет дочерних элементов
                    product_data[tag_name] = elem.text.strip()

        # Обработка специфичных полей (при необходимости)
        # Например, извлечение цен, атрибутов, изображений и т.д.

        # Извлечение цен (пример)
        prices = extract_prices(root)
        if prices:
            product_data["prices"] = prices

        # Извлечение атрибутов (пример)
        attributes = extract_attributes(root)
        if attributes:
            product_data["attributes"] = attributes

        # Извлечение изображений (пример)
        images = extract_images(root)
        if images:
            product_data["images"] = images

        return product_data
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных из XML: {e}")
        return product_data


def extract_prices(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Извлекает информацию о ценах продукта.

    Args:
        root (ET.Element): Корневой элемент XML.

    Returns:
        List[Dict[str, Any]]: Список цен продукта.
    """
    prices = []
    try:
        # Здесь логика зависит от структуры XML
        # Пример:
        price_elements = root.findall(".//price") or root.findall(".//prices/price")

        for price_elem in price_elements:
            price_data = {}

            # Извлекаем атрибуты цены
            for attr, value in price_elem.attrib.items():
                price_data[attr] = value

            # Извлекаем значение цены
            if price_elem.text:
                price_data["value"] = price_elem.text.strip()

            # Извлекаем вложенные элементы
            for child in price_elem:
                if child.tag and child.text:
                    price_data[child.tag] = child.text.strip()

            prices.append(price_data)

        return prices
    except Exception as e:
        logger.error(f"Ошибка при извлечении цен из XML: {e}")
        return prices


def extract_attributes(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Извлекает атрибуты продукта.

    Args:
        root (ET.Element): Корневой элемент XML.

    Returns:
        List[Dict[str, Any]]: Список атрибутов продукта.
    """
    attributes = []
    try:
        # Здесь логика зависит от структуры XML
        # Пример:
        attr_elements = root.findall(".//attribute") or root.findall(
            ".//attributes/attribute"
        )

        for attr_elem in attr_elements:
            attr_data = {}

            # Извлекаем атрибуты
            for attr, value in attr_elem.attrib.items():
                attr_data[attr] = value

            # Извлекаем имя и значение атрибута
            name_elem = attr_elem.find("./name")
            value_elem = attr_elem.find("./value")

            if name_elem is not None and name_elem.text:
                attr_data["name"] = name_elem.text.strip()

            if value_elem is not None and value_elem.text:
                attr_data["value"] = value_elem.text.strip()

            attributes.append(attr_data)

        return attributes
    except Exception as e:
        logger.error(f"Ошибка при извлечении атрибутов из XML: {e}")
        return attributes


def extract_images(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Извлекает изображения продукта.

    Args:
        root (ET.Element): Корневой элемент XML.

    Returns:
        List[Dict[str, Any]]: Список изображений продукта.
    """
    images = []
    try:
        # Здесь логика зависит от структуры XML
        # Пример:
        image_elements = root.findall(".//image") or root.findall(".//images/image")

        for img_elem in image_elements:
            img_data = {}

            # Извлекаем атрибуты изображения
            for attr, value in img_elem.attrib.items():
                img_data[attr] = value

            # Если элемент содержит URL или путь к изображению
            if img_elem.text:
                img_data["url"] = img_elem.text.strip()

            images.append(img_data)

        return images
    except Exception as e:
        logger.error(f"Ошибка при извлечении изображений из XML: {e}")
        return images


def save_products_to_csv(
    products: List[Dict[str, Any]], output_path: Optional[Path] = None
) -> None:
    """
    Сохраняет данные о продуктах в CSV файл.

    Args:
        products (List[Dict[str, Any]]): Список словарей с данными продуктов.
        output_path (Optional[Path]): Путь для сохранения CSV. Если None, используется путь по умолчанию.
    """
    if not products:
        logger.warning("Нет данных для сохранения в CSV")
        return

    output_path = output_path or csv_output_file

    try:
        # Определяем все возможные поля (столбцы)
        all_fields = set()
        for product in products:
            all_fields.update(product.keys())

        # Добавляем нужные поля в начало списка для лучшей читаемости
        priority_fields = [
            "id",
            "code",
            "name",
            "price",
            "currency",
            "category",
            "brand",
            "description",
        ]
        fieldnames = []

        # Сначала добавляем приоритетные поля, если они есть в данных
        for field in priority_fields:
            if field in all_fields:
                fieldnames.append(field)
                all_fields.remove(field)

        # Затем добавляем оставшиеся поля
        fieldnames.extend(sorted(all_fields))

        # Записываем данные в CSV
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Преобразуем вложенные словари и списки в строки перед записью
            for product in products:
                row = {}
                for key, value in product.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)

        logger.info(
            f"Данные о {len(products)} продуктах сохранены в CSV: {output_path}"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в CSV: {e}")


def save_products_to_json(
    products: List[Dict[str, Any]], output_path: Optional[Path] = None
) -> None:
    """
    Сохраняет данные о продуктах в JSON файл.

    Args:
        products (List[Dict[str, Any]]): Список словарей с данными продуктов.
        output_path (Optional[Path]): Путь для сохранения JSON. Если None, используется путь по умолчанию.
    """
    if not products:
        logger.warning("Нет данных для сохранения в JSON")
        return

    output_path = output_path or json_output_file

    try:
        with open(output_path, "w", encoding="utf-8") as jsonfile:
            json.dump(products, jsonfile, ensure_ascii=False, indent=2)

        logger.info(
            f"Данные о {len(products)} продуктах сохранены в JSON: {output_path}"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в JSON: {e}")


def process_all_xml_files(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Обрабатывает все XML файлы в указанной директории.

    Args:
        directory (Optional[Path]): Директория с XML файлами. Если None, используется директория по умолчанию.

    Returns:
        List[Dict[str, Any]]: Список данных о всех продуктах.
    """
    directory = directory or xml_directory
    all_products = []

    try:
        xml_files = list(directory.glob("*.xml"))
        logger.info(f"Найдено {len(xml_files)} XML файлов для обработки")

        for xml_file in xml_files:
            product_data = parse_xml_file(xml_file)
            if product_data:
                # Добавляем имя файла как ID продукта, если ID не указан
                if "id" not in product_data:
                    product_id = re.search(r"product_(\d+)\.xml", xml_file.name)
                    if product_id:
                        product_data["id"] = product_id.group(1)

                all_products.append(product_data)

        logger.info(f"Успешно обработано {len(all_products)} XML файлов")
        return all_products
    except Exception as e:
        logger.error(f"Ошибка при обработке XML файлов: {e}")
        return all_products


def extract_simplified_product_data(
    xml_file_path: Union[str, Path],
) -> Optional[Dict[str, Any]]:
    """
    Извлекает из XML файла только основные данные (код товара и цену).

    Args:
        xml_file_path (Union[str, Path]): Путь к XML файлу продукта.

    Returns:
        Optional[Dict[str, Any]]: Словарь с основными данными или None в случае ошибки.
    """
    try:
        xml_path = (
            Path(xml_file_path) if isinstance(xml_file_path, str) else xml_file_path
        )

        if not xml_path.exists():
            logger.error(f"XML файл не найден: {xml_path}")
            return None

        # Пытаемся открыть файл как текст
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # Поиск символа и цены с помощью регулярных выражений
        symbol_match = re.search(r"<Symbol>([^<]+)</Symbol>", xml_content)
        price_match = re.search(
            r"<Cena>.*?<Netto>([^<]+)</Netto>", xml_content, re.DOTALL
        )

        if symbol_match and price_match:
            symbol = symbol_match.group(1).strip()
            price = price_match.group(1).strip()

            # Преобразуем цену в число
            try:
                price = float(price.replace(",", "."))
            except ValueError:
                logger.warning(
                    f"Не удалось преобразовать цену '{price}' в число для продукта {xml_path.name}"
                )

            return {"Symbol": symbol, "Cena": price}
        else:
            logger.warning(f"Не удалось найти Symbol или Cena в файле {xml_path.name}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при извлечении данных из XML файла {xml_path}: {e}")
        return None


def process_all_xml_files_simplified(
    directory: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Обрабатывает все XML файлы в указанной директории и извлекает только основные данные.

    Args:
        directory (Optional[Path]): Директория с XML файлами. Если None, используется директория по умолчанию.

    Returns:
        List[Dict[str, Any]]: Список словарей с основными данными продуктов.
    """
    directory = directory or xml_directory
    all_products = []

    try:
        xml_files = list(directory.glob("*.xml"))
        logger.info(f"Найдено {len(xml_files)} XML файлов для обработки")

        for xml_file in xml_files:
            product_data = extract_simplified_product_data(xml_file)
            if product_data:
                all_products.append(product_data)

        logger.info(
            f"Успешно обработано {len(all_products)} XML файлов в упрощенном режиме"
        )
        return all_products
    except Exception as e:
        logger.error(f"Ошибка при обработке XML файлов в упрощенном режиме: {e}")
        return all_products


# def extract_simplified_product_data(
#     xml_file_path: Union[str, Path],
# ) -> Optional[Dict[str, Any]]:
#     """
#     Извлекает из XML файла только основные данные (код товара и цену).

#     Args:
#         xml_file_path (Union[str, Path]): Путь к XML файлу продукта.

#     Returns:
#         Optional[Dict[str, Any]]: Словарь с основными данными или None в случае ошибки.
#     """
#     try:
#         xml_path = (
#             Path(xml_file_path) if isinstance(xml_file_path, str) else xml_file_path
#         )

#         if not xml_path.exists():
#             logger.error(f"XML файл не найден: {xml_path}")
#             return None

#         # Пытаемся открыть файл как текст
#         with open(xml_path, "r", encoding="utf-8") as f:
#             xml_content = f.read()

#         # Поиск символа и цены с помощью регулярных выражений
#         symbol_match = re.search(r"<Symbol>([^<]+)</Symbol>", xml_content)
#         price_match = re.search(
#             r"<Cena>.*?<Netto>([^<]+)</Netto>", xml_content, re.DOTALL
#         )

#         if symbol_match and price_match:
#             symbol = symbol_match.group(1).strip()
#             price = price_match.group(1).strip()

#             # Преобразуем цену в число
#             try:
#                 price = float(price.replace(",", "."))
#             except ValueError:
#                 logger.warning(
#                     f"Не удалось преобразовать цену '{price}' в число для продукта {xml_path.name}"
#                 )

#             return {"Symbol": symbol, "Cena": price}
#         else:
#             logger.warning(f"Не удалось найти Symbol или Cena в файле {xml_path.name}")
#             return None

#     except Exception as e:
#         logger.error(f"Ошибка при извлечении данных из XML файла {xml_path}: {e}")
#         return None


# def process_all_xml_files_simplified(
#     directory: Optional[Path] = None,
# ) -> List[Dict[str, Any]]:
#     """
#     Обрабатывает все XML файлы в указанной директории и извлекает только основные данные.

#     Args:
#         directory (Optional[Path]): Директория с XML файлами. Если None, используется директория по умолчанию.

#     Returns:
#         List[Dict[str, Any]]: Список словарей с основными данными продуктов.
#     """
#     directory = directory or xml_directory
#     all_products = []

#     try:
#         xml_files = list(directory.glob("*.xml"))
#         logger.info(f"Найдено {len(xml_files)} XML файлов для обработки")

#         for xml_file in xml_files:
#             product_data = extract_simplified_product_data(xml_file)
#             if product_data:
#                 all_products.append(product_data)

#         logger.info(
#             f"Успешно обработано {len(all_products)} XML файлов в упрощенном режиме"
#         )
#         return all_products
#     except Exception as e:
#         logger.error(f"Ошибка при обработке XML файлов в упрощенном режиме: {e}")
#         return all_products
