# -*- mode: python ; coding: utf-8 -*-
# Парсим url компани с папки list
import json
import csv
import os
import glob


def main():
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    list_path = os.path.join(temp_path, "list")
    folder = os.path.join(list_path, "*.json")
    files_json = glob.glob(folder)
    
    # Использование множества для исключения дубликатов
    company_ids = set()

    for item in files_json:
        with open(item, "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                for company in data.get("items", []):  # Предполагаем, что data может не иметь ключа "items"
                    company_ids.add(f'https://www.centraldispatch.com/protected/rating/client-snapshot?id={company["companyId"]}')
            except json.JSONDecodeError:
                print(f"Ошибка чтения JSON из файла {item}")

    # Запись уникальных companyId в CSV
    csv_file = "unique_company_ids.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["companyId"])  # Заголовок для CSV файла
        for company_id in company_ids:
            writer.writerow([company_id])

    print(f"Уникальные companyId были записаны в файл {csv_file}.")

if __name__ == "__main__":
    main()
