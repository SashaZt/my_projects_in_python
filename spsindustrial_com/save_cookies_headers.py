import json
from pathlib import Path

# Инструкция:
# 1. Перейдите на сайт curlconverter.com и вставьте ваш cURL-запрос.
# 2. Скопируйте сгенерированные cookies и headers в файл raw_cookies.txt.
# 3. Запустите этот скрипт для создания файлов cookies.json и headers.json.

# Директория для конфигурации
config_directory = Path("configuration")
config_directory.mkdir(exist_ok=True)

# Пути к файлам
raw_cookies_file = config_directory / "raw_cookies.txt"
cookies_file = config_directory / "cookies.json"
headers_file = config_directory / "headers.json"

# Чтение данных из файла raw_cookies.txt
with open(raw_cookies_file, "r", encoding="utf-8") as f:
    raw_data = f.read()

# Выполнение кода из файла для создания переменных cookies и headers
exec(raw_data)

# Сохранение cookies в JSON файл
with open(cookies_file, "w", encoding="utf-8") as f:
    json.dump(cookies, f, ensure_ascii=False, indent=4)

# Сохранение headers в JSON файл
with open(headers_file, "w", encoding="utf-8") as f:
    json.dump(headers, f, ensure_ascii=False, indent=4)

print(f"Cookies сохранены в {cookies_file}")
print(f"Headers сохранены в {headers_file}")
