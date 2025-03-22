# ebay_location_creator.py
import json
import requests
from auth import EbayAuth
from logger import logger

def create_warehouse_location():
    """
    Создание склада (warehouse) в eBay Inventory API согласно официальной документации
    """
    # Инициализация авторизации
    auth = EbayAuth()
    
    # Проверка токена
    if not auth.user_token:
        logger.error("Не найден User токен. Необходима авторизация пользователя.")
        return False
    
    # Создаем уникальный ключ местоположения (без дефисов и специальных символов)
    location_key = "warehouse101" # Простой алфавитно-цифровой ключ
    
    # Формируем URL запроса (обратите внимание, используется PUT, а не POST!)
    url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location/{location_key}"
    
    # Формируем заголовки в соответствии с документацией
    headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Language": "en-US" # Важно указать язык
    }
    
    # Формируем минимальное тело запроса для warehouse (склада)
    # Для warehouse достаточно указать postalCode + country ИЛИ city + stateOrProvince + country
    payload = {
        "location": {
            "address": {
                "city": "Berlin",
                "stateOrProvince": "Berlin",
                "country": "DE",
                "postalCode": "10115"
            },
            "name": "Berlin Warehouse",
            "merchantLocationStatus": "ENABLED"
        },
        "locationTypes": ["WAREHOUSE"]
    }
    
    logger.info(f"Создание местоположения типа WAREHOUSE с ключом: {location_key}")
    logger.debug(f"URL запроса: {url}")
    logger.debug(f"Заголовки: {headers}")
    logger.debug(f"Тело запроса: {json.dumps(payload, indent=2)}")
    
    try:
        # Отправляем запрос (PUT, а не POST!)
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        
        # Обработка ответа
        if response.status_code == 204:  # Ожидаемый код успешного ответа согласно документации
            logger.info(f"✅ Местоположение успешно создано: {location_key}")
            return True
        else:
            logger.error(f"❌ Ошибка при создании местоположения: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Ответ сервера: {json.dumps(error_data, indent=2)}")
                
                # Анализ ошибок
                if "errors" in error_data:
                    for error in error_data["errors"]:
                        logger.error(f"Ошибка ID: {error.get('errorId')}")
                        logger.error(f"Домен: {error.get('domain')}")
                        logger.error(f"Категория: {error.get('category')}")
                        logger.error(f"Сообщение: {error.get('message')}")
                        if "longMessage" in error:
                            logger.error(f"Подробное сообщение: {error['longMessage']}")
                        if "parameters" in error:
                            for param in error["parameters"]:
                                logger.error(f"Параметр {param.get('name')}: {param.get('value')}")
            except:
                logger.error(f"Ответ сервера (не JSON): {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при выполнении запроса: {e}")
        return False


def create_store_location():
    """
    Создание магазина (store) в eBay Inventory API согласно официальной документации
    """
    # Инициализация авторизации
    auth = EbayAuth()
    
    # Проверка токена
    if not auth.user_token:
        logger.error("Не найден User токен. Необходима авторизация пользователя.")
        return False
    
    # Создаем уникальный ключ местоположения (без дефисов и специальных символов)
    location_key = "store101" # Простой алфавитно-цифровой ключ
    
    # Формируем URL запроса (обратите внимание, используется PUT, а не POST!)
    url = f"{auth.token_storage.get_base_url()}/sell/inventory/v1/location/{location_key}"
    
    # Формируем заголовки в соответствии с документацией
    headers = {
        "Authorization": f"Bearer {auth.user_token['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Language": "en-US" # Важно указать язык
    }
    
    # Формируем полное тело запроса для store (магазина) согласно документации
    # Для магазина требуется полный адрес и geoCoordinates
    payload = {
        "location": {
            "address": {
                "addressLine1": "123 Main Street",
                "city": "Berlin",
                "stateOrProvince": "Berlin",
                "country": "DE",
                "postalCode": "10115"
            },
            "geoCoordinates": {
                "latitude": 52.520008,
                "longitude": 13.404954
            },
            "name": "Berlin Store",
            "merchantLocationStatus": "ENABLED",
            "phone": "+4912345678"  # Телефон обязателен для store
        },
        "locationTypes": ["STORE"],
        # Часы работы рекомендуются для магазинов
        "operatingHours": [
            {
                "dayOfWeekEnum": "MONDAY",
                "intervals": [
                    {
                        "open": "09:00:00",
                        "close": "20:00:00"
                    }
                ]
            },
            {
                "dayOfWeekEnum": "TUESDAY",
                "intervals": [
                    {
                        "open": "09:00:00",
                        "close": "20:00:00"
                    }
                ]
            },
            {
                "dayOfWeekEnum": "WEDNESDAY",
                "intervals": [
                    {
                        "open": "09:00:00",
                        "close": "20:00:00"
                    }
                ]
            },
            {
                "dayOfWeekEnum": "THURSDAY",
                "intervals": [
                    {
                        "open": "09:00:00",
                        "close": "20:00:00"
                    }
                ]
            },
            {
                "dayOfWeekEnum": "FRIDAY",
                "intervals": [
                    {
                        "open": "09:00:00",
                        "close": "20:00:00"
                    }
                ]
            },
            {
                "dayOfWeekEnum": "SATURDAY",
                "intervals": [
                    {
                        "open": "10:00:00",
                        "close": "18:00:00"
                    }
                ]
            }
        ],
        "locationInstructions": "Please use the side entrance for pickups."
    }
    
    logger.info(f"Создание местоположения типа STORE с ключом: {location_key}")
    logger.debug(f"URL запроса: {url}")
    logger.debug(f"Заголовки: {headers}")
    logger.debug(f"Тело запроса: {json.dumps(payload, indent=2)}")
    
    try:
        # Отправляем запрос (PUT, а не POST!)
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        
        # Обработка ответа
        if response.status_code == 204:  # Ожидаемый код успешного ответа согласно документации
            logger.info(f"✅ Магазин успешно создан: {location_key}")
            return True
        else:
            logger.error(f"❌ Ошибка при создании магазина: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Ответ сервера: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Ответ сервера (не JSON): {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при выполнении запроса: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Создание местоположения в eBay Inventory API ===")
    print("1. Создать местоположение типа WAREHOUSE (склад)")
    print("2. Создать местоположение типа STORE (магазин)")
    print("0. Выход")
    
    choice = input("Выберите действие: ")
    
    if choice == "1":
        create_warehouse_location()
    elif choice == "2":
        create_store_location()
    else:
        print("Выход из программы")