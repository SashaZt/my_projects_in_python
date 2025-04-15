import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from loguru import logger
from client_import_stats import import_user_stats
from client_import_live import import_daily_analytics, import_live_streams
from client_import_user import import_all_users, import_user_data
from tikapi import ResponseException, TikAPI, ValidationException
import time

current_directory = Path.cwd()
log_directory = current_directory / "log"
temp_directory = current_directory / "temp"
user_live_analytics_directory = current_directory / "user_live_analytics"
user_live_list_directory = current_directory / "user_live_list"
user_info_directory = current_directory / "user_info"


temp_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
user_live_analytics_directory.mkdir(parents=True, exist_ok=True)
user_live_list_directory.mkdir(parents=True, exist_ok=True)
user_info_directory.mkdir(parents=True, exist_ok=True)

user_json_file = current_directory / "users.json"

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


def user_live_analytics():
    day = 1
    users = load_product_data(user_json_file)
    result = []
    # Текущие сутки по Гринвичу в Unix timestamp
    timestamp = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    for user in users:
        account_key = user["account_key"]
        tik_tok_id = user["tik_tok_id"]
        user_data_file = temp_directory / f"user_live_analytics_{timestamp}_{tik_tok_id}.json"
        
        if user_data_file.exists():
            # Если файл существует, читаем из него данные
            with open(user_data_file, "r", encoding="utf-8") as json_file:
                user_data = json.load(json_file)

            all_data = {"tik_tok_id": tik_tok_id}
            diamonds_now, live_duration_now, date = parsing_json_user_live_analytics(user_data)
            all_data["diamonds_now"] = diamonds_now
            all_data["live_duration_now"] = live_duration_now
            all_data["date"] = date
            result.append(all_data)

            continue

        account_user = api_key.user(accountKey=account_key)
        try:
            # Передаем целое число, а не строку
            # # Ууазывае только количество дней
            # response = account_user.live.analytics(days=day)
            # По-умолчанию 7 дней
            # Добавляем логику повторных попыток
            max_attempts = 10
            attempt = 0
            success = False
            
            while attempt < max_attempts and not success:
                try:
                    response = account_user.live.analytics()
                    # Проверяем статус ответа
                    if hasattr(response, 'status_code') and response.status_code == 200:
                        success = True
                    else:
                        # Если статус не 200, ждем и повторяем
                        attempt += 1
                        logger.warning(f"Attempt {attempt}/{max_attempts}: Got status code {getattr(response, 'status_code', 'unknown')}. Retrying in 5 seconds...")
                        time.sleep(5)
                except Exception as e:
                    attempt += 1
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed with error: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            
            # Проверяем, был ли успешный запрос
            if not success:
                logger.error(f"Failed to get analytics for user {tik_tok_id} after {max_attempts} attempts")
                continue
            with open(user_data_file, "w", encoding="utf-8") as json_file:
                json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

            all_data = {"tik_tok_id": tik_tok_id}
            diamonds_now, live_duration_now, date = parsing_json_user_live_analytics(response.json())
            all_data["diamonds_now"] = diamonds_now
            all_data["live_duration_now"] = live_duration_now
            all_data["date"] = date
            result.append(all_data)
            
        except ValidationException as e:
            # Правильная обработка исключения ValidationException
            logger.error(f"Validation error: {e}")
            # Если нужен доступ к полю, используйте отдельный лог
            if hasattr(e, 'field'):
                logger.error(f"Field with error: {e.field}")
        except ResponseException as e:
            # Обработка ResponseException
            logger.error(f"Response error: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.error(f"Status code: {e.response.status_code}")
        except Exception as e:
            # Общая обработка других исключений
            logger.error(f"Unexpected error: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_daily_analytics(result))       
    
    # Исправлено форматирование имени файла
    user_live_analytic_json_file = user_live_analytics_directory / f"{timestamp}.json"
    
    with open(user_live_analytic_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(result)


def user_live_list():
    # Текущее время по Гринвичу в Unix timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())

    users = load_product_data(user_json_file)
    result = []
    for user in users:
        account_key = user["account_key"]
        tik_tok_id = user["tik_tok_id"]
        account_user = api_key.user(accountKey=account_key)
        user_live_list_file = temp_directory / f"user_live_list_{timestamp}_{tik_tok_id}.json"
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
                    
                    user_live_list_file = temp_directory / f"user_live_list_{timestamp}_{tik_tok_id}.json"
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
    user_live_list_json_file = user_live_list_directory / f"{timestamp}.json"
    with open(user_live_list_json_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(import_live_streams(result))


def user_info():
    # Текущие сутки по Гринвичу в Unix timestamp
    timestamp = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    users = load_product_data(user_json_file)
    result = []
    for user in users:
        account_key = user["account_key"]
        account_user = api_key.user(accountKey=account_key)

        user_info_file = temp_directory / f"user_info_{timestamp}_{account_key}.json"
        if user_info_file.exists():
            # Если файл существует, читаем из него данные
            with open(user_info_file, "r", encoding="utf-8") as json_file:
                user_data = json.load(json_file)

            data_json = parsing_user_info(user_data)
            result.append(data_json)

            continue

        # Добавляем логику повторных попыток
        max_attempts = 10
        attempt = 0
        success = False
            
        while attempt < max_attempts and not success:
            try:
                response = account_user.info()
                
                # Проверяем статус ответа
                if hasattr(response, 'status_code') and response.status_code == 200:
                    success = True

                    data_json = parsing_user_info(response.json())
                    result.append(data_json)
                    logger.info(f"Successfully got user info for account {account_key}")
                    
                    user_info_file = temp_directory / f"user_info_{timestamp}_{account_key}.json"
                    with open(user_info_file, "w", encoding="utf-8") as json_file:
                        json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
                
                elif response.status_code == 401:
                    logger.warning(f"Проверить аккаунт с {account_key}")
                    break

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
                logger.error(f"Response error {account_key} (attempt {attempt}/{max_attempts}): {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    status_code = e.response.status_code
                    logger.error(f"Status code: {status_code}")
                    
                    # Если статус 401, выходим из цикла
                    if status_code == 401:
                        logger.error(f"ТРЕБУЕТСЯ ПРОВЕРКА АККАУНТА! ОШИБКА АВТОРИЗАЦИИ 401 для account_key: {account_key}")
                        
                        # Запись в отдельный файл для последующей проверки
                        auth_error_file = user_info_directory / "auth_errors.json"
                        try:
                            # Загружаем существующие ошибки если файл есть
                            if auth_error_file.exists():
                                with open(auth_error_file, "r", encoding="utf-8") as error_file:
                                    auth_errors = json.load(error_file)
                            else:
                                auth_errors = []
                            
                            # Добавляем новую ошибку
                            auth_errors.append({
                                "timestamp": timestamp,
                                "account_key": account_key,
                                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                "error_message": str(e)
                            })
                            
                            # Сохраняем обновленный список
                            with open(auth_error_file, "w", encoding="utf-8") as error_file:
                                json.dump(auth_errors, error_file, ensure_ascii=False, indent=4)
                        except Exception as save_err:
                            logger.error(f"Не удалось записать информацию об ошибке авторизации: {save_err}")
                        
                        # Выходим из цикла
                        break
            except Exception as e:
                attempt += 1
                logger.error(f"Unexpected error (attempt {attempt}/{max_attempts}): {e}")
                time.sleep(5)
        
        # Проверяем, был ли успешный запрос
        if not success:
            logger.error(f"Failed to get user info for account {account_key} after {max_attempts} attempts")
    
    # Исправлено форматирование имени файла и запись всего списка result
    user_info_result_file = user_info_directory / f"{timestamp}.json"
    with open(user_info_result_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    
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

    return diamonds_now, live_duration_now,date

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

def parsing_user_info(json_data):
    # json_data = load_product_data("result_info_NYaRLHw0uSLhou1v0Ztie9jQjMVioKSu0lcTfGTsi3EK6arK.json")
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
        "uniqueId": json_data["userInfo"]["user"]["uniqueId"]
    }
    return all_data

if __name__ == "__main__":
    # 1. Раз в сутки запускать
    # user_info()
    # user_live_analytics()

    # 2. Раз в 4 часа
    user_live_list()
    