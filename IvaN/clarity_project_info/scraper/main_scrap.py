import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import pandas as pd
from bs4 import BeautifulSoup
from config.logger import logger
from tqdm import tqdm

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

data = {}

# Список полей для извлечения
fields = [
    "ЄДРПОУ",
    "Назва",
    "Організаційна форма",
    "Адреса",
    "Стан",
    "Дата реєстрації",
    "Уповноважені особи",
    "Види діяльності",
]
with open("_edr_00010808.html", encoding="utf-8") as file:
    src = file.read()
soup = BeautifulSoup(src, "lxml")
# Создаем объект BeautifulSoup

# Словарь для хранения данных


# Проходим по строкам таблицы
for row in soup.find("table").find_all("tr"):
    cells = row.find_all("td")
    if len(cells) == 2:
        label = cells[0].text.strip().replace(":", "").strip()
        value = cells[1].text.strip()

        # Извлекаем данные для указанных полей
        if label in fields:
            if label == "Види діяльності":
                # Извлекаем только первую строку видов деятельности
                activity = (
                    cells[1]
                    .find("div", class_="company-activity-list")
                    .find("div", class_="activity-item")
                    .text.strip()
                )
                # Убираем лишние пробелы и табуляции, добавляем пробел после кода
                activity = re.sub(r"\s+", " ", activity).strip()
                data[label] = activity
            elif label == "Назва":
                # Извлекаем только основное название, без дополнительной информации в <div>
                main_name = cells[1].contents[0].strip()
                data[label] = main_name
            elif label == "Адреса":
                # Извлекаем основной адрес, игнорируя дополнительный в <div>
                main_address = cells[1].contents[0].strip()
                data[label] = main_address
            elif label == "Уповноважені особи":
                # Извлекаем имя и должность
                person = (
                    cells[1].find("a").text.strip()
                    + " - "
                    + cells[1].find("span", class_="text-secondary").text.strip()
                )
                data[label] = person
            elif label == "Стан":
                # Извлекаем только текст статуса
                status = (
                    cells[1]
                    .find("div", class_="text-primary")
                    .text.strip()
                    .replace("Зареєстровано", "")
                    .strip()
                )
                data[label] = "Зареєстровано"
            else:
                # Для остальных полей извлекаем текст
                data[label] = value.split("\n")[0].strip()

                # Вывод результата
print(data)
