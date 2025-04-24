# /scr/category.py
from typing import List

import requests
from bs4 import BeautifulSoup
from config.logger import logger
from src.utils import fetch_html, get_soup


def get_category_urls(
    session: requests.Session, url: str = "https://panel.bachasport.pl/group/153l"
) -> List[str]:
    """
    Получает HTML стартовой страницы и извлекает из неё ссылки категорий для дальнейшего скрапинга.

    Args:
        session (requests.Session): Сессия для выполнения запросов.
        url (str): URL стартовой страницы.

    Returns:
        List[str]: Список URL категорий для скрапинга или пустой список в случае ошибки.
    """
    html = fetch_html(session, url)
    if html:
        soup = get_soup(html)
        urls = extract_category_urls(soup)
        logger.info(f"Получены URL категорий: {len(urls)} ссылок")
        return urls
    else:
        logger.error("Не удалось получить HTML стартовой страницы")
        return []


def extract_category_urls(soup: BeautifulSoup) -> List[str]:
    """
    Извлекает ссылки категорий для скрапинга из объекта BeautifulSoup.

    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-кодом страницы.

    Returns:
        List[str]: Список URL категорий для скрапинга.
    """
    urls = []
    try:
        # Находим нужное меню боковой панели
        urls_tag = soup.find("ul", attrs={"class": "treeview-menu menu-open"})
        if urls_tag:
            # Извлекаем все ссылки из меню
            for li in urls_tag.find_all("li"):
                a_tag = li.find("a")
                if a_tag and a_tag.get("href"):
                    url = a_tag.get("href")
                    url = f"https://panel.bachasport.pl/{url}"
                    urls.append(url)

            logger.info(f"Найдено {len(urls)} ссылок категорий")
        else:
            logger.warning("Не найден элемент с классом 'sidebar-menu sidebar-last'")

        return urls
    except Exception as e:
        logger.error(f"Ошибка при извлечении ссылок категорий: {e}")
        return urls
