# upload_item.py
"""
Модуль для загрузки товаров на eBay через Inventory API.
Использует настроенные местоположения продавца для создания и публикации товаров.
"""

import json
import os
import time
from typing import Any, Dict

import requests
from auth import EbayAuth
from inventory_client import EbayInventoryClient
from logger import logger

from config import (
    MERCHANT_LOCATION_KEY,
    PAYMENT_POLICY_ID,
    RETURN_POLICY_ID,
    SHIPPING_POLICY_ID,
)


def load_product_data(json_file: str) -> Dict[str, Any]:
    """Загрузка данных товара из JSON-файла"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"Файл {json_file} не найден.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {json_file}.")
        return {}


def check_inventory_api_access():
    """Проверка доступа к Inventory API"""
    logger.info("Проверка доступа к Inventory API...")
    # Инициализируем клиент, который имеет логику обновления токена
    client = EbayInventoryClient()

    # Проверяем аутентификацию
    if not client.authenticate():
        logger.error(
            "Не удалось аутентифицироваться для проверки доступа к Inventory API"
        )
        return False

    # Используем токен из клиента
    try:
        headers = {
            "Authorization": f"Bearer {client.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Отправляем запрос для получения списка товаров
        response = requests.get(
            f"{client.base_url}/sell/inventory/v1/inventory_item",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        # Анализируем ответ
        data = response.json()
        total_items = data.get("total", 0)
        logger.info(f"✅ Inventory API доступен, найдено товаров: {total_items}")

        # Вывод подробной информации о первых 3 товарах (если они есть)
        items = data.get("inventoryItems", [])
        if items:
            logger.info("Примеры товаров в инвентаре:")
            for i, item in enumerate(items[:3], 1):
                sku = item.get("sku", "Н/Д")
                title = item.get("product", {}).get("title", "Без названия")
                logger.info(f"  {i}. SKU: {sku}, Название: {title}")

        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке доступа к Inventory API: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Код ошибки: {e.response.status_code}")
            logger.error(f"Ответ сервера: {e.response.text}")

            # Попытка обновления токена при ошибке авторизации
            if e.response.status_code == 401:
                logger.info("Попытка обновления токена...")
                if client.authenticate():
                    logger.info("Токен обновлен, повторная попытка проверки доступа...")
                    return (
                        check_inventory_api_access()
                    )  # Рекурсивный вызов после обновления токена
        return False


def upload_product_to_ebay(json_file: str) -> bool:
    """Загрузка товара на eBay из JSON-файла"""
    # Проверка доступа к API
    if not check_inventory_api_access():
        logger.error("Нет доступа к Inventory API. Публикация товара невозможна.")
        return False

    # Загрузка данных товара
    product_data = load_product_data(json_file)

    if not product_data:
        logger.error("Не удалось загрузить данные товара.")
        return False

    # Проверка обязательных полей
    required_fields = ["title", "description", "category_id", "price"]
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        logger.error(
            f"В данных товара отсутствуют обязательные поля: {', '.join(missing_fields)}"
        )
        return False

    # Генерация уникального SKU, если он не указан
    if "sku" not in product_data:
        import time

        product_data["sku"] = f"ITEM-{int(time.time())}"

    # Инициализация клиента
    client = EbayInventoryClient()

    # Проверка аутентификации
    if not client.authenticate():
        logger.error("Не удалось выполнить аутентификацию")
        return False

    # Проверка наличия местоположения
    if not MERCHANT_LOCATION_KEY:
        logger.error(
            "Не настроено местоположение продавца (MERCHANT_LOCATION_KEY) в config.py"
        )
        logger.info(
            "Используйте location_management.py для создания местоположения и добавьте его ключ в config.py"
        )
        return False

    # Шаг 1: Создание товара в инвентаре
    sku = product_data["sku"]
    logger.info(f"Создание товара в инвентаре с SKU: {sku}")

    inventory_result = client.create_inventory_item(sku, product_data)

    if isinstance(inventory_result, dict) and "error" in inventory_result:
        logger.error(
            f"Ошибка при создании товара в инвентаре: {inventory_result['error']}"
        )
        return False

    logger.info(f"Товар успешно создан в инвентаре с SKU: {sku}")

    # Добавляем задержку для синхронизации
    logger.info("Ожидание синхронизации товара (5 секунд)...")
    time.sleep(5)

    # Шаг 2: Создание предложения для товара
    logger.info(f"Создание предложения для товара с SKU: {sku}")

    offer_result = client.create_offer(sku, product_data)

    if isinstance(offer_result, dict) and "error" in offer_result:
        logger.error(f"Ошибка при создании предложения: {offer_result['error']}")
        return False

    if not isinstance(offer_result, dict) or "offerId" not in offer_result:
        logger.error("Не удалось получить ID предложения")
        return False

    offer_id = offer_result["offerId"]
    logger.info(f"Предложение успешно создано, ID: {offer_id}")

    # Шаг 3: Публикация предложения на eBay
    logger.info(f"Публикация предложения с ID: {offer_id}")

    publish_result = client.publish_offer(offer_id)

    if isinstance(publish_result, dict) and "error" in publish_result:
        logger.error(f"Ошибка при публикации предложения: {publish_result['error']}")
        return False

    if isinstance(publish_result, dict) and "listingId" in publish_result:
        listing_id = publish_result["listingId"]
        logger.info(f"Товар успешно опубликован на eBay, ID объявления: {listing_id}")
        listing_url = f"https://www.sandbox.ebay.de/itm/{listing_id}"
        logger.info(f"URL объявления: {listing_url}")
        return True
    else:
        logger.error("Не удалось получить ID опубликованного объявления")
        return False


def prepare_and_create_offer_from_json(json_file="offer.json"):
    """
    Подготовка и создание предложения из JSON-файла

    Args:
        json_file (str): Путь к JSON-файлу с данными предложения

    Returns:
        bool: Результат операции
    """
    logger.info(f"Подготовка и создание предложения из файла {json_file}")

    # Проверка доступа к API
    if not check_inventory_api_access():
        logger.error("Нет доступа к Inventory API. Создание предложения невозможно.")
        return False

    # Получаем актуальные ID политик продавца
    from ebay.API.config.setup_policies import get_seller_policies

    logger.info("Получение актуальных ID политик продавца...")

    # Создаем клиент для вызова API
    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Получаем политики продавца
    policy_result = get_seller_policies()
    if not policy_result:
        logger.error(
            "Не удалось получить ID политик продавца. Запуск создания политик..."
        )
        from ebay.API.config.setup_policies import create_seller_policies

        if not create_seller_policies():
            logger.error("Не удалось создать политики продавца")
            return False
        else:
            logger.info("Политики продавца успешно созданы")

    # Загружаем конфигурационный файл с актуальными ID политик
    config_file = "config/policy_ids.json"
    if not os.path.exists(config_file):
        logger.error(f"Файл конфигурации {config_file} не найден")
        return False

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            policy_ids = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {config_file}: {e}")
        return False

    # Проверяем наличие всех необходимых ID политик
    required_policies = [
        "PAYMENT_POLICY_ID",
        "RETURN_POLICY_ID",
        "SHIPPING_POLICY_ID",
        "MERCHANT_LOCATION_KEY",
    ]
    missing_policies = [
        policy for policy in required_policies if policy not in policy_ids
    ]
    if missing_policies:
        logger.error(
            f"В файле {config_file} отсутствуют ID некоторых политик: {', '.join(missing_policies)}"
        )
        return False

    # Загрузка данных предложения из файла
    offer_data = load_product_data(json_file)
    if not offer_data:
        logger.error(f"Не удалось загрузить данные предложения из файла {json_file}")
        return False

    # Обновляем данные предложения актуальными ID политик
    if "listingPolicies" in offer_data:
        offer_data["listingPolicies"]["fulfillmentPolicyId"] = policy_ids[
            "SHIPPING_POLICY_ID"
        ]
        offer_data["listingPolicies"]["paymentPolicyId"] = policy_ids[
            "PAYMENT_POLICY_ID"
        ]
        offer_data["listingPolicies"]["returnPolicyId"] = policy_ids["RETURN_POLICY_ID"]
    else:
        offer_data["listingPolicies"] = {
            "fulfillmentPolicyId": policy_ids["SHIPPING_POLICY_ID"],
            "paymentPolicyId": policy_ids["PAYMENT_POLICY_ID"],
            "returnPolicyId": policy_ids["RETURN_POLICY_ID"],
        }

    # Обновляем ключ местоположения
    offer_data["merchantLocationKey"] = policy_ids["MERCHANT_LOCATION_KEY"]

    logger.info(
        f"Данные предложения с актуальными ID политик: {json.dumps(offer_data, indent=2)}"
    )

    # Создание предложения
    headers = {
        "Content-Type": "application/json",
        "Content-Language": "de-DE",
        "Accept-Language": "de-DE",
    }

    # Создание предложения через API eBay
    endpoint = "sell/inventory/v1/offer"

    logger.info(
        f"Отправка запроса на создание предложения: {json.dumps(offer_data, indent=2)}"
    )
    result = client._call_api(endpoint, "POST", data=offer_data, headers=headers)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при создании предложения: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при создании предложения: {result['error']}")
        return False

    if not isinstance(result, dict) or "offerId" not in result:
        logger.error("Не удалось получить ID предложения")
        return False

    offer_id = result["offerId"]
    logger.info(f"Предложение успешно создано, ID: {offer_id}")

    # Публикация предложения
    publish_result = client.publish_offer(offer_id)

    if isinstance(publish_result, dict) and "listingId" in publish_result:
        listing_id = publish_result["listingId"]
        logger.info(f"Предложение успешно опубликовано! ID объявления: {listing_id}")
        logger.info(f"URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}")
        return True
    else:
        logger.error("Не удалось опубликовать предложение")
        if isinstance(publish_result, dict) and "error" in publish_result:
            logger.error(f"Ошибка: {publish_result['error']}")
        if isinstance(publish_result, dict) and "errors" in publish_result:
            for error in publish_result.get("errors", []):
                logger.error(f"Ошибка eBay: {error.get('message', '')}")
                if "longMessage" in error:
                    logger.error(f"Подробности: {error['longMessage']}")
        return False


def main():
    """Основная функция для работы с модулем"""
    print("=== Загрузка товаров на eBay ===")
    print("1. Загрузить товар из файла product_template.json")
    print("2. Загрузить товар из product_template_mattress.json")
    print("3. Загрузить товар из другого файла")
    print("4. Проверить доступ к Inventory API")
    print("5. Создать предложение из файла offer.json")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        file_name = "product_template.json"
        result = upload_product_to_ebay(file_name)

        if result:
            print("Товар успешно опубликован на eBay!")
        else:
            print("Не удалось опубликовать товар на eBay.")

    elif choice == "2":
        file_name = "product_template_mattress.json"
        result = upload_product_to_ebay(file_name)

        if result:
            print("Матрас успешно опубликован на eBay!")
        else:
            print("Не удалось опубликовать матрас на eBay.")

    elif choice == "3":
        file_name = input("Введите имя файла JSON: ")
        result = upload_product_to_ebay(file_name)

        if result:
            print("Товар успешно опубликован на eBay!")
        else:
            print("Не удалось опубликовать товар на eBay.")

    elif choice == "4":
        if check_inventory_api_access():
            print("Доступ к Inventory API подтвержден.")
        else:
            print("Нет доступа к Inventory API. Проверьте настройки и токены.")

    elif choice == "5":
        result = prepare_and_create_offer_from_json()
        if result:
            print("Предложение успешно создано и опубликовано на eBay!")
        else:
            print("Не удалось создать или опубликовать предложение.")

    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
