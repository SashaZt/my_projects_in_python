import json
import os

current_directory = os.getcwd()
# Путь к исходному файлу с cookies
input_file = os.path.join(current_directory, "shop_olekmotocykle.json")

# Путь к файлу для сохранения нового JSON
output_file = os.path.join(current_directory, "cookies.json")

# Читаем исходный JSON файл
with open(input_file, "r", encoding="utf-8") as file:
    original_cookies = json.load(file)

# Создаем новый словарь для cookies
new_cookies = {}

# Добавляем cookies из исходного файла в новый словарь
for cookie in original_cookies:
    new_cookies[cookie["name"]] = cookie["value"]

# Записываем новый словарь cookies в новый JSON файл
with open(output_file, "w", encoding="utf-8") as file:
    json.dump({"cookies": new_cookies}, file, ensure_ascii=False, indent=4)

print("Новый JSON файл с cookies успешно создан.")
