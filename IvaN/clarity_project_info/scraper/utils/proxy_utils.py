# /utils/proxy_utils.py
import random
from pathlib import Path
from typing import Dict, List, Optional

from config.logger import logger

from config.config import PROXY_HOST, PROXY_PORT


def load_proxies(file_path: Path) -> List[str]:
    """
    Загружает список прокси-серверов из файла или использует настройки из конфигурации.
    """
    # Если указан прокси в настройках, используем его с уникальным параметром
    if PROXY_HOST and PROXY_PORT:
        proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
        logger.info(f"Используется прокси из конфигурации: {proxy_url}")
        return [proxy_url]

    # Иначе загружаем список прокси из файла
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file if line.strip()]
        logger.info(f"Загружено {len(proxies)} прокси из файла")
        return proxies
    else:
        logger.warning("Файл с прокси не найден. Работаем без прокси.")
        return []


def get_random_proxy(proxies: List[str]) -> Optional[Dict[str, str]]:
    """
    Возвращает прокси для запроса.
    Если используется прокси из конфигурации, добавляет уникальный параметр.
    """
    if not proxies:
        return None

    if PROXY_HOST and PROXY_PORT:
        # Используем конфигурационный прокси
        proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}?r={random.randint(1, 1000000)}"
        return {"http": proxy_url, "https": proxy_url}
    else:
        # Иначе выбираем случайный из списка
        proxy = random.choice(proxies)
        return {"http": proxy, "https": proxy}
