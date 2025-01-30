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

def get_json(dr_common_data):
    
    cookies = {
    '_csrf': 'c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D',
    'device-referrer': 'https://edrpou.ubki.ua/ua/FO12726884',
    'LNG': 'UA',
    'device-source': 'https://edrpou.ubki.ua/ua/00015332',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'cookie': '_csrf=c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D; device-referrer=https://edrpou.ubki.ua/ua/FO12726884; LNG=UA; device-source=https://edrpou.ubki.ua/ua/00015332',
        'dnt': '1',
        'origin': 'https://edrpou.ubki.ua',
        'priority': 'u=1, i',
        'referer': 'https://edrpou.ubki.ua/ua?dr_common_data=00015332&dr_search_type=1',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-csrf-token': 'BEMaSJfpN0uLPi7PFQPBt0o2IY-W41p5D9iHU05qQY93E1Mv_45EDr0MXrl_dojTOUZY_PmBCz5sr7YWDB5y5Q==',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    params = {
    'dr_common_data': dr_common_data,
    'dr_search_type': '1',
    'signature': '2c3f41431f6f1a69b508ae94a025c133cfd4526f',
    'scheme': 'cki',
    'reqid': '',
    }
    
    data = {
    'tp': '1',
    'page': '1',
    'dr_common_data': dr_common_data,
    'dr_regions': '',
    'dr_edrstate': '',
    'dr_kvedcode': '',
    'dr_search_just': 'false',
    'dr_search_type': '1',
}
    json_files = json_directory / f"{dr_common_data}.json"

    if json_files.exists():
        logger.info(f"В наличии {json_files}")
        with open(json_files, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return json_data["clients"][0]["taxNumber"]
    
    response = requests.post('https://edrpou.ubki.ua/srchopenitems', params=params, cookies=cookies, headers=headers, data=data, timeout=30)
    if response.status_code == 200:
        logger.info(f"{response.status_code} для {dr_common_data}")
        json_data = response.json()
        
        
        if json_data.get("clients") and len(json_data["clients"]) > 0:
            try:
                client = json_data["clients"][0]["taxNumber"]
                with open(json_files, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
                return client
            except KeyError:
                logger.error(f"Ошибка: нет ключа 'taxNumber' для {dr_common_data}")
        else:
            logger.error(f"Нет клиентов для {dr_common_data}")
        return None
    else:
        logger.error(f"{response.status_code} для {dr_common_data}")
    return None  # Возвращаем None, если ни один запрос не был успешным

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

def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()
def main():
    urls = read_cities_from_csv(output_csv_file)  # Берём все URL

    # Здесь укажите количество потоков, которое вы хотите использовать
    num_threads = 20  # Например, 5 потоков

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Создаем список задач для get_json
        future_to_url = {executor.submit(get_json, url): url for url in urls}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                taxNumber = future.result()
                if taxNumber is not None:
                    # Вызываем get_html для полученного taxNumber
                    executor.submit(get_html, taxNumber)
                else:
                    logger.error(f"Не удалось получить номер налогоплательщика для {url}.")
            except Exception as e:
                logger.error(f"Произошла ошибка при обработке {url}: {e}")
if __name__ == "__main__":
    main()
    