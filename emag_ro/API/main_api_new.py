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
    try:
        response = session.post(
            f"{api_url}/category/read", headers=headers, json={"id": category_id}
        )
        data = response.json()
        logger.debug(f"Category access check response: {data}")
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


if __name__ == "__main__":
    # Пример использования
    try:
        # # В основном блоке перед отправкой продукта
        # if not check_category_access(1868):
        #     logger.warning("No access to category 1868 (Treadmills), but trying anyway")
        # # Проверка авторизации
        # auth_check = check_auth()
        # if not auth_check:
        #     logger.error("Authentication failed, cannot proceed")
        #     sys.exit(1)
        # Данные продукта
        product_data = {
            "data": [
                {
                    "id": 1234567,
                    "category_id": 1868,
                    "name": "Banda de alergat electrica FitTronic D100",
                    "brand": "FitTronic",
                    "part_number": "XR500-2023",
                    "description": "Cumpara Banda de alergat electrica FitTronic® D100, motor 2.5 CP, Bluetooth, Kinomap, Zwift, Newrunway, Self oil - ungere automata, sistem de amortizare in 6 puncte + arcuri, pliabila cu cilindru, intrare mp3 si USB pt muzica, cheie siguranta de la eMAG! Ai libertatea sa platesti in rate, beneficiezi de promotiile zilei, deschiderea coletului la livrare, easybox, retur gratuit in 30 de zile si Instant Money Back.",
                    "ean": ["5948004020165"],
                    "status": 1,
                    "sale_price": 1999.99,
                    "recommended_price": 2499.99,
                    "min_sale_price": 1899.99,
                    "max_sale_price": 2599.99,
                    "vat_id": 1,
                    "warranty": 24,
                    # "family": {
                    #     "id": 219,
                    #     "name": "Culoare (visible)",
                    #     "family_type_id": 219,
                    # },
                    "characteristics": [
                        {
                            "id": 7764,  # Maximum supported weight (обязательная характеристика)
                            "value": "140 kg",
                        },
                        {
                            "id": 8147,  # Number of programs (обязательная характеристика)
                            "value": "12",
                        },
                        {
                            "id": 9080,  # Leg length (обязательная характеристика)
                            "value": "Electric",
                        },
                        # {"id": 5401, "value": "Black"},  # Color
                        # {"id": 6779, "value": "130 cm"},  # Height
                        # {"id": 6780, "value": "85 cm"},  # Width
                        # {"id": 6862, "value": "180 cm"},  # Length
                        # {"id": 6878, "value": "120 kg"},  # Weight
                        # {"id": 7163, "value": "20 km/h"},  # Maximum speed
                        # {"id": 7442, "value": "2.50 W"},  # Power engine
                        # {"id": 9082, "value": "Running"},  # Sport
                        # {"id": 9083, "value": "Professional"},  # Ability level
                        # {"id": 9275, "value": "Electric"},  # Incline type
                        # {"id": 9277, "value": "15"},  # Incline percentage
                        # {"id": 9280, "value": "20"},  # Levels of speed
                        # {"id": 9281, "value": "10"},  # Levels of incline
                        # {"id": 9282, "value": "0.5 km/h"},  # Minimum speed
                        # {"id": 9283, "value": "Yes"},  # Training computer
                        # {"id": 9286, "value": "500 x 1400"},  # Running surface
                        # {
                        #     "id": 9139,  # Functions
                        #     "value": "Heart rate monitor, Bluetooth, LCD display, Speakers",
                        # },
                        # {
                        #     "id": 8382,  # Measured values
                        #     "value": "Heart rate, Distance, Calories, Speed, Time",
                        # },
                    ],
                    "images": [
                        {
                            "display_type": 1,  # 1 = главное изображение
                            "url": "https://static.efitness.ro/i/imagini-produse/banda-de-alergat-electrica-fittronic-d100-10.jpg",
                        },
                        {
                            "display_type": 2,  # 2 = дополнительное изображение
                            "url": "https://static.efitness.ro/i/imagini-produse/banda-de-alergat-electrica-fittronic-d100-2.jpg",
                        },
                        {
                            "display_type": 0,  # 0 = другое изображение
                            "url": "https://static.efitness.ro/i/imagini-produse/banda-de-alergat-electrica-fittronic-d100-3.png",
                        },
                    ],
                    "stock": [{"warehouse_id": 1, "value": 10}],
                    "handling_time": [{"warehouse_id": 1, "value": 2}],
                    # "safety_information": "Перед использованием прочтите инструкцию. Не подходит для детей младше 14 лет.",
                    # "manufacturer": [
                    #     {
                    #         "name": "FitnessExpert Manufacturing Ltd.",
                    #         "address": "123 Industrial Park, Manufacturing City, Country",
                    #         "email": "info@fitnessexpert-manufacturing.com",
                    #     }
                    # ],
                }
            ]
        }
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
