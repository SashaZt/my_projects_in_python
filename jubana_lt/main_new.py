import os
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Union
import json
import re
from pathlib import Path
import re
from html import unescape
import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "jubana.html"


class ProductDataExtractor:
    def __init__(self):
        self.soup = None
    
    def parse_html(self, html_content):
        """Инициализирует парсер BeautifulSoup с HTML-контентом"""
        self.soup = BeautifulSoup(html_content, 'html.parser')
        return self
    
    def extract_product_attributes(self):
        """Извлекает атрибуты продукта из блока класса product-attributes"""
        attributes = {}
        
        if not self.soup:
            logger.error("HTML не был инициализирован")
            return attributes
        
        # Ищем блок с атрибутами продукта
        attribute_divs = self.soup.select('.product-attribute')
        
        if not attribute_divs:
            logger.warning("Блок атрибутов продукта не найден")
            # Попробуем извлечь из текста в разделе описания
            return self.extract_attributes_from_description()
        
        # Обрабатываем каждый атрибут
        for attr_div in attribute_divs:
            # Получаем имя атрибута
            name_div = attr_div.select_one('.product-attribute-name')
            if not name_div:
                continue
            
            # Очищаем имя от лишних пробелов
            attribute_name = name_div.get_text().strip()
            
            # Получаем значение атрибута
            value_div = attr_div.select_one('.product-attribute-value')
            if not value_div:
                continue
                
            # Очищаем значение от лишних пробелов
            attribute_value = value_div.get_text().strip()
            
            # Преобразуем имя атрибута в ключ словаря
            key = attribute_name.lower().replace(' ', '_')
            
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
        description_div = self.soup.select_one('.tabs-description')
        if not description_div:
            logger.warning("Блок описания не найден")
            return attributes
        
        # Ищем параграфы с маркированными списками
        bullet_paragraphs = description_div.find_all('p', string=lambda text: text and '•' in text if text else False)
        
        for p in bullet_paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
                
            # Разбиваем текст на строки по маркеру списка
            lines = [line.strip() for line in text.split('•') if line.strip()]
            
            for line in lines:
                # Ищем разделители между названием и значением (обычно ":" или разделение с помощью тега <strong>)
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(' ', '_')
                        value = parts[1].strip()
                        attributes[key] = value
                
                # Если в параграфе есть теги <strong>, ищем их
                strong_tags = p.find_all('strong')
                for strong in strong_tags:
                    if strong.next_sibling and ':' in str(strong.next_sibling):
                        key = strong.get_text().strip().lower().replace(' ', '_')
                        value_text = str(strong.next_sibling).split(':', 1)[1].strip()
                        attributes[key] = value_text
        
        return attributes
    
    def extract_reference_numbers(self):
        """Извлекает референсные номера из таблицы"""
        reference_numbers = {}
        
        if not self.soup:
            logger.error("HTML не был инициализирован")
            return reference_numbers
        
        # Ищем заголовок с текстом "REFERENCE NUMBERS"
        ref_header = self.soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'REFERENCE NUMBERS' in tag.get_text())
        
        if not ref_header:
            logger.warning("Заголовок REFERENCE NUMBERS не найден")
            return reference_numbers
        
        # Ищем таблицу после заголовка
        table = ref_header.find_next('table')
        
        if not table:
            logger.warning("Таблица с референсными номерами не найдена")
            return reference_numbers
        
        # Получаем все строки таблицы (пропускаем заголовок)
        rows = table.find_all('tr')[1:] if table.find_all('tr') else []
        
        for row in rows:
            cells = row.find_all('td')
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
        app_header = self.soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'APPLICATIONS' in tag.get_text())
        
        if not app_header:
            logger.warning("Заголовок APPLICATIONS не найден")
            return applications
        
        # Ищем таблицу после заголовка
        table = app_header.find_next('table')
        
        if not table:
            logger.warning("Таблица с применениями не найдена")
            return applications
        
        # Получаем заголовки столбцов
        headers_row = table.find('tr')
        if not headers_row:
            logger.warning("В таблице применений не найдены заголовки")
            return applications
            
        headers = [th.get_text().strip() for th in headers_row.find_all('th')]
        
        # Получаем все строки таблицы (пропускаем заголовок)
        rows = table.find_all('tr')[1:] if table.find_all('tr') else []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                application = {}
                
                for i, header in enumerate(headers):
                    key = header.lower().strip().replace(' ', '_')
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
        product_header = self.soup.find('h2')
        
        if product_header:
            product_text = product_header.get_text().strip()
            product_info['product_name'] = product_text
            
            # Ищем номер модели (обычно после дефиса)
            model_match = re.search(r'[-–]\s*(\d+)\s*$', product_text)
            if model_match:
                product_info['model'] = model_match.group(1)
        
        return product_info
    
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
            data['reference_numbers'] = reference_numbers
        
        # Извлекаем применения
        applications = self.extract_applications()
        if applications:
            data['applications'] = applications
        
        return data

def process_html_file(html_content: str) -> Dict[str, Any]:
    """
    Обрабатывает HTML файл и извлекает структурированные данные
    
    Args:
        html_content (str): Содержимое HTML файла
        
    Returns:
        dict: Структурированные данные о продукте
    """
    try:
        extractor = ProductDataExtractor()
        extractor.parse_html(html_content)
        result = extractor.extract_all_data()
        return result
    except Exception as e:
        logger.error(f"Ошибка при обработке HTML файла: {e}")
        return {}

def convert_to_json(data: Dict[str, Any]) -> str:
    """
    Преобразует извлеченные данные в JSON формат
    
    Args:
        data (dict): Извлеченные данные
        
    Returns:
        str: Данные в формате JSON
    """
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при преобразовании в JSON: {e}")
        return "{}"

def load_json_data(json_content: str) -> Dict[str, Any]:
    """
    Загружает данные из JSON строки
    
    Args:
        json_content (str): Содержимое JSON файла
        
    Returns:
        dict: Загруженные данные
    """
    try:
        # Проверяем, если json_content - это строка, содержащая json в виде строки
        # (такое может произойти, если JSON был сохранен как строка внутри JSON)
        if json_content.startswith('"') and json_content.endswith('"'):
            # Удаляем внешние кавычки и экранированные символы
            json_content = json_content[1:-1].replace('\\n', '\n').replace('\\"', '"')
        
        return json.loads(json_content)
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON: {e}")
        return {}

def process_directory(html_directory: str, output_directory: str) -> None:
    """
    Обрабатывает все HTML файлы в указанной директории и сохраняет результаты в JSON
    
    Args:
        html_directory (str): Путь к директории с HTML файлами
        output_directory (str): Путь к директории для сохранения JSON
    """
    html_path = Path(html_directory)
    output_path = Path(output_directory)
    
    # Создаем выходную директорию, если не существует
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Обрабатываем все HTML файлы
    for html_file in html_path.glob("*.html"):
        try:
            logger.info(f"Обработка файла: {html_file}")
            
            # Создаем имя выходного файла
            output_json_file = output_path / f"{html_file.stem}.json"
            
            # Читаем HTML файл
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Обрабатываем HTML и извлекаем данные
            product_data = process_html_file(content)
            
            # Сохраняем результат в JSON файл
            with open(output_json_file, "w", encoding="utf-8") as json_file:
                json.dump(product_data, json_file, ensure_ascii=False, indent=4)
                
            logger.info(f"Файл успешно обработан и сохранен: {output_json_file}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file}: {e}")

def extract_product_info_from_json(json_path: str) -> Dict[str, Any]:
    """
    Извлекает информацию о продукте из JSON файла
    
    Args:
        json_path (str): Путь к JSON файлу
        
    Returns:
        dict: Структурированные данные о продукте
    """
    try:
        # Проверяем, существует ли файл
        json_file = Path(json_path)
        if not json_file.exists():
            logger.error(f"Файл не найден: {json_path}")
            return {}
        
        # Читаем JSON файл
        with open(json_file, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Загружаем данные из JSON
        data = load_json_data(content)
        
        return data
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных из JSON файла: {e}")
        return {}
def extract_product_images(html_content: str) -> List[Dict[str, str]]:
    """
    Извлекает информацию о фотографиях продукта из HTML.
    
    Args:
        html_content (str): HTML содержимое страницы
        
    Returns:
        List[Dict[str, str]]: Список словарей с информацией о фотографиях
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        images = []
        
        # Ищем все изображения в галерее продукта
        gallery_images = soup.select('.gallery-container .product-gallery-element')
        
        for img in gallery_images:
            image_info = {
                'title': img.get('title', ''),
                'alt': img.get('alt', ''),
                'src': img.get('src', ''),
                'data_src': img.get('data-src', '')  # Часто содержит ссылку на большое изображение
            }
            
            # Если есть родительский элемент source, добавляем информацию о разных размерах
            source_parent = img.parent.find('source')
            if source_parent and source_parent.has_attr('srcset'):
                srcset = source_parent['srcset']
                # Разбираем srcset на отдельные изображения разных размеров
                srcset_parts = srcset.split(',')
                resolutions = {}
                
                for part in srcset_parts:
                    part = part.strip()
                    if part:
                        # Обычно формат: URL 1x или URL 2x или URL 3x
                        url_resolution = part.split(' ')
                        if len(url_resolution) >= 2:
                            url = url_resolution[0]
                            resolution = url_resolution[1]
                            resolutions[resolution] = url
                
                if resolutions:
                    image_info['resolutions'] = resolutions
            
            # Добавляем только если есть хотя бы URL изображения
            if image_info['src'] or image_info['data_src']:
                # Удаляем дубликаты изображений, проверяя по URL
                if not any(img_info['src'] == image_info['src'] for img_info in images):
                    images.append(image_info)
        
        # Если в галерее не нашли изображения, ищем на всей странице
        if not images:
            all_images = soup.select('img')
            for img in all_images:
                # Фильтруем только изображения продукта (обычно имеют определенные классы или атрибуты)
                if 'product' in img.get('class', '') or 'gallery' in img.get('class', '') or 'item' in img.get('class', ''):
                    image_info = {
                        'title': img.get('title', ''),
                        'alt': img.get('alt', ''),
                        'src': img.get('src', ''),
                        'data_src': img.get('data-src', '')
                    }
                    
                    # Добавляем только если есть хотя бы URL изображения
                    if image_info['src'] or image_info['data_src']:
                        # Удаляем дубликаты
                        if not any(img_info['src'] == image_info['src'] for img_info in images):
                            images.append(image_info)
        
        # Обрабатываем thumbnails (миниатюры), если они есть отдельно
        thumbnail_images = soup.select('.gallery-container-thumbnails img')
        thumbnail_info = []
        
        for thumbnail in thumbnail_images:
            thumb_info = {
                'title': thumbnail.get('title', ''),
                'alt': thumbnail.get('alt', ''),
                'src': thumbnail.get('src', ''),
                'data_item_index': thumbnail.get('data-item-index', '')
            }
            
            # Добавляем только если есть хотя бы URL миниатюры
            if thumb_info['src']:
                thumbnail_info.append(thumb_info)
        
        # Если нашли миниатюры, добавляем их к результату
        if thumbnail_info:
            return {'main_images': images, 'thumbnails': thumbnail_info}
        
        return images
    except Exception as e:
        logger.error(f"Ошибка при извлечении фотографий продукта: {e}")
        return []

def download_product_images(image_info: Union[List[Dict[str, str]], Dict[str, Any]], output_dir: str, product_id: str = None) -> List[str]:
    """
    Скачивает фотографии продукта по информации из extract_product_images.
    
    Args:
        image_info: Информация об изображениях (из extract_product_images)
        output_dir (str): Директория для сохранения изображений
        product_id (str, optional): ID продукта для именования файлов
        
    Returns:
        List[str]: Список путей к скачанным изображениям
    """
    import requests
    from urllib.parse import urlparse
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    downloaded_files = []
    
    try:
        # Проверяем, получили ли мы словарь с main_images и thumbnails или только список изображений
        if isinstance(image_info, dict) and 'main_images' in image_info:
            images = image_info['main_images']
        else:
            images = image_info
        
        for idx, img_data in enumerate(images):
            # Используем data_src если доступен, иначе src
            img_url = img_data.get('data_src') or img_data.get('src')
            
            if not img_url:
                continue
                
            # Проверяем, является ли URL относительным
            if not img_url.startswith(('http://', 'https://')):
                # Для относительных URL нужно добавить базовый URL сайта
                # Предполагаем, что базовый URL - jubana.lt
                base_url = "https://www.jubana.lt"
                if not img_url.startswith('/'):
                    img_url = '/' + img_url
                img_url = base_url + img_url
            
            # Получаем расширение файла из URL
            path_parts = urlparse(img_url).path.split('/')
            if '.' in path_parts[-1]:
                ext = path_parts[-1].split('.')[-1]
                if '?' in ext:  # Удаляем параметры запроса из расширения
                    ext = ext.split('?')[0]
            else:
                ext = 'jpg'  # По умолчанию jpg
            
            # Формируем имя файла
            if product_id:
                filename = f"{product_id}_{idx+1}.{ext}"
            else:
                # Если product_id не указан, используем часть URL или title/alt
                name_base = img_data.get('title') or img_data.get('alt') or f"product_{idx+1}"
                # Очищаем имя файла от недопустимых символов
                name_base = ''.join(c for c in name_base if c.isalnum() or c in [' ', '_', '-'])
                name_base = name_base.replace(' ', '_')
                filename = f"{name_base}.{ext}"
            
            file_path = output_path / filename
            
            # Скачиваем изображение
            try:
                response = requests.get(img_url,timeout=30, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded_files.append(str(file_path))
                    logger.info(f"Скачано изображение: {file_path}")
                else:
                    logger.warning(f"Не удалось скачать изображение {img_url}. Код ответа: {response.status_code}")
            except Exception as e:
                logger.error(f"Ошибка при скачивании изображения {img_url}: {e}")
        
        # Если у нас также есть thumbnails, скачаем и их
        if isinstance(image_info, dict) and 'thumbnails' in image_info:
            thumbnails_dir = output_path / 'thumbnails'
            thumbnails_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, thumb_data in enumerate(image_info['thumbnails']):
                thumb_url = thumb_data.get('src')
                
                if not thumb_url:
                    continue
                
                # Проверяем, является ли URL относительным
                if not thumb_url.startswith(('http://', 'https://')):
                    base_url = "https://www.jubana.lt"
                    if not thumb_url.startswith('/'):
                        thumb_url = '/' + thumb_url
                    thumb_url = base_url + thumb_url
                
                # Получаем расширение файла из URL
                path_parts = urlparse(thumb_url).path.split('/')
                if '.' in path_parts[-1]:
                    ext = path_parts[-1].split('.')[-1]
                    if '?' in ext:
                        ext = ext.split('?')[0]
                else:
                    ext = 'jpg'
                
                # Формируем имя файла
                if product_id:
                    filename = f"{product_id}_thumb_{idx+1}.{ext}"
                else:
                    name_base = thumb_data.get('title') or thumb_data.get('alt') or f"thumbnail_{idx+1}"
                    name_base = ''.join(c for c in name_base if c.isalnum() or c in [' ', '_', '-'])
                    name_base = name_base.replace(' ', '_')
                    filename = f"{name_base}.{ext}"
                
                file_path = thumbnails_dir / filename
                
                # Скачиваем миниатюру
                try:
                    response = requests.get(thumb_url, stream=True)
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        downloaded_files.append(str(file_path))
                        logger.info(f"Скачана миниатюра: {file_path}")
                    else:
                        logger.warning(f"Не удалось скачать миниатюру {thumb_url}. Код ответа: {response.status_code}")
                except Exception as e:
                    logger.error(f"Ошибка при скачивании миниатюры {thumb_url}: {e}")
        
        return downloaded_files
    except Exception as e:
        logger.error(f"Ошибка при скачивании изображений: {e}")
        return downloaded_files

def integrate_image_extraction_in_product_extractor(extractor_class):
    """
    Интегрирует функцию извлечения изображений в класс ProductDataExtractor.
    
    Args:
        extractor_class: Класс ProductDataExtractor для расширения
    """
    # Добавляем метод извлечения изображений в класс
    def extract_images(self):
        """Извлекает информацию о фотографиях продукта"""
        if not self.soup:
            logger.error("HTML не был инициализирован")
            return []
        
        return extract_product_images(str(self.soup))
    
    # Добавляем метод в класс
    extractor_class.extract_images = extract_images
    
    # Расширяем метод extract_all_data для включения информации об изображениях
    original_extract_all_data = extractor_class.extract_all_data
    
    def extended_extract_all_data(self):
        """Расширенная версия extract_all_data, которая включает информацию об изображениях"""
        data = original_extract_all_data(self)
        
        # Добавляем информацию об изображениях
        images = self.extract_images()
        if images:
            data['images'] = images
        
        return data
    
    # Заменяем оригинальный метод на расширенный
    extractor_class.extract_all_data = extended_extract_all_data
    
    return extractor_class
# Обновляем класс ProductDataExtractor
ProductDataExtractor = integrate_image_extraction_in_product_extractor(ProductDataExtractor)
def create_product_database(json_directory: str, output_file: str) -> None:
    """
    Создает базу данных продуктов из нескольких JSON файлов
    
    Args:
        json_directory (str): Путь к директории с JSON файлами
        output_file (str): Путь к выходному файлу базы данных
    """
    json_path = Path(json_directory)
    products = []
    
    # Обрабатываем все JSON файлы
    for json_file in json_path.glob("*.json"):
        try:
            logger.info(f"Добавление продукта из файла: {json_file}")
            
            # Извлекаем данные из JSON файла
            product_data = extract_product_info_from_json(json_file)
            
            if product_data:
                products.append(product_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {json_file}: {e}")
    
    # Сохраняем базу данных в файл
    with open(output_file, "w", encoding="utf-8") as db_file:
        json.dump(products, db_file, ensure_ascii=False, indent=4)
    
    logger.info(f"База данных успешно создана и сохранена в {output_file}")

# Функция для удобного использования в скрипте
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Извлечение данных о продуктах из HTML и создание JSON базы данных")
    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")
    
    # Парсер для обработки HTML файлов
    html_parser = subparsers.add_parser("html", help="Обработка HTML файлов")
    html_parser.add_argument("html_directory", help="Директория с HTML файлами")
    html_parser.add_argument("output_directory", help="Директория для сохранения JSON")
    
    # Парсер для создания базы данных из JSON файлов
    db_parser = subparsers.add_parser("db", help="Создание базы данных из JSON файлов")
    db_parser.add_argument("json_directory", help="Директория с JSON файлами")
    db_parser.add_argument("output_file", help="Выходной файл базы данных")
    
    # Парсер для обработки одного файла
    file_parser = subparsers.add_parser("file", help="Обработка одного файла")
    file_parser.add_argument("input_file", help="Входной файл (HTML или JSON)")
    file_parser.add_argument("output_file", help="Выходной файл JSON")
    
    args = parser.parse_args()
    
    if args.command == "html":
        process_directory(args.html_directory, args.output_directory)
    elif args.command == "db":
        create_product_database(args.json_directory, args.output_file)
    elif args.command == "file":
        input_file = Path(args.input_file)
        if input_file.suffix.lower() == ".html":
            with open(input_file, "r", encoding="utf-8") as file:
                content = file.read()
            product_data = process_html_file(content)
            with open(args.output_file, "w", encoding="utf-8") as json_file:
                json.dump(product_data, json_file, ensure_ascii=False, indent=4)
        elif input_file.suffix.lower() == ".json":
            product_data = extract_product_info_from_json(input_file)
            with open(args.output_file, "w", encoding="utf-8") as json_file:
                json.dump(product_data, json_file, ensure_ascii=False, indent=4)
        else:
            logger.error(f"Неподдерживаемый формат файла: {input_file}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()