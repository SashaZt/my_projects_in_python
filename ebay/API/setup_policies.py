import json
import logging
import os
import sys

# Импорт модуля авторизации
from auth import EbayAuth

# Импорт клиента API
from inventory_client import EbayInventoryClient  # Добавьте эту строку
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET, DEFAULT_MARKETPLACE_ID, RUNAME

# # Добавление текущей директории в путь поиска модулей
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # Настройка логирования
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(lineno)d | %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
# )
# logger = logging.getLogger(__name__)

# Импорт модуля авторизации и клиента
# try:
#     from auth import EbayAuth
# except ImportError:
#     # Если файла auth.py нет, используем класс EbayAuth из upload_item.py
#     from upload_item import EbayAuth, EbayInventoryClient


def create_seller_policies():
    """Создание базовых политик продавца для eBay Германия"""
    # Инициализация клиента API (без передачи auth как параметра)
    client = EbayInventoryClient()

    # Аутентификация для получения User токена
    if not client.authenticate():
        logger.error("Не удалось пройти аутентификацию")
        return False

    # Создание конфигурационного файла для сохранения ID политик
    config_updates = {}

    # 1. Создание местоположения продавца
    location_key = "main-warehouse-de"

    location = {
        "location": {
            "address": {
                "addressLine1": "Musterstrasse 1",
                "city": "Berlin",
                "country": "DE",
                "postalCode": "10115",
                "stateOrProvince": "Berlin",
            }
        },
        "locationInstructions": "Standard location",
        "name": "Main Warehouse",
        "merchantLocationStatus": "ENABLED",
        "merchantLocationKey": location_key,
    }

    logger.info(f"Создание местоположения продавца '{location_key}'...")
    location_result = client._call_api(
        f"sell/inventory/v1/location/{location_key}", "PUT", data=location
    )

    if "errors" in location_result:
        logger.error(f"Ошибка при создании местоположения: {location_result['errors']}")
    else:
        logger.info(f"Местоположение продавца создано: {location_key}")
        config_updates["MERCHANT_LOCATION_KEY"] = location_key

    # 2. Создание политики оплаты
    payment_policy = {
        "name": "Standard Payment Policy DE",
        "description": "Standard payment policy for eBay Germany",
        "marketplaceId": DEFAULT_MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}],
        "paymentMethods": [
            {
                "paymentMethodType": "PAYPAL",
                "recipientAccountReference": {
                    "referenceType": "PAYPAL_EMAIL",
                    "referenceId": "test-paypal@example.com",  # Замените на ваш PayPal email в Sandbox
                },
            }
        ],
    }

    logger.info("Создание политики оплаты...")
    payment_result = client._call_api(
        "sell/account/v1/payment_policy", "POST", data=payment_policy
    )

    if "errors" in payment_result:
        logger.error(
            f"Ошибка при создании политики оплаты: {payment_result.get('errors', [])}"
        )
    elif "paymentPolicyId" in payment_result:
        policy_id = payment_result["paymentPolicyId"]
        logger.info(f"Политика оплаты создана: ID {policy_id}")
        config_updates["PAYMENT_POLICY_ID"] = policy_id
    else:
        logger.error(
            f"Неожиданный ответ при создании политики оплаты: {payment_result}"
        )

    # 3. Создание политики возврата
    return_policy = {
        "name": "Standard Return Policy DE",
        "description": "Standard 30-day return policy for Germany",
        "marketplaceId": DEFAULT_MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}],
        "returnsAccepted": True,
        "returnPeriod": {"value": 30, "unit": "DAY"},
        "refundMethod": "MONEY_BACK",
        "returnShippingCostPayer": "SELLER",
        "returnMethod": "REPLACEMENT",
    }

    logger.info("Создание политики возврата...")
    return_result = client._call_api(
        "sell/account/v1/return_policy", "POST", data=return_policy
    )

    if "errors" in return_result:
        logger.error(
            f"Ошибка при создании политики возврата: {return_result.get('errors', [])}"
        )
    elif "returnPolicyId" in return_result:
        policy_id = return_result["returnPolicyId"]
        logger.info(f"Политика возврата создана: ID {policy_id}")
        config_updates["RETURN_POLICY_ID"] = policy_id
    else:
        logger.error(
            f"Неожиданный ответ при создании политики возврата: {return_result}"
        )

    # 4. Создание политики доставки
    fulfillment_policy = {
        "name": "Standard Shipping Policy DE",
        "description": "Standard shipping policy for Germany",
        "marketplaceId": DEFAULT_MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": True}],
        "handlingTime": {"value": 1, "unit": "DAY"},
        "shippingOptions": [
            {
                "optionType": "DOMESTIC",
                "costType": "FLAT_RATE",
                "shippingServices": [
                    {
                        "sortOrder": 1,
                        "shippingCarrierCode": "DHL",
                        "shippingServiceCode": "DE_DHLPaket",
                        "shippingCost": {"currency": "EUR", "value": "5.99"},
                        "additionalShippingCost": {"currency": "EUR", "value": "1.99"},
                    }
                ],
            }
        ],
    }

    logger.info("Создание политики доставки...")
    fulfillment_result = client._call_api(
        "sell/account/v1/fulfillment_policy", "POST", data=fulfillment_policy
    )

    if "errors" in fulfillment_result:
        logger.error(
            f"Ошибка при создании политики доставки: {fulfillment_result.get('errors', [])}"
        )
    elif "fulfillmentPolicyId" in fulfillment_result:
        policy_id = fulfillment_result["fulfillmentPolicyId"]
        logger.info(f"Политика доставки создана: ID {policy_id}")
        config_updates["SHIPPING_POLICY_ID"] = policy_id
    else:
        logger.error(
            f"Неожиданный ответ при создании политики доставки: {fulfillment_result}"
        )

    # Сохранение ID политик в файл для дальнейшего использования
    if config_updates:
        save_policy_ids(config_updates)

    return bool(config_updates)


def get_seller_policies():
    """Получение существующих политик продавца"""
    # Инициализация авторизации и клиента
    client = EbayInventoryClient()

    # Аутентификация для получения User токена
    if not client.authenticate():
        logger.error("Не удалось пройти аутентификацию")
        return False

    config_updates = {}

    # 1. Получение политик оплаты
    logger.info("Получение политик оплаты...")
    payment_policies = client._call_api(
        "sell/account/v1/payment_policy",
        "GET",
        params={"marketplace_id": DEFAULT_MARKETPLACE_ID},
    )

    if "paymentPolicies" in payment_policies and payment_policies["paymentPolicies"]:
        policy = payment_policies["paymentPolicies"][0]
        policy_id = policy["paymentPolicyId"]
        logger.info(
            f"Найдена политика оплаты: ID {policy_id}, Название: {policy['name']}"
        )
        config_updates["PAYMENT_POLICY_ID"] = policy_id
    else:
        logger.warning("Политики оплаты не найдены")

    # 2. Получение политик возврата
    logger.info("Получение политик возврата...")
    return_policies = client._call_api(
        "sell/account/v1/return_policy",
        "GET",
        params={"marketplace_id": DEFAULT_MARKETPLACE_ID},
    )

    if "returnPolicies" in return_policies and return_policies["returnPolicies"]:
        policy = return_policies["returnPolicies"][0]
        policy_id = policy["returnPolicyId"]
        logger.info(
            f"Найдена политика возврата: ID {policy_id}, Название: {policy['name']}"
        )
        config_updates["RETURN_POLICY_ID"] = policy_id
    else:
        logger.warning("Политики возврата не найдены")

    # 3. Получение политик доставки
    logger.info("Получение политик доставки...")
    fulfillment_policies = client._call_api(
        "sell/account/v1/fulfillment_policy",
        "GET",
        params={"marketplace_id": DEFAULT_MARKETPLACE_ID},
    )

    if (
        "fulfillmentPolicies" in fulfillment_policies
        and fulfillment_policies["fulfillmentPolicies"]
    ):
        policy = fulfillment_policies["fulfillmentPolicies"][0]
        policy_id = policy["fulfillmentPolicyId"]
        logger.info(
            f"Найдена политика доставки: ID {policy_id}, Название: {policy['name']}"
        )
        config_updates["SHIPPING_POLICY_ID"] = policy_id
    else:
        logger.warning("Политики доставки не найдены")

    # 4. Получение местоположений продавца
    logger.info("Получение местоположений продавца...")
    merchant_locations = client._call_api("sell/inventory/v1/location", "GET")

    if "locations" in merchant_locations and merchant_locations["locations"]:
        location = merchant_locations["locations"][0]
        location_key = location["merchantLocationKey"]
        logger.info(
            f"Найдено местоположение продавца: Ключ {location_key}, Название: {location['name']}"
        )
        config_updates["MERCHANT_LOCATION_KEY"] = location_key
    else:
        logger.warning("Местоположения продавца не найдены")

    # Сохранение ID политик в файл для дальнейшего использования
    if config_updates:
        save_policy_ids(config_updates)

    return bool(config_updates)


def save_policy_ids(config_updates):
    """Сохранение ID политик в файл config_updates.json"""
    try:
        # Создание директории для конфигурации, если не существует
        os.makedirs("config", exist_ok=True)

        # Путь к файлу конфигурации
        config_file = "config/policy_ids.json"

        # Чтение существующей конфигурации, если файл существует
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)

        # Обновление конфигурации
        existing_config.update(config_updates)

        # Сохранение обновленной конфигурации
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)

        logger.info(f"ID политик сохранены в файл {config_file}")

        # Вывод инструкций для обновления config.py
        print("\nДля завершения настройки выполните следующие шаги:")
        print("1. Откройте файл config.py")
        print("2. Замените значения следующих переменных:")
        for key, value in config_updates.items():
            print(f'   {key} = "{value}"')

        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении ID политик: {e}")
        return False


if __name__ == "__main__":
    logger.info("Запуск скрипта настройки политик продавца...")

    # Проверка наличия RuName
    if not RUNAME:
        logger.error(
            "RuName не настроен в файле config.py. Настройте RuName перед запуском скрипта."
        )
        sys.exit(1)

    # Проверка наличия существующих политик
    logger.info("Проверка наличия существующих политик продавца...")
    if get_seller_policies():
        logger.info("Существующие политики найдены и сохранены.")
    else:
        logger.info("Существующие политики не найдены. Создание новых политик...")
        if create_seller_policies():
            logger.info("Политики продавца успешно созданы и сохранены.")
        else:
            logger.error("Не удалось создать политики продавца.")

    logger.info("Выполнение скрипта завершено.")
