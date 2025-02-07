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
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    headers = {
        "Accept": "application/json, text/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        # 'Cookie': 'ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        "DNT": "1",
        "Referer": "https://kaspi.kz/shop/c/categories/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-KS-City": "750000000",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "depth": "2",
        "city": "750000000",
        "code": "Smartphones and gadgets",
        "rootType": "desktop",
    }

    response = requests.get(
        "https://kaspi.kz/yml/main-navigation/n/n/desktop-menu",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    # Проверка успешности запроса
    if response.status_code == 200:
        json_data = response.json()
        with open("kaspi.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        logger.info(json_data)
        time.sleep(10)
    else:
        logger.error(response.status_code)
