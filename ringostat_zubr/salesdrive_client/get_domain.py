import json
from pathlib import Path
from urllib.parse import urlparse

from config.logger import logger

current_directory = Path.cwd()
file_sajt = current_directory / "sajt.json"


def load_sajt_options():
    """
    Загружает опции sajt из файла
    """
    try:
        if file_sajt.exists():
            with open(file_sajt, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.error(
                "Файл sajt.json не найден. Сначала выполните extract_and_save_sajt_options()"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке sajt.json: {e}")
        return None


def create_sajt_text_to_value_mapping():
    """
    Создает словарь для поиска value по text (домену)
    """
    sajt_options = load_sajt_options()
    if sajt_options:
        return {option["text"]: option["value"] for option in sajt_options}
    return {}


def extract_domain_from_utm_page(utm_page):
    """
    Извлекает домен из utmPage
    """
    if not utm_page:
        return None

    try:
        # Если URL не содержит схему, добавляем её
        if not utm_page.startswith(("http://", "https://")):
            utm_page = "https://" + utm_page

        parsed_url = urlparse(utm_page)
        domain = parsed_url.netloc

        # Убираем www. если есть
        if domain.startswith("www."):
            domain = domain[4:]

        return domain
    except Exception as e:
        logger.error(f"Ошибка при извлечении домена из {utm_page}: {e}")
        return None


def find_sajt_value_by_domain(domain, sajt_mapping):
    """
    Ищет value в sajt.json по домену
    """
    if not domain or not sajt_mapping:
        return None

    # Ищем точное совпадение
    if domain in sajt_mapping:
        return sajt_mapping[domain]

    # Ищем среди вариантов с https://
    https_domain = f"https://{domain}"
    if https_domain in sajt_mapping:
        return sajt_mapping[https_domain]

    # Ищем среди вариантов с www
    www_domain = f"www.{domain}"
    if www_domain in sajt_mapping:
        return sajt_mapping[www_domain]

    return None
