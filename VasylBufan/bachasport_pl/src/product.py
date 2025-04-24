# /src/product.py
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from config.logger import logger
from src.utils import extract_csrf_token, fetch_html, get_soup, random_pause

# Получаем текущую директорию и пути
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = data_directory / "xml"
xml_directory.mkdir(parents=True, exist_ok=True)


def extract_product_id(product_url: str) -> Optional[str]:
    """
    Извлекает ID продукта из URL.

    Args:
        product_url (str): URL страницы продукта.

    Returns:
        Optional[str]: ID продукта или None, если не удалось извлечь.
    """
    try:
        # Метод 1: Поиск по параметру first_id в URL
        match = re.search(r"first_id=(\d+)", product_url)
        if match:
            return match.group(1)

        # Метод 2: Поиск по пути /product-details/НАЗВАНИЕ/UUID
        match = re.search(r"/product-details/[^/]+/([^/?]+)", product_url)
        if match:
            return match.group(1)

        logger.warning(f"Не удалось извлечь ID продукта из URL: {product_url}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении ID продукта: {e}")
        return None


def get_product_details(
    session: requests.Session, product_url: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Получает детали продукта и его XML.

    Args:
        session (requests.Session): Сессия для выполнения запросов.
        product_url (str): URL страницы продукта.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: Кортеж (ID продукта, путь к XML файлу, доступность) или (None, None, None) в случае ошибки.
    """
    try:
        # Получаем HTML страницы продукта
        html = fetch_html(session, product_url)
        if not html:
            logger.error(f"Не удалось получить HTML страницы продукта: {product_url}")
            return None, None, None

        # Извлекаем ID продукта
        product_id_from_url = extract_product_id(product_url)

        # Находим ID продукта на странице (более надежный способ)
        soup = get_soup(html)
        result = extract_product_id_from_page(soup, product_id_from_url)

        # Распаковываем результат с проверкой
        if isinstance(result, tuple) and len(result) == 2:
            product_id, availability = result
        else:
            product_id = result
            availability = None

        if not product_id:
            logger.error(f"Не удалось определить ID продукта: {product_url}")
            return None, None, None

        logger.info(f"Извлечен ID продукта: {product_id}")

        # Извлекаем CSRF токен для запроса XML
        csrf_token = extract_csrf_token(html)
        if not csrf_token:
            logger.error(f"Не удалось извлечь CSRF токен для продукта: {product_id}")
            return product_id, None, availability

        # Скачиваем XML продукта
        xml_path = download_product_xml(session, product_id, csrf_token)

        return product_id, xml_path, availability
    except Exception as e:
        logger.error(f"Ошибка при получении деталей продукта {product_url}: {e}")
        return None, None, None


def extract_product_id_from_page(
    soup: BeautifulSoup, fallback_id: Optional[str] = None
) -> Union[str, Tuple[str, str]]:
    """
    Извлекает ID продукта и информацию о доступности из страницы продукта.

    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-кодом страницы.
        fallback_id (Optional[str]): Резервный ID продукта, если не удается найти на странице.

    Returns:
        Union[str, Tuple[str, str]]: ID продукта или кортеж (ID продукта, доступность)
    """
    try:
        # Поиск по скрытым полям формы
        product_id_input = soup.find("input", {"name": "product_id"})
        product_id = None

        if product_id_input and product_id_input.get("value"):
            product_id = product_id_input.get("value")

        # Проверяем наличие таблицы с информацией о продукте
        availability_text = None
        try:
            table = soup.find("table", {"class": "table table-striped"})
            if table:
                # Сначала ищем строку с заголовком "Dostępność"
                availability_row = None
                for tr in table.find_all("tr"):
                    th = tr.find("th")
                    if th and "Dostępność" in th.text:
                        availability_row = tr
                        break

                # Если нашли нужную строку, извлекаем значение из ячейки
                if availability_row:
                    td = availability_row.find("td")
                    if td:
                        availability_tag = td.find("span", {"class": "label"})
                        if availability_tag:
                            availability_text = availability_tag.get_text(strip=True)
        except Exception as e:
            logger.warning(f"Ошибка при извлечении информации о доступности: {e}")

        # Если ID не найден через скрытые поля, ищем по URL
        if not product_id:
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if "product" in href and "/b/" in href:
                    match = re.search(r"/product/(\d+)/b/", href)
                    if match:
                        product_id = match.group(1)
                        break

        # Если ID все еще не найден, используем резервный ID
        if not product_id:
            product_id = fallback_id

        # Возвращаем кортеж с ID и доступностью, если есть информация о доступности
        if availability_text:
            return product_id, availability_text

        # Иначе возвращаем только ID
        return product_id

    except Exception as e:
        logger.error(f"Ошибка при извлечении ID продукта из страницы: {e}")
        return fallback_id


def download_product_xml(
    session: requests.Session, product_id: str, csrf_token: str
) -> Optional[str]:
    """
    Скачивает XML продукта.

    Args:
        session (requests.Session): Сессия для выполнения запросов.
        product_id (str): ID продукта.
        csrf_token (str): CSRF токен.

    Returns:
        Optional[str]: Путь к сохраненному XML файлу или None в случае ошибки.
    """
    try:
        # Формируем URL для скачивания XML
        xml_url = f"https://panel.bachasport.pl/product/{product_id}/b/xml"

        # Подготавливаем параметры запроса
        params = {"_token": csrf_token, "product_id": product_id}

        # Формируем путь для сохранения файла
        xml_file_path = xml_directory / f"product_{product_id}.xml"

        # Выполняем запрос
        logger.info(f"Скачивание XML для продукта {product_id}")
        response = session.get(xml_url, params=params)

        if response.status_code == 200:
            # Проверяем, что ответ действительно содержит XML
            if "<" in response.text and ">" in response.text:
                # Сохраняем XML в файл
                with open(xml_file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.info(f"XML продукта {product_id} сохранен: {xml_file_path}")
                return str(xml_file_path)
            else:
                logger.error(f"Ответ не содержит XML для продукта {product_id}")
                return None
        else:
            logger.error(
                f"Ошибка при скачивании XML для продукта {product_id}: статус {response.status_code}"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при скачивании XML для продукта {product_id}: {e}")
        return None
