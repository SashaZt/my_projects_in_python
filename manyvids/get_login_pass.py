import csv
import json

# Путь к вашему CSV-файлу
csv_file_path = 'login_pass.csv'

# Словарь для хранения преобразованных данных
data = {}

# Чтение CSV-файла и заполнение словаря
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        key = f"{row[0]}_{row[1]}"
        data[key] = {row[2]: row[3]}

# Преобразование словаря в JSON и запись в файл
with open('login_pass.json', mode='w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=3)

print("CSV успешно преобразован в JSON.")
