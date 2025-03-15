# create_location_corrected.py
import json

import requests
from auth import EbayAuth
from logger import logger


def create_location_corrected():
    """
    Создание местоположения в соответствии с документацией eBay API
    https://developer.ebay.com/api-docs/sell/inventory/resources/location/methods/createOrReplaceInventoryLocation
    """
    # Инициализируем авторизацию
    auth = EbayAuth()

    # Получаем токен доступа
    if not auth.user_token:
        logger.error("Не найден User токен. Необходима авторизация пользователя.")
        return False

    # Генерируем уникальный ключ местоположения
    import random

    merchant_location_key = f"test-loc-{random.randint(1000, 9999)}"

    # URL для создания местоположения
    url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location/{merchant_location_key}"

    # Заголовки запроса (в соответствии с документацией)
    headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Language": "en-US",
    }

    # Данные для создания местоположения (минимальный набор полей по документации)
    data = {
        "location": {
            "address": {
                "addressLine1": "123 Main Street",
                "city": "Berlin",
                "country": "DE",
                "postalCode": "10115",
            },
            "name": "Test Location",
            "merchantLocationStatus": "ENABLED",
        },
        "locationTypes": ["WAREHOUSE"],
    }

    logger.info(f"Создание местоположения с ключом: {merchant_location_key}")
    logger.debug(f"URL запроса: {url}")
    logger.debug(f"Данные запроса: {json.dumps(data, indent=2)}")

    try:
        # Отправляем PUT запрос для создания местоположения
        response = requests.put(url, headers=headers, json=data, timeout=30)

        # Код 204 означает успешное создание без содержимого в ответе
        if response.status_code == 204:
            logger.info(f"Местоположение {merchant_location_key} успешно создано")
            return {"success": True, "merchantLocationKey": merchant_location_key}

        # Обработка ошибок
        logger.error(
            f"Ошибка при создании местоположения: {response.status_code} {response.reason}"
        )

        try:
            error_data = response.json()
            logger.error(f"Ответ сервера: {json.dumps(error_data, indent=2)}")

            # Анализ ошибок
            if "errors" in error_data:
                for error in error_data["errors"]:
                    logger.error(f"Ошибка eBay: {error.get('message')}")
                    if "longMessage" in error:
                        logger.error(f"Подробно: {error['longMessage']}")
                    if "parameters" in error:
                        for param in error["parameters"]:
                            logger.error(
                                f"Параметр {param.get('name')}: {param.get('value')}"
                            )

            # Попробуем альтернативные варианты данных
            if response.status_code == 400:
                logger.info(
                    "Попытка создания местоположения с альтернативной структурой данных..."
                )
                return create_location_alternative()

            return {
                "error": f"{response.status_code} {response.reason}",
                "details": error_data,
            }
        except:
            logger.error(f"Ответ сервера (не JSON): {response.text}")
            return {
                "error": f"{response.status_code} {response.reason}",
                "details": response.text,
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return {"error": str(e)}


def create_location_alternative():
    """Альтернативный вариант создания местоположения"""
    # Инициализируем авторизацию
    auth = EbayAuth()

    # Получаем токен доступа
    if not auth.user_token:
        logger.error("Не найден User токен. Необходима авторизация пользователя.")
        return False

    # Генерируем уникальный ключ местоположения
    import random

    merchant_location_key = f"testloc{random.randint(1000, 9999)}"  # Без дефисов

    # URL для создания местоположения
    url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location/{merchant_location_key}"

    # Заголовки запроса (в соответствии с документацией)
    headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Language": "en-US",
    }

    # Альтернативная структура данных (на основе примера из документации)
    data = {
        "location": {
            "address": {
                "addressLine1": "2722 Main Street",
                "city": "Berlin",
                "country": "DE",
                "postalCode": "10115",
            },
            "name": "Test Location Alternative",
            "merchantLocationStatus": "ENABLED",
        },
        "locationTypes": ["WAREHOUSE"],
        "locationWebUrl": "https://example.com",  # Добавляем дополнительное поле
    }

    logger.info(
        f"Создание местоположения (альтернативный вариант) с ключом: {merchant_location_key}"
    )
    logger.debug(f"URL запроса: {url}")
    logger.debug(f"Данные запроса: {json.dumps(data, indent=2)}")

    try:
        # Отправляем PUT запрос для создания местоположения
        response = requests.put(url, headers=headers, json=data, timeout=30)

        # Код 204 означает успешное создание без содержимого в ответе
        if response.status_code == 204:
            logger.info(f"Местоположение {merchant_location_key} успешно создано")
            return {"success": True, "merchantLocationKey": merchant_location_key}

        # Обработка ошибок
        logger.error(
            f"Ошибка при создании местоположения (альтернативный вариант): {response.status_code} {response.reason}"
        )

        try:
            error_data = response.json()
            logger.error(f"Ответ сервера: {json.dumps(error_data, indent=2)}")
            return {
                "error": f"{response.status_code} {response.reason}",
                "details": error_data,
            }
        except:
            logger.error(f"Ответ сервера (не JSON): {response.text}")
            return {
                "error": f"{response.status_code} {response.reason}",
                "details": response.text,
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    result = create_location_corrected()
    print(f"Результат: {result}")
