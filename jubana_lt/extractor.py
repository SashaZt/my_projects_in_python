import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


class ProductDataExtractor:
    def __init__(self):
        self.soup = None

    def parse_html(self, html_content):
        """Инициализирует парсер BeautifulSoup с HTML-контентом"""
        self.soup = BeautifulSoup(html_content, "lxml")
        return self

    def extract_product_attributes(self):
        """Извлекает атрибуты продукта из блока класса product-attributes"""
        attributes = {}

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return attributes

        # Ищем блок с атрибутами продукта
        attribute_divs = self.soup.select(".product-attribute")

        if not attribute_divs:
            logger.warning("Блок атрибутов продукта не найден")
            # Попробуем извлечь из текста в разделе описания
            return self.extract_attributes_from_description()

        # Обрабатываем каждый атрибут
        for attr_div in attribute_divs:
            # Получаем имя атрибута
            name_div = attr_div.select_one(".product-attribute-name")
            if not name_div:
                continue

            # Очищаем имя от лишних пробелов
            attribute_name = name_div.get_text().strip()

            # Получаем значение атрибута
            value_div = attr_div.select_one(".product-attribute-value")
            if not value_div:
                continue

            # Очищаем значение от лишних пробелов
            attribute_value = value_div.get_text().strip()

            # Преобразуем имя атрибута в ключ словаря
            key = attribute_name.lower().replace(" ", "_")

            # Добавляем атрибут в словарь
            attributes[key] = attribute_value

        return attributes

    def extract_attributes_from_description(self):
        """Извлекает атрибуты из текстового описания, если блок атрибутов не найден"""
        attributes = {}

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return attributes

        # Ищем блок с описанием
        description_div = self.soup.select_one(".tabs-description")
        if not description_div:
            logger.warning("Блок описания не найден")
            return attributes

        # Ищем параграфы с маркированными списками
        bullet_paragraphs = description_div.find_all(
            "p", string=lambda text: text and "•" in text if text else False
        )

        for p in bullet_paragraphs:
            text = p.get_text().strip()
            if not text:
                continue

            # Разбиваем текст на строки по маркеру списка
            lines = [line.strip() for line in text.split("•") if line.strip()]

            for line in lines:
                # Ищем разделители между названием и значением (обычно ":" или разделение с помощью тега <strong>)
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        attributes[key] = value

                # Если в параграфе есть теги <strong>, ищем их
                strong_tags = p.find_all("strong")
                for strong in strong_tags:
                    if strong.next_sibling and ":" in str(strong.next_sibling):
                        key = strong.get_text().strip().lower().replace(" ", "_")
                        value_text = str(strong.next_sibling).split(":", 1)[1].strip()
                        attributes[key] = value_text

        return attributes

    def extract_reference_numbers(self):
        """Извлекает референсные номера из таблицы"""
        reference_numbers = {}

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return reference_numbers

        # Ищем заголовок с текстом "REFERENCE NUMBERS"
        ref_header = self.soup.find(
            lambda tag: tag.name in ["h2", "h3"]
            and "REFERENCE NUMBERS" in tag.get_text()
        )

        if not ref_header:
            logger.warning("Заголовок REFERENCE NUMBERS не найден")
            return reference_numbers

        # Ищем таблицу после заголовка
        table = ref_header.find_next("table")

        if not table:
            logger.warning("Таблица с референсными номерами не найдена")
            return reference_numbers

        # Получаем все строки таблицы (пропускаем заголовок)
        rows = table.find_all("tr")[1:] if table.find_all("tr") else []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                manufacturer = cells[0].get_text().strip()
                number = cells[1].get_text().strip()

                # Добавляем номер к списку номеров производителя
                if manufacturer not in reference_numbers:
                    reference_numbers[manufacturer] = []

                reference_numbers[manufacturer].append(number)

        return reference_numbers

    def extract_applications(self):
        """Извлекает данные о применении продукта из таблицы"""
        applications = []

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return applications

        # Ищем заголовок с текстом "APPLICATIONS"
        app_header = self.soup.find(
            lambda tag: tag.name in ["h2", "h3"] and "APPLICATIONS" in tag.get_text()
        )

        if not app_header:
            logger.warning("Заголовок APPLICATIONS не найден")
            return applications

        # Ищем таблицу после заголовка
        table = app_header.find_next("table")

        if not table:
            logger.warning("Таблица с применениями не найдена")
            return applications

        # Получаем заголовки столбцов
        headers_row = table.find("tr")
        if not headers_row:
            logger.warning("В таблице применений не найдены заголовки")
            return applications

        headers = [th.get_text().strip() for th in headers_row.find_all("th")]

        # Получаем все строки таблицы (пропускаем заголовок)
        rows = table.find_all("tr")[1:] if table.find_all("tr") else []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= len(headers):
                application = {}

                for i, header in enumerate(headers):
                    key = header.lower().strip().replace(" ", "_")
                    value = cells[i].get_text().strip()
                    application[key] = value

                applications.append(application)

        return applications

    def extract_product_info(self):
        """Извлекает основную информацию о продукте (название, номер модели)"""
        product_info = {}

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return product_info

        # Ищем заголовок с названием продукта
        product_header = self.soup.find("h2")

        if product_header:
            product_text = product_header.get_text().strip()
            product_info["product_name"] = product_text

            # Ищем номер модели (обычно после дефиса)
            model_match = re.search(r"[-–]\s*(\d+)\s*$", product_text)
            if model_match:
                product_info["model"] = model_match.group(1)

        return product_info

    def extract_images(self):
        """Извлекает информацию о фотографиях продукта"""
        from image_utils import extract_product_images

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return []

        return extract_product_images(str(self.soup))

    def extract_all_data(self):
        """Извлекает все доступные данные о продукте"""
        if not self.soup:
            logger.error("HTML не был инициализирован")
            return {}

        # Объединяем все извлеченные данные
        data = {}

        # Извлекаем основную информацию о продукте
        product_info = self.extract_product_info()
        data.update(product_info)

        # Извлекаем атрибуты продукта
        attributes = self.extract_product_attributes()
        data.update(attributes)

        # Извлекаем референсные номера
        reference_numbers = self.extract_reference_numbers()
        if reference_numbers:
            data["reference_numbers"] = reference_numbers

        # Извлекаем применения
        applications = self.extract_applications()
        if applications:
            data["applications"] = applications

        # Добавляем информацию об изображениях
        images = self.extract_images()
        if images:
            data["images"] = images

        return data
