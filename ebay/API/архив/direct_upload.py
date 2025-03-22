import json
import logging
import time
from typing import Any, Dict, Optional

import requests
from auth import EbayAuth
from logger import logger

from config import CLIENT_ID, CLIENT_SECRET, RUNAME


class SimpleEbayClient:
    def __init__(self):
        self.auth = EbayAuth(CLIENT_ID, CLIENT_SECRET)
        self.base_url = "https://api.sandbox.ebay.com"
        self.access_token = None

        # Попытка аутентификации
        self.authenticate()

    def authenticate(self):
        """Аутентификация с использованием существующего токена или обновление через refresh token"""
        if hasattr(self.auth, "user_token") and self.auth.user_token:
            self.access_token = self.auth.user_token.get("access_token")
            logger.info("Используется существующий токен.")
            return True

        # Проверка наличия refresh токена
        if hasattr(self.auth, "refresh_token") and self.auth.refresh_token:
            logger.info("Обновление токена через refresh token.")
            token_data = self.auth.refresh_user_token()
            if token_data:
                self.access_token = token_data.get("access_token")
                return True

        # Запрос нового токена через авторизацию
        auth_url = self.auth.get_authorization_url(
            [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.account",
            ]
        )

        if auth_url:
            logger.info(f"Перейдите по ссылке для авторизации: {auth_url}")
            auth_code = input("Введите код авторизации: ")
            token_data = self.auth.get_user_token(auth_code)
            if token_data:
                self.access_token = token_data.get("access_token")
                return True

        return False

    def call_api(self, endpoint, method="GET", data=None, params=None, headers=None):
        """Базовый метод для вызова API eBay"""
        if not self.access_token:
            logger.error("Отсутствует токен доступа. Необходима аутентификация.")
            return None

        url = f"{self.base_url}/{endpoint}"
        default_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "en-US",
        }
        # Используем переданные headers, если есть, иначе default_headers
        headers = headers or default_headers

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
            else:
                logger.error(f"Неподдерживаемый метод: {method}")
                return None

            response.raise_for_status()

            if not response.content:
                return {"success": True}

            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка: {e}")
            print(f"DEBUG: Ответ сервера: {e.response.text}")  # Временный вывод
            if hasattr(e, "response") and e.response:
                logger.error(f"Код ошибки: {e.response.status_code}")
                logger.error(f"Ответ сервера: {e.response.text}")
                print(f"DEBUG: Ответ сервера: {e.response.text}")  # Временный вывод
            return None
        except Exception as e:
            logger.error(f"Ошибка при вызове API: {e}")
            return None

    def create_inventory_item(self, sku, product_data):
        """Создание товара в инвентаре"""
        # Генерация нового SKU с временной меткой для уникальности
        timestamp = int(time.time())
        unique_sku = f"{sku}-{timestamp}"
        logger.info(f"Использование уникального SKU: {unique_sku}")

        endpoint = f"sell/inventory/v1/inventory_item/{unique_sku}"

        # Подготовка данных товара
        inventory_item = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": product_data.get("quantity", 1)
                }
            },
            "condition": product_data.get("condition", "USED_EXCELLENT"),
            "conditionDescription": product_data.get("condition_description", ""),
            "product": {
                "title": product_data.get("title", ""),
                "description": product_data.get("description", ""),
                "aspects": product_data.get("aspects", {}),
                "imageUrls": product_data.get("images", []),
            },
        }

        result = self.call_api(endpoint, "PUT", data=inventory_item)
        if result:
            logger.info(f"Товар создан в инвентаре с SKU: {unique_sku}")
            return unique_sku

        logger.error("Не удалось создать товар в инвентаре")
        return None

    def get_inventory_item(self, sku):
        """Проверка наличия товара в инвентаре"""
        endpoint = f"sell/inventory/v1/inventory_item/{sku}"
        result = self.call_api(endpoint, "GET")
        return result is not None

    def create_location(self, product_data=None):
        location_key = f"location-{int(time.time())}"
        endpoint = f"sell/inventory/v1/location/{location_key}"
        location_info = product_data.get("location", {}) if product_data else {}
        location_data = {
            "location": {
                "address": {
                    "addressLine1": "123 Main Street",
                    "city": "Berlin",
                    "countryCode": location_info.get("country", "DE"),
                    "postalCode": location_info.get("zip_code", "12345"),
                    "stateOrProvince": "Berlin",
                }
            },
            "locationInstructions": "Standard location",
            "name": "Default Location",
            "merchantLocationStatus": "ENABLED",
            "phone": "+49123456789",
            "locationTypes": ["WAREHOUSE"],
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "de-DE",  # Исправлено для EBAY_DE
        }
        result = self.call_api(endpoint, "PUT", data=location_data, headers=headers)
        if result:
            logger.info(f"Создано местоположение продавца с ключом: {location_key}")
            return location_key
        logger.error("Не удалось создать местоположение продавца")
        return None

    def create_offer(self, sku, product_data, location_key):
        endpoint = "sell/inventory/v1/offer"
        shipping_info = product_data.get("shipping_options", [{}])[0]
        return_policy = product_data.get("return_policy", {})
        listing_policies = product_data.get("listing_policies", {})

        offer = {
            "sku": sku,
            "marketplaceId": "EBAY_DE",
            "format": "FIXED_PRICE",
            "availableQuantity": product_data.get("quantity", 1),
            "categoryId": product_data.get("category_id", "9355"),
            "listingDescription": product_data.get("description", "Test laptop"),
            "listingDuration": listing_policies.get("listing_duration", "GTC"),
            "merchantLocationKey": location_key,
            "pricingSummary": {
                "price": {
                    "value": str(product_data.get("price", {}).get("value", "599.99")),
                    "currency": product_data.get("price", {}).get("currency", "EUR"),
                }
            },
            "shippingOptions": [
                {
                    "costType": "FLAT_RATE",
                    "optionType": "DOMESTIC",
                    "shippingServices": [
                        {
                            "shippingServiceCode": shipping_info.get(
                                "shipping_service", "DE_DHLPaket"
                            ),
                            "shippingCost": {
                                "currency": shipping_info.get("shipping_cost", {}).get(
                                    "currency", "EUR"
                                ),
                                "value": str(
                                    shipping_info.get("shipping_cost", {}).get(
                                        "value", "5.99"
                                    )
                                ),
                            },
                        }
                    ],
                }
            ],
            "returnTerms": {
                "returnsAccepted": return_policy.get("return_accepted", True),
                "returnPeriod": return_policy.get(
                    "return_period", {"value": 14, "unit": "DAY"}
                ),
                "returnMethod": "MONEY_BACK",
                "returnShippingCostPayer": return_policy.get(
                    "return_shipping_cost_payer", "SELLER"
                ),
            },
            "listingPolicies": {
                "bestOfferTerms": {
                    "bestOfferEnabled": listing_policies.get(
                        "best_offer_enabled", False
                    )
                }
            },
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "de-DE",  # Для EBAY_DE
        }
        result = self.call_api(endpoint, "POST", data=offer, headers=headers)
        if result and "offerId" in result:
            logger.info(f"Предложение создано, ID: {result['offerId']}")
            return result["offerId"]
        logger.error("Не удалось создать предложение")
        return None

    def publish_offer(self, offer_id):
        """Публикация предложения"""
        endpoint = f"sell/inventory/v1/offer/{offer_id}/publish"
        result = self.call_api(endpoint, "POST")

        if result and "listingId" in result:
            logger.info(
                f"Предложение опубликовано, ID объявления: {result['listingId']}"
            )
            return result["listingId"]

        logger.error("Не удалось опубликовать предложение")
        return None


def load_product_data(file_path):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def upload_product():
    """Основная функция для выгрузки товара"""
    # Загрузка данных товара
    product_data = load_product_data("product_template.json")
    if not product_data:
        logger.error("Не удалось загрузить данные товара")
        return False

    # Инициализация клиента
    client = SimpleEbayClient()

    # Создание местоположения продавца
    logger.info("Создание местоположения продавца...")
    location_key = client.create_location()
    if not location_key:
        logger.error(
            "Не удалось создать местоположение. Попытка использования 'default'"
        )
        location_key = "default"

    # Создание товара в инвентаре
    sku = client.create_inventory_item("LAPTOP", product_data)
    if not sku:
        return False

    # Ожидание синхронизации
    logger.info(f"Ожидание синхронизации (20 секунд)...")
    time.sleep(20)

    # Проверка наличия товара в инвентаре
    logger.info(f"Проверка наличия товара в инвентаре...")
    if not client.get_inventory_item(sku):
        logger.warning(
            f"Товар с SKU {sku} не найден в инвентаре. Повторная проверка..."
        )
        time.sleep(10)
        if not client.get_inventory_item(sku):
            logger.error(
                f"Товар с SKU {sku} не доступен. Невозможно создать предложение."
            )
            return False

    # Создание предложения
    logger.info(f"Создание предложения для товара с SKU: {sku}")
    offer_id = client.create_offer(sku, product_data, location_key)
    if not offer_id:
        return False

    # Публикация предложения
    logger.info(f"Публикация предложения с ID: {offer_id}")
    listing_id = client.publish_offer(offer_id)
    if not listing_id:
        return False

    logger.info(f"Товар успешно опубликован! ID объявления: {listing_id}")
    return True


if __name__ == "__main__":
    if upload_product():
        logger.info("Выгрузка товара завершена успешно!")
    else:
        logger.error("Не удалось выгрузить товар.")
