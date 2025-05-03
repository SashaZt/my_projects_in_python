import csv
import os
import re
from pathlib import Path

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)


def generate_edr_urls_to_csv(output_csv="yearly_finances.csv"):
    # Множество для хранения уникальных HTML-файлов
    html_files = {
        f
        for f in os.listdir(html_files_directory)
        if f.endswith(".html") and f.startswith("_edr_")
    }

    # Список для хранения данных
    data = []

    # Обрабатываем каждый файл
    for file_name in html_files:
        # Извлекаем код ЄДРПОУ из имени файла (например, _edr_00012109.html -> 00012109)
        edrpo_match = re.search(r"_edr_(\d+)\.html", file_name)
        if edrpo_match:
            edrpo = edrpo_match.group(1)
            # Формируем URL
            url = f"https://clarity-project.info/edr/{edrpo}/yearly-finances"
            # Добавляем данные в список
            data.append({"URL": url})

    # Записываем данные в CSV
    with open(output_csv, mode="w", encoding="utf-8", newline="") as csv_file:
        fieldnames = ["URL"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    return data
