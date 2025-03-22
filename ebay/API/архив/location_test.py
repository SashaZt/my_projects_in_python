# location_test.py
import json

from inventory_client import EbayInventoryClient
from logger import logger


def load_product_data(file_path):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def test_create_location():
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


if __name__ == "__main__":
    test_create_location()
