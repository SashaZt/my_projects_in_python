import json
import sys
from pathlib import Path

from loguru import logger

from tikapi import ResponseException, TikAPI, ValidationException

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

user_live_analytics_json_file = current_directory / "user_live_analytics.json"
user_info_json_file = current_directory / "users.json"
log_file_path = log_directory / "log_message.log"
api = TikAPI("vNkKTf5VFTPmyxhg0YsNkPo5TrCe4OLFDh8xmMxJNpaMmVvB")
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


def user_live_analytics(day):
    
    users = load_product_data(user_info_json_file)
    result = []
    for user in users:
        account_key = user["account_key"]
        User = api.user(accountKey=account_key)
        tik_tok_id = user["tik_tok_id"]
        try:
            # Передаем целое число, а не строку
            response = User.live.analytics(days=day)
            # Обработка результата
            user_data_file = current_directory / f"users{tik_tok_id}.json"
            with open(user_data_file, "w", encoding="utf-8") as json_file:
                json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

            all_data = {"tik_tok_id":tik_tok_id}
            diamonds_now, live_duration_now,date = parsing_json_user_live_analytics(response.json())
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
        except Exception as e:
            # Общая обработка других исключений
            logger.error(f"Unexpected error: {e}")
            
            
        except ValidationException as e:
            logger.error(e, e.field)

        except ResponseException as e:
            logger.error(e, e.response.status_code)
    with open(f"result_{date}.json", "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    logger.info(result)



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
    
def user_live_list():
    users = load_product_data(user_info_json_file)
    result = []
    for user in users[:1]:
        account_key = user["account_key"]
        User = api.user(accountKey=account_key)
        tik_tok_id = user["tik_tok_id"]

        try:
            response = User.live.list()

            with open(f"result_{tik_tok_id}.json", "w", encoding="utf-8") as json_file:
                json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
            logger.info(result)

        except ValidationException as e:
            print(e, e.field)

        except ResponseException as e:
            print(e, e.response.status_code)
def parsing_json_user_live_list():
    json_data = load_product_data("result_7312401215441126406.json")
    video_list = json_data["data"]["video_list"]
    
    name = 7312401215441126406
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
    print(result)

def user_info():
    users = load_product_data(user_info_json_file)
    result = []
    for user in users[:1]:
        account_key = user["account_key"]

        User = api.user(accountKey=account_key)

        try:
            response = User.info()

            with open(f"result_info_{account_key}.json", "w", encoding="utf-8") as json_file:
                json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

        except ValidationException as e:
            print(e, e.field)

        except ResponseException as e:
            print(e, e.response.status_code)
def parsing_user_info():
    json_data = load_product_data("result_info_NYaRLHw0uSLhou1v0Ztie9jQjMVioKSu0lcTfGTsi3EK6arK.json")
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
        "nickNameModifyTime": json_data["userInfo"]["user"]["nickNameModifyTime"],
        "nickname": json_data["userInfo"]["user"]["nickname"],
        "openFavorite": json_data["userInfo"]["user"]["openFavorite"],
        "privateAccount": json_data["userInfo"]["user"]["privateAccount"],
        "signature": json_data["userInfo"]["user"]["signature"],
        "uniqueId": json_data["userInfo"]["user"]["uniqueId"]
    }
    print(all_data)

if __name__ == "__main__":
    day = 1
    user_live_analytics(day)
    # user_live_list()
    # parsing_json_user_live_list()
    # user_info()
    # parsing_user_info()