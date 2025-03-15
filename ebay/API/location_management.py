# location_management.py
import json

from inventory_client import EbayInventoryClient
from logger import logger


def get_locations():
    """Получение и отображение всех местоположений продавца"""
    client = EbayInventoryClient()

    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться для получения местоположений")
        return False

    # Добавляем метод для получения местоположений
    endpoint = "sell/inventory/v1/location"
    response = client._call_api(endpoint, "GET")

    if not response or "locations" not in response:
        logger.warning(
            "Местоположения не найдены или ошибка при получении местоположений"
        )
        logger.debug(f"Ответ API: {response}")
        return []

    locations = response.get("locations", [])
    logger.info(f"Найдено {len(locations)} местоположений:")

    for idx, location in enumerate(locations, 1):
        logger.info(f"Местоположение #{idx}:")
        logger.info(f"  Ключ: {location.get('merchantLocationKey')}")
        logger.info(f"  Имя: {location.get('location', {}).get('name')}")
        logger.info(f"  Типы: {location.get('locationTypes', [])}")
        logger.info(
            f"  Статус: {location.get('location', {}).get('merchantLocationStatus')}"
        )
        # Выводим полное содержимое для анализа структуры
        logger.debug(f"  Полные данные: {json.dumps(location, indent=2)}")

    return locations


def create_sample_location():
    """Попытка создать тестовое местоположение на основе существующих шаблонов"""
    client = EbayInventoryClient()

    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться")
        return False

    # Получаем существующие местоположения для анализа
    locations = get_locations()

    if not locations:
        logger.warning("Нет существующих местоположений для анализа структуры")
        # Пробуем создать с минимальной структурой по документации
        location_data = {
            "location": {
                "address": {
                    "addressLine1": "123 Example St",
                    "city": "Berlin",
                    "country": "DE",
                    "postalCode": "10115",
                    "stateOrProvince": "Berlin",
                },
                "name": "Test Warehouse Berlin",
                "merchantLocationStatus": "ENABLED",
            },
            "locationTypes": ["WAREHOUSE"],
        }
    else:
        # Берем первое местоположение как шаблон
        template = locations[0]
        # Создаем копию без ключа
        location_data = {
            "location": template.get("location", {}),
            "locationTypes": template.get("locationTypes", ["WAREHOUSE"]),
        }
        # Обновляем имя, чтобы отличать
        location_data["location"]["name"] = "Test Warehouse Based on Template"

    # Генерируем уникальный ключ
    import random

    merchant_location_key = f"test-warehouse-{random.randint(1000, 9999)}"

    logger.info(f"Попытка создания местоположения с ключом: {merchant_location_key}")
    logger.debug(f"Данные: {json.dumps(location_data, indent=2)}")

    # Пробуем создать
    result = client.create_location(merchant_location_key, location_data)

    if isinstance(result, dict) and (
        result.get("success", False) or "merchantLocationKey" in result
    ):
        logger.info(f"Местоположение успешно создано: {merchant_location_key}")
        return True
    else:
        logger.error(f"Не удалось создать местоположение: {result}")
        return False


def main():
    """Основная функция управления местоположениями"""
    print("=== Управление местоположениями eBay ===")
    print("1. Получить список местоположений")
    print("2. Создать тестовое местоположение")
    print("0. Выход")

    choice = input("Выберите действие: ")

    if choice == "1":
        get_locations()
    elif choice == "2":
        create_sample_location()
    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
