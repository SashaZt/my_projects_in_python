import json
import os

current_directory = os.getcwd()

# Путь к исходному файлу с cookies
input_file = os.path.join(current_directory, "raw_cookies.json")

# Путь к файлу конфигурации, который нужно обновить
config_file = os.path.join(current_directory, "config.json")

# Читаем исходный JSON файл с cookies
with open(input_file, "r", encoding="utf-8") as file:
    original_cookies = json.load(file)

# Создаем новый словарь для cookies
new_cookies = {}

# Добавляем cookies из исходного файла в новый словарь
for cookie in original_cookies:
    new_cookies[cookie["name"]] = cookie["value"]

# Проверяем, существует ли конфигурационный файл и содержит ли он данные
if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
    config_data = {}
else:
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            config_data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e.msg}")
        print(f"Line: {e.lineno}, Column: {e.colno}")
        print(f"Error at character: {e.pos}")
        raise

# Обновляем cookies в конфигурации
config_data["cookies"] = new_cookies

# Если блок headers еще не существует, добавляем его
if "headers" not in config_data:
    config_data["headers"] = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3MTg4NjY2NzQsImlhdCI6MTcxODc4MDI3NCwidXNlcl9pZCI6OTk5MjQxLCJ1biI6IkRldiBPcHMiLCJjdXN0X2lkIjozMzE0NTF9.wpVSVd9N7o4l_CC--ioPj07bvUbIlxu_xv4aX4j2f8Y",
        "dnt": "1",
        "priority": "u=1, i",
        "se-client-version": "d806d9976e8e549810d064a212e4614598edaf0c",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

# Сохраняем обновленный конфигурационный файл
with open(config_file, "w", encoding="utf-8") as file:
    json.dump(config_data, file, ensure_ascii=False, indent=4)

print("Конфигурационный файл успешно обновлен.")
