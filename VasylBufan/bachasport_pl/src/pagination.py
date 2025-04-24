# /src/pagination.py
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from config.logger import logger
from src.utils import fetch_html, get_soup, random_pause


def get_product_urls_from_category(
    session: requests.Session, category_url: str, max_pages: int = 10
) -> List[str]:
    """
    Получает все URL продуктов из категории, учитывая пагинацию.

    Args:
        session (requests.Session): Сессия для выполнения запросов.
        category_url (str): URL категории.
        max_pages (int): Максимальное количество страниц для обработки.

    Returns:
        List[str]: Список URL продуктов.
    """
    all_product_urls = []
    current_url = category_url
    current_page = 1

    # Добавляем параметры для большего количества продуктов на странице
    if "?" in current_url:
        current_url += "&perPage=200"
    else:
        current_url += "?perPage=200"

    while current_page <= max_pages:
        logger.info(f"Обработка страницы {current_page} категории: {current_url}")

        html = fetch_html(session, current_url)
        if not html:
            logger.error(f"Не удалось получить HTML для страницы {current_page}")
            break

        soup = get_soup(html)

        # Извлекаем URL продуктов с текущей страницы
        product_urls = extract_product_urls_from_page(soup)
        logger.info(f"Найдено {len(product_urls)} продуктов на странице {current_page}")
        all_product_urls.extend(product_urls)

        # Находим ссылку на следующую страницу
        next_page_url = get_next_page_url(soup)
        if not next_page_url:
            logger.info(f"Достигнута последняя страница категории ({current_page})")
            break

        current_url = next_page_url
        current_page += 1

        # Делаем паузу между запросами страниц пагинации
        random_pause(1, 3)

    logger.info(f"Всего найдено {len(all_product_urls)} продуктов в категории")
    return all_product_urls


def extract_product_urls_from_page(soup: BeautifulSoup) -> List[str]:
    """
    Извлекает URL продуктов со страницы категории.

    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-кодом страницы.

    Returns:
        List[str]: Список URL продуктов.
    """
    product_urls = []
    try:
        # Находим таблицу с продуктами
        table_div = soup.find("div", {"class": "table-responsive double-scroll"})
        if not table_div:
            logger.warning("Не найдена таблица с продуктами")
            return product_urls

        # Находим все строки таблицы с продуктами
        rows = table_div.find_all("tr")

        for row in rows:
            # Проверяем наличие ячеек с данными
            cells = row.find_all("td")
            if not cells:
                continue  # Пропускаем заголовок таблицы или пустые строки

            # Ищем ссылки во всех ячейках строки
            # a_tags = row.find_all("a")

            for a_tag in cells:
                href = a_tag.get("href")
                if href and "product-details" in href:
                    # Убедимся, что URL абсолютный
                    if not href.startswith("http"):
                        href = f"https://panel.bachasport.pl{href}"

                    # Добавляем только уникальные URL
                    if href not in product_urls:
                        product_urls.append(href)

        # Если не нашли ни одной ссылки, возможно структура страницы другая
        if not product_urls:
            logger.warning(
                "Не найдены ссылки на продукты в таблице. Пробуем альтернативный метод."
            )
            # Ищем все ссылки, содержащие "product-details"
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href")
                if href and "product-details" in href:
                    # Убедимся, что URL абсолютный
                    if not href.startswith("http"):
                        href = f"https://panel.bachasport.pl{href}"

                    # Добавляем только уникальные URL
                    if href not in product_urls:
                        product_urls.append(href)

        logger.info(f"Найдено {len(product_urls)} ссылок на продукты")
        return product_urls
    except Exception as e:
        logger.error(f"Ошибка при извлечении URL продуктов: {e}")
        return product_urls


def get_next_page_url(soup: BeautifulSoup) -> Optional[str]:
    """
    Находит URL следующей страницы пагинации.

    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-кодом страницы.

    Returns:
        Optional[str]: URL следующей страницы или None, если следующей страницы нет.
    """
    try:
        # Ищем пагинацию
        pagination = soup.find("ul", {"class": "pagination"})
        if not pagination:
            return None

        # Ищем ссылку с атрибутом rel="next"
        next_link = pagination.find("a", {"rel": "next"})
        if next_link and next_link.get("href"):
            next_url = next_link.get("href")

            # Убедимся, что URL абсолютный
            if not next_url.startswith("http"):
                next_url = f"https://panel.bachasport.pl{next_url}"

            return next_url

        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске URL следующей страницы: {e}")
        return None
