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


    cookies = {
        'ci_session': '89ce1ca80a105d611439fd301899ef03bde4a024',
        'ff_ux_sid': '019504fc-3a84-7388-ad96-2a3660bb4ef4',
        'cart_session': '8f322e0aec7afe3d66f11648c5a0f7b0',
        'cf_clearance': '3_rpruEg5qJb_bEkgrShX00.uUS7cgkTeh30KaXEY2c-1739545395-1.2.1.1-Z.choenG0Cu6BPOhFvB5Hfa4HqdQwMid._Hx_9_NPzFTxXU7sG69sCQ36QqNBnH9I8uWm.AQZm1LsVbgxSeeimo9csm51D84Adgcu2o1ytqUrFNCKg8OGCn2uyDl4zhwj6H0L.hfXKjanULzFhwO755tO_TZruaKx4TmXFEOYiI1UlM.Q.H0uZ7nCsX0j_OrSX0105wENn_gGFnoz9QzVXwgnG1OKNj9bAK4LfymlkLEcuxcMdb9xV2LuL_Hhz8ib58lGDTV5zRgiKQEHmphBH_pXyyu2uAyfzb2BJ3IJSo',
        'CookieConsent': '{stamp:%27FJYq039mXvwLvGGsA1nWSv4CIb/hW9IQAXsfAVNMdGD0OSicpLwRFg==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cmethod:%27explicit%27%2Cver:1%2Cutc:1739545396288%2Cregion:%27ua%27}',
        'soundestID': '20250214150314-tTLL7sADxlRmvWiM8vE5ME7ri725ZI8QIgpd3Qjq3SMoreXXt',
        'disable_ovoko_modal': '67af5b37d1b665.14705006',
        'wishlist': '537d367fad7fd4dac69b5e9a31296570',
    }

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'cache-control': 'no-cache',
        # 'cookie': 'ci_session=89ce1ca80a105d611439fd301899ef03bde4a024; ff_ux_sid=019504fc-3a84-7388-ad96-2a3660bb4ef4; cart_session=8f322e0aec7afe3d66f11648c5a0f7b0; cf_clearance=3_rpruEg5qJb_bEkgrShX00.uUS7cgkTeh30KaXEY2c-1739545395-1.2.1.1-Z.choenG0Cu6BPOhFvB5Hfa4HqdQwMid._Hx_9_NPzFTxXU7sG69sCQ36QqNBnH9I8uWm.AQZm1LsVbgxSeeimo9csm51D84Adgcu2o1ytqUrFNCKg8OGCn2uyDl4zhwj6H0L.hfXKjanULzFhwO755tO_TZruaKx4TmXFEOYiI1UlM.Q.H0uZ7nCsX0j_OrSX0105wENn_gGFnoz9QzVXwgnG1OKNj9bAK4LfymlkLEcuxcMdb9xV2LuL_Hhz8ib58lGDTV5zRgiKQEHmphBH_pXyyu2uAyfzb2BJ3IJSo; CookieConsent={stamp:%27FJYq039mXvwLvGGsA1nWSv4CIb/hW9IQAXsfAVNMdGD0OSicpLwRFg==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cmethod:%27explicit%27%2Cver:1%2Cutc:1739545396288%2Cregion:%27ua%27}; soundestID=20250214150314-tTLL7sADxlRmvWiM8vE5ME7ri725ZI8QIgpd3Qjq3SMoreXXt; disable_ovoko_modal=67af5b37d1b665.14705006; wishlist=537d367fad7fd4dac69b5e9a31296570',
        'dnt': '1',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://rrr.lt/ru/poisk?q=K6D39U438AD',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'q': 'K6D39U438AD',
        'prs': '1',
        'page': '1',
    }

    response = requests.get('https://rrr.lt/ru/poisk', params=params, cookies=cookies, headers=headers)
    # Проверка успешности запроса
    if response.status_code == 200:
        json_data = response.json()
        with open("rrr.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        logger.info(json_data)
        time.sleep(10)
    else:
        logger.error(response.status_code)


# def extract_user_name(user_id, user_options):
#     filtered_user = list(filter(lambda x: x["value"] == user_id, user_options))
#     return filtered_user[0]["text"] if filtered_user else None


def process_data():
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)


if __name__ == "__main__":
    get_json()
