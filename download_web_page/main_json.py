import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

current_directory = Path.cwd()
json_directory = current_directory / "json"
log_directory = current_directory / "log"

log_directory.mkdir(parents=True, exist_ok=True)

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


def get_json():


    import requests

    url = "https://rrr.lt/ru/poisk"

    params = {
        "q": "K6D39U438AD",
        "prs": "1",
        "page": "1",
        "_": "1739806171498"
    }

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "dnt": "1",
        "priority": "u=1, i",
        "referer": "https://rrr.lt/ru/poisk?q=K6D39U438AD",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    # Передаём cookies в виде словаря
    cookies = {
        "ff_ux_sid": "019504fc-3a84-7388-ad96-2a3660bb4ef4",
        "cart_session": "8f322e0aec7afe3d66f11648c5a0f7b0",
        "CookieConsent": "{stamp:'FJYq039mXvwLvGGsA1nWSv4CIb/hW9IQAXsfAVNMdGD0OSicpLwRFg==',necessary:true,preferences:true,statistics:true,marketing:true,method:'explicit',ver:1,utc:1739545396288,region:'ua'}",
        "soundestID": "20250214150314-tTLL7sADxlRmvWiM8vE5ME7ri725ZI8QIgpd3Qjq3SMoreXXt",
        "disable_ovoko_modal": "67af5b37d1b665.14705006",
        "wishlist": "537d367fad7fd4dac69b5e9a31296570",
        "_sp_id.1c83": "a0bf4e27-4e81-4056-890d-cb7fa6f6a40c.1739797427.1.1739797428..ed012ab0-4695-4520-b3c8-892aa2c4d963..1413d343-f311-4ca7-bd52-d97b150fd93a.1739797427295.8",
        "ci_session": "2c801ede895c447cfb8aa46c3369057d98b282ab",
        "cf_clearance": "RLFWc49rIAzflS_iuFxkQntUfCzG28vWd4FAZOreLxE-1739806139-1.2.1.1-FaYUsB7JXWEujJq7FQRMv2SA8yvqB7wsz06niBH_lQj9bQCj_OFwoioaBlWc9M_UH3IllD0zXs501A.zz.QrSrj1CgcXw03r9wJc.tSTjrYaUeIPInsQvfc3ivO5whHLadvRUqEYKPmNYcjltXlUhXL2bub508Va9V_PnIwAi73D_o8Ji9rz9LGPBGOlm.skp5_6J5vGKMDk2PCkWaJ_6hz5PaHjxMn_KnzwFQRyE_Bmrbt9ForEsZR3sFxosg2DQgKrAQra__BlvLl.P.fV.3DSmjzVg6uUX696BjcisVQ",
        "omnisendSessionID": "QL3CO2dEvKI1o0-20250217152858"
    }

    response = requests.get(url, params=params, headers=headers, cookies=cookies)

    # Если сервер вернул корректный JSON, то выводим его:
    try:
        print(response)
        response
        data = response.json()
        with open("rrr.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        print(data)
    except ValueError:
        print("Ошибка: ответ не содержит JSON")

    # # Проверка успешности запроса
    # if response.status_code == 200:
    #     json_data = response.json()
    #     with open("rrr.json", "w", encoding="utf-8") as f:
    #         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    #     logger.info(json_data)
    #     time.sleep(10)
    # else:
    #     logger.error(response.status_code)


# def extract_user_name(user_id, user_options):
#     filtered_user = list(filter(lambda x: x["value"] == user_id, user_options))
#     return filtered_user[0]["text"] if filtered_user else None


def process_data():
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)


if __name__ == "__main__":
    get_json()
