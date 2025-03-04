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

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "origin": "https://ba.prg.kz",
    "priority": "u=1, i",
    "referer": "https://ba.prg.kz/",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}
def get_json(id_company):

    

    params = {
        "id": id_company,
        "lang": "ru",
    }

    response = requests.get(
        "https://apiba.prgapp.kz/CompanyFullInfo",
        params=params,
        headers=headers,
        timeout=30,
    )
    file_name = json_directory / f"{id_company}.json"
    # Если сервер вернул корректный JSON, то выводим его:
    try:
        data = response.json()
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    except ValueError:
        print("Ошибка: ответ не содержит JSON")



def process_data():
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)


if __name__ == "__main__":
    get_json()
