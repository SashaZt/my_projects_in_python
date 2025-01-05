import json
import os

current_directory = os.getcwd()

# Путь к исходному файлу с cookies
input_file = os.path.join(current_directory, "cookies.json")

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

# Загружаем текущий конфигурационный файл
with open(config_file, "r", encoding="utf-8") as file:
    config_data = json.load(file)

# Обновляем cookies в конфигурации
config_data["cookies"] = new_cookies

# Сохраняем обновленный конфигурационный файл
with open(config_file, "w", encoding="utf-8") as file:
    json.dump(config_data, file, ensure_ascii=False, indent=4)

print("Конфигурационный файл успешно обновлен.")
