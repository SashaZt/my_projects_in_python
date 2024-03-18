import csv
import requests
import os
from pathlib import Path
from multiprocessing import Pool

# Функция для скачивания и сохранения данных по URL
def download_url(url, index):
    headers = {
        # Вставьте ваш заголовок сюда
    }
    filename = Path('c:/DATA/exist/product/') / f'data_{index}.html'
    if not os.path.exists(filename):
        try:
            # response = requests.get(url, headers=headers)
            response = requests.get(f'http://api.scraperapi.com?api_key=6e0e2776344e126bc1e85c60d58c42bc&url={url}')
            src = response.text
            with open(filename, "w", encoding='utf-8') as file:
                file.write(src)
        except Exception as e:
            print(f"Ошибка при скачивании URL {url}: {str(e)}")

# Функция для обработки одного процесса
def process_chunk(chunk, start_index):
    for index, url in enumerate(chunk, start=start_index):
        download_url(url, index)

def get_requests():
    if __name__ == "__main__":
        # Загрузите список URL из файла csv
        csv_file = Path('c:/scrap_tutorial-master/exist/') / 'url_amortyzatory.csv'
        with open(csv_file, 'r') as file:
            url_list = [line.strip() for line in file]

        # Разделите список URL на части для каждого процесса
        num_processes = 5  # Укажите количество желаемых процессов
        chunk_size = len(url_list) // num_processes
        chunks = [url_list[i:i + chunk_size] for i in range(0, len(url_list), chunk_size)]

        # Создайте пул процессов и выполните обработку URL
        with Pool(processes=num_processes) as pool:
            pool.starmap(process_chunk, [(chunk, i * chunk_size) for i, chunk in enumerate(chunks)])

if __name__ == "__main__":
    get_requests()
