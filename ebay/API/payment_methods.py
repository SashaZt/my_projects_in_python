# payment_methods.py
"""
Модуль для управления платежными методами на eBay через Checkout API.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from inventory_client import EbayInventoryClient
from logger import logger

from config import DEFAULT_MARKETPLACE_ID


class PaymentMethodManager:
    """Класс для управления платежными методами на eBay"""

    def __init__(self):
        """Инициализация менеджера платежных методов"""
        self.client = EbayInventoryClient()
        if not self.client.authenticate():
            logger.error("Не удалось аутентифицироваться")
            return None

    def add_credit_card(self, card_data: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """
        Добавление кредитной карты в аккаунт eBay через инициализацию сессии оформления заказа

        eBay не предоставляет прямой эндпоинт для добавления кредитной карты в аккаунт.
        Вместо этого кредитные карты добавляются во время оформления заказа.

        Args:
            card_data (Dict[str, Any]): Данные кредитной карты

        Returns:
            Union[Dict[str, Any], None]: Результат операции или None в случае ошибки
        """
        logger.info("Добавление кредитной карты через инициализацию сессии...")

        # Проверка наличия обязательных полей
        required_fields = [
            "accountHolderName",
            "cardNumber",
            "cvvNumber",
            "expireMonth",
            "expireYear",
            "brand",
        ]

        for field in required_fields:
            if field not in card_data:
                logger.error(f"Отсутствует обязательное поле: {field}")
                return None

        # Проверка наличия адреса для выставления счета
        if "billingAddress" not in card_data:
            logger.error("Отсутствует адрес для выставления счета (billingAddress)")
            return None

        # Инициализируем сессию оформления заказа с минимальными данными
        # и включаем данные кредитной карты
        session_data = {
            "lineItems": [
                {"itemId": "v1|123456789|0", "quantity": 1}  # Фиктивный ID товара
            ],
            "paymentMethod": {"type": "CREDIT_CARD", "creditCard": card_data},
        }

        # Используем правильный эндпоинт согласно документации eBay
        endpoint = "buy/order/v1/checkout_session/initiate"

        # Добавляем заголовки
        headers = {
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": DEFAULT_MARKETPLACE_ID,
        }

        result = self.client._call_api(
            endpoint, "POST", data=session_data, headers=headers
        )

        if isinstance(result, dict) and "errors" in result:
            logger.error(f"Ошибка при добавлении кредитной карты: {result['errors']}")
            return None

        if isinstance(result, dict) and "error" in result:
            logger.error(f"Ошибка при добавлении кредитной карты: {result['error']}")
            return None

        if not isinstance(result, dict) or "checkoutSessionId" not in result:
            logger.error("Не удалось получить ID сессии оформления заказа")
            return None

        logger.info("Кредитная карта успешно добавлена в сессию оформления заказа")
        return result

    def update_payment_info(
        self, session_id: str, card_data: Dict[str, Any]
    ) -> Union[Dict[str, Any], None]:
        """
        Обновление платежной информации в сессии оформления заказа

        Args:
            session_id (str): ID сессии оформления заказа
            card_data (Dict[str, Any]): Данные кредитной карты

        Returns:
            Union[Dict[str, Any], None]: Результат операции или None в случае ошибки
        """
        logger.info(f"Обновление платежной информации в сессии: {session_id}")

        # Используем правильный эндпоинт согласно документации eBay
        endpoint = f"buy/order/v1/checkout_session/{session_id}/update_payment_info"

        # Форматируем данные в соответствии с требованиями API
        payment_data = {
            "paymentMethod": {"type": "CREDIT_CARD", "creditCard": card_data}
        }

        # Добавляем заголовки, если они требуются
        headers = {
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": DEFAULT_MARKETPLACE_ID,
        }

        result = self.client._call_api(
            endpoint, "POST", data=payment_data, headers=headers
        )

        if isinstance(result, dict) and "errors" in result:
            logger.error(
                f"Ошибка при обновлении платежной информации: {result['errors']}"
            )
            return None

        if isinstance(result, dict) and "error" in result:
            logger.error(
                f"Ошибка при обновлении платежной информации: {result['error']}"
            )
            return None

        logger.info("Платежная информация успешно обновлена")
        return result

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Получение списка сохраненных платежных методов

        Returns:
            List[Dict[str, Any]]: Список платежных методов
        """
        logger.info("Получение списка платежных методов...")

        # В текущей версии API eBay нет прямого эндпоинта для получения сохраненных
        # платежных методов без создания сессии оформления заказа.
        # Эта функция может быть реализована с использованием
        # Order API и получения информации через сессию.

        logger.warning(
            "API eBay не предоставляет прямой эндпоинт для получения списка платежных методов"
        )
        logger.info("Пытаемся получить платежные методы через инициализацию сессии...")

        # Инициализируем сессию оформления заказа с минимальными данными
        session_data = {
            "lineItems": [
                {"itemId": "v1|123456789|0", "quantity": 1}  # Фиктивный ID товара
            ]
        }

        # Пытаемся инициализировать сессию
        endpoint = "buy/order/v1/checkout_session/initiate"
        result = self.client._call_api(endpoint, "POST", data=session_data)

        if isinstance(result, dict) and "errors" in result:
            logger.error(f"Ошибка при получении платежных методов: {result['errors']}")
            return []

        if isinstance(result, dict) and "error" in result:
            logger.error(f"Ошибка при получении платежных методов: {result['error']}")
            return []

        # Если есть информация о платежных методах, извлекаем ее
        payment_methods = []
        if isinstance(result, dict) and "paymentMethods" in result:
            payment_methods = result.get("paymentMethods", [])
            logger.info(f"Получено платежных методов: {len(payment_methods)}")
        else:
            logger.warning("Информация о платежных методах не найдена в ответе API")

        return payment_methods

    def delete_payment_method(self, payment_method_id: str) -> bool:
        """
        Удаление платежного метода

        Примечание: В текущей версии API eBay нет прямого эндпоинта для удаления
        сохраненного платежного метода. В некоторых случаях это может быть
        доступно через настройки аккаунта пользователя.

        Args:
            payment_method_id (str): ID платежного метода

        Returns:
            bool: Результат операции
        """
        logger.info(f"Попытка удаления платежного метода с ID: {payment_method_id}")
        logger.warning(
            "API eBay не предоставляет прямой эндпоинт для удаления платежного метода"
        )
        logger.info(
            "Рекомендуется удалить платежный метод через настройки аккаунта eBay"
        )

        # Возвращаем False, так как операция не поддерживается через API
        return False

    def initiate_checkout_session(
        self, order_data: Dict[str, Any]
    ) -> Union[Dict[str, Any], None]:
        """
        Инициализация сессии оформления заказа

        Args:
            order_data (Dict[str, Any]): Данные заказа

        Returns:
            Union[Dict[str, Any], None]: Результат операции или None в случае ошибки
        """
        logger.info("Инициализация сессии оформления заказа...")

        # Используем правильный эндпоинт согласно документации eBay
        endpoint = "buy/order/v1/checkout_session/initiate"

        # Добавляем заголовки, если они требуются
        headers = {
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": DEFAULT_MARKETPLACE_ID,
        }

        result = self.client._call_api(
            endpoint, "POST", data=order_data, headers=headers
        )

        if isinstance(result, dict) and "errors" in result:
            logger.error(f"Ошибка при инициализации сессии: {result['errors']}")
            return None

        if isinstance(result, dict) and "error" in result:
            logger.error(f"Ошибка при инициализации сессии: {result['error']}")
            return None

        if not isinstance(result, dict) or "checkoutSessionId" not in result:
            logger.error("Не удалось получить ID сессии оформления заказа")
            return None

        session_id = result["checkoutSessionId"]
        logger.info(
            f"Сессия оформления заказа успешно инициализирована, ID: {session_id}"
        )
        return result

    def create_sandbox_credit_card(self) -> Dict[str, Any]:
        """
        Создание тестовой кредитной карты для песочницы eBay

        Returns:
            Dict[str, Any]: Данные тестовой кредитной карты
        """
        logger.info("Создание тестовой кредитной карты для песочницы...")

        # Данные тестовой карты для песочницы eBay
        # Обратите внимание, что это фиктивные данные для тестирования
        sandbox_card = {
            "accountHolderName": "Test User",
            "cardNumber": "4111111111111111",  # Тестовый номер карты Visa
            "cvvNumber": "123",
            "expireMonth": 12,
            "expireYear": 2030,
            "brand": "VISA",
            "billingAddress": {
                "addressLine1": "123 Test Street",
                "addressLine2": "Apt 1",
                "city": "Test City",
                "country": "DE",
                "county": "Test County",
                "postalCode": "12345",
                "stateOrProvince": "Test State",
            },
        }

        logger.info("Тестовая кредитная карта создана")
        return sandbox_card


def save_card_data(
    card_data: Dict[str, Any], filename: str = "sandbox_card.json"
) -> bool:
    """
    Сохранение данных кредитной карты в JSON-файл

    Args:
        card_data (Dict[str, Any]): Данные кредитной карты
        filename (str): Имя файла для сохранения

    Returns:
        bool: Результат операции
    """
    try:
        # Создание директории для конфигурации, если не существует
        config_dir = "config"
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_file = os.path.join(config_dir, filename)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(card_data, f, indent=4)

        logger.info(f"Данные кредитной карты сохранены в файл {config_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных кредитной карты: {e}")
        return False


def load_card_data(filename: str = "sandbox_card.json") -> Dict[str, Any]:
    """
    Загрузка данных кредитной карты из JSON-файла

    Args:
        filename (str): Имя файла для загрузки

    Returns:
        Dict[str, Any]: Данные кредитной карты или пустой словарь в случае ошибки
    """
    config_file = os.path.join("config", filename)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"Файл {config_file} не найден.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {config_file}.")
        return {}


def main():
    """Основная функция для работы с платежными методами"""
    print("=== Управление платежными методами на eBay ===")
    print("1. Создать тестовую кредитную карту для песочницы")
    print("2. Добавить кредитную карту в аккаунт eBay")
    print("3. Получить список платежных методов")
    print("4. Удалить платежный метод")
    print("5. Инициализировать сессию оформления заказа")
    print("0. Выход")

    choice = input("Выберите действие: ")
    payment_manager = PaymentMethodManager()

    if choice == "1":
        # Создание тестовой карты и сохранение в файл
        card_data = payment_manager.create_sandbox_credit_card()
        if save_card_data(card_data):
            print(
                "Тестовая кредитная карта создана и сохранена в файл config/sandbox_card.json"
            )
            print(f"Данные карты: {json.dumps(card_data, indent=2)}")
        else:
            print("Не удалось сохранить данные тестовой карты")

    elif choice == "2":
        # Загрузка данных карты из файла или ввод новых данных
        card_data = load_card_data()

        if not card_data:
            print("Данные карты не найдены в файле. Введите данные вручную:")
            card_data = {
                "accountHolderName": input("Имя держателя карты: "),
                "cardNumber": input("Номер карты: "),
                "cvvNumber": input("CVV код: "),
                "expireMonth": int(input("Месяц истечения срока (1-12): ")),
                "expireYear": int(input("Год истечения срока (например, 2030): ")),
                "brand": input("Бренд карты (VISA, MASTERCARD, AMEX, DISCOVER): "),
                "billingAddress": {
                    "addressLine1": input("Адрес (строка 1): "),
                    "city": input("Город: "),
                    "country": input("Страна (код, например DE): "),
                    "postalCode": input("Почтовый индекс: "),
                    "stateOrProvince": input("Штат/провинция: "),
                },
            }

            # Опционально спрашиваем о второй строке адреса
            address_line2 = input("Адрес (строка 2, опционально): ")
            if address_line2:
                card_data["billingAddress"]["addressLine2"] = address_line2

            # Сохраняем введенные данные
            save_card_data(card_data)

        # Добавляем карту в аккаунт eBay
        result = payment_manager.add_credit_card(card_data)
        if result:
            print("Кредитная карта успешно добавлена в аккаунт eBay")
        else:
            print("Не удалось добавить кредитную карту в аккаунт eBay")

    elif choice == "3":
        # Получение списка платежных методов
        payment_methods = payment_manager.get_payment_methods()

        if payment_methods:
            print(f"Найдено платежных методов: {len(payment_methods)}")
            for i, method in enumerate(payment_methods, 1):
                method_id = method.get("paymentMethodId", "Н/Д")
                method_type = method.get("paymentMethodType", "Н/Д")

                # Для кредитных карт показываем дополнительную информацию
                if method_type == "CREDIT_CARD" and "creditCard" in method:
                    card = method["creditCard"]
                    card_brand = card.get("brand", "Н/Д")
                    card_number = card.get("cardNumber", "Н/Д")
                    if len(card_number) > 4:
                        # Маскируем номер карты для безопасности
                        masked_number = "*" * (len(card_number) - 4) + card_number[-4:]
                    else:
                        masked_number = card_number

                    expire_month = card.get("expireMonth", "Н/Д")
                    expire_year = card.get("expireYear", "Н/Д")

                    print(f"{i}. ID: {method_id}, Тип: {method_type}")
                    print(f"   Карта: {card_brand}, Номер: {masked_number}")
                    print(f"   Срок действия: {expire_month}/{expire_year}")
                else:
                    print(f"{i}. ID: {method_id}, Тип: {method_type}")
        else:
            print("Платежные методы не найдены или произошла ошибка")

    elif choice == "4":
        # Удаление платежного метода
        payment_method_id = input("Введите ID платежного метода для удаления: ")
        confirm = input(
            f"Вы уверены, что хотите удалить платежный метод с ID '{payment_method_id}'? (y/n): "
        )

        if confirm.lower() == "y":
            if payment_manager.delete_payment_method(payment_method_id):
                print(f"Платежный метод успешно удален: {payment_method_id}")
            else:
                print("Не удалось удалить платежный метод")
        else:
            print("Операция отменена")

    elif choice == "5":
        # Инициализация сессии оформления заказа
        print("Для инициализации сессии оформления заказа необходимы данные о заказе.")
        print("Введите базовую информацию для сессии:")

        order_data = {
            "lineItems": [
                {
                    "itemId": input("ID товара: "),
                    "quantity": int(input("Количество: ")),
                }
            ],
            "shippingAddress": {
                "recipientName": input("Имя получателя: "),
                "addressLine1": input("Адрес доставки (строка 1): "),
                "city": input("Город: "),
                "country": input("Страна (код, например DE): "),
                "postalCode": input("Почтовый индекс: "),
                "stateOrProvince": input("Штат/провинция: "),
            },
        }

        # Опционально спрашиваем о второй строке адреса
        address_line2 = input("Адрес доставки (строка 2, опционально): ")
        if address_line2:
            order_data["shippingAddress"]["addressLine2"] = address_line2

        result = payment_manager.initiate_checkout_session(order_data)
        if result:
            session_id = result.get("checkoutSessionId", "Н/Д")
            print(
                f"Сессия оформления заказа успешно инициализирована, ID: {session_id}"
            )

            # Спрашиваем, нужно ли обновить платежную информацию
            if (
                input("Обновить платежную информацию в этой сессии? (y/n): ").lower()
                == "y"
            ):
                # Загружаем данные карты из файла или используем тестовую карту
                card_data = load_card_data()
                if not card_data:
                    card_data = payment_manager.create_sandbox_credit_card()

                if payment_manager.update_payment_info(session_id, card_data):
                    print("Платежная информация успешно обновлена в сессии")
                else:
                    print("Не удалось обновить платежную информацию в сессии")
        else:
            print("Не удалось инициализировать сессию оформления заказа")

    else:
        print("Выход из программы")


if __name__ == "__main__":
    main()
