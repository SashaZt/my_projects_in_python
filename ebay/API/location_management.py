# location_management.py
# Модуль для управления местоположениями продавца на eBay
# Позволяет получить список местоположений и создать новое местоположение
# Для работы требуется наличие файла конфигурации location_warehouse.json
# Последние изменения 2025-03-22
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


def load_product_data(file_path):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def create_sample_location():
    """Попытка создать тестовое местоположение на основе существующих шаблонов"""
    client = EbayInventoryClient()

    # Проверяем, что клиент аутентифицирован
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться для создания местоположения")
        return False

    # Создаем уникальный ключ местоположения с новым значением
    # Поскольку может быть конфликт с существующим ключом
    merchant_location_key = "warehouseberlin002"

    location_data = load_product_data("location_warehouse.json")

    # Создаем местоположение
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
