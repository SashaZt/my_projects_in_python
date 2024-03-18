import json
import os
import requests
import glob
import time
from config import cookies, headers
from proxi import proxies
import random
from datetime import datetime




current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")

def get_param_hotels():

    folder = os.path.join(all_hotels, "*.json")
    files_json = glob.glob(folder)
    # Инициализируем список для хранения собранных данных из всех файлов
    all_data = []

    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            data_json = json.load(f)

        for j in data_json:
            collected_data = {}
            bazowe_informacje = j.get('BazoweInformacje', {})
            zdjecia = j.get('Zdjecia', [])
            ocena = j.get('Ocena', {})
            przystanki = j.get('Przystanki', [])
            wyzywienia = j.get('Wyzywienia', [])
            
            # Собираем информацию из BazoweInformacje
            for key, value in bazowe_informacje.items():
                collected_data[key] = value
            
            # Добавляем фотографии
            collected_data['Zdjecia'] = zdjecia
            
            # Добавляем оценку
            collected_data.update(ocena)
            
            # Добавляем пристанки и IATA коды
            iata_codes = [przystanek.get('Iata') for przystanek in przystanki]
            collected_data['Przystanki'] = przystanki
            collected_data['IataCodes'] = iata_codes
            
            # Добавляем информацию о питании
            collected_data['Wyzywienia'] = [{'Nazwa': wyz['Nazwa'], 'URL': wyz['URL']} for wyz in wyzywienia]
            
            # Добавляем собранные данные в список всех данных
            all_data.append(collected_data)

    # Записываем все собранные данные в один файл
    output_file = "static_parameters_from_all_hotels.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    get_param_hotels()