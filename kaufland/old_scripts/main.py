#
import json
import sys
from pathlib import Path

import requests
from loguru import logger

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_json_product(id_product):
    API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
    target_url = f"https://www.kaufland.de/api/pdp-frontend/v1/{id_product}/product"

    # Формируем URL для ScraperAPI
    scraper_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={target_url}"

    try:
        response = requests.get(scraper_url, verify=False, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        with open(f"{id_product}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        logger.info(f"Статус ответа: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе: {str(e)}")
        raise


if __name__ == "__main__":
    id_product = "512063298"
    get_json_product(id_product)
