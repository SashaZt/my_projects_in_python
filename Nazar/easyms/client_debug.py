import json
import os
import sys
from pathlib import Path
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

current_directory = Path.cwd()
config_directory = current_directory / "config"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

ORDERS_JSON_FILE = data_directory / "orders.json"


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
    test_data = {
        "id": "TEST" + str(int(time.time())),
        "organizationId": 595,
        "customer": {
            "name": "Тестовый Клиент",
            "email": "test@example.com",
            "telephone": "+380501234567",
            "remarks": "Тестовое бронирование",
        },
        "rooms": [
            {
                "roomReservationId": "ROOM" + str(int(time.time())),
                "roomId": "4759b1db-c899-4f26-924b-d75da8bec6ef",
                "categoryId": 16342,
                "arrival": 1742515200000,
                "departure": 1742774400000,
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
    }

    return post_reservation(test_data)


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


import time

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

    # Попробуем сначала отправить одно тестовое бронирование
    logger.info("Отправка тестового бронирования...")
    if write_single_reservation():
        logger.info("Тестовое бронирование успешно создано")
    else:
        logger.error("Не удалось создать тестовое бронирование")

    # Теперь отправим бронирования из файла
    logger.info("Отправка бронирований из файла...")
    success = write_orders_to_api()
    if success:
        logger.info("Все бронирования успешно отправлены")
    else:
        logger.error("Возникли ошибки при отправке бронирований")
