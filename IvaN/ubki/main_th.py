import requests
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import time
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

cookies = {
    'LNG': 'UA',
    '_csrf': 'c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D',
    'device-referrer': 'https://edrpou.ubki.ua/ua/FO12726884',
    'device-source': 'https://edrpou.ubki.ua/ua/37798175',
    }

headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'cache-control': 'no-cache',
        'dnt': '1',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

def download_html(url):
    
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании {url}: {e}")
        return None

    

def download_and_save(url):
    
    file_path = html_directory / f"{url}.html"
    if file_path.exists():
        return None
    url = f"https://edrpou.ubki.ua/ua/{url}"
    html_content = download_html(url)
    if html_content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        time.sleep(5)

def main_html():
    # Чтение файла matched_urls.csv
    urls_df = pd.read_csv("urls.csv")
    urls = urls_df["url"].tolist()

    

    # Многопоточное скачивание HTML-файлов
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_and_save, url) for url in urls]
        for future in as_completed(futures):
            future.result()
if __name__ == '__main__':
    main_html()
    