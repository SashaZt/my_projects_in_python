import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from client_import_live import import_live_streams
from config.config import TEMP_DIR, USER_JSON_FILE, USER_LIVE_LIST_DIR
from config.logger import logger

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


def user_live_list():
    # Текущее время по Гринвичу в Unix timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())

    users = load_product_data(USER_JSON_FILE)
    result = []
    for user in users:
        account_key = user["account_key"]
        tik_tok_id = user["tik_tok_id"]

        url = "https://api.tikapi.io/user/live/list"
        headers = {
            "X-API-KEY": api_key,
            "X-ACCOUNT-KEY": account_key,
            "accept": "application/json",
        }
        logger.info(f"Запрос по account_key: {account_key}")

        response = requests.get(url, headers=headers)
        json_data = None
        try:
            json_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка {e} {account_key}")
            logger.error(f"Ошибка {e} {response.text}")
            continue

        user_live_list_file = TEMP_DIR / f"user_live_list_{timestamp}_{tik_tok_id}.json"
        status_error = json_data.get("status")
        if status_error == "error":
            logger.error(account_key)
            continue

        with open(user_live_list_file, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        logger.info(
            f"Файл по account_key: {account_key} сохранен {user_live_list_file}"
        )
        data_json = parsing_json_user_live_list(json_data, tik_tok_id)
        result.append(data_json)
        time.sleep(5)
    # Исправлено форматирование имени файла
    user_live_list_json_file = USER_LIVE_LIST_DIR / f"{timestamp}.json"
    with open(user_live_list_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(
        f"Итоговый файл по всем стримерам сохранен в {user_live_list_json_file}"
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_live_streams(result))


def parsing_json_user_live_list(json_data, name):
    video_list = json_data["data"]["video_list"]

    result = {name: []}
    for video in video_list:
        all_data = {
            "room_id": video["room_id"],
            "start_time": video["start_time"],
            "end_time": video["end_time"],
            "diamonds": video["diamonds"],
            "duration": video["duration"],
        }
        result[name].append(all_data)
    return result


if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Запуск задачи каждые 4 часа: {start_time}")

    try:
        # Выполняем сбор информации о трансляциях
        user_live_list()
        logger.info("Сбор данных о трансляциях успешно завершен")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи: {e}", exc_info=True)

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Задача завершена. Длительность выполнения: {duration}")
