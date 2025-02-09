import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger
from openpyxl import Workbook

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
json_files_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
json_files_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

csv_output_file = data_directory / "output.csv"
json_result = data_directory / "result.json"
xlsx_result = data_directory / "result.xlsx"


def read_cities_from_csv(input_csv_file):
    # Загрузка CSV-файла с указанием, что столбец "url" является строкой
    df = pd.read_csv(input_csv_file, dtype={"url": str})
    return df["url"].tolist()


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def fetch_and_save_json(tin, year):
    out_json_file = json_files_directory / f"{tin}_{year}.json"
    if out_json_file.exists():
        return  # Пропускаем, если файл уже существует

    params = {
        "tin": tin,
        "year": year,
        "startMonth": "1",
        "endMonth": "12",
    }
    try:
        r = requests.get(
            "https://budget.okmot.kg/api/income/tin",
            params=params,
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            json_data = r.json()
            with open(out_json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
        else:
            logger.error(f"Error {r.status_code} for TIN {tin}, Year {year}")
    except requests.RequestException as e:
        logger.error(f"Request failed for TIN {tin}, Year {year}: {e}")


def process_tin(tin, years):
    for year in years:
        fetch_and_save_json(tin, year)


def get_json(num_threads=10):
    tins = read_cities_from_csv(csv_output_file)
    years = ["2021", "2022", "2023", "2024"]

    # Используем ThreadPoolExecutor для многопоточности
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for tin in tins:  # Ограничение для примера, используйте нужный диапазон
            executor.submit(process_tin, tin, years)


def parsin_json():
    # Список словарей для результата
    result = []

    for json_file in json_files_directory.glob("*.json"):
        # Разделяем имя файла, чтобы извлечь INN и год
        inn, year = json_file.stem.split(
            "_"
        )  # Используем .stem для имени файла без расширения

        # Читаем содержимое файла
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        # Извлекаем значение "Sum" из содержимого файла
        file_sum = data.get("Sum", "0.00")

        # Ищем словарь с текущим INN в результате
        inn_entry = next((entry for entry in result if entry["inn"] == inn), None)

        if not inn_entry:
            # Если словаря с таким INN еще нет, создаем его
            inn_entry = {"inn": inn}
            result.append(inn_entry)

        # Добавляем год и сумму в словарь
        inn_entry[year] = file_sum
    save_to_excel(result)


def save_to_excel(result, output_file="result.xlsx"):
    # Создаем новую книгу Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"

    # Записываем заголовки
    headers = ["INN"] + sorted(
        {year for entry in result for year in entry.keys() if year != "inn"}
    )
    sheet.append(headers)

    # Записываем данные
    for entry in result:
        row = [entry.get("inn", "")]
        for year in headers[1:]:
            row.append(entry.get(year, "0.00"))
        sheet.append(row)

    # Сохраняем в файл
    workbook.save(output_file)


if __name__ == "__main__":
    num_threads = 10  # Задайте нужное количество потоков
    get_json(num_threads=num_threads)
    parsin_json()
