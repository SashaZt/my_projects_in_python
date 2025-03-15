# api_tester.py
import json

import requests
from auth import EbayAuth
from logger import logger


def test_api_call(endpoint, method="GET", data=None, query_params=None, headers=None):
    """
    Прямой вызов API eBay для тестирования

    Args:
        endpoint (str): Эндпоинт API (без базового URL)
        method (str): HTTP метод (GET, POST, PUT, DELETE)
        data (dict, optional): Данные для отправки в теле запроса
        query_params (dict, optional): Параметры запроса
        headers (dict, optional): Дополнительные заголовки

    Returns:
        dict: Результат выполнения запроса
    """
    # Инициализируем авторизацию
    auth = EbayAuth()

    # Получаем токен пользователя (для Inventory API требуется User токен)
    if not hasattr(auth, "user_token") or not auth.user_token:
        logger.warning("Не найден User токен. Запрашиваем авторизацию пользователя.")
        if auth.refresh_token:
            token_data = auth.refresh_user_token()
            if not token_data:
                logger.error("Не удалось обновить User токен.")
                return None
        else:
            logger.error("Требуется авторизация пользователя.")
            return None

    # Полный URL запроса
    url = f"{auth.token_storage.get_base_url()}/{endpoint}"

    # Заголовки запроса
    request_headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Добавляем дополнительные заголовки
    if headers:
        request_headers.update(headers)

    logger.info(f"Отправка {method} запроса на {url}")
    logger.debug(f"Заголовки: {request_headers}")

    if data:
        logger.debug(f"Данные запроса: {json.dumps(data, indent=2)}")

    if query_params:
        logger.debug(f"Параметры запроса: {query_params}")

    try:
        if method.upper() == "GET":
            response = requests.get(
                url, headers=request_headers, params=query_params, timeout=30
            )
        elif method.upper() == "POST":
            response = requests.post(
                url, headers=request_headers, json=data, params=query_params, timeout=30
            )
        elif method.upper() == "PUT":
            response = requests.put(
                url, headers=request_headers, json=data, params=query_params, timeout=30
            )
        elif method.upper() == "DELETE":
            response = requests.delete(
                url, headers=request_headers, params=query_params, timeout=30
            )
        else:
            logger.error(f"Неподдерживаемый HTTP метод: {method}")
            return None

        logger.info(f"Код ответа: {response.status_code}")

        # Проверка на успешный ответ без контента
        if response.status_code == 204:
            logger.info("Успешный ответ (204 No Content)")
            return {"success": True}

        # Проверка на ошибку
        if response.status_code >= 400:
            logger.error(f"Ошибка запроса: {response.status_code}")
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

        # Проверка на пустой ответ
        if not response.content:
            logger.warning("Получен пустой ответ")
            return {"success": True}

        # Парсим JSON ответ
        try:
            response_data = response.json()
            logger.debug(f"Ответ сервера: {json.dumps(response_data, indent=2)}")
            return response_data
        except:
            logger.warning(f"Не удалось распарсить JSON: {response.text}")
            return {"success": True, "content": response.text}

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return {"error": str(e)}


def test_get_locations():
    """Тест получения местоположений"""
    return test_api_call("sell/inventory/v1/location")


def test_create_location():
    """Тест создания местоположения с различными вариантами данных"""
    # Вариант 1: Минимальная структура
    merchant_location_key = "test-location-minimal"
    data_minimal = {
        "location": {
            "address": {
                "addressLine1": "123 Main St",
                "city": "Berlin",
                "country": "DE",
                "postalCode": "10115",
            },
            "name": "Test Location Minimal",
            "merchantLocationStatus": "ENABLED",
        },
        "locationTypes": ["WAREHOUSE"],
    }

    headers = {"Content-Language": "en-US", "Accept-Language": "en-US"}

    logger.info("=== Тест создания местоположения (минимальная структура) ===")
    result_minimal = test_api_call(
        f"sell/inventory/v1/location/{merchant_location_key}",
        method="PUT",
        data=data_minimal,
        headers=headers,
    )

    if result_minimal and (
        result_minimal.get("success", False) or "merchantLocationKey" in result_minimal
    ):
        logger.info(f"Успешно создано местоположение: {merchant_location_key}")
        return True
    else:
        logger.error(
            f"Не удалось создать местоположение с минимальной структурой: {result_minimal}"
        )

        # Вариант 2: Структура без locationTypes
        logger.info("=== Тест создания местоположения (без locationTypes) ===")
        merchant_location_key = "test-location-no-types"
        data_no_types = {
            "location": {
                "address": {
                    "addressLine1": "123 Main St",
                    "city": "Berlin",
                    "country": "DE",
                    "postalCode": "10115",
                },
                "name": "Test Location No Types",
                "merchantLocationStatus": "ENABLED",
            }
        }

        result_no_types = test_api_call(
            f"sell/inventory/v1/location/{merchant_location_key}",
            method="PUT",
            data=data_no_types,
            headers=headers,
        )

        if result_no_types and (
            result_no_types.get("success", False)
            or "merchantLocationKey" in result_no_types
        ):
            logger.info(f"Успешно создано местоположение: {merchant_location_key}")
            return True
        else:
            logger.error(
                f"Не удалось создать местоположение без locationTypes: {result_no_types}"
            )

            # Вариант 3: Структура без стейта
            logger.info("=== Тест создания местоположения (без stateOrProvince) ===")
            merchant_location_key = "test-location-no-state"
            data_no_state = {
                "location": {
                    "address": {
                        "addressLine1": "123 Main St",
                        "city": "Berlin",
                        "country": "DE",
                        "postalCode": "10115",
                        # Без stateOrProvince
                    },
                    "name": "Test Location No State",
                    "merchantLocationStatus": "ENABLED",
                },
                "locationTypes": ["WAREHOUSE"],
            }

            result_no_state = test_api_call(
                f"sell/inventory/v1/location/{merchant_location_key}",
                method="PUT",
                data=data_no_state,
                headers=headers,
            )

            if result_no_state and (
                result_no_state.get("success", False)
                or "merchantLocationKey" in result_no_state
            ):
                logger.info(f"Успешно создано местоположение: {merchant_location_key}")
                return True
            else:
                logger.error(
                    f"Не удалось создать местоположение без stateOrProvince: {result_no_state}"
                )
                return False


def main():
    """Основная функция для тестирования API"""
    print("=== Tester API eBay ===")
    print("1. Получить список местоположений")
    print("2. Тест создания местоположения (разные варианты)")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        result = test_get_locations()
        if result and "locations" in result:
            print(f"Найдено {len(result['locations'])} местоположений")
        else:
            print("Не удалось получить местоположения или они отсутствуют")
    elif choice == "2":
        test_create_location()
    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
