import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import urllib3
from loguru import logger

# Отключаем предупреждения о непроверенных HTTPS сертификатах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


current_directory = Path.cwd()
config_directory = current_directory / "config"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

ORDERS_JSON_FILE = data_directory / "orders.json"
log_file_path = log_directory / "log_message.log"
token_file = config_directory / "access_token.json"


BASE_URL = "https://185.233.116.213:5000"
organization_id = 595

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_token():
    # URL для API
    url = "https://my.easyms.co/api/integration/auth"

    # Данные для запроса
    payload = {"password": "3332220876", "username": "terranovahotel2012@gmail.com"}

    # Заголовки для запроса
    headers = {"accept": "*/*", "Content-Type": "application/json"}

    # Выполнение POST-запроса
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    # Проверка ответа
    if response.status_code == 200:
        # Парсим JSON из ответа
        json_data = response.json()
        # Извлекаем access_token
        access_token = json_data.get("data", {}).get("access_token")
        if access_token:
            # Сохраняем access_token в JSON-файл
            with open(token_file, "w", encoding="utf-8") as file:
                json.dump({"access_token": access_token}, file, indent=4)
            logger.info("Access token saved to access_token.json")
        else:
            logger.error("Access token not found in the response.")
    else:
        logger.error(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


def get_access_token_from_file(file_path: str) -> str:
    """
    Читает access_token из JSON-файла.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("access_token")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
    return None


def fetch_users(organization_id: int, token_file: str):
    """
    Выполняет GET-запрос для получения списка пользователей с использованием токена.
    """
    # Извлекаем токен из файла
    access_token = get_access_token_from_file(token_file)
    if not access_token:
        print("Access token not found or invalid.")
        return

    # URL для запроса
    url = f"https://my.easyms.co/api/integration/users?organizationId={organization_id}"

    # Заголовки для запроса
    headers = {"accept": "*/*", "Authorization": f"Bearer {access_token}"}

    # Выполнение GET-запроса
    response = requests.get(url, headers=headers, timeout=30)

    # Проверка ответа
    if response.status_code == 200:
        print("Users fetched successfully:")
        print(response.json())
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


def convert_to_unix_range(
    from_time_str: str, to_time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> tuple:
    """
    Преобразует время из строки в Unix timestamp в миллисекундах

    Args:
        from_time_str: начальное время в формате строки (например, "2025-03-21 12:00:00")
        to_time_str: конечное время в формате строки
        format_str: формат входной строки даты (по умолчанию "YYYY-MM-DD HH:MM:SS")

    Returns:
        tuple: кортеж (arrivalFrom, arrivalTo) в миллисекундах
    """
    try:
        # Преобразуем строки в объекты datetime
        from_time = datetime.strptime(from_time_str, format_str)
        to_time = datetime.strptime(to_time_str, format_str)

        # Преобразуем в Unix timestamp в миллисекундах
        arrival_from = int(from_time.timestamp() * 1000)
        arrival_to = int(to_time.timestamp() * 1000)

        return arrival_from, arrival_to
    except ValueError as e:
        raise ValueError(f"Ошибка формата времени: {str(e)}")


def fetch_orders():
    """
    Выполняет GET-запрос для получения списка заказов с использованием токена.
    """
    # Извлекаем токен из файла
    access_token = get_access_token_from_file(token_file)
    if not access_token:
        print("Access token not found or invalid.")
        return

    # Получаем текущее время
    current_time = datetime.now()

    # Вычитаем сутки (24 часа)
    time_minus_day = current_time - timedelta(days=1)

    # Форматируем в нужный вид
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    time_minus_day_str = time_minus_day.strftime("%Y-%m-%d %H:%M:%S")

    # Исправлено: правильный порядок аргументов - сначала более раннее время, затем более позднее
    arrivalFrom, arrivalTo = convert_to_unix_range(time_minus_day_str, current_time_str)

    params = {
        "arrivalFrom": arrivalFrom,
        "arrivalTo": arrivalTo,
        "status": "",
        "source": "",
        "responsible": "",
        "organizationId": organization_id,
    }

    # URL для запроса
    url = "https://my.easyms.co/api/orders"

    # Заголовки для запроса
    headers = {"accept": "*/*", "Authorization": f"Bearer {access_token}"}

    # Выполнение GET-запроса
    response = requests.get(url, params=params, headers=headers, timeout=30)

    # Проверка ответа
    if response.status_code == 200:
        data = response.json()
        with open(ORDERS_JSON_FILE, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info(ORDERS_JSON_FILE)
    else:
        logger.error(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


def load_json_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Загрузка данных из JSON файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
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

        # Отправляем запрос (verify=False для игнорирования проверки сертификата)
        response = requests.post(
            url, data=json_data, headers=headers, timeout=30, verify=False
        )

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
        return False


def post_bulk_reservations(reservations_data: List[Dict[str, Any]]) -> bool:
    """Отправляет несколько бронирований на API в одном запросе."""
    headers = {"Content-Type": "application/json"}
    endpoint = "/easyms/reservations/bulk"
    url = f"{BASE_URL}{endpoint}"

    try:
        # Преобразуем данные в JSON строку
        json_data = json.dumps(reservations_data)

        # Отправляем запрос
        response = requests.post(
            url, data=json_data, headers=headers, timeout=60, verify=False
        )

        # Проверяем успешность
        response.raise_for_status()

        # Логируем результат
        result = response.json()
        logger.info(f"Массовая отправка успешна: {result.get('count', 0)} бронирований")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при массовой отправке бронирований: {e}")
        return False


def get_reservations(
    filters: Optional[Dict[str, Any]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Получает список бронирований с фильтрацией."""
    endpoint = "/easyms/reservations/"
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=filters, timeout=30, verify=False)
        response.raise_for_status()

        reservations = response.json()
        logger.info(f"Получено {len(reservations)} бронирований")
        return reservations

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении бронирований: {e}")
        return None


def get_reservation_by_id(reservation_id: str) -> Optional[Dict[str, Any]]:
    """Получает бронирование по ID."""
    endpoint = f"/easyms/reservations/{reservation_id}"
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()

        reservation = response.json()
        logger.info(f"Получено бронирование с ID {reservation_id}")
        return reservation

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении бронирования {reservation_id}: {e}")
        return None


def update_reservation_status(reservation_id: str, status: str) -> bool:
    """Обновляет статус бронирования."""
    endpoint = f"/easyms/reservations/status/{reservation_id}"
    url = f"{BASE_URL}{endpoint}"

    try:
        params = {"status": status}
        response = requests.put(url, params=params, timeout=30, verify=False)
        response.raise_for_status()

        logger.info(f"Статус бронирования {reservation_id} обновлен на {status}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(
            f"Ошибка при обновлении статуса бронирования {reservation_id}: {e}"
        )
        return False


def update_reservation(
    reservation_id: str, reservation_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Обновляет бронирование."""
    headers = {"Content-Type": "application/json"}
    endpoint = f"/easyms/reservations/{reservation_id}"
    url = f"{BASE_URL}{endpoint}"

    try:
        json_data = json.dumps(reservation_data)
        response = requests.put(
            url, data=json_data, headers=headers, timeout=30, verify=False
        )
        response.raise_for_status()

        updated_reservation = response.json()
        logger.info(f"Бронирование {reservation_id} успешно обновлено")
        return updated_reservation

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обновлении бронирования {reservation_id}: {e}")
        return None


def delete_reservation(reservation_id: str) -> bool:
    """Удаляет бронирование."""
    endpoint = f"/easyms/reservations/{reservation_id}"
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.delete(url, timeout=30, verify=False)
        response.raise_for_status()

        logger.info(f"Бронирование {reservation_id} успешно удалено")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при удалении бронирования {reservation_id}: {e}")
        return False


# def process_single_order(order):
#     """Обрабатывает одно бронирование - создаёт новое или обновляет существующее."""
#     order_id = order.get("id")

#     # Проверяем существование бронирования
#     existing_order = get_reservation_by_id(order_id)

#     if existing_order:
#         # Бронирование существует - обновляем его
#         logger.info(f"Обновляем существующее бронирование {order_id}")
#         success = update_reservation(order_id, order)
#     else:
#         # Бронирование не существует - создаём новое
#         logger.info(f"Создаём новое бронирование {order_id}")
#         success = post_reservation(order)

#     return success


def update_reservation_status_only(reservation_id: str, status: str) -> bool:
    """Обновляет только статус бронирования."""
    endpoint = f"/easyms/reservations/status/{reservation_id}"
    url = f"{BASE_URL}{endpoint}"
    params = {"status": status}

    try:
        response = requests.put(url, params=params, timeout=30, verify=False)

        # Выводим полный ответ для отладки
        logger.debug(f"Статус ответа: {response.status_code}")
        logger.debug(f"Заголовки ответа: {response.headers}")
        logger.debug(f"Тело ответа: {response.text}")

        # Проверяем успешность
        response.raise_for_status()

        logger.info(
            f"Статус бронирования {reservation_id} успешно обновлен на {status}"
        )
        return True

    except requests.exceptions.RequestException as e:
        logger.error(
            f"Ошибка при обновлении статуса бронирования {reservation_id}: {e}"
        )
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Статус ответа: {e.response.status_code}")
            logger.error(f"Тело ответа: {e.response.text}")
        return False


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

    # Получаем список существующих бронирований
    existing_reservations = get_reservations() or []
    existing_ids = [res["id"] for res in existing_reservations]
    logger.info(f"Найдено {len(existing_ids)} существующих бронирований")

    # Разделяем бронирования на новые и существующие
    new_orders = []
    update_orders = []

    for order in orders:
        order_id = order.get("id")
        if order_id in existing_ids:
            update_orders.append(order)
        else:
            new_orders.append(order)

    logger.info(
        f"Найдено {len(new_orders)} новых и {len(update_orders)} существующих бронирований для обновления"
    )

    # Обрабатываем новые бронирования
    new_success_count = 0
    for order in new_orders:
        if post_reservation(order):
            new_success_count += 1

    # Обрабатываем существующие бронирования (обновление)
    update_success_count = 0
    for order in update_orders:
        order_id = order.get("id")
        status = order.get("status", "ok")
        if update_reservation_status_only(order_id, status):
            update_success_count += 1

    logger.info(f"Создано {new_success_count} из {len(new_orders)} новых бронирований")
    logger.info(
        f"Обновлено {update_success_count} из {len(update_orders)} существующих бронирований"
    )

    return (new_success_count == len(new_orders)) and (
        update_success_count == len(update_orders)
    )


# Пример использования функции
if __name__ == "__main__":
    # get_token()
    fetch_orders()
    success = write_orders_to_api()
    if success:
        logger.info("Все бронирования успешно отправлены")
    else:
        logger.error("Возникли ошибки при отправке бронирований")
