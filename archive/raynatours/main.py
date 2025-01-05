import asyncio
import json
import os
from datetime import datetime
import asyncio
import time
import sys
import os


from curl_cffi.requests import AsyncSession


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    headers = config["headers"]

    # Генерация строки кукисов из конфигурации
    if "cookies" in config:
        cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
        headers["Cookie"] = cookies_str

    # Добавление JSON строки в данные запроса
    data = '{"Flag": 2}'  # Форматируем JSON строку правильно
    config["data"] = data
    return config


async def get_city():
    config = load_config()
    headers = config.get("headers", {})
    data = config.get("data", {})
    json_data = {
        "TourIds": "",
        "CountryId": 13063,
        "CityId": 13668,
    }
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    # Создание директории, если она не существует
    os.makedirs(temp_path, exist_ok=True)
    session = AsyncSession()
    url_city = "https://www.raynatours.com/AjaxCall.aspx/GetTourListWithTourType"
    response = await session.get(url_city, headers=headers, json=json_data)
    json_data = response.json()
    with open(f"get_city.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

    await session.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_city())
