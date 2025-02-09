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
    api_url = "https://marketplace-api.emag.ro/api-3"
    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url, headers, session


api_url, headers, session = get_headers_session()


def get_categories():
    """Получение списка категорий"""
    response = session.get(f"{api_url}/category/read", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def get_vat_rates():
    """Получение ставок НДС"""
    response = session.get(f"{api_url}/vat/read", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def get_handling_times():
    """Получение времени обработки заказа"""
    response = session.get(f"{api_url}/handling_time/read", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def prepare_draft_data(product):
    """Подготовка данных для черновика"""
    draft_data = {
        "id": product["id"],
        "name": product["name"],
        "brand": product["brand"],
        "part_number": product["part_number"],
        "category_id": product["category_id"],
        "sale_price": product.get("sale_price", 0),
        "vat_id": product.get("vat_id", 4003),
        "stock": [{"warehouse_id": 1, "value": product.get("stock", 0)}],
        # Обновленные характеристики
        "characteristics": [
            {"id": 9623, "value": "Maini"},  # Zona corporala
            {
                "id": 5704,  # Tip produs
                "value": "Pila electrica",  # Исправленное значение
            },
        ],
        # Обязательные изображения
        "images": [
            {
                "display_type": 1,  # Главное изображение
                "url": product["main_image"],  # Должно быть в данных продукта
            }
        ],
    }

    if "additional_images" in product:
        for img_url in product["additional_images"]:
            draft_data["images"].append({"display_type": 0, "url": img_url})

    # Добавляем EAN если есть
    if "ean" in product and product["ean"]:
        valid_eans = []
        for ean in product["ean"]:
            if validate_ean(ean):
                valid_eans.append(ean)
            else:
                logger.warning(f"Invalid EAN: {ean}")
        if valid_eans:
            draft_data["ean"] = valid_eans
        else:
            raise ValueError("No valid EAN codes provided")
    else:
        raise ValueError("EAN is mandatory")

    return draft_data


# def send_draft(product_draft):
#     """Отправка черновика"""
#     # Оборачиваем данные в массив, как требует API
#     data = {"data": [product_draft]}  # Изменение здесь
#     response = session.post(f"{api_url}/product_offer/save", headers=headers, json=data)
#     return response.json()


# def get_allowed_brands():
#     """Получение списка разрешенных брендов"""
#     try:
#         response = session.get(f"{api_url}/brands/read", headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         logger.error(f"Failed to get brands. Status code: {response.status_code}")
#         logger.error(f"Response: {response.text}")
#     except Exception as e:
#         logger.error(f"Exception getting brands: {str(e)}")
#     return None


def validate_ean(ean):
    """Проверка валидности EAN кода"""
    if not ean.isdigit():
        return False
    if len(ean) not in [8, 13]:  # EAN-8 или EAN-13
        return False

    # Проверка контрольной суммы
    checksum = 0
    for i, digit in enumerate(reversed(ean[:-1])):
        checksum += int(digit) * (3 if i % 2 else 1)
    calculated_check = (10 - (checksum % 10)) % 10
    return calculated_check == int(ean[-1])


def process_products(products):
    """Обработка списка товаров"""
    results = []
    logger.info(f"Starting processing {len(products)} products")

    for product in products:
        try:
            logger.info(f"Processing product ID: {product['id']}")

            # Валидация данных
            validate_product_data(product)

            # Создание и обновление черновика
            result = process_draft(product)
            results.append(result)

            # Задержка между запросами
            time.sleep(0.4)

        except Exception as e:
            logger.error(f"Error processing product {product['id']}: {str(e)}")
            results.append(
                {
                    "id": product["id"],
                    "result": {"isError": True, "message": str(e)},
                    "type": "error",
                }
            )

    logger.info(f"Finished processing {len(products)} products")
    return results


def send_draft(product_draft):
    """Отправка черновика"""
    # Готовим данные согласно документации API
    draft_data = {
        "id": product_draft["id"],
        "name": product_draft["name"],
        "part_number": product_draft["part_number"],
        "brand": product_draft["brand"],
    }

    # Опциональные поля
    optional_fields = ["ean", "category_id", "source_language"]
    for field in optional_fields:
        if field in product_draft:
            draft_data[field] = product_draft[field]

    response = session.post(f"{api_url}/api/v1/draft", headers=headers, json=draft_data)
    return response.json()


def get_draft(ext_id):
    """Получение черновика по ID"""
    response = session.get(f"{api_url}/api/v1/draft/{ext_id}", headers=headers)
    return response.json()


def update_draft(ext_id, product_data):
    """Обновление черновика"""
    response = session.put(
        f"{api_url}/api/v1/draft/{ext_id}", headers=headers, json=product_data
    )
    return response.json()


def get_drafts_list(page=1, per_page=100):
    """Получение списка черновиков"""
    params = {"page": page, "per_page": per_page}
    response = session.get(f"{api_url}/api/v1/draft", headers=headers, params=params)
    return response.json()


def check_existing_product(ean):
    """Проверка существования товара по EAN и получение part_number_key"""
    # Оборачиваем параметры поиска в массив
    data = {"data": {"ean": [ean]}}  # Изменение здесь

    response = session.post(f"{api_url}/product_offer/read", headers=headers, json=data)
    data = response.json()
    if not data.get("isError") and data.get("results"):
        return data["results"][0].get("part_number_key")
    return None


def attach_offer_to_existing_product(product, part_number_key):
    """Привязка предложения к существующему товару"""
    offer_data = {
        "id": product["id"],
        "part_number_key": part_number_key,
        "name": product["name"],
        "status": 1,
        "sale_price": product.get("sale_price"),
        "vat_id": product.get("vat_id"),
        "stock": [{"warehouse_id": 1, "value": product.get("stock", 0)}],
        "handling_time": [{"warehouse_id": 1, "value": 1}],
    }

    # Оборачиваем данные в массив
    data = {"data": [offer_data]}  # Изменение здесь

    response = session.post(f"{api_url}/product_offer/save", headers=headers, json=data)
    return response.json()


def get_category_details(category_id):
    """Получение детальной информации о категории"""
    response = session.post(
        f"{api_url}/category/read", headers=headers, json={"data": {"id": category_id}}
    )
    if response.status_code == 200:
        data = response.json()
        if not data.get("isError") and data.get("results"):
            return data["results"][0]
    return None


def validate_category_characteristics(product, category_details):
    """Проверка обязательных характеристик категории"""
    if not category_details:
        return False

    required_characteristics = [
        char["id"]
        for char in category_details.get("characteristics", [])
        if char.get("is_mandatory")
    ]

    product_characteristics = [
        char["id"] for char in product.get("characteristics", [])
    ]

    missing = set(required_characteristics) - set(product_characteristics)
    if missing:
        raise ValueError(f"Missing mandatory characteristics: {missing}")

    return True


def validate_product_data(product):
    """Расширенная валидация данных товара"""
    # Существующие проверки...

    # Проверка наличия изображений
    if "main_image" not in product:
        raise ValueError("Main image is required")

    # # Проверка бренда
    # allowed_brands = get_allowed_brands()
    # if allowed_brands and product["brand"] not in allowed_brands:
    #     raise ValueError(f"Invalid brand: {product['brand']}")

    # Проверка характеристик
    required_characteristics = {
        5704: ["Pila electrica"],  # Разрешенные значения для Tip produs
        9623: ["Maini"],  # Разрешенные значения для Zona corporala
    }

    for char in product.get("characteristics", []):
        char_id = char["id"]
        if char_id in required_characteristics:
            if char["value"] not in required_characteristics[char_id]:
                raise ValueError(
                    f"Invalid value for characteristic {char_id}: {char['value']}"
                )

    return True


def process_draft(product):
    """Обработка одного продукта с созданием черновика"""
    try:
        # 1. Создаем черновик с минимальными данными
        draft_result = send_draft(
            {
                "id": product["id"],
                "name": product["name"],
                "part_number": product["part_number"],
                "brand": product["brand"],
                "category_id": product.get("category_id"),
                "ean": product.get("ean"),
                "source_language": product.get("source_language", "ro_RO"),
            }
        )

        if draft_result.get("id"):  # Если черновик создан успешно
            draft_id = draft_result["id"]
            logger.info(f"Draft created successfully with ID: {draft_id}")

            # 2. Обновляем черновик дополнительными данными
            update_data = {
                "id": product["id"],
                "characteristics": product.get("characteristics", []),
                "images": product.get("images", []),
            }

            update_result = update_draft(draft_id, update_data)
            return {
                "id": product["id"],
                "draft_id": draft_id,
                "result": update_result,
                "type": "draft",
            }
        else:
            logger.error(f"Failed to create draft for product {product['id']}")
            return {"id": product["id"], "result": draft_result, "type": "error"}

    except Exception as e:
        logger.error(f"Error processing draft for product {product['id']}: {str(e)}")
        return {
            "id": product["id"],
            "result": {"isError": True, "message": str(e)},
            "type": "error",
        }


if __name__ == "__main__":
    # Загрузка справочников
    # brands = get_allowed_brands()
    # if brands and not brands.get("isError"):
    #     logger.info("Brands loaded successfully")
    #     with open("brands.json", "w") as f:
    #         json.dump(brands, f)
    # else:
    #     logger.error("Error loading brands")
    #     sys.exit(1)
    # 1. Получаем и проверяем справочные данные
    categories = get_categories()
    if categories and not categories.get("isError"):
        logger.info("Categories loaded successfully")
        with open("categories.json", "w") as f:
            json.dump(categories, f)
    else:
        logger.error("Error loading categories")
        sys.exit(1)  # Выходим, если не удалось загрузить категории

    vat_rates = get_vat_rates()
    if vat_rates and not vat_rates.get("isError"):
        logger.info("VAT rates loaded successfully")
        with open("vat_rates.json", "w") as f:
            json.dump(vat_rates, f)
    else:
        logger.error("Error loading VAT rates")
        sys.exit(1)  # Выходим, если не удалось загрузить ставки НДС

    # 2. Тестовые данные
    test_products = [
        {
            "id": 17006903216,
            "name": "3,5-calowa konsola D22 HD Large Screen",
            "brand": "Example Brand",  # Реальный бренд из списка разрешенных
            "part_number": "A8-1106-A7085",
            "category_id": 2768,
            "ean": ["5901234123457"],
            "sale_price": 153.0,
            "vat_id": 4003,
            "stock": 10,
            "characteristics": [
                {"id": 9623, "value": "Maini"},
                {"id": 5704, "value": "Pila electrica"},  # Исправленное значение
            ],
            "main_image": "https://example.com/images/main.jpg",  # Главное изображение
            "additional_images": [  # Дополнительные изображения
                "https://example.com/images/1.jpg",
                "https://example.com/images/2.jpg",
            ],
        },
        {
            "id": 17006903217,
            "name": "Test Product Without EAN",
            "brand": "Test Brand",
            "part_number": "TEST-001",
            "category_id": 2768,
            "ean": ["4003994155486"],
            "sale_price": 99.99,
            "vat_id": 4003,
            "stock": 5,
            "characteristics": [
                {"id": 9623, "value": "Maini"},
                {"id": 5704, "value": "Freza electrica"},
            ],
        },
    ]

    # 3. Предварительная валидация товаров
    validated_products = []
    for product in test_products:
        try:
            # Проверяем категорию
            category_details = get_category_details(product["category_id"])
            if not category_details:
                logger.error(
                    f"Category {product['category_id']} not found for product {product['id']}"
                )
                continue

            # Валидируем характеристики категории
            validate_category_characteristics(product, category_details)

            # Валидируем основные данные
            validate_product_data(product)

            validated_products.append(product)
            logger.info(f"Product {product['id']} validated successfully")

        except ValueError as e:
            logger.error(f"Validation error for product {product['id']}: {str(e)}")

    # 4. Обработка валидных товаров
    if validated_products:
        try:
            results = process_products(validated_products)
            logger.info("\nProcessing results:")
            for result in results:
                logger.info(f"Product ID: {result['id']}")
                logger.info(
                    f"Status: {'Success' if not result['result'].get('isError') else 'Error'}"
                )
                logger.info(f"Response: {result['result']}")
                logger.info("-" * 50)

            # Сохраняем результаты
            with open("processing_results.json", "w") as f:
                json.dump(results, f, indent=2)

            # Статистика
            drafts = len([r for r in results if r.get("type") == "draft"])
            attached = len([r for r in results if r.get("type") == "attached"])
            validation_errors = len(
                [r for r in results if r.get("type") == "validation_error"]
            )
            api_errors = len([r for r in results if r.get("type") == "error"])

            logger.info("\nProcessing statistics:")
            logger.info(f"Total products to process: {len(test_products)}")
            logger.info(f"Products passed validation: {len(validated_products)}")
            logger.info(f"New drafts created: {drafts}")
            logger.info(f"Attached to existing products: {attached}")
            logger.info(f"Validation errors: {validation_errors}")
            logger.info(f"API errors: {api_errors}")

        except Exception as e:
            logger.error(f"Error processing products: {str(e)}")
    else:
        logger.error("No products passed validation")
