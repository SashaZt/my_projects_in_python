import random
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from config.logger import logger


def get_soup(html: str) -> BeautifulSoup:
    """
    Создает объект BeautifulSoup из HTML-кода.

    Args:
        html (str): HTML-код страницы.

    Returns:
        BeautifulSoup: Объект BeautifulSoup.
    """
    return BeautifulSoup(html, "lxml")


def fetch_html(session: requests.Session, url: str) -> Optional[str]:
    """
    Получает HTML-код страницы по указанному URL.

    Args:
        session (requests.Session): Сессия для выполнения запросов.
        url (str): URL страницы.

    Returns:
        Optional[str]: HTML-код страницы или None в случае ошибки.
    """
    try:
        response = session.get(url)
        if response.status_code == 200:
            logger.info(f"Успешно получен HTML с {url}")
            return response.text
        else:
            logger.error(
                f"Ошибка при получении HTML-кода страницы: {response.status_code}"
            )
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сетевого запроса при получении HTML: {e}")
        return None


def random_pause(min_seconds: int = 3, max_seconds: int = 10) -> int:
    """
    Выполняет случайную паузу в заданном диапазоне.

    Args:
        min_seconds (int): Минимальная длительность паузы (целое число).
        max_seconds (int): Максимальная длительность паузы (целое число).

    Returns:
        int: Фактическая длительность паузы.
    """
    if min_seconds > max_seconds:
        raise ValueError("min_seconds не может быть больше max_seconds")

    pause_duration = random.randint(min_seconds, max_seconds)
    logger.info(f"Пауза {pause_duration} секунд.")
    time.sleep(pause_duration)
    return pause_duration


def extract_csrf_token(html: str) -> Optional[str]:
    """
    Извлекает CSRF-токен из HTML-страницы.

    Args:
        html (str): HTML-код страницы.

    Returns:
        Optional[str]: CSRF-токен или None, если токен не найден.
    """
    try:
        soup = get_soup(html)
        token_input = soup.find("input", {"name": "_token"})

        if token_input and token_input.get("value"):
            return token_input.get("value")

        # Альтернативный способ - поиск в мета-тегах
        meta_token = soup.find("meta", {"name": "csrf-token"})
        if meta_token and meta_token.get("content"):
            return meta_token.get("content")

        logger.error("CSRF токен не найден в HTML")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении CSRF токена: {e}")
        return None
