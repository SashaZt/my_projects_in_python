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
data_directory = current_directory / "data"
log_directory = current_directory / "log"


data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
category_file_path = data_directory / "category.json"

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
        "Accept": "application/json",
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
    }
    api_url_draft = "https://marketplace-api.emag.ro"
    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url_draft, headers, session


api_url_draft, headers, session = get_headers_session()


# Функция для создания черновика
def get_draft():

    try:
        response = session.get(
            f"{api_url_draft}/api/v1/draft", headers=headers, timeout=30
        )

        if response.status_code == 200:
            with open("draft_get.json", "w") as f:
                json.dump(response.json(), f)
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
            f"{api_url_draft}/api/v1/draft", headers=headers, json=product_data
        )

        if response.status_code == 200:
            logger.info(
                f"Draft created successfully for product ID: {product_data['id']}"
            )
            return response.json()
        else:
            return {
                "isError": True,
                "status_code": response.status_code,
                "message": response.text,
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {"isError": True, "message": str(e)}


# Функция для создания черновика
def updates_draft(product_data):

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
            f"{api_url_draft}/api/v1/draft", headers=headers, json=product_data
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


def get_category():
    api_url = "https://marketplace-api.emag.ro/api-3"
    # Параметры пагинации
    current_page = 1
    items_per_page = 100  # Максимальное количество элементов на странице
    all_results = []

    while True:
        data = {"data": {"currentPage": current_page, "itemsPerPage": items_per_page}}

        response = session.post(
            f"{api_url}/category/read", headers=headers, json=data, timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Ошибка {response.status_code}: {response.text}")
            break

        response_data = response.json()

        if response_data.get("isError"):
            logger.error(f"Ошибка API: {response_data.get('messages')}")
            break

        results = response_data.get("results", [])
        if not results:
            break  # Прекращаем, если больше нет данных

        all_results.extend(results)
        logger.info(f"Загружено {len(all_results)} категорий...")

        current_page += 1

    # Сохранение всех данных в файл
    with open(category_file_path, "w", encoding="utf-8") as json_file:
        json.dump(all_results, json_file, ensure_ascii=False, indent=4)

    logger.info(f"Всего загружено {len(all_results)} категорий")


if __name__ == "__main__":
    # get_category()

    # Пример данных для черновика
    product_example = {
        "id": "1234565",  # Обязательное
        "name": "Test product",  # Обязательное
        "brand": "Brand name",  # Обязательное
        "part_number": "md788hc/aA",  # Обязательное
        "category_id": "58",  # Опционально
        "ean": "5906476016758",  # Опционально
        "source_language": "pl_PL",  # Опционально
    }
    # get_draft()
    # # Создание черновика
    response = create_draft(product_example)
    logger.info(response)
