import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from client_import_live import import_daily_analytics
from client_import_user import import_all_users, import_user_data
from config import (
    DATA_DIR,
    TEMP_DIR,
    USER_INFO_DIR,
    USER_JSON_FILE,
    USER_LIVE_ANALYTICS_DIR,
    USER_LIVE_LIST_DIR,
)
from loguru import logger
from main_sheets import sheets

from tikapi import ResponseException, TikAPI, ValidationException

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

user_json_file = DATA_DIR / "users.json"

log_file_path = log_directory / "log_message.log"


api_key = TikAPI("ozUfhAazflu4zj1LyqvxYv4IaAs6OCX9cX0zI1fQxexQVxQU")

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


def load_product_data(file_name):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


"""
Начался блок аналитики
"""


def user_live_analytics():
    """Основная функция для сбора и обработки аналитики пользователей."""
    timestamp = get_current_day_timestamp()
    users = load_users_data()
    analytics_results = collect_users_analytics(users, timestamp)
    save_analytics_results(analytics_results, timestamp)
    process_analytics_results(analytics_results)


def get_current_day_timestamp():
    """Получение текущего дня в формате Unix timestamp (начало дня по UTC)."""
    return int(
        datetime.now(timezone.utc)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def load_users_data():
    """Загрузка данных пользователей из JSON файла."""
    return load_product_data(USER_JSON_FILE)


def collect_users_analytics(users, timestamp, days=30):
    """Сбор аналитики для каждого пользователя."""
    result = []

    for user in users[:1]:
        logger.info(user)
        analytics_data = get_user_analytics(user, timestamp, days)
        if analytics_data:
            # analytics_data теперь может быть списком данных за разные даты
            if isinstance(analytics_data, list):
                result.extend(analytics_data)
            else:
                result.append(analytics_data)

    return result


def get_user_analytics(user, timestamp, days=30):
    """Получение аналитики для конкретного пользователя."""
    account_key = user["account_key"]
    tik_tok_id = user["tik_tok_id"]
    user_data_file = get_user_data_filename(timestamp, tik_tok_id)

    # Пробуем загрузить данные из кэша
    cached_data = load_cached_analytics(user_data_file, tik_tok_id)
    if cached_data:
        return cached_data

    # Если нет в кэше, получаем через API
    return fetch_user_analytics_from_api(account_key, tik_tok_id, user_data_file, days)


def get_user_data_filename(timestamp, tik_tok_id):
    """Формирование имени файла для кэширования данных пользователя."""
    return TEMP_DIR / f"user_live_analytics_{timestamp}_{tik_tok_id}.json"


def load_cached_analytics(user_data_file, tik_tok_id):
    """Загрузка кэшированных данных аналитики пользователя, если они существуют."""
    if not user_data_file.exists():
        return None

    with open(user_data_file, "r", encoding="utf-8") as json_file:
        user_data = json.load(json_file)

    combined_data = parsing_json_user_live_analytics(user_data)

    # Создаем список результатов с данными за каждую дату
    results = []
    for entry in combined_data:
        result = {
            "tik_tok_id": tik_tok_id,
            "diamonds_now": entry["diamonds_now"],
            "live_duration_now": entry["live_duration_now"],
            "date": entry["date"],
        }
        results.append(result)

    return results


def fetch_user_analytics_from_api(account_key, tik_tok_id, user_data_file, days=30):
    """Получение аналитики пользователя через API с повторными попытками."""
    account_user = api_key.user(accountKey=account_key)

    response_json = retry_api_request(account_user, days)
    if not response_json:
        logger.warning(account_key)
        return None

    # Сохраняем ответ от API в файл
    with open(user_data_file, "w", encoding="utf-8") as json_file:
        json.dump(response_json, json_file, ensure_ascii=False, indent=4)

    # Обрабатываем и возвращаем данные
    combined_data = parsing_json_user_live_analytics(response_json)

    # Создаем список результатов с данными за каждую дату
    results = []
    for entry in combined_data:
        result = {
            "tik_tok_id": tik_tok_id,
            "diamonds_now": entry["diamonds_now"],
            "live_duration_now": entry["live_duration_now"],
            "date": entry["date"],
        }
        results.append(result)

    return results


def retry_api_request(account_user, days, max_attempts=1):
    """Выполнение запроса к API с повторными попытками."""
    attempt = 0

    while attempt < max_attempts:
        try:
            response = account_user.live.analytics(days=days)

            # Проверяем статус ответа
            if hasattr(response, "status_code") and response.status_code == 200:
                return response.json()

            # Если статус не 200, ждем и повторяем
            attempt += 1
            logger.warning(
                f"Попытка {attempt}/{max_attempts}: Получен код статуса {getattr(response, 'status_code', 'неизвестно')}. Повторная попытка через 5 секунд..."
            )
            time.sleep(5)

        except ValidationException as e:
            log_validation_error(e, attempt, max_attempts)
            attempt += 1
            time.sleep(5)

        except ResponseException as e:
            log_response_error(e, attempt, max_attempts)
            attempt += 1
            time.sleep(5)

        except Exception as e:
            log_unexpected_error(e, attempt, max_attempts)
            attempt += 1
            time.sleep(5)

    logger.error(f"Не удалось получить аналитику после {max_attempts} попыток")
    return None


def log_validation_error(error, attempt, max_attempts):
    """Логирование ошибок валидации."""
    logger.error(f"Ошибка валидации (попытка {attempt}/{max_attempts}): {error}")
    if hasattr(error, "field"):
        logger.error(f"Поле с ошибкой: {error.field}")


def log_response_error(error, attempt, max_attempts):
    """Логирование ошибок ответа API."""
    logger.error(f"Ошибка ответа (попытка {attempt}/{max_attempts}): {error}")
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        logger.error(f"Код статуса: {error.response.status_code}")


def log_unexpected_error(error, attempt, max_attempts):
    """Логирование непредвиденных ошибок."""
    logger.error(f"Непредвиденная ошибка (попытка {attempt}/{max_attempts}): {error}")


def save_analytics_results(result, timestamp):
    """Сохранение результатов аналитики в JSON файл."""
    user_live_analytic_json_file = USER_LIVE_ANALYTICS_DIR / f"{timestamp}.json"

    with open(user_live_analytic_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)

    logger.info(f"Сохранены результаты аналитики: {result}")


def process_analytics_results(result):
    """Обработка и отправка результатов аналитики."""
    try:
        # Используем asyncio.run вместо создания нового цикла событий
        asyncio.run(import_daily_analytics(result))
    except Exception as e:
        logger.error(f"Ошибка при обработке результатов аналитики: {e}")


def parsing_json_user_live_analytics(json_data):
    """Обработка JSON с аналитикой, возвращает все значения вместо только последних"""
    # Получаем все данные о бриллиантах
    diamonds_values = []
    diamonds_dates = []

    if (
        "data" in json_data
        and "diamonds_detail" in json_data["data"]
        and "diamonds" in json_data["data"]["diamonds_detail"]
        and "Total" in json_data["data"]["diamonds_detail"]["diamonds"]
    ):
        diamonds_list = json_data["data"]["diamonds_detail"]["diamonds"]["Total"]
        for item in diamonds_list:
            diamonds_values.append(item["Value"])
            diamonds_dates.append(item["Date"])
    else:
        logger.warning("Не найдены данные о бриллиантах в полученном JSON")
        diamonds_values = [0]
        diamonds_dates = [0]

    # Получаем все данные о продолжительности трансляций
    live_duration_values = []
    live_duration_dates = []

    if (
        "data" in json_data
        and "live_duration_detail" in json_data["data"]
        and "live_duration" in json_data["data"]["live_duration_detail"]
    ):
        live_duration_list = json_data["data"]["live_duration_detail"]["live_duration"]
        for item in live_duration_list:
            live_duration_values.append(item["Value"])
            live_duration_dates.append(item["Date"])
    else:
        logger.warning(
            "Не найдены данные о продолжительности трансляций в полученном JSON"
        )
        live_duration_values = [0]
        live_duration_dates = [0]

    # Сопоставляем даты между бриллиантами и продолжительностью
    # Создаем словарь с общими датами
    combined_data = []

    # Объединяем все уникальные даты
    all_dates = set(diamonds_dates + live_duration_dates)

    for date_value in all_dates:
        entry = {"date": date_value}

        # Находим индекс даты в списке бриллиантов, если она есть
        if date_value in diamonds_dates:
            idx = diamonds_dates.index(date_value)
            entry["diamonds_now"] = diamonds_values[idx]
        else:
            entry["diamonds_now"] = 0

        # Находим индекс даты в списке продолжительности, если она есть
        if date_value in live_duration_dates:
            idx = live_duration_dates.index(date_value)
            entry["live_duration_now"] = live_duration_values[idx]
        else:
            entry["live_duration_now"] = 0

        combined_data.append(entry)

    # Сортируем по дате, чтобы последние значения шли последними
    combined_data.sort(key=lambda x: x["date"])

    return combined_data


"""
Закончился блок аналитики
"""


if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Запуск ежедневной задачи: {start_time}")

    try:

        # Выполняем сбор аналитики по трансляциям
        logger.info("Начинаем сбор аналитики трансляций")
        user_live_analytics()
        logger.info("Сбор аналитики трансляций успешно завершен")

    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи: {e}", exc_info=True)

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Задача завершена. Длительность выполнения: {duration}")
