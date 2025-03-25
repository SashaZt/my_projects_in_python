import json
import sys
from pathlib import Path

from loguru import logger

from tikapi import ResponseException, TikAPI, ValidationException

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

user_live_analytics_json_file = current_directory / "user_live_analytics.json"
user_info_json_file = current_directory / "user_info.json"
log_file_path = log_directory / "log_message.log"

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
api = TikAPI("vNkKTf5VFTPmyxhg0YsNkPo5TrCe4OLFDh8xmMxJNpaMmVvB")
User = api.user(accountKey="Zk87nslgswy8Nvu4y2GpyouVlwzB8dyuglJbrCb3esSmHMAO")


def user_info():
    try:
        response = User.info()
        with open(user_info_json_file, "w", encoding="utf-8") as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

    except ValidationException as e:
        print(e, e.field)

    except ResponseException as e:
        print(e, e.response.status_code)


def user_live_analytics():
    try:
        response = User.live.analytics()
        with open(user_live_analytics_json_file, "w", encoding="utf-8") as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)

    except ValidationException as e:
        logger.error(e, e.field)

    except ResponseException as e:
        logger.error(e, e.response.status_code)


def load_product_data(file_name):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


def parsing_json():
    json_data = load_product_data(user_live_analytics_json_file)
    diamonds_total = json_data["data"]["diamonds_detail"]["diamonds"]["Total"][-1]

    diamonds_now = diamonds_total["Value"]
    diamonds_date = diamonds_total["Date"]

    live_duration = json_data["data"]["live_duration_detail"]["live_duration"][-1]
    live_duration_now = live_duration["Value"]
    live_duration_date = live_duration["Date"]
    date = None
    if diamonds_date == live_duration_date:
        date = diamonds_date

    all_data = {
        "diamonds_value": diamonds_now,
        "live_duration": live_duration_now,
        "date": date,
    }
    logger.info(all_data)


if __name__ == "__main__":
    user_info()
    # user_live_analytics()
    # parsing_json()


# # 1.
# try:
#     response = User.live.permissions()

#     print(response.json())

# except ValidationException as e:
#     print(e, e.field)

# except ResponseException as e:
#     print(e, e.response.status_code)

# 2.
# # Детальная информация по стриму 'duration': 259,
# try:
#     response = User.live.details(        room_id="7485764067316960006"    )

#     print(response.json())

# except ValidationException as e:
#     print(e, e.field)

# except ResponseException as e:
#     print(e, e.response.status_code)


# try:
#     response = User.live.list()

#     print(response.json())

# except ValidationException as e:
#     print(e, e.field)

# except ResponseException as e:
#     print(e, e.response.status_code)


# try:
#     response = User.live.chat(
#         room_id="7485757040473950982"
#     )

#     print(response.json())

#     while(response):
#         nextCursor = response.json().get('nextCursor')
#         print("Getting next items ", nextCursor)
#         response = response.next_items()

# except ValidationException as e:
#     print(e, e.field)

# except ResponseException as e:
#     print(e, e.response.status_code)
