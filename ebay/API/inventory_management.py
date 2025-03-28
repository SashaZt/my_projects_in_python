# inventory_management.py
"""
Модуль для управления инвентарем на eBay через Inventory API.
"""
import json
import time
from typing import Any, Dict, List, Optional, Union

import requests
from inventory_client import EbayInventoryClient
from logger import logger


def check_inventory_api_access() -> bool:
    """Проверка доступа к Inventory API"""
    logger.info("Проверка доступа к Inventory API...")
    # Инициализируем клиент, который имеет логику обновления токена
    client = EbayInventoryClient()

    # Проверяем аутентификацию
    if not client.authenticate():
        logger.error(
            "Не удалось аутентифицироваться для проверки доступа к Inventory API"
        )
        return False

    # Используем токен из клиента
    try:
        headers = {
            "Authorization": f"Bearer {client.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Отправляем запрос для получения списка товаров
        response = requests.get(
            f"{client.base_url}/sell/inventory/v1/inventory_item",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        # Анализируем ответ
        data = response.json()
        total_items = data.get("total", 0)
        logger.info(f"✅ Inventory API доступен, найдено товаров: {total_items}")

        # Вывод подробной информации о первых 3 товарах (если они есть)
        items = data.get("inventoryItems", [])
        if items:
            logger.info("Примеры товаров в инвентаре:")
            for i, item in enumerate(items[:3], 1):
                sku = item.get("sku", "Н/Д")
                title = item.get("product", {}).get("title", "Без названия")
                logger.info(f"  {i}. SKU: {sku}, Название: {title}")

        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке доступа к Inventory API: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Код ошибки: {e.response.status_code}")
            logger.error(f"Ответ сервера: {e.response.text}")

            # Попытка обновления токена при ошибке авторизации
            if e.response.status_code == 401:
                logger.info("Попытка обновления токена...")
                if client.authenticate():
                    logger.info("Токен обновлен, повторная попытка проверки доступа...")
                    return (
                        check_inventory_api_access()
                    )  # Рекурсивный вызов после обновления токена
        return False


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


def create_inventory_item(
    sku: str,
    product_data: Dict[str, Any],
) -> bool:
    """
    Создание товара в инвентаре eBay

    Args:
        sku (str): SKU товара
        product_data (dict): Данные товара
        brand_name (str, optional): Название бренда (если не указано в product_data)

    Returns:
        bool: Результат операции
    """
    logger.info(f"Создание товара в инвентаре с SKU: {sku}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Подготовка данных для инвентаря
    inventory_data = {}

    # Копируем необходимые поля из product_data
    if "product" in product_data:
        inventory_data["product"] = product_data["product"]
    else:
        inventory_data["product"] = {
            "title": product_data.get("title", "Товар без названия"),
            "description": product_data.get("description", "Описание отсутствует"),
        }

    # Проверяем наличие структуры для аспектов
    if "aspects" not in inventory_data["product"]:
        inventory_data["product"]["aspects"] = {}

    # Копируем данные о доступности
    if "availability" in product_data:
        inventory_data["availability"] = product_data["availability"]
    else:
        inventory_data["availability"] = {
            "shipToLocationAvailability": {"quantity": product_data.get("quantity", 10)}
        }

    # Выполняем запрос
    endpoint = f"sell/inventory/v1/inventory_item/{sku}"
    result = client._call_api(
        endpoint, "PUT", data=inventory_data, headers={"Content-Language": "de-DE"}
    )

    if not isinstance(result, dict):
        logger.info(f"Товар успешно создан в инвентаре с SKU: {sku}")
        return True
    elif "errors" in result:
        logger.error(f"Ошибка при создании товара в инвентаре: {result['errors']}")
        return False
    elif "error" in result:
        logger.error(f"Ошибка при создании товара в инвентаре: {result['error']}")
        return False
    else:
        logger.info(f"Товар успешно создан в инвентаре с SKU: {sku}")
        return True


def get_inventory_item(sku: str) -> Union[Dict[str, Any], None]:
    """
    Получение информации о товаре из инвентаря

    Args:
        sku (str): SKU товара

    Returns:
        dict: Данные товара или None в случае ошибки
    """
    logger.info(f"Получение данных товара с SKU: {sku}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return None

    endpoint = f"sell/inventory/v1/inventory_item/{sku}"
    result = client._call_api(endpoint, "GET")

    if isinstance(result, dict) and ("error" in result or "errors" in result):
        error = result.get("error") or result.get("errors")
        logger.error(f"Ошибка при получении данных товара: {error}")
        return None

    return result


def update_inventory_item(sku: str, update_data: Dict[str, Any]) -> bool:
    """
    Обновление товара в инвентаре

    Args:
        sku (str): SKU товара
        update_data (dict): Данные для обновления

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление товара в инвентаре с SKU: {sku}")

    # Получаем текущие данные товара
    current_data = get_inventory_item(sku)
    if not current_data:
        logger.error(f"Не удалось получить текущие данные товара с SKU: {sku}")
        return False

    # Обновляем данные
    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Объединяем текущие данные с обновлениями
    for key, value in update_data.items():
        if key in current_data:
            if isinstance(value, dict) and isinstance(current_data[key], dict):
                # Рекурсивно обновляем вложенные словари
                current_data[key].update(value)
            else:
                current_data[key] = value
        else:
            current_data[key] = value

    endpoint = f"sell/inventory/v1/inventory_item/{sku}"
    result = client._call_api(
        endpoint, "PUT", data=current_data, headers={"Content-Language": "de-DE"}
    )

    if not isinstance(result, dict):
        logger.info(f"Товар успешно обновлен в инвентаре: {sku}")
        return True
    elif "errors" in result:
        logger.error(f"Ошибка при обновлении товара: {result['errors']}")
        return False
    elif "error" in result:
        logger.error(f"Ошибка при обновлении товара: {result['error']}")
        return False
    else:
        logger.info(f"Товар успешно обновлен в инвентаре: {sku}")
        return True


def update_inventory_item_brand(sku: str, brand_name: str = "Orthomatic") -> bool:
    """
    Обновление бренда товара в инвентаре

    Args:
        sku (str): SKU товара
        brand_name (str): Название бренда

    Returns:
        bool: Результат операции
    """
    logger.info(f"Обновление бренда товара с SKU {sku}: {brand_name}")

    # Получаем текущие данные товара
    current_data = get_inventory_item(sku)
    if not current_data:
        logger.error(f"Не удалось получить текущие данные товара с SKU: {sku}")

        # Пытаемся создать новый товар с минимальными данными
        minimal_data = {
            "product": {
                "title": f"Товар {sku}",
                "description": "Описание отсутствует",
                "aspects": {"Brand": [brand_name]},
            },
            "availability": {"shipToLocationAvailability": {"quantity": 10}},
        }

        return create_inventory_item(sku, minimal_data)

    # Обновляем бренд
    if "product" not in current_data:
        current_data["product"] = {}

    if "aspects" not in current_data["product"]:
        current_data["product"]["aspects"] = {}

    current_data["product"]["aspects"]["Brand"] = [brand_name]

    # Обновляем товар
    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/inventory/v1/inventory_item/{sku}"
    result = client._call_api(
        endpoint, "PUT", data=current_data, headers={"Content-Language": "de-DE"}
    )

    if not isinstance(result, dict):
        logger.info(f"Бренд товара успешно обновлен: {sku} -> {brand_name}")
        return True
    elif "errors" in result:
        logger.error(f"Ошибка при обновлении бренда товара: {result['errors']}")
        return False
    elif "error" in result:
        logger.error(f"Ошибка при обновлении бренда товара: {result['error']}")
        return False
    else:
        logger.info(f"Бренд товара успешно обновлен: {sku} -> {brand_name}")
        return True


def delete_inventory_item(sku: str) -> bool:
    """
    Удаление товара из инвентаря

    Args:
        sku (str): SKU товара

    Returns:
        bool: Результат операции
    """
    logger.info(f"Удаление товара из инвентаря с SKU: {sku}")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    endpoint = f"sell/inventory/v1/inventory_item/{sku}"
    result = client._call_api(endpoint, "DELETE")

    # Успешное удаление обычно возвращает пустой ответ (204 No Content)
    if result is None or (isinstance(result, dict) and not result):
        logger.info(f"Товар успешно удален из инвентаря: {sku}")
        return True
    elif isinstance(result, dict) and "errors" in result:
        logger.error(f"Ошибка при удалении товара: {result['errors']}")
        return False
    elif isinstance(result, dict) and "error" in result:
        logger.error(f"Ошибка при удалении товара: {result['error']}")
        return False
    else:
        logger.info(f"Товар успешно удален из инвентаря: {sku}")
        return True


def get_all_inventory_items(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Получение всех товаров из инвентаря

    Args:
        limit (int): Максимальное количество товаров для получения

    Returns:
        list: Список товаров
    """
    logger.info(f"Получение списка товаров из инвентаря (лимит: {limit})")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return []

    endpoint = "sell/inventory/v1/inventory_item"
    params = {"limit": limit}

    result = client._call_api(endpoint, "GET", params=params)

    if isinstance(result, dict) and "inventoryItems" in result:
        items = result.get("inventoryItems", [])
        total = result.get("total", 0)
        logger.info(f"Получено товаров: {len(items)} из {total}")
        return items
    else:
        logger.error("Не удалось получить список товаров")
        return []


def bulk_update_inventory_quantity(sku_quantity_map: Dict[str, int]) -> bool:
    """
    Массовое обновление количества товаров в инвентаре

    Args:
        sku_quantity_map (dict): Словарь соответствия SKU и количества

    Returns:
        bool: Результат операции
    """
    logger.info(f"Массовое обновление количества для {len(sku_quantity_map)} товаров")

    client = EbayInventoryClient()
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Подготавливаем данные для обновления
    bulk_quantity_request = {"requests": []}

    for sku, quantity in sku_quantity_map.items():
        bulk_quantity_request["requests"].append(
            {"sku": sku, "shipToLocationAvailability": {"quantity": quantity}}
        )

    endpoint = "sell/inventory/v1/bulk_update_inventory_item"
    result = client._call_api(endpoint, "POST", data=bulk_quantity_request)

    if isinstance(result, dict) and "responses" in result:
        responses = result.get("responses", [])
        success_count = sum(1 for resp in responses if resp.get("statusCode") == 200)
        logger.info(f"Успешно обновлено: {success_count} из {len(sku_quantity_map)}")

        # Логируем ошибки, если есть
        for resp in responses:
            if resp.get("statusCode") != 200:
                sku = resp.get("sku", "Н/Д")
                errors = resp.get("errors", [])
                for error in errors:
                    logger.error(
                        f"Ошибка при обновлении {sku}: {error.get('message', '')}"
                    )

        return success_count > 0
    else:
        logger.error("Ошибка при массовом обновлении количества")
        return False


def main():
    """Основная функция для работы с модулем инвентаря"""
    print("=== Управление инвентарем на eBay ===")
    print("1. Проверить доступ к Inventory API")
    print("2. Получить список всех товаров в инвентаре")
    print("3. Получить информацию о товаре по SKU")
    print("4. Создать товар в инвентаре из JSON-файла")
    print("5. Обновить бренд товара")
    print("6. Обновить количество товара")
    print("7. Удалить товар из инвентаря")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        if check_inventory_api_access():
            print("Доступ к Inventory API подтвержден.")
        else:
            print("Нет доступа к Inventory API. Проверьте настройки и токены.")

    elif choice == "2":
        limit = input("Введите максимальное количество товаров (по умолчанию 100): ")
        limit = int(limit) if limit.isdigit() else 100

        items = get_all_inventory_items(limit)
        if items:
            print(f"Найдено товаров: {len(items)}")
            for i, item in enumerate(items, 1):
                sku = item.get("sku", "Н/Д")
                title = item.get("product", {}).get("title", "Без названия")
                quantity = (
                    item.get("availability", {})
                    .get("shipToLocationAvailability", {})
                    .get("quantity", 0)
                )
                print(f"{i}. SKU: {sku}, Название: {title}, Количество: {quantity}")
        else:
            print("Товары не найдены или произошла ошибка.")

    elif choice == "3":
        sku = input("Введите SKU товара: ")
        item = get_inventory_item(sku)

        if item:
            print("Информация о товаре:")
            title = item.get("product", {}).get("title", "Без названия")
            description = item.get("product", {}).get(
                "description", "Описание отсутствует"
            )
            aspects = item.get("product", {}).get("aspects", {})
            quantity = (
                item.get("availability", {})
                .get("shipToLocationAvailability", {})
                .get("quantity", 0)
            )

            print(f"SKU: {sku}")
            print(f"Название: {title}")
            print(f"Описание: {description}")
            print(f"Количество: {quantity}")
            print("Характеристики:")
            for key, values in aspects.items():
                print(f"  - {key}: {', '.join(values)}")
        else:
            print(f"Товар с SKU {sku} не найден или произошла ошибка.")

    elif choice == "4":
        file_name = input("Введите имя JSON-файла с данными товара: ")

        product_data = load_product_data(file_name)
        if not product_data:
            print("Не удалось загрузить данные товара.")
            return

        sku = product_data.get("sku")
        if not sku:
            sku = input("SKU не найден в файле. Введите SKU для товара: ")
            if not sku:
                print("SKU не указан, невозможно создать товар.")
                return
            product_data["sku"] = sku

        if create_inventory_item(sku, product_data):
            print(f"Товар успешно создан в инвентаре с SKU: {sku}")
        else:
            print("Не удалось создать товар в инвентаре.")

    elif choice == "5":
        sku = input("Введите SKU товара: ")
        brand_name = (
            input("Введите название бренда (по умолчанию Orthomatic): ") or "Orthomatic"
        )

        if update_inventory_item_brand(sku, brand_name):
            print(f"Бренд товара успешно обновлен: {sku} -> {brand_name}")
        else:
            print("Не удалось обновить бренд товара.")

    elif choice == "6":
        sku = input("Введите SKU товара: ")
        quantity_str = input("Введите новое количество товара: ")

        if not quantity_str.isdigit():
            print("Ошибка: количество должно быть целым числом.")
            return

        quantity = int(quantity_str)
        update_data = {
            "availability": {"shipToLocationAvailability": {"quantity": quantity}}
        }

        if update_inventory_item(sku, update_data):
            print(f"Количество товара успешно обновлено: {sku} -> {quantity}")
        else:
            print("Не удалось обновить количество товара.")

    elif choice == "7":
        sku = input("Введите SKU товара для удаления: ")
        confirm = input(f"Вы уверены, что хотите удалить товар с SKU '{sku}'? (y/n): ")

        if confirm.lower() == "y":
            if delete_inventory_item(sku):
                print(f"Товар успешно удален из инвентаря: {sku}")
            else:
                print("Не удалось удалить товар из инвентаря.")
        else:
            print("Операция отменена.")

    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
