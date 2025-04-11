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

        # Ищем блок с атрибутами продукта - пробуем несколько селекторов
        attribute_container = self.soup.select_one(".product-attributes")
        
        if attribute_container:
            # Ищем все div с классом product-attribute
            attribute_divs = attribute_container.select(".product-attribute")
            
            if attribute_divs:
                logger.info(f"Найдено {len(attribute_divs)} блоков атрибутов")
                
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
                    key = attribute_name.lower().replace(" ", "_").replace("(", "_").replace(")", "")

                    # Добавляем атрибут в словарь
                    attributes[key] = attribute_value
        
        # Если атрибуты не найдены в основном блоке, попробуем другие методы
        if not attributes:
            individual_attributes = self.soup.select(".attribute.product-attribute")
            if individual_attributes:
                logger.info(f"Найдено {len(individual_attributes)} индивидуальных блоков атрибутов")
                
                for attr_div in individual_attributes:
                    name_div = attr_div.select_one(".product-attribute-name")
                    value_div = attr_div.select_one(".product-attribute-value")
                    
                    if name_div and value_div:
                        attribute_name = name_div.get_text().strip()
                        attribute_value = value_div.get_text().strip()
                        key = attribute_name.lower().replace(" ", "_").replace("(", "_").replace(")", "")
                        attributes[key] = attribute_value
        
        # Просто возвращаем найденные атрибуты, даже если их нет
        # Не вызываем extract_attributes_from_description здесь
        return attributes

    def extract_attributes_from_description(self):
        """Извлекает атрибуты из текстового описания, если блок атрибутов не найден"""
        attributes = {}

        if not self.soup:
            logger.error("HTML не был инициализирован")
            return attributes

        # Ищем блок с описанием, пробуем несколько селекторов
        description_selectors = [".tabs-description", "#tab_description", ".product-description", ".description"]
        description_div = None
        
        for selector in description_selectors:
            description_div = self.soup.select_one(selector)
            if description_div:
                break
        
        if not description_div:
            logger.warning("Блок описания не найден по известным селекторам")
            return attributes

        # Получаем весь текст блока описания
        description_text = description_div.get_text().strip()
        
        # Обрабатываем текст напрямую, разбивая его на строки
        for line in description_text.split('\n'):
            line = line.strip()
            # Удаляем маркеры списка в начале строки
            line = re.sub(r'^[•*\-\s]+', '', line)
            
            # Ищем строки с двоеточием - ключевой признак пары ключ:значение
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    # Очищаем ключ от маркеров списка и специальных символов
                    key = parts[0].strip().lower()
                    key = re.sub(r'^[•*\-\s]+', '', key)  # Удаляем маркеры списка в начале
                    key = key.replace(" ", "_").replace("(", "_").replace(")", "")
                    
                    value = parts[1].strip()
                    attributes[key] = value
        
        # Для параграфов и других структурированных элементов
        bullet_paragraphs = description_div.find_all(
            "p", string=lambda text: text and ("•" in text or "*" in text or "-" in text) if text else False
        )
        
        if not bullet_paragraphs:
            bullet_paragraphs = [p for p in description_div.find_all("p") if p.find("strong")]
            
            if not bullet_paragraphs:
                all_paragraphs = description_div.find_all("p")
                
                for p in all_paragraphs:
                    text = p.get_text().strip()
                    # Удаляем маркеры списка в начале строки
                    text = re.sub(r'^[•*\-\s]+', '', text)
                    
                    if ":" in text:
                        parts = text.split(":", 1)
                        if len(parts) == 2:
                            # Очищаем ключ от маркеров списка и специальных символов
                            key = parts[0].strip().lower()
                            key = re.sub(r'^[•*\-\s]+', '', key)  # Удаляем маркеры списка в начале
                            key = key.replace(" ", "_").replace("(", "_").replace(")", "")
                            
                            value = parts[1].strip()
                            attributes[key] = value
        
        for p in bullet_paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
            
            # Удаляем маркеры списка в начале каждой строки
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Удаляем маркеры списка в начале строки
                line = re.sub(r'^[•*\-\s]+', '', line)
                
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        # Очищаем ключ от маркеров списка и специальных символов
                        key = parts[0].strip().lower()
                        key = re.sub(r'^[•*\-\s]+', '', key)  # Удаляем маркеры списка в начале
                        key = key.replace(" ", "_").replace("(", "_").replace(")", "")
                        
                        value = parts[1].strip()
                        attributes[key] = value
        
        # Обработка для <strong> тегов аналогично...
        
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

        # Ищем заголовок с названием продукта - сначала h1, потом h2
        product_header = self.soup.find("h1")
        
        if not product_header:
            product_header = self.soup.find("h2")
        
        # Также проверяем heading2 div, который может содержать h1
        if not product_header:
            heading_div = self.soup.find(id="heading2")
            if heading_div:
                product_header = heading_div.find("h1") or heading_div.find("span")

        if product_header:
            # Если найден заголовок, извлекаем текст
            product_text = product_header.get_text().strip()
            product_info["product_name"] = product_text

            # Ищем номер модели (может быть в конце после пробела, дефиса или цифры)
            model_patterns = [
                r"[-–]\s*(\d+)\s*$",  # После дефиса в конце
                r"\s+(\d+)\s*$",       # После пробела в конце
                r"(\d+)$",             # Просто цифры в конце
                r"for alternator (\d+)", # После фразы "for alternator"
                r"(\d{5,})"            # Любая последовательность из 5+ цифр
            ]
            
            for pattern in model_patterns:
                model_match = re.search(pattern, product_text, re.IGNORECASE)
                if model_match:
                    product_info["model"] = model_match.group(1)
                    logger.info(f"Извлечен номер модели с помощью шаблона '{pattern}': {model_match.group(1)}")
                    break

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
        # logger.info(f"Извлеченная информация о продукте: {product_info}")
        data.update(product_info)

        # Извлекаем атрибуты продукта из блока атрибутов
        attributes_from_product = self.extract_product_attributes()
        # logger.info(f"Извлеченные атрибуты из блока продукта: {attributes_from_product}")
        data.update(attributes_from_product)
        
        # Извлекаем атрибуты из блока описания независимо
        attributes_from_description = self.extract_attributes_from_description()
        # logger.info(f"Извлеченные атрибуты из блока описания: {attributes_from_description}")
        
        # Добавляем только те атрибуты из описания, которые еще не были добавлены
        for key, value in attributes_from_description.items():
            if key not in data:
                data[key] = value
                # logger.info(f"Добавлен атрибут из описания: {key} = {value}")

        # Извлекаем референсные номера
        reference_numbers = self.extract_reference_numbers()
        if reference_numbers:
            data["reference_numbers"] = reference_numbers
            logger.info(f"Извлечено {len(reference_numbers)} групп референсных номеров")

        # Извлекаем применения
        applications = self.extract_applications()
        if applications:
            data["applications"] = applications
            logger.info(f"Извлечено {len(applications)} применений")

        # Добавляем информацию об изображениях
        images = self.extract_images()
        if images:
            data["images"] = images
            # logger.info(f"Извлечено {len(images)} изображений")

        # logger.info(f"Итоговые данные: {data.keys()}")
        return data