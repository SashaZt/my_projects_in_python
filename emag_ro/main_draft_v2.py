import base64
import json
import sys
import time
from pathlib import Path

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

current_directory = Path.cwd()
log_directory = current_directory / "log"
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


def get_headers_session():

    # Данные для авторизации
    username = "resteqsp@gmail.com"
    password = "Q7Hd.ATGCc5$ym2"
    auth_string = f"{username}:{password}"
    base64_auth = base64.b64encode(auth_string.encode()).decode()

    # Заголовки запроса
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
    }
    api_url = "https://marketplace-api.emag.ro"
    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url, headers, session


api_url, headers, session = get_headers_session()


# Функция для создания черновика
def create_draft(product_data):

    # Проверка на наличие обязательных полей
    required_fields = ["id", "name", "part_number", "brand"]
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        logger.error(f"Missing mandatory fields: {', '.join(missing_fields)}")
        return {
            "isError": True,
            "message": f"Missing fields: {', '.join(missing_fields)}",
        }

    try:
        response = session.post(
            f"{api_url}/api/v1/draft", headers=headers, json=product_data
        )

        if response.status_code == 200:
            logger.info(
                f"Draft created successfully for product ID: {product_data['id']}"
            )
            return response.json()
        else:
            logger.error(
                f"Failed to create draft. Status code: {response.status_code}, Response: {response.text}"
            )
            return {
                "isError": True,
                "status_code": response.status_code,
                "message": response.text,
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {"isError": True, "message": str(e)}


# Пример данных для черновика
product_example = {
    "id": 17006903216,
    "name": "Test Product",
    "part_number": "ABC123",
    "brand": "BrandName",
    "ean": "5906476016758",
    "category_id": 100,
    "source_language": "ro_RO",
}

# Создание черновика
response = create_draft(product_example)
logger.info(response)
