import json
import logging
import os
import sys
import time

# Импорт модуля авторизации
from auth import EbayAuth

# Импорт клиента API
from inventory_client import EbayInventoryClient  # Добавьте эту строку
from logger import logger


def save_policy_id(key, value):
    """
    Сохранение ID политики в файл config/policy_ids.json

    Args:
        key (str): Ключ (название политики)
        value (str): Значение (ID политики)
    """
    # Создание директории, если не существует
    os.makedirs("config", exist_ok=True)

    config_file = "config/policy_ids.json"

    # Чтение существующего файла или создание нового словаря
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            policy_ids = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        policy_ids = {}

    # Обновление словаря и сохранение
    policy_ids[key] = value

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(policy_ids, f, indent=2, ensure_ascii=False)

    logger.info(f"ID политики {key} сохранен в файл {config_file}: {value}")


def opt_in_to_business_policies(client):
    """
    Активация бизнес-политик для аккаунта eBay

    Args:
        client (EbayInventoryClient): Инициализированный клиент eBay API

    Returns:
        bool: Результат операции
    """
    logger.info("Активация бизнес-политик для аккаунта...")

    # Проверка аутентификации
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться для активации бизнес-политик")
        return False

    # Данные для запроса
    opt_in_data = {"programType": "SELLING_POLICY_MANAGEMENT"}

    # Заголовки для API
    headers = {"Content-Type": "application/json"}

    # Отправка запроса на активацию бизнес-политик
    result = client._call_api(
        "sell/account/v1/program/opt_in", "POST", data=opt_in_data, headers=headers
    )

    # Обработка результата
    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при активации бизнес-политик: {result['errors']}")
        return False

    # Если нет ошибок, то считаем операцию успешной
    logger.info("Бизнес-политики успешно активированы")
    return True


def setup_ebay_business_policies():
    """
    Комплексная настройка бизнес-политик eBay:
    1. Активация бизнес-политик
    2. Получение/создание политики оплаты
    3. Получение/создание политики возврата
    4. Получение/создание политики доставки
    5. Получение/создание местоположения продавца

    Returns:
        dict: Словарь с ID всех политик или None в случае ошибки
    """
    logger.info("Комплексная настройка бизнес-политик eBay...")

    # Инициализация клиента
    client = EbayInventoryClient()

    # Проверка аутентификации
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться для настройки бизнес-политик")
        return None

    # 1. Активация бизнес-политик
    logger.info("Шаг 1: Активация бизнес-политик...")
    if not opt_in_to_business_policies(client):
        logger.warning(
            "Не удалось активировать бизнес-политики. Возможно, они уже активированы."
        )
        # Продолжаем работу даже если активация не удалась (она может быть уже выполнена)

    # Словарь для хранения ID политик
    policy_ids = {}

    # 2. Получение или создание политики оплаты
    logger.info("Шаг 2: Получение/создание политики оплаты...")
    payment_policies = client._call_api(
        "sell/account/v1/payment_policy", "GET", params={"marketplace_id": "EBAY_DE"}
    )

    if (
        isinstance(payment_policies, dict)
        and "paymentPolicies" in payment_policies
        and payment_policies["paymentPolicies"]
    ):
        # Используем существующую политику оплаты
        policy = payment_policies["paymentPolicies"][0]
        policy_id = policy["paymentPolicyId"]
        logger.info(
            f"Найдена политика оплаты: ID {policy_id}, Название: {policy['name']}"
        )
        policy_ids["PAYMENT_POLICY_ID"] = policy_id
    else:
        # Создаем новую политику оплаты
        logger.info("Создание новой политики оплаты...")
        payment_policy = {
            "name": "Standard Payment Policy DE " + str(int(time.time())),
            "description": "Standard payment policy for eBay Germany",
            "marketplaceId": "EBAY_DE",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        }

        payment_result = client._call_api(
            "sell/account/v1/payment_policy",
            "POST",
            data=payment_policy,
            headers={"Content-Type": "application/json", "Content-Language": "de-DE"},
        )

        if isinstance(payment_result, dict) and "paymentPolicyId" in payment_result:
            policy_id = payment_result["paymentPolicyId"]
            logger.info(f"Создана новая политика оплаты: ID {policy_id}")
            policy_ids["PAYMENT_POLICY_ID"] = policy_id
        else:
            logger.error(f"Не удалось создать политику оплаты: {payment_result}")

    # 3. Получение или создание политики возврата
    logger.info("Шаг 3: Получение/создание политики возврата...")
    return_policies = client._call_api(
        "sell/account/v1/return_policy", "GET", params={"marketplace_id": "EBAY_DE"}
    )

    if (
        isinstance(return_policies, dict)
        and "returnPolicies" in return_policies
        and return_policies["returnPolicies"]
    ):
        # Используем существующую политику возврата
        policy = return_policies["returnPolicies"][0]
        policy_id = policy["returnPolicyId"]
        logger.info(
            f"Найдена политика возврата: ID {policy_id}, Название: {policy['name']}"
        )
        policy_ids["RETURN_POLICY_ID"] = policy_id
    else:
        # Создаем новую политику возврата
        logger.info("Создание новой политики возврата...")
        return_policy = {
            "name": "Standard Return Policy DE " + str(int(time.time())),
            "description": "Standard 30-day return policy for Germany",
            "marketplaceId": "EBAY_DE",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "returnsAccepted": True,
            "returnPeriod": {"value": 30, "unit": "DAY"},
            "refundMethod": "MONEY_BACK",
            "returnShippingCostPayer": "SELLER",
            "returnMethod": "REPLACEMENT",
        }

        return_result = client._call_api(
            "sell/account/v1/return_policy",
            "POST",
            data=return_policy,
            headers={"Content-Type": "application/json", "Content-Language": "de-DE"},
        )

        if isinstance(return_result, dict) and "returnPolicyId" in return_result:
            policy_id = return_result["returnPolicyId"]
            logger.info(f"Создана новая политика возврата: ID {policy_id}")
            policy_ids["RETURN_POLICY_ID"] = policy_id
        else:
            logger.error(f"Не удалось создать политику возврата: {return_result}")

    # 4. Получение или создание политики доставки
    logger.info("Шаг 4: Получение/создание политики доставки...")
    fulfillment_policies = client._call_api(
        "sell/account/v1/fulfillment_policy",
        "GET",
        params={"marketplace_id": "EBAY_DE"},
    )

    if (
        isinstance(fulfillment_policies, dict)
        and "fulfillmentPolicies" in fulfillment_policies
        and fulfillment_policies["fulfillmentPolicies"]
    ):
        # Используем существующую политику доставки
        policy = fulfillment_policies["fulfillmentPolicies"][0]
        policy_id = policy["fulfillmentPolicyId"]
        logger.info(
            f"Найдена политика доставки: ID {policy_id}, Название: {policy['name']}"
        )
        policy_ids["SHIPPING_POLICY_ID"] = policy_id
    else:
        # Создаем новую политику доставки
        logger.info("Создание новой политики доставки...")
        fulfillment_policy = {
            "name": "Standard Shipping Policy DE " + str(int(time.time())),
            "description": "Standard shipping policy for Germany",
            "marketplaceId": "EBAY_DE",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "handlingTime": {"unit": "DAY", "value": 1},
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
                            "additionalShippingCost": {
                                "currency": "EUR",
                                "value": "1.99",
                            },
                        }
                    ],
                }
            ],
            "shipToLocations": {"regionIncluded": [{"regionName": "Worldwide"}]},
        }

        fulfillment_result = client._call_api(
            "sell/account/v1/fulfillment_policy",
            "POST",
            data=fulfillment_policy,
            headers={"Content-Type": "application/json", "Content-Language": "de-DE"},
        )

        if (
            isinstance(fulfillment_result, dict)
            and "fulfillmentPolicyId" in fulfillment_result
        ):
            policy_id = fulfillment_result["fulfillmentPolicyId"]
            logger.info(f"Создана новая политика доставки: ID {policy_id}")
            policy_ids["SHIPPING_POLICY_ID"] = policy_id
        else:
            logger.error(f"Не удалось создать политику доставки: {fulfillment_result}")

    # 5. Получение или создание местоположения продавца
    logger.info("Шаг 5: Получение/создание местоположения продавца...")
    locations = client._call_api("sell/inventory/v1/location", "GET")

    if (
        isinstance(locations, dict)
        and "locations" in locations
        and locations["locations"]
    ):
        # Используем существующее местоположение
        location = locations["locations"][0]
        location_key = location["merchantLocationKey"]
        logger.info(f"Найдено местоположение: Ключ {location_key}")
        policy_ids["MERCHANT_LOCATION_KEY"] = location_key
    else:
        # Создаем новое местоположение
        logger.info("Создание нового местоположения...")
        merchant_location_key = "warehouseberlin" + str(int(time.time()) % 1000)

        location_data = {
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
        }

        location_result = client._call_api(
            f"sell/inventory/v1/location/{merchant_location_key}",
            "PUT",
            data=location_data,
            headers={"Content-Type": "application/json"},
        )

        if isinstance(location_result, dict) and location_result.get("success", False):
            logger.info(f"Создано новое местоположение: Ключ {merchant_location_key}")
            policy_ids["MERCHANT_LOCATION_KEY"] = merchant_location_key
        else:
            logger.error(f"Не удалось создать местоположение: {location_result}")

    # Сохранение ID политик в файл
    logger.info("Сохранение ID политик в файл...")
    os.makedirs("config", exist_ok=True)
    config_file = "config/policy_ids.json"

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(policy_ids, f, indent=2, ensure_ascii=False)

    logger.info(f"ID политик сохранены в файл {config_file}: {policy_ids}")
    return policy_ids


def test_setup_ebay_business_policies():
    """
    Тестирование комплексной настройки бизнес-политик
    """

    logger.info("Тестирование комплексной настройки бизнес-политик...")

    policy_ids = setup_ebay_business_policies()

    if policy_ids:
        print("Бизнес-политики успешно настроены:")
        for key, value in policy_ids.items():
            print(f"  {key}: {value}")
        print(f"ID политик сохранены в файл config/policy_ids.json")
    else:
        print("Не удалось настроить бизнес-политики")


if __name__ == "__main__":
    test_setup_ebay_business_policies()
