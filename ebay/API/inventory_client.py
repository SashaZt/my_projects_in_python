import json
from typing import Any, Dict, Optional

import requests
from auth import EbayAuth

# Настройка логирования
from logger import logger

from config import (
    BASE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    MERCHANT_LOCATION_KEY,
    PAYMENT_POLICY_ID,
    RETURN_POLICY_ID,
    RUNAME,
    SHIPPING_POLICY_ID,
)


class EbayInventoryClient:
    """Клиент для работы с Inventory API eBay"""

    def __init__(self, auth: Optional[EbayAuth] = None):
        """Инициализация клиента Inventory API"""
        self.auth = auth or EbayAuth(CLIENT_ID, CLIENT_SECRET)
        self.base_url = BASE_URL
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

            # Используем расширенный набор scopes
            full_scopes = [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly",
                "https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.item.draft",
                "https://api.ebay.com/oauth/api_scope/sell.item",
                "https://api.ebay.com/oauth/api_scope/sell.reputation",
                "https://api.ebay.com/oauth/api_scope/sell.reputation.readonly",
            ]

            # Если нет refresh токена или не удалось обновить токен,
            # нужно пройти процесс авторизации
            auth_url = self.auth.get_authorization_url(full_scopes)

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

    def create_location(self, merchant_location_key, location_data=None):
        """
        Создание местоположения продавца на eBay

        Args:
            merchant_location_key (str): Уникальный ключ местоположения
            location_data (dict, optional): Данные о местоположении

        Returns:
            dict: Результат выполнения запроса
        """
        if not self.authenticate():
            logger.error("Не удалось аутентифицироваться для создания местоположения")
            return {"error": "Ошибка аутентификации"}

        endpoint = f"sell/inventory/v1/location/{merchant_location_key}"

        # Добавляем необходимые заголовки для API eBay
        headers = {
            "Content-Type": "application/json",
        }

        logger.info(f"Создание местоположения с ключом: {merchant_location_key}")
        logger.debug(f"Полный URL запроса: {self.base_url}/{endpoint}")
        logger.debug(f"Данные запроса: {json.dumps(location_data, indent=2)}")

        # Непосредственно перед отправкой запроса проверяем токен
        if not self.access_token:
            logger.error("Отсутствует токен доступа")
            return {"error": "Токен доступа отсутствует"}

        # Используем PUT запрос для создания/обновления местоположения
        result = self._call_api(endpoint, "POST", data=location_data, headers=headers)

        # Код 204 означает успешное создание без содержимого в ответе
        if isinstance(result, dict) and result.get("success", False):
            logger.info(f"Местоположение {merchant_location_key} успешно создано")
            return {"success": True, "merchantLocationKey": merchant_location_key}

        # Если получили ошибку, логируем подробную информацию
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Не удалось создать местоположение: {result['error']}")
        else:
            logger.error(f"Не удалось создать местоположение: {result}")

        return result

    # def ensure_default_location(self):
    #     """Создание местоположения по умолчанию, если оно не существует"""
    #     endpoint = "sell/inventory/v1/location/default"

    #     location_data = {
    #         "location": {
    #             "address": {
    #                 "addressLine1": "123 Main Street",
    #                 "city": "Berlin",
    #                 "country": "DE",
    #                 "postalCode": "10115",
    #                 "stateOrProvince": "Berlin",
    #             }
    #         },
    #         "locationInstructions": "Default location",
    #         "name": "Default Location",
    #         "merchantLocationStatus": "ENABLED",
    #     }

    #     return self._call_api(endpoint, "PUT", data=location_data)

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Базовый метод для вызова API eBay Inventory"""
        if not self.access_token and not self.authenticate():
            logger.error("Не удалось аутентифицироваться. Невозможно выполнить запрос.")
            return {"error": "Ошибка аутентификации"}

        url = f"{self.base_url}/{endpoint}"

        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Добавляем дополнительные заголовки, если они предоставлены
        if headers:
            request_headers.update(headers)

        try:
            logger.debug(f"Отправка {method} запроса на {url}")
            logger.debug(f"Заголовки: {request_headers}")

            if method.upper() == "GET":
                logger.debug(f"Параметры запроса: {params}")
                response = requests.get(
                    url, headers=request_headers, params=params, timeout=30
                )
            elif method.upper() == "POST":
                logger.debug(f"Данные запроса: {data}")
                response = requests.post(
                    url, headers=request_headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "PUT":
                logger.debug(f"Данные запроса: {data}")
                response = requests.put(
                    url, headers=request_headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "DELETE":
                logger.debug(f"Параметры запроса: {params}")
                response = requests.delete(
                    url, headers=request_headers, params=params, timeout=30
                )
            else:
                logger.error(f"Неподдерживаемый HTTP метод: {method}")
                return {"error": f"Неподдерживаемый HTTP метод: {method}"}

            logger.debug(f"Код ответа: {response.status_code}")

            # Обработка кодов ответа
            if response.status_code == 204:  # No Content
                logger.info("Успешный запрос с кодом 204 (No Content)")
                return {"success": True}

            # Для всех остальных кодов пытаемся получить содержимое ответа
            response.raise_for_status()

            # Проверка на пустой ответ
            if not response.content:
                logger.warning("Получен пустой ответ")
                return {"success": True}  # Предполагаем успех при пустом ответе

            response_data = response.json()
            logger.debug(f"Получен ответ: {response_data}")
            return response_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при вызове API: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Код ошибки: {e.response.status_code}")

                # Более подробное логирование ошибок eBay
                try:
                    error_data = e.response.json()
                    if "errors" in error_data:
                        for error in error_data["errors"]:
                            logger.error(
                                f"Ошибка eBay: {error.get('message', 'Неизвестная ошибка')}"
                            )
                            if "longMessage" in error:
                                logger.error(
                                    f"Подробное описание: {error['longMessage']}"
                                )
                            if "parameters" in error:
                                logger.error(f"Параметры ошибки: {error['parameters']}")

                    logger.error(f"Полное содержание ответа: {error_data}")
                except Exception as json_error:
                    logger.error(f"Ответ сервера (не JSON): {e.response.text}")

                # Попытка обновления токена при ошибке авторизации
                if e.response.status_code == 401:
                    logger.info("Попытка обновления токена...")
                    if self.authenticate():
                        logger.info("Токен обновлен, повторная попытка вызова API...")
                        return self._call_api(endpoint, method, params, data, headers)

            return {
                "error": str(e),
                "details": (
                    e.response.text
                    if hasattr(e, "response") and e.response is not None
                    else ""
                ),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при вызове API: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при вызове API: {e}")
            import traceback

            logger.error(f"Трассировка: {traceback.format_exc()}")
            return {"error": f"Непредвиденная ошибка: {str(e)}"}

    def create_inventory_item(
        self, sku: str, inventory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создание товара в инвентаре (Inventory Item)"""
        endpoint = f"sell/inventory/v1/inventory_item/{sku}"

        # Подготовка данных для инвентаря (это первый шаг - создание товара в инвентаре)
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

        # Добавляем обязательные заголовки для API eBay
        headers = {
            "Content-Type": "application/json",
            "Content-Language": "de-DE",  # или другой язык, например "de-DE" для немецкого
        }

        # Запрос на создание/обновление товара в инвентаре
        return self._call_api(endpoint, "PUT", data=inventory_item, headers=headers)

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
            "listingPolicies": {
                "paymentPolicyId": PAYMENT_POLICY_ID,
                "returnPolicyId": RETURN_POLICY_ID,
                "fulfillmentPolicyId": SHIPPING_POLICY_ID,
            },
            "pricingSummary": {
                "price": {
                    "value": str(offer_data.get("price", {}).get("value", 0)),
                    "currency": offer_data.get("price", {}).get("currency", "EUR"),
                }
            },
            "merchantLocationKey": MERCHANT_LOCATION_KEY,
        }

        # Добавление настроек объявления
        if "listing_policies" in offer_data:
            policies = offer_data["listing_policies"]
            if "best_offer_enabled" in policies:
                offer["listingPolicies"]["bestOfferEnabled"] = policies[
                    "best_offer_enabled"
                ]
            if "listing_duration" in policies:
                offer["listingDuration"] = policies["listing_duration"]

        # Запрос на создание предложения
        return self._call_api(endpoint, "POST", data=offer)

    def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        """Публикация предложения (Offer) на eBay"""
        endpoint = f"sell/inventory/v1/offer/{offer_id}/publish"
        return self._call_api(endpoint, "POST")
