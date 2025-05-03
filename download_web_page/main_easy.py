import csv
import json
import os

# Папка с JSON-файлами
folder_path = "json"

# Список для хранения всех id
all_ids = set()

# Обход всех файлов в папке
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Проверка и извлечение id
                bizlist = data.get("bizlist", {})
                for item in bizlist.get("list", []):
                    if "id" in item:
                        all_ids.add(item["id"])
            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

# Запись в urls.csv
with open("urls.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["id"])  # заголовок
    for id_value in all_ids:
        writer.writerow([id_value])

print(f"Извлечено {len(all_ids)} id и записано в urls.csv")
