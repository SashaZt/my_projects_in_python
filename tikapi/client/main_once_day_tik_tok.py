import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from client_import_live import import_daily_analytics
from client_import_user import import_all_users, import_user_data
from config.config import (
    TEMP_DIR,
    USER_INFO_DIR,
    USER_JSON_FILE,
    USER_LIVE_ANALYTICS_DIR,
)
from config.logger import logger
from main_sheets import sheets

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
# Создание директорий, если они не существуют
config_directory.mkdir(parents=True, exist_ok=True)

# Файлы
config_file = config_directory / "config.json"


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


config = get_config()
api_key = config["tikapi"]["api_key"]


def load_product_data(file_name):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def user_live_analytics():
    users = load_product_data(USER_JSON_FILE)
    result = []
    # Текущие сутки по Гринвичу в Unix timestamp
    timestamp = int(
        datetime.now(timezone.utc)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    for user in users:
        account_key = user["account_key"]
        tik_tok_id = user["tik_tok_id"]
        user_data_file = TEMP_DIR / f"user_live_analytics_{timestamp}_{tik_tok_id}.json"
        #     continue
        url = "https://api.tikapi.io/user/live/analytics?days=7"

        headers = {
            "X-API-KEY": api_key,
            "X-ACCOUNT-KEY": account_key,
            "accept": "application/json",
        }

        if user_data_file.exists():
            continue
        logger.info(f"Запрос по account_key: {account_key}")
        response = requests.get(url, headers=headers)
        json_data = None
        try:
            json_data = response.json()

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка {e} {account_key}")
            logger.error(f"Ошибка {e} {response.text}")

            continue
        status_error = json_data.get("status")
        if status_error == "error":
            logger.error(account_key)
            continue
        with open(user_data_file, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        logger.info(f"Файл по account_key: {account_key} сохранен {user_data_file}")

        all_data = {"tik_tok_id": tik_tok_id}
        diamonds_now, live_duration_now, date = parsing_json_user_live_analytics(
            json_data
        )
        all_data["diamonds_now"] = diamonds_now
        all_data["live_duration_now"] = live_duration_now
        all_data["date"] = date
        result.append(all_data)
        time.sleep(5)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_daily_analytics(result))

    # Исправлено форматирование имени файла
    user_live_analytic_json_file = USER_LIVE_ANALYTICS_DIR / f"{timestamp}.json"

    with open(user_live_analytic_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(
        f"Итоговый файл по всем стримерам сохранен в {user_live_analytic_json_file}"
    )


def user_info():
    # Текущие сутки по Гринвичу в Unix timestamp
    timestamp = int(
        datetime.now(timezone.utc)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )

    users = load_product_data(USER_JSON_FILE)
    result = []
    for user in users:
        account_key = user["account_key"]
        url = "https://api.tikapi.io/user/info"

        headers = {
            "X-API-KEY": api_key,
            "X-ACCOUNT-KEY": account_key,
            "accept": "application/json",
        }

        user_info_file = TEMP_DIR / f"user_info_{timestamp}_{account_key}.json"
        if user_info_file.exists():
            logger.debug(f"Файл уже есть {user_info_file} пропускаем")
            continue
        logger.info(f"Запрос по account_key: {account_key}")
        response = requests.get(url, headers=headers)
        json_data = None
        try:
            json_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка {e} {account_key}")
            logger.error(f"Ошибка {e} {response.text}")

            continue
        status_error = json_data.get("status")
        if status_error == "error":
            logger.error(account_key)
            continue
        with open(user_info_file, "w", encoding="utf-8") as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

        logger.info(f"Файл по account_key: {account_key} сохранен {user_info_file}")

        data_json = parsing_user_info(json_data)
        result.append(data_json)
    # Исправлено форматирование имени файла и запись всего списка result
    user_info_result_file = USER_INFO_DIR / f"{timestamp}.json"
    with open(user_info_result_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(f"Итоговый файл по всем стримерам сохранен в {user_info_result_file}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_all_users(users))
    loop.run_until_complete(import_user_data(result))


def parsing_json_user_live_analytics(json_data):
    # json_data = load_product_data(user_live_analytics_json_file)
    diamonds_total = json_data["data"]["diamonds_detail"]["diamonds"]["Total"][-1]

    diamonds_now = diamonds_total["Value"]
    diamonds_date = diamonds_total["Date"]

    live_duration = json_data["data"]["live_duration_detail"]["live_duration"][-1]
    live_duration_now = live_duration["Value"]
    live_duration_date = live_duration["Date"]
    date = None
    if diamonds_date == live_duration_date:
        date = diamonds_date

    return diamonds_now, live_duration_now, date


def parsing_user_info(json_data):
    all_data = {
        "now_data": json_data["extra"]["now"],
        "followerCount": json_data["userInfo"]["stats"]["followerCount"],
        "followingCount": json_data["userInfo"]["stats"]["followingCount"],
        "friendCount": json_data["userInfo"]["stats"]["friendCount"],
        "heart": json_data["userInfo"]["stats"]["heart"],
        "videoCount": json_data["userInfo"]["stats"]["videoCount"],
        "avatarMedium": json_data["userInfo"]["user"]["avatarMedium"],
        "followingVisibility": json_data["userInfo"]["user"]["followingVisibility"],
        "tik_tok_id": json_data["userInfo"]["user"]["id"],
        "isUnderAge18": json_data["userInfo"]["user"]["isUnderAge18"],
        "nickname": json_data["userInfo"]["user"]["nickname"],
        "openFavorite": json_data["userInfo"]["user"]["openFavorite"],
        "privateAccount": json_data["userInfo"]["user"]["privateAccount"],
        "signature": json_data["userInfo"]["user"]["signature"],
        "uniqueId": json_data["userInfo"]["user"]["uniqueId"],
    }
    return all_data


def delete_json():
    # Находим все файлы .json в папке
    json_files = TEMP_DIR.glob("*.json")
    # Собираем все файлы .json в список
    json_files = list(TEMP_DIR.glob("*.json"))
    # Удаляем файлы с минимальной обработкой ошибок
    for json_file in json_files:
        try:
            json_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Ошибка при удалении {json_file}: {e}")


if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Запуск ежедневной задачи: {start_time}")

    try:
        logger.info("Удаляем старые файлы")
        delete_json()
        # # # Выполняем сбор информации о пользователях
        logger.info("Начинаем сбор информации о пользователях")
        user_info()
        logger.info("Сбор информации о пользователях успешно завершен")

        # Выполняем сбор аналитики по трансляциям
        logger.info("Начинаем сбор аналитики трансляций")
        user_live_analytics()
        logger.info("Сбор аналитики трансляций успешно завершен")

        # Запускаем функцию sheets
        logger.info("Начинаем обновление данных в таблицах")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(sheets())
        logger.info("Обновление данных в таблицах успешно завершено")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи: {e}", exc_info=True)

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Задача завершена. Длительность выполнения: {duration}")
