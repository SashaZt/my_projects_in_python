import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from loguru import logger
from client_import_live import import_live_streams
from tikapi import ResponseException, TikAPI, ValidationException
import time
from config import DATA_DIR, TEMP_DIR, USER_INFO_DIR, USER_LIVE_LIST_DIR, USER_LIVE_ANALYTICS_DIR, USER_JSON_FILE

current_directory = Path.cwd()
log_directory = current_directory / "log"
# data_directory = current_directory / "data"
# temp_directory = current_directory / "temp"
# user_live_analytics_directory = current_directory / "user_live_analytics"
# user_live_list_directory = current_directory / "user_live_list"
# user_info_directory = current_directory / "user_info"


# data_directory.mkdir(parents=True, exist_ok=True)
# temp_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
# user_live_analytics_directory.mkdir(parents=True, exist_ok=True)
# user_live_list_directory.mkdir(parents=True, exist_ok=True)
# user_info_directory.mkdir(parents=True, exist_ok=True)

# user_json_file = data_directory / "users.json"

log_file_path = log_directory / "log_message.log"



api_key = TikAPI("vNkKTf5VFTPmyxhg0YsNkPo5TrCe4OLFDh8xmMxJNpaMmVvB")

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

def user_live_list():
    # Текущее время по Гринвичу в Unix timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())

    users = load_product_data(USER_JSON_FILE)
    result = []
    for user in users:
        account_key = user["account_key"]
        tik_tok_id = user["tik_tok_id"]
        account_user = api_key.user(accountKey=account_key)
        user_live_list_file = TEMP_DIR / f"user_live_list_{timestamp}_{tik_tok_id}.json"
        if user_live_list_file.exists():
            # Если файл существует, читаем из него данные
            with open(user_live_list_file, "r", encoding="utf-8") as json_file:
                user_data = json.load(json_file)

            data_json = parsing_json_user_live_list(user_data, tik_tok_id)
            result.append(data_json)

            continue
        # Добавляем логику повторных попыток
        max_attempts = 10
        attempt = 0
        success = False
            
        while attempt < max_attempts and not success:
            try:
                response = account_user.live.list()
                
                # Проверяем статус ответа
                if hasattr(response, 'status_code') and response.status_code == 200:
                    success = True
                    data_json = parsing_json_user_live_list(response.json(), tik_tok_id)
                    result.append(data_json)
                    logger.info(f"Successfully got live list for user {tik_tok_id}")
                    
                    user_live_list_file = TEMP_DIR / f"user_live_list_{timestamp}_{tik_tok_id}.json"
                    with open(user_live_list_file, "w", encoding="utf-8") as json_file:
                        json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
                else:
                    # Если статус не 200, ждем и повторяем
                    attempt += 1
                    logger.warning(f"Attempt {attempt}/{max_attempts}: Got status code {getattr(response, 'status_code', 'unknown')}. Retrying in 5 seconds...")
                    time.sleep(5)
            except ValidationException as e:
                attempt += 1
                logger.error(f"Validation error (attempt {attempt}/{max_attempts}): {e}")
                if hasattr(e, 'field'):
                    logger.error(f"Field with error: {e.field}")
                time.sleep(5)
            except ResponseException as e:
                attempt += 1
                logger.error(f"Response error (attempt {attempt}/{max_attempts}): {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    logger.error(f"Status code: {e.response.status_code}")
                time.sleep(5)
            except Exception as e:
                attempt += 1
                logger.error(f"Unexpected error (attempt {attempt}/{max_attempts}): {e}")
                time.sleep(5)
        
        # Проверяем, был ли успешный запрос
        if not success:
            logger.error(f"Failed to get live list for user {tik_tok_id} after {max_attempts} attempts")
    
    # Исправлено форматирование имени файла
    user_live_list_json_file = USER_LIVE_LIST_DIR / f"{timestamp}.json"
    with open(user_live_list_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_live_streams(result))


def parsing_json_user_live_list(json_data,name):
    # json_data = load_product_data("result_7312401215441126406.json")
    video_list = json_data["data"]["video_list"]
    
    # name = 7312401215441126406
    result = {name: []}
    for video in video_list:
        all_data = {
            "room_id": video["room_id"],
            "start_time": video["start_time"],
            "end_time": video["end_time"],
            "diamonds": video["diamonds"],
            "duration": video["duration"],
        }
        result[name].append(all_data)  # Просто добавляем словарь в список
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
    