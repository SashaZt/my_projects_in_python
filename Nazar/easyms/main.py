import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from loguru import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

orders_json_file = data_directory / "orders.json"
# output_xlsx_file = data_directory / "output.xlsx"
# output_csv_file = data_directory / "output.csv"
# output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"
token_file = config_directory / "access_token.json"
# Укажите ID организации и путь к файлу с токеном
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
        with open(orders_json_file, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info(orders_json_file)
    else:
        logger.error(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


# Пример использования функции
if __name__ == "__main__":
    get_token()
    fetch_orders()

    # fetch_users(organization_id, token_file)
