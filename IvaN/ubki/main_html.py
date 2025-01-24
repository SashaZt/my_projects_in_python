import concurrent.futures
import json
import os
from pathlib import Path
import concurrent.futures
import csv
import json
import os
import random
import re
import time
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger 

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"
# Пути к файлам
output_csv_file = current_directory / "urls.csv"
txt_file_proxies = configuration_directory / "proxies.txt"
# Создание директорий, если их нет
html_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

def load_json_file(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    try:
        return json_data["clients"][0]["taxNumber"]
    except (KeyError, IndexError):
        logger.error(f"Ошибка при чтении JSON файла {json_file.name}: Нет доступа к 'taxNumber'")
        return None

def process_json_files(json_directory):
    json_files = list(json_directory.glob('*.json'))
    taxNumbers = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(load_json_file, file): file for file in json_files}
        
        for future in concurrent.futures.as_completed(future_to_file):
            taxNumber = future.result()
            if taxNumber:
                taxNumbers.append(taxNumber)
    
    return taxNumbers

def main():
    
    taxNumbers = process_json_files(json_directory)

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:  # Опционально, задайте количество потоков
        # Отправляем каждый taxNumber на обработку через get_html
        futures = [executor.submit(get_html, taxNumber) for taxNumber in taxNumbers if taxNumber]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # Проверка успешности выполнения задачи
            except Exception as e:
                logger.error(f"Произошла ошибка при загрузке HTML: {e}")

def get_html(taxNumber):
    if taxNumber is None:
        logger.error("Не удалось получить номер налогоплательщика.")
        return
    cookies = {
        'LNG': 'UA',
        'LNG': 'UA',
        '_csrf': 'c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D',
        'device-referrer': 'https://edrpou.ubki.ua/ua/FO12726884',
        'device-source': 'https://edrpou.ubki.ua/ua/FO14352035',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'cache-control': 'no-cache',
        # 'cookie': 'LNG=UA; LNG=UA; _csrf=c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D; device-referrer=https://edrpou.ubki.ua/ua/FO12726884; device-source=https://edrpou.ubki.ua/ua/FO14352035',
        'dnt': '1',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://edrpou.ubki.ua/ua',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    html_files = html_directory / f"{taxNumber}.html"

    if html_files.exists():
        return

    response = requests.get(f'https://edrpou.ubki.ua/ua/{taxNumber}', cookies=cookies, headers=headers, timeout=30)
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open(html_files, "w", encoding="utf-8") as file:
            file.write(response.text)
    else:
        logger.error(response.status_code)

if __name__ == "__main__":
    main()