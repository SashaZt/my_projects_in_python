import json
import logging
import time

import requests
from auth import EbayAuth
from logger import logger


class SimpleUploadClient:
    def __init__(self):
        # Инициализация EbayAuth и получение токена
        self.auth = EbayAuth()
        if hasattr(self.auth, "user_token") and self.auth.user_token:
            self.token = self.auth.user_token.get("access_token")
            logger.info("Используется существующий токен")
        else:
            logger.error(
                "Токен не найден. Запустите setup_policies.py для получения токена"
            )
            self.token = None

    def create_item(self):
        """Создание товара с минимальным набором полей"""
        if not self.token:
            return False

        # Генерация уникального SKU
        sku = f"LAPTOP-{int(time.time())}"

        # Шаг 1: Создание товара в инвентаре
        inventory_url = (
            f"https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/{sku}"
        )
        inventory_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
        }

        inventory_data = {
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "condition": "USED_EXCELLENT",
            "product": {
                "title": "HP EliteBook 840 G6 Laptop - i5, 16GB RAM, 512GB SSD",
                "description": "<p>Excellent condition business laptop with Windows 10 Pro</p>",
                "aspects": {
                    "Brand": ["HP"],
                    "Model": ["EliteBook 840 G6"],
                    "Operating System": ["Windows 10 Pro"],
                },
                "imageUrls": [
                    "https://i.ebayimg.com/images/g/5J4AAOSwvBdihbj9/s-l1600.jpg"
                ],
            },
        }

        try:
            inventory_response = requests.put(
                inventory_url,
                headers=inventory_headers,
                json=inventory_data,
                timeout=30,
            )
            inventory_response.raise_for_status()
            logger.info(f"Товар успешно создан в инвентаре с SKU: {sku}")

            # Ожидание синхронизации
            logger.info("Ожидание синхронизации (20 секунд)...")
            time.sleep(20)

            # Шаг 2: Создание местоположения продавца
            location_key = f"loc-{int(time.time())}"
            location_url = f"https://api.sandbox.ebay.com/sell/inventory/v1/location/{location_key}"

            location_data = {
                "location": {
                    "address": {
                        "addressLine1": "123 Main Street",
                        "city": "Berlin",
                        "countryCode": "DE",
                        "postalCode": "10115",
                    }
                },
                "name": "Default Location",
                "merchantLocationStatus": "ENABLED",
            }

            location_response = requests.put(
                location_url, headers=inventory_headers, json=location_data, timeout=30
            )

            if (
                location_response.status_code != 204
                and location_response.status_code != 200
            ):
                logger.warning(
                    f"Предупреждение при создании местоположения: {location_response.text}"
                )
                location_key = "default"  # Попробуем использовать default
            else:
                logger.info(f"Создано местоположение продавца с ключом: {location_key}")

            # Шаг 3: Создание предложения
            offer_url = "https://api.sandbox.ebay.com/sell/inventory/v1/offer"

            offer_data = {
                "sku": sku,
                "marketplaceId": "EBAY_DE",
                "format": "FIXED_PRICE",
                "availableQuantity": 1,
                "categoryId": "177",
                "merchantLocationKey": location_key,
                "pricingSummary": {"price": {"value": "599.99", "currency": "EUR"}},
                "listingDescription": "<p>HP EliteBook 840 G6 in excellent condition</p>",
                "listingDuration": "GTC",
                "shippingOptions": [
                    {
                        "costType": "FLAT_RATE",
                        "optionType": "DOMESTIC",
                        "shippingServices": [
                            {
                                "shippingServiceCode": "Standard",
                                "shippingCost": {"currency": "EUR", "value": "5.99"},
                            }
                        ],
                    }
                ],
                "returnTerms": {
                    "returnsAccepted": True,
                    "returnPeriod": {"value": 30, "unit": "DAY"},
                    "returnMethod": "MONEY_BACK",
                    "returnShippingCostPayer": "SELLER",
                },
            }

            offer_response = requests.post(
                offer_url, headers=inventory_headers, json=offer_data, timeout=30
            )

            if offer_response.status_code != 200:
                logger.error(f"Ошибка при создании предложения: {offer_response.text}")
                return False

            offer_result = offer_response.json()
            if "offerId" not in offer_result:
                logger.error("Не удалось получить ID предложения")
                return False

            offer_id = offer_result["offerId"]
            logger.info(f"Предложение создано, ID: {offer_id}")

            # Шаг 4: Публикация предложения
            publish_url = f"https://api.sandbox.ebay.com/sell/inventory/v1/offer/{offer_id}/publish"

            publish_response = requests.post(
                publish_url, headers=inventory_headers, json={}, timeout=30
            )

            if publish_response.status_code != 200:
                logger.error(
                    f"Ошибка при публикации предложения: {publish_response.text}"
                )
                return False

            publish_result = publish_response.json()
            if "listingId" in publish_result:
                listing_id = publish_result["listingId"]
                logger.info(
                    f"Товар успешно опубликован на eBay, ID объявления: {listing_id}"
                )
                return True
            else:
                logger.error("Не удалось получить ID опубликованного объявления")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return False


if __name__ == "__main__":
    client = SimpleUploadClient()
    if client.create_item():
        logger.info("Товар успешно опубликован на eBay!")
    else:
        logger.error("Не удалось опубликовать товар.")
