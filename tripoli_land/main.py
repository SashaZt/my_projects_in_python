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


# Определяем общие заголовки
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://tripoli.land/farmers/proizvoditeli-zerna/zhitomirskaya/proizvoditeli-gorokha?",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-csrf-token": "NtuuufcEKCAtU7cnH/C/RZTCJbd6EigY1YfyyR+EUsBtYG7S3h9sR5IvymKj/KvrHUOWKXLgR8dxLUr1qh7E2A==",
    "x-xsrf-token": "cZlab2OutJ7Qoc3KJFT7ENIY5Vx1Ix34khifFUm0qyUqIpoESrXw+W/dsI+YWO++W5lWwn3Rcic2sicp/C49PQ==",
}

# Определяем куки
cookies = {
    "prev_locale": "PREV",
    "sc": "B08943C0-AD6F-889F-98CC-CD720CAD8092",
    "_ga": "GA1.2.2078179902.1742825923",
    "remember_user_token": "W1syOTEzOTBdLCIkMmEkMTAkVlFCN21yN0xHSkU1MVFWemxrVm5DTyJd--540dcdc9c2fef77aca2ba602ba2647d7ec42b08a",
    "write_entrance": "20250405",
    "XSRF-TOKEN": "cZlab2OutJ7Qoc3KJFT7ENIY5Vx1Ix34khifFUm0qyUqIpoESrXw%2BW%2FdsI%2BYWO%2B%2BW5lWwn3Rcic2sicp%2FC49PQ%3D%3D",
    "_ack_session": "L1YrMFpXcW1hSDlubW9FalRkbVhvcTJpK2plcW5qdmNXcHdlWUVmN0VHNDViYUNNT2JpR25xRjRZQXlvdFd3VlVWY2tyVGRiNTcyYXJSU0tSdXl5bnJ5ME5tOUMrZnBEM3Y1TXJQVVhHTVpoZGNlK0RHVnNHSVRKc0hhMFo0STZFWms1UXZ6OStHTVFiOG1yVmgrSFpLaFpZOU1yNEEyZmZHYmtxdENWSVZOZXdWaFJyZ3hNcUtLeXkzL0xHd3RPWDYvYXJRa2hpek9DcGQ5L2FVVlRleXpydjRJRzk2Z2hvR0twcHFpemxBdjlLcU5kRlZoT1VqL29xN3QzeXgxNmVtbVRiTXNZc01zL2x0RXdnTFhPVlRzZzkyc3B0eHdZZHRJZERFR1J6VjFvOWlkSm1GNS9jZmZlWXc0RWFiRlIxeDAxTDhHNjRhUnAwUE5SR0Y0c3ZzOHRiTmF4ZmxlSFNHc25PTll2KzhVPS0tNGl0ZHRFR3pDVmo1UkYraG9Fdkt6Zz09--78e65366dd4520bdf4720d1cd19f25989dbcceeb",
}
id_company = "9356"
# Список URL и имен файлов для сохранения
requests_list = [
    {
        "url": f"https://tripoli.land/load-lazy-resources/{id_company}",
        "filename": f"{id_company}_lazy_resources.json",
    },
    {
        "url": f"https://tripoli.land/profile/org_corrections?org_id={id_company}",
        "filename": f"{id_company}_org_corrections.json",
    },
    {
        "url": f"https://tripoli.land/profile/auxiliary_contacts?catalog_org_id={id_company}",
        "filename": f"{id_company}_auxiliary_contacts.json",
    },
]

# Создаем сессию
# Создаем сессию
with requests.Session() as session:
    # Устанавливаем куки и заголовки для сессии
    session.cookies.update(cookies)
    session.headers.update(headers)

    # Выполняем все запросы
    for request in requests_list:
        try:
            response = session.get(request["url"])
            response.raise_for_status()  # Проверка на ошибки HTTP

            # Формируем путь к файлу
            file_path = json_directory / request["filename"]

            # Парсим JSON и сохраняем в файл
            data = response.json()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Успешно сохранено: {file_path}")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе {request['url']}: {e}")
        except json.JSONDecodeError as e:
            print(f"Ошибка при парсинге JSON для {request['url']}: {e}")
