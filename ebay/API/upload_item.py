# ./ebay/API/upload_item.py

import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

# Импорт модулей API клиента
from auth import EbayAuth
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET

# # Добавление родительской директории в путь для импорта
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)


class EbayInventoryClient:
    """Клиент для работы с Inventory API eBay (для создания и управления товарами)"""

    def __init__(self, auth: Optional[EbayAuth] = None):
        """Инициализация клиента Inventory API"""
        self.auth = auth or EbayAuth(CLIENT_ID, CLIENT_SECRET)
        self.sandbox = True
        self.base_url = (
            "https://api.sandbox.ebay.com" if self.sandbox else "https://api.ebay.com"
        )
        self.access_token = None

    def authenticate(self) -> bool:
        """Аутентификация и получение user токена (требуется для Inventory API)"""
        # Для Inventory API требуется User токен с соответствующими правами
        if not hasattr(self.auth, "user_token") or not self.auth.user_token:
            logger.warning(
                "Не найден User токен. Запрашиваем авторизацию пользователя."
            )

            # Проверяем, есть ли сохраненный refresh токен
            if hasattr(self.auth, "refresh_token") and self.auth.refresh_token:
                logger.info("Найден Refresh токен. Пытаемся обновить User токен.")
                token_data = self.auth.refresh_user_token()
                if token_data:
                    self.access_token = token_data["access_token"]
                    return True

            # Если нет refresh токена или не удалось обновить токен,
            # нужно пройти процесс авторизации
            auth_url = self.auth.get_authorization_url(
                [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.marketing",
                    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.account",
                    "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
                ]
            )

            if auth_url:
                logger.info(f"Перейдите по следующей ссылке для авторизации:")
                logger.info(auth_url)
                auth_code = input("Введите полученный код авторизации: ")

                token_data = self.auth.get_user_token(auth_code)
                if token_data:
                    self.access_token = token_data["access_token"]
                    return True
                else:
                    logger.error("Не удалось получить User токен.")
                    return False
            else:
                logger.error("Не удалось сгенерировать URL для авторизации.")
                return False
        else:
            # Используем существующий токен
            self.access_token = self.auth.user_token["access_token"]
            return True

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Базовый метод для вызова API eBay Inventory"""
        if not self.access_token and not self.authenticate():
            logger.error("Не удалось аутентифицироваться. Невозможно выполнить запрос.")
            return {}

        url = f"{self.base_url}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "en-US",  # Добавьте этот заголовок
        }

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=headers, params=params, timeout=30
                )
            else:
                logger.error(f"Неподдерживаемый HTTP метод: {method}")
                return {}

            # Обработка кодов ответа
            if response.status_code == 204:  # No Content
                return {"success": True}

            response.raise_for_status()

            # Проверка на пустой ответ
            if not response.content:
                return {}

            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при вызове API: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Код ошибки: {e.response.status_code}")
                logger.error(f"Ответ сервера: {e.response.text}")

                # Попытка обновления токена при ошибке авторизации
                if e.response.status_code == 401:
                    logger.info("Попытка обновления токена...")
                    if self.authenticate():
                        logger.info("Токен обновлен, повторная попытка вызова API...")
                        return self._call_api(endpoint, method, params, data)

            return {"error": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при вызове API: {e}")
            return {"error": str(e)}

    def ensure_default_location(self):
        """Создание местоположения по умолчанию, если оно не существует"""
        endpoint = "sell/inventory/v1/location/default"

        location_data = {
            "location": {
                "address": {
                    "addressLine1": "123 Main Street",
                    "city": "Berlin",
                    "country": "DE",
                    "postalCode": "10115",
                    "stateOrProvince": "Berlin",
                }
            },
            "locationInstructions": "Default location",
            "name": "Default Location",
            "merchantLocationStatus": "ENABLED",
        }

        return self._call_api(endpoint, "PUT", data=location_data)

    def create_inventory_item(
        self, sku: str, inventory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создание товара в инвентаре (Inventory Item)"""
        endpoint = "sell/inventory/v1/inventory_item"

        # Подготовка данных для инвентаря
        inventory_item = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": inventory_data.get("quantity", 1)
                }
            },
            "condition": inventory_data.get("condition", "USED_EXCELLENT"),
            "conditionDescription": inventory_data.get("condition_description", ""),
            "product": {
                "title": inventory_data.get("title", ""),
                "description": inventory_data.get("description", ""),
                "aspects": inventory_data.get("aspects", {}),
                "imageUrls": inventory_data.get("images", []),
            },
        }

        # Добавление данных о местоположении
        if "location" in inventory_data:
            location = inventory_data["location"]
            inventory_item["product"]["packageWeightAndSize"] = {
                "packageType": "PACKAGE_THICK_ENVELOPE"
            }
            inventory_item["product"]["isbn"] = []
            inventory_item["product"]["upc"] = []
            inventory_item["product"]["brand"] = inventory_data.get("aspects", {}).get(
                "Brand", [""]
            )[0]

        # Явно добавляем доступность для маркетплейса EBAY_DE
        inventory_item["availability"]["shipToLocationAvailability"] = {
            "quantity": inventory_data.get("quantity", 1),
            "availableDate": "2025-03-20T00:00:00.000Z",  # Дата доступности
            "merchantLocationKey": "default",  # Ключ местоположения
        }

        # Запрос на создание/обновление товара в инвентаре
        return self._call_api(f"{endpoint}/{sku}", "PUT", data=inventory_item)

    def create_offer(self, sku: str, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание предложения (Offer) для товара"""
        endpoint = "sell/inventory/v1/offer"

        # Подготовка данных предложения (второй шаг - создание предложения для товара)
        offer = {
            "sku": sku,
            "marketplaceId": "EBAY_DE",
            "format": "FIXED_PRICE",
            "availableQuantity": offer_data.get("quantity", 1),
            "categoryId": offer_data.get("category_id", ""),
            "listingDescription": offer_data.get("description", ""),
            "pricingSummary": {
                "price": {
                    "value": str(offer_data.get("price", {}).get("value", 0)),
                    "currency": offer_data.get("price", {}).get("currency", "EUR"),
                }
            },
        }

        # Добавляем прямые настройки доставки и возврата вместо политик
        offer["shippingOptions"] = [
            {
                "costType": "FLAT_RATE",
                "optionType": "DOMESTIC",
                "shippingServices": [
                    {
                        "shippingServiceCode": "DE_DHLPaket",
                        "shippingCost": {"currency": "EUR", "value": "5.99"},
                        "additionalShippingCost": {"currency": "EUR", "value": "1.99"},
                        "shippingCarrierCode": "DHL",
                        "sortOrder": 1,
                    }
                ],
            }
        ]

        offer["returnTerms"] = {
            "returnsAccepted": True,
            "returnPeriod": {"value": 30, "unit": "DAY"},
            "returnMethod": "REPLACEMENT_OR_MONEY_BACK",
            "returnShippingCostPayer": "SELLER",
        }

        # Добавление настроек объявления
        if "listing_policies" in offer_data:
            policies = offer_data["listing_policies"]
            if "best_offer_enabled" in policies:
                offer["bestOfferEnabled"] = policies["best_offer_enabled"]
            if "listing_duration" in policies:
                offer["listingDuration"] = policies["listing_duration"]

        # Запрос на создание предложения
        return self._call_api(endpoint, "POST", data=offer)

    def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        """Публикация предложения (Offer) на eBay"""
        endpoint = f"sell/inventory/v1/offer/{offer_id}/publish"
        return self._call_api(endpoint, "POST")


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


def upload_product_to_ebay(json_file: str) -> bool:
    """Загрузка товара на eBay из JSON-файла"""
    # Загрузка данных товара
    product_data = load_product_data(json_file)

    if not product_data:
        logger.error("Не удалось загрузить данные товара.")
        return False

    # Проверка обязательных полей
    required_fields = ["sku", "title", "description", "category_id", "price"]
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        logger.error(
            f"В данных товара отсутствуют обязательные поля: {', '.join(missing_fields)}"
        )
        return False

    # Инициализация клиента
    client = EbayInventoryClient()
    # Создание местоположения по умолчанию
    logger.info("Создание местоположения по умолчанию...")
    location_result = client.ensure_default_location()
    if "error" in location_result:
        logger.warning(
            f"Предупреждение при создании местоположения: {location_result['error']}"
        )

    # Шаг 1: Создание товара в инвентаре
    sku = product_data["sku"]
    logger.info(f"Создание товара в инвентаре с SKU: {sku}")

    inventory_result = client.create_inventory_item(sku, product_data)

    if "error" in inventory_result:
        logger.error(
            f"Ошибка при создании товара в инвентаре: {inventory_result['error']}"
        )
        return False

    logger.info("Товар успешно создан в инвентаре")
    # Добавляем задержку для синхронизации
    logger.info("Ожидание синхронизации товара (5 секунд)...")
    time.sleep(5)
    # Шаг 2: Создание предложения для товара
    logger.info(f"Создание предложения для товара с SKU: {sku}")

    offer_result = client.create_offer(sku, product_data)

    if "error" in offer_result:
        logger.error(f"Ошибка при создании предложения: {offer_result['error']}")
        return False

    if "offerId" not in offer_result:
        logger.error("Не удалось получить ID предложения")
        return False

    offer_id = offer_result["offerId"]
    logger.info(f"Предложение успешно создано, ID: {offer_id}")

    # Шаг 3: Публикация предложения на eBay
    logger.info(f"Публикация предложения с ID: {offer_id}")

    publish_result = client.publish_offer(offer_id)

    if "error" in publish_result:
        logger.error(f"Ошибка при публикации предложения: {publish_result['error']}")
        return False

    if "listingId" in publish_result:
        listing_id = publish_result["listingId"]
        logger.info(f"Товар успешно опубликован на eBay, ID объявления: {listing_id}")
        return True
    else:
        logger.error("Не удалось получить ID опубликованного объявления")
        return False


if __name__ == "__main__":
    file_name = "product_template.json"

    result = upload_product_to_ebay(file_name)

    if result:
        logger.info("Товар успешно опубликован на eBay!")
    else:
        logger.error("Не удалось опубликовать товар на eBay.")
