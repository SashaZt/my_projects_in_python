import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests
import urllib3
from loguru import logger

# Отключаем предупреждения о непроверенных HTTPS сертификатах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка логгера
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add("api_client.log", rotation="10 MB", level="DEBUG")

# Базовый URL API
BASE_URL = "https://185.233.116.213:5000"

# Путь к файлу с данными заказов (установите правильный путь к файлу)
ORDERS_JSON_FILE = "orders.json"


def load_json_data(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """Загрузка данных из JSON файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"Успешно загружены данные из {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        return None


def post_reservation(reservation_data: Dict[str, Any]) -> bool:
    """Отправляет одно бронирование на API."""
    headers = {"Content-Type": "application/json"}
    endpoint = "/easyms/reservations/"
    url = f"{BASE_URL}{endpoint}"

    try:
        # Преобразуем данные в JSON строку
        json_data = json.dumps(reservation_data)
        logger.debug(f"Отправляем данные: {json_data[:200]}...")

        # Отправляем запрос (verify=False для игнорирования проверки сертификата)
        response = requests.post(
            url, data=json_data, headers=headers, timeout=30, verify=False
        )

        # Выводим полный ответ для отладки
        logger.debug(f"Статус ответа: {response.status_code}")
        logger.debug(f"Заголовки ответа: {response.headers}")
        logger.debug(f"Тело ответа: {response.text}")

        # Проверяем успешность
        response.raise_for_status()

        # Логируем результат
        logger.info(
            f"Бронирование {reservation_data['id']} успешно отправлено: {response.status_code}"
        )
        return True

    except requests.exceptions.RequestException as e:
        logger.error(
            f"Ошибка при отправке бронирования {reservation_data.get('id', 'unknown')}: {e}"
        )
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Статус ответа: {e.response.status_code}")
            logger.error(f"Тело ответа: {e.response.text}")
        return False


def post_bulk_reservations(reservations_data: List[Dict[str, Any]]) -> bool:
    """Отправляет несколько бронирований на API в одном запросе."""
    headers = {"Content-Type": "application/json"}
    endpoint = "/easyms/reservations/bulk"
    url = f"{BASE_URL}{endpoint}"

    try:
        # Преобразуем данные в JSON строку
        json_data = json.dumps(reservations_data)
        logger.debug(
            f"Отправляем массовые данные, количество бронирований: {len(reservations_data)}"
        )
        logger.debug(
            f"Первое бронирование: {json.dumps(reservations_data[0])[:200]}..."
        )

        # Отправляем запрос
        response = requests.post(
            url, data=json_data, headers=headers, timeout=60, verify=False
        )

        # Выводим полный ответ для отладки
        logger.debug(f"Статус ответа: {response.status_code}")
        logger.debug(f"Заголовки ответа: {response.headers}")
        logger.debug(f"Тело ответа: {response.text}")

        # Проверяем успешность
        response.raise_for_status()

        # Логируем результат
        result = response.json()
        logger.info(f"Массовая отправка успешна: {result.get('count', 0)} бронирований")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при массовой отправке бронирований: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Статус ответа: {e.response.status_code}")
            logger.error(f"Тело ответа: {e.response.text}")
        return False


def write_single_reservation():
    """Отправляет одно тестовое бронирование."""
    # Используем текущее время в секундах для ID
    current_time = int(time.time())

    test_data = {
        "id": f"TEST{current_time}",
        "organizationId": 595,
        "customer": {
            "name": "Тестовый Клиент",
            "email": "test@example.com",
            "telephone": "+380501234567",
            "remarks": "Тестовое бронирование",
        },
        "rooms": [
            {
                "roomReservationId": f"ROOM{current_time}",
                "roomId": "4759b1db-c899-4f26-924b-d75da8bec6ef",
                "categoryId": 16342,
                "arrival": 1642515200000,  # Использование меньших значений времени
                "departure": 1642774400000,  # Использование меньших значений времени
                "guestName": "Тестовый Клиент",
                "addOns": [],
                "numberOfGuests": 2,
                "guestExtraCharges": [],
                "rateId": 9999999,
                "status": "booked",
                "currencyCode": "UAH",
                "invoice": 5000.0,
                "paid": 2500.0,
                "locked": False,
                "detailed": False,
            }
        ],
        "status": "ok",
        "services": [],
        "source": "test",
        "responsibleUserId": 1203,
        "bookedAt": 1642392825348,  # Использование меньших значений времени
        "modifiedAt": 1642493688687,  # Использование меньших значений времени
    }

    return post_reservation(test_data)


def create_sample_orders_file():
    """Создает образец файла orders.json с правильными значениями времени."""
    sample_orders = [
        {
            "id": "TEST12345",
            "organizationId": 595,
            "customer": {
                "name": "Иванов Иван",
                "email": "ivanov@example.com",
                "telephone": "+380501234567",
                "remarks": "VIP-клиент",
            },
            "rooms": [
                {
                    "roomReservationId": "ROOM12345",
                    "roomId": "4759b1db-c899-4f26-924b-d75da8bec6ef",
                    "categoryId": 16342,
                    "arrival": 1642515200000,  # Использование меньших значений времени
                    "departure": 1642774400000,  # Использование меньших значений времени
                    "guestName": "Иванов Иван",
                    "addOns": [],
                    "numberOfGuests": 2,
                    "guestExtraCharges": [],
                    "rateId": 9999999,
                    "status": "booked",
                    "currencyCode": "UAH",
                    "invoice": 5000.0,
                    "paid": 2500.0,
                    "locked": False,
                    "detailed": False,
                }
            ],
            "status": "ok",
            "services": [],
            "bookedAt": 1642392825348,  # Использование меньших значений времени
            "modifiedAt": 1642493688687,  # Использование меньших значений времени
            "source": "website",
            "responsibleUserId": 1203,
        }
    ]

    try:
        with open("sample_orders.json", "w", encoding="utf-8") as f:
            json.dump(sample_orders, f, ensure_ascii=False, indent=2)
        logger.info("Создан образец файла sample_orders.json")
    except Exception as e:
        logger.error(f"Ошибка при создании образца файла: {e}")


def write_orders_to_api():
    """Основная функция для загрузки и отправки данных бронирований."""
    # Загружаем данные
    orders = load_json_data(ORDERS_JSON_FILE)

    if not orders:
        logger.error("Невозможно загрузить данные заказов")
        return False

    # Проверяем, является ли orders списком
    if not isinstance(orders, list):
        logger.error("Данные заказов должны быть в формате списка")
        return False

    logger.info(f"Загружено {len(orders)} бронирований из файла")

    # Если элементов меньше 5, отправляем по одному
    if len(orders) < 5:
        success_count = 0
        for order in orders:
            if post_reservation(order):
                success_count += 1

        logger.info(f"Отправлено {success_count} из {len(orders)} бронирований")
        return success_count == len(orders)

    # Иначе отправляем массово
    else:
        return post_bulk_reservations(orders)


if __name__ == "__main__":
    # Пример использования
    logger.info("Запуск клиента API бронирования")

    # Проверка связи с сервером
    try:
        response = requests.get(
            f"{BASE_URL}/easyms/reservations/", verify=False, timeout=5
        )
        logger.info(f"Соединение с API установлено. Статус: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка соединения с API: {e}")

    # Создаем образец файла orders.json
    create_sample_orders_file()

    # Попробуем сначала отправить одно тестовое бронирование
    logger.info("Отправка тестового бронирования...")
    if write_single_reservation():
        logger.info("Тестовое бронирование успешно создано")
    else:
        logger.error("Не удалось создать тестовое бронирование")

    # Если у вас готов файл orders.json, раскомментируйте следующие строки
    # logger.info("Отправка бронирований из файла...")
    # success = write_orders_to_api()
    # if success:
    #     logger.info("Все бронирования успешно отправлены")
    # else:
    #     logger.error("Возникли ошибки при отправке бронирований")
