# offer_management.py
"""
Модуль для управления предложениями (offers) на eBay через Inventory API.
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import inventory_management as inventory
import requests
from inventory_client import EbayInventoryClient
from logger import logger
from setup_policies import create_seller_policies, get_seller_policies

current_directory = Path.cwd()
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
payment_policy_file_path = config_directory / "policy_ids.json"


def load_policy_data(json_file: str) -> Dict[str, Any]:
    """Загрузка данных политики из JSON-файла"""
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


policy_ids = load_policy_data(payment_policy_file_path)

MERCHANT_LOCATION_KEY = policy_ids.get("MERCHANT_LOCATION_KEY", "")
PAYMENT_POLICY_ID = policy_ids.get("PAYMENT_POLICY_ID", "")
RETURN_POLICY_ID = policy_ids.get("RETURN_POLICY_ID", "")
SHIPPING_POLICY_ID = policy_ids.get("SHIPPING_POLICY_ID", "")


def get_policy_ids() -> Dict[str, str]:
    """
    Получение актуальных ID политик продавца

    Returns:
        dict: Словарь с ID политик или пустой словарь в случае ошибки
    """
    logger.info("Получение актуальных ID политик продавца...")

    # Если файл не существует или в нем нет всех политик, пытаемся получить их через API
    policy_result = get_seller_policies()
    if not policy_result:
        logger.warning("Не удалось получить ID политик через API. Попытка создания...")
        if not create_seller_policies():
            logger.error("Не удалось создать политики продавца")
            return {}

        # Пробуем снова получить политики после создания
        policy_result = get_seller_policies()
        if not policy_result:
            logger.error("Не удалось получить ID политик после создания")
            return {}

    return {}


def create_offer(sku: str, offer_data: Dict[str, Any]) -> Union[Dict[str, Any], None]:
    """
    Создание предложения для товара

    Args:
        sku (str): SKU товара
        offer_data (dict): Данные предложения
        brand_name (str): Название бренда (если не указано в данных товара)

    Returns:
        dict: Результат создания предложения или None в случае ошибки
    """
    logger.info(f"Создание предложения для товара с SKU: {sku}")

    # Проверяем доступ к API
    if not inventory.check_inventory_api_access():
        logger.error("Нет доступа к Inventory API. Создание предложения невозможно.")
        return None

    # Проверяем существование товара в инвентаре и обновляем бренд
    item = inventory.get_inventory_item(sku)
    if not item:
        logger.warning(f"Товар с SKU {sku} не найден в инвентаре. Попытка создания...")

    # Инициализируем клиент и выполняем запрос
    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    # Выполняем запрос на создание предложения
    endpoint = "sell/inventory/v1/offer"
    headers = {
        "Content-Type": "application/json",
        "Content-Language": "de-DE",
    }

    logger.info(f"Отправка запроса на создание предложения для SKU: {sku}")
    result = client._call_api(endpoint, "POST", data=offer_data, headers=headers)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при создании предложения: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при создании предложения: {result['error']}")
        return None

    if not isinstance(result, dict) or "offerId" not in result:
        logger.error("Не удалось получить ID предложения")
        return None

    logger.info(f"Предложение успешно создано, ID: {result['offerId']}")
    return result


def publish_offer(offer_id: str) -> Union[Dict[str, Any], None]:
    """
    Публикация предложения на eBay

    Args:
        offer_id (str): ID предложения

    Returns:
        dict: Результат публикации или None в случае ошибки
    """
    logger.info(f"Публикация предложения с ID: {offer_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/inventory/v1/offer/{offer_id}/publish"
    result = client._call_api(endpoint, "POST")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при публикации предложения: {result['errors']}")
        for error in result.get("errors", []):
            logger.error(f"Ошибка eBay: {error.get('message', '')}")
            if "longMessage" in error:
                logger.error(f"Подробности: {error['longMessage']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при публикации предложения: {result['error']}")
        return None

    if not isinstance(result, dict) or "listingId" not in result:
        logger.error("Не удалось получить ID опубликованного объявления")
        return None

    listing_id = result["listingId"]
    logger.info(f"Предложение успешно опубликовано! ID объявления: {listing_id}")
    logger.info(f"URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}")

    return result


def get_offer(offer_id: str) -> Union[Dict[str, Any], None]:
    """
    Получение информации о предложении по его ID

    Args:
        offer_id (str): ID предложения

    Returns:
        dict: Данные предложения или None в случае ошибки
    """
    logger.info(f"Получение информации о предложении с ID: {offer_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/inventory/v1/offer/{offer_id}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении предложения: {result['errors']}")
        return None

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении предложения: {result['error']}")
        return None

    return result


def update_offer(offer_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Обновление предложения

    Args:
        offer_id (str): ID предложения
        update_data (dict): Данные для обновления

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление предложения с ID: {offer_id}")

    # Получаем текущие данные предложения
    current_offer = get_offer(offer_id)
    if not current_offer:
        logger.error(f"Не удалось получить данные предложения с ID: {offer_id}")
        return False

    # Обновляем данные
    for key, value in update_data.items():
        if key in current_offer:
            if isinstance(value, dict) and isinstance(current_offer[key], dict):
                # Рекурсивно обновляем вложенные словари
                current_offer[key].update(value)
            else:
                current_offer[key] = value
        else:
            current_offer[key] = value

    # Выполняем запрос на обновление
    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/inventory/v1/offer/{offer_id}"
    headers = {
        "Content-Type": "application/json",
        "Content-Language": "de-DE",
        "Accept-Language": "de-DE",
    }

    result = client._call_api(endpoint, "PUT", data=current_offer, headers=headers)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при обновлении предложения: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при обновлении предложения: {result['error']}")
        return False

    logger.info(f"Предложение успешно обновлено: {offer_id}")
    return True


def delete_offer(offer_id: str) -> bool:
    """
    Удаление предложения

    Args:
        offer_id (str): ID предложения

    Returns:
        bool: Результат операции
    """
    logger.info(f"Удаление предложения с ID: {offer_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/inventory/v1/offer/{offer_id}"
    result = client._call_api(endpoint, "DELETE")

    # Успешное удаление обычно возвращает пустой ответ (204 No Content)
    if result is None or (isinstance(result, dict) and not result):
        logger.info(f"Предложение успешно удалено: {offer_id}")
        return True

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при удалении предложения: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при удалении предложения: {result['error']}")
        return False

    logger.info(f"Предложение успешно удалено: {offer_id}")
    return True


def get_offers_by_sku(
    sku: str, marketplace_id: str = None, format_type: str = None
) -> List[Dict[str, Any]]:
    """
    Получение всех предложений для указанного SKU

    Args:
        sku (str): SKU товара
        marketplace_id (str, optional): ID маркетплейса (например, EBAY_DE)
        format_type (str, optional): Тип формата (FIXED_PRICE или AUCTION)

    Returns:
        list: Список предложений
    """
    logger.info(f"Получение предложений для SKU: {sku}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return []

    # Формирование параметров запроса
    params = {"sku": sku}

    if marketplace_id:
        params["marketplace_id"] = marketplace_id

    if format_type:
        params["format"] = format_type

    # Выполнение запроса
    endpoint = "sell/inventory/v1/offer"
    result = client._call_api(endpoint, "GET", params=params)

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при получении предложений: {result['errors']}")
        return []

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при получении предложений: {result['error']}")
        return []

    if not isinstance(result, dict):
        logger.error(f"Неожиданный ответ: {result}")
        return []

    offers = result.get("offers", [])
    logger.info(f"Найдено предложений для SKU {sku}: {len(offers)}")

    # Вывод информации о найденных предложениях
    for i, offer in enumerate(offers, 1):
        offer_id = offer.get("offerId", "Н/Д")
        status = offer.get("status", "Н/Д")
        marketplace = offer.get("marketplaceId", "Н/Д")
        format_type = offer.get("format", "Н/Д")

        logger.info(f"Предложение #{i}:")
        logger.info(f"  ID: {offer_id}")
        logger.info(f"  Статус: {status}")
        logger.info(f"  Маркетплейс: {marketplace}")
        logger.info(f"  Формат: {format_type}")

        # Если предложение опубликовано, показываем ID листинга
        if status == "PUBLISHED":
            listing_id = offer.get("listingId", "Н/Д")
            logger.info(f"  ID листинга: {listing_id}")
            logger.info(f"  URL листинга: https://www.sandbox.ebay.de/itm/{listing_id}")

    return offers


def withdraw_offer(offer_id: str) -> bool:
    """
    Отзыв опубликованного предложения

    Args:
        offer_id (str): ID предложения

    Returns:
        bool: Результат операции
    """
    logger.info(f"Отзыв опубликованного предложения с ID: {offer_id}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/inventory/v1/offer/{offer_id}/withdraw"
    result = client._call_api(endpoint, "POST")

    if isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при отзыве предложения: {result['errors']}")
        return False

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при отзыве предложения: {result['error']}")
        return False

    logger.info(f"Предложение успешно отозвано: {offer_id}")
    return True


def create_and_publish_offer_from_json(
    json_file: str,
) -> Union[Dict[str, Any], None]:
    """
    Подготовка, создание и публикация предложения из JSON-файла

    Args:
        json_file (str): Путь к JSON-файлу с данными предложения
        brand_name (str): Название бренда для товара

    Returns:
        dict: Результат публикации или None в случае ошибки
    """
    logger.info(f"Подготовка и создание предложения из файла {json_file}")

    # Загрузка данных предложения из файла
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            offer_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл {json_file} не найден.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {json_file}.")
        return None
    sku = offer_data["sku"]
    offer_data["listingPolicies"]["fulfillmentPolicyId"] = policy_ids[
        "SHIPPING_POLICY_ID"
    ]
    offer_data["listingPolicies"]["paymentPolicyId"] = policy_ids["PAYMENT_POLICY_ID"]
    offer_data["listingPolicies"]["returnPolicyId"] = policy_ids["RETURN_POLICY_ID"]
    # Создаем предложение
    offer_result = create_offer(sku, offer_data)
    if not offer_result:
        logger.error("Не удалось создать предложение")
        return None

    offer_id = offer_result["offerId"]
    logger.info(f"Предложение успешно создано, ID: {offer_id}")

    # Публикуем предложение
    publish_result = publish_offer(offer_id)
    if not publish_result:
        logger.error("Не удалось опубликовать предложение")
        return None

    return publish_result


def update_offer_add_brand(offer_id: str, brand_name: str = "Orthomatic") -> bool:
    """
    Обновление предложения: добавление атрибута бренда

    Args:
        offer_id (str): ID предложения
        brand_name (str): Название бренда

    Returns:
        bool: Результат обновления
    """
    logger.info(f"Обновление предложения {offer_id}: добавление бренда {brand_name}")

    # Получаем данные о предложении
    offer_data = get_offer(offer_id)
    if not offer_data:
        logger.error(f"Не удалось получить предложение {offer_id}")
        return False

    # Получаем SKU товара
    sku = offer_data.get("sku")
    if not sku:
        logger.error(f"Не удалось получить SKU для предложения {offer_id}")
        return False

    # Обновляем бренд товара в инвентаре
    if not inventory.update_inventory_item_brand(sku, brand_name):
        logger.error(f"Не удалось обновить бренд товара с SKU {sku}")
        return False

    logger.info(f"Бренд товара успешно обновлен: {sku} -> {brand_name}")

    # Ждем синхронизацию данных
    logger.info("Ожидание синхронизации данных (5 секунд)...")
    time.sleep(5)

    return True


def main():
    """Основная функция для работы с модулем предложений"""
    print("=== Управление предложениями на eBay ===")
    print("1. Создать предложение из JSON-файла")
    print("2. Получить список предложений по SKU")
    print("3. Получить информацию о предложении по ID")
    print("4. Обновить бренд в предложении")
    print("5. Опубликовать предложение по ID")
    print("6. Отозвать опубликованное предложение")
    print("7. Удалить предложение")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        json_file = "offer.json"

        result = create_and_publish_offer_from_json(json_file)
        if result:
            listing_id = result.get("listingId", "Н/Д")
            print(f"Предложение успешно создано и опубликовано!")
            print(f"ID объявления: {listing_id}")
            print(f"URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}")
        else:
            print("Не удалось создать или опубликовать предложение.")

    elif choice == "2":
        sku = input("Введите SKU товара: ")
        marketplace = input(
            "Введите ID маркетплейса (необязательно, например EBAY_DE): "
        )
        format_type = input("Введите формат (необязательно, FIXED_PRICE или AUCTION): ")

        marketplace_id = marketplace if marketplace else None
        format_type = format_type if format_type else None

        offers = get_offers_by_sku(sku, marketplace_id, format_type)
        if offers:
            print(f"Найдено предложений: {len(offers)}")
            for i, offer in enumerate(offers, 1):
                offer_id = offer.get("offerId", "Н/Д")
                status = offer.get("status", "Н/Д")
                marketplace = offer.get("marketplaceId", "Н/Д")

                print(
                    f"{i}. ID: {offer_id}, Статус: {status}, Маркетплейс: {marketplace}"
                )

                if status == "PUBLISHED":
                    listing_id = offer.get("listingId", "Н/Д")
                    print(f"   ID объявления: {listing_id}")
                    print(
                        f"   URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}"
                    )
        else:
            print(f"Предложения для SKU {sku} не найдены или произошла ошибка.")

    elif choice == "3":
        offer_id = input("Введите ID предложения: ")
        offer = get_offer(offer_id)

        if offer:
            print("Информация о предложении:")
            sku = offer.get("sku", "Н/Д")
            status = offer.get("status", "Н/Д")
            marketplace = offer.get("marketplaceId", "Н/Д")
            format_type = offer.get("format", "Н/Д")

            print(f"ID: {offer_id}")
            print(f"SKU: {sku}")
            print(f"Статус: {status}")
            print(f"Маркетплейс: {marketplace}")
            print(f"Формат: {format_type}")

            if status == "PUBLISHED":
                listing_id = offer.get("listingId", "Н/Д")
                print(f"ID объявления: {listing_id}")
                print(f"URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}")
        else:
            print(f"Предложение с ID {offer_id} не найдено или произошла ошибка.")

    elif choice == "4":
        offer_id = input("Введите ID предложения: ")
        brand_name = (
            input("Введите название бренда (по умолчанию Orthomatic): ") or "Orthomatic"
        )

        if update_offer_add_brand(offer_id, brand_name):
            print(f"Бренд в предложении успешно обновлен: {brand_name}")

            # Спрашиваем, нужно ли переопубликовать
            if input("Перепубликовать предложение? (y/n): ").lower() == "y":
                if publish_offer(offer_id):
                    print("Предложение успешно переопубликовано!")
                else:
                    print("Не удалось переопубликовать предложение.")
        else:
            print("Не удалось обновить бренд в предложении.")

    elif choice == "5":
        offer_id = input("Введите ID предложения для публикации: ")

        result = publish_offer(offer_id)
        if result:
            listing_id = result.get("listingId", "Н/Д")
            print(f"Предложение успешно опубликовано!")
            print(f"ID объявления: {listing_id}")
            print(f"URL объявления: https://www.sandbox.ebay.de/itm/{listing_id}")
        else:
            print("Не удалось опубликовать предложение.")

    elif choice == "6":
        offer_id = input("Введите ID предложения для отзыва: ")

        if withdraw_offer(offer_id):
            print(f"Предложение успешно отозвано: {offer_id}")
        else:
            print("Не удалось отозвать предложение.")

    elif choice == "7":
        offer_id = input("Введите ID предложения для удаления: ")
        confirm = input(
            f"Вы уверены, что хотите удалить предложение с ID '{offer_id}'? (y/n): "
        )

        if confirm.lower() == "y":
            if delete_offer(offer_id):
                print(f"Предложение успешно удалено: {offer_id}")
            else:
                print("Не удалось удалить предложение.")
        else:
            print("Операция отменена.")
    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
