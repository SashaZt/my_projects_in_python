import base64
import json
import re
import sys
import time
from pathlib import Path

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

current_directory = Path.cwd()
log_directory = current_directory / "log"
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
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
    api_url = "https://marketplace-api.emag.ro/api-3"

    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url, headers, session


# Получаем сессию и заголовки
api_url, headers, session = get_headers_session()


def validate_product_data(product):
    """Проверка обязательных полей продукта"""
    required_fields = [
        "id",
        "category_id",
        "name",
        "part_number",
        "brand",
        "description",
        "status",
        "sale_price",
        "vat_id",
        "stock",
        "handling_time",
    ]

    missing_fields = [field for field in required_fields if field not in product]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Проверка характеристик
    if "characteristics" in product:
        for char in product["characteristics"]:
            if not all(key in char for key in ["id", "value"]):
                raise ValueError("Invalid characteristic format")

    # Проверка stock
    if not isinstance(product["stock"], list) or not product["stock"]:
        raise ValueError("Stock must be a non-empty list")

    # Проверка handling_time
    if not isinstance(product["handling_time"], list) or not product["handling_time"]:
        raise ValueError("Handling time must be a non-empty list")


def get_vat_rates():
    response = session.post(f"{api_url}/vat/read", headers=headers)
    vat_rates = response.json()
    # Сохраняем vat_rates в файл vat_rates.json
    vat_rates_file_path = current_directory / "vat_rates.json"
    with open(vat_rates_file_path, "w", encoding="utf-8") as vat_file:
        json.dump(vat_rates, vat_file, ensure_ascii=False, indent=4)


def clean_description(description):
    # Паттерн для поиска img тегов с base64
    pattern = (
        r'<img[^>]*?class="lazy"[^>]*?data-src="([^"]*)"[^>]*?src="data:image[^>]*?>'
    )

    # Замена на чистый img тег
    cleaned = re.sub(pattern, r'<img src="\1" alt="Product Image"/>', description)

    # Убираем пустые атрибуты
    cleaned = re.sub(r'\s+(?:height|width|style|align)=["\']\s*["\']', "", cleaned)

    return cleaned


def upload_product(product_data):
    try:

        # Проверяем наличие ключа data и что это список
        if not isinstance(product_data.get("data"), list):
            raise ValueError("Data should be a list of products")

        # Проверяем каждый продукт в списке
        for product in product_data["data"]:
            validate_product_data(product)

        # Конвертируем строковые значения в числовые
        for product in product_data["data"]:
            product["id"] = int(product["id"])
            product["category_id"] = int(product["category_id"])
            product["status"] = int(product["status"])
            product["sale_price"] = float(product["sale_price"])
            product["min_sale_price"] = float(product["min_sale_price"])
            product["max_sale_price"] = float(product["max_sale_price"])
            product["vat_id"] = int(product["vat_id"])
            product["warranty"] = int(product["warranty"])

        # Отправляем запрос
        response = session.post(
            f"{api_url}/product_offer/save", headers=headers, json=product_data
        )
        # Вывести полный ответ для отладки
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")

        # Проверяем ответ
        response.raise_for_status()
        try:
            result = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            raise Exception("Invalid JSON response")

        # Проверяем на ошибки в ответе eMAG
        if result.get("isError"):
            error_messages = result.get("messages", [])
            raise Exception(f"eMAG API Error: {error_messages}")

        # Проверяем наличие документационных ошибок
        if "doc_errors" in result:
            logger.warning(f"Documentation errors: {result['doc_errors']}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        # Вывести больше информации об ошибке
        if hasattr(e, "response") and e.response:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        raise


def check_category_access(category_id):
    # В файле находим is_mandatory": 1 - категория обязательная

    try:
        response = session.post(
            f"{api_url}/category/read", headers=headers, json={"id": category_id}
        )
        data = response.json()
        output_json_file = data_directory / f"category_{category_id}.json"
        with open(output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Category data saved to {output_json_file}")

        return data.get("is_allowed", 0) == 1
    except Exception as e:
        logger.error(f"Category access check failed: {str(e)}")
        return False


# Проверка авторизации
def check_auth():
    try:
        # Простой запрос для проверки авторизации
        response = session.post(f"{api_url}/category/count", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Auth check failed: {str(e)}")
        return None


def main():
    # Выгрузка товара
    try:
        # Чтение данных о товаре из JSON-файла
        with open("product.json", "r", encoding="utf-8") as file:
            product_data = json.load(file)
        # Очистка описания
        product_data["data"][0]["description"] = clean_description(
            product_data["data"][0]["description"]
        )

        # Отправка продукта
        result = upload_product(product_data)
        logger.info("Product uploaded successfully!")
        logger.info(f"Response: {json.dumps(result, indent=2)}")

    except Exception as e:
        logger.error(f"Error uploading product: {str(e)}")


if __name__ == "__main__":
    main()
    # check_category_access(3698)
