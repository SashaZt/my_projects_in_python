# location_test.py
from inventory_client import EbayInventoryClient
from logger import logger


def test_create_location():
    client = EbayInventoryClient()

    # Проверяем, что клиент аутентифицирован
    if not client.authenticate():
        logger.error("Не удалось аутентифицироваться для создания местоположения")
        return False

    # Создаем уникальный ключ местоположения с новым значением
    # Поскольку может быть конфликт с существующим ключом
    merchant_location_key = "warehouse-berlin-002"

    # Данные о местоположении - строго следуем документации API eBay
    location_data = {
        "location": {
            "address": {
                "addressLine1": "123 Example St",
                "city": "Berlin",
                "country": "DE",
                "postalCode": "10115",
                "stateOrProvince": "Berlin",
            },
            "name": "Main Warehouse Berlin",
            "merchantLocationStatus": "ENABLED",
        },
        "locationTypes": ["WAREHOUSE"],
        # Удалили поле merchantLocationKey из тела запроса, так как оно уже есть в URL
    }

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
