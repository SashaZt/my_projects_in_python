# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import os
import random
from io import BytesIO
import time
import requests
from PIL import Image
from bs4 import BeautifulSoup
import csv
from config import cookies, headers, time_a, time_b


def get_img():
    all_product = []
    now = datetime.now()  # Текущие дата и время
    currentTime = now.strftime("%H_%M")  # Форматирование текущего времени
    currentDate = now.strftime("%d_%m_%Y")  # Форматирование текущей даты
    name_folder = f'{currentTime}_{currentDate}'

    current_directory = os.getcwd()
    image_path = os.path.join(current_directory, name_folder)
    if not os.path.exists(image_path):
        os.makedirs(image_path)

    # Файл CSV будет сохранен в этой же папке
    csv_filename = os.path.join(image_path, f'{name_folder}.csv')

    with open('list.csv', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            parts = line.split(';')
            if len(parts) >= 2:  # Убедитесь, что строка содержит как минимум 2 части
                name, url = parts[:2]  # Извлекаем имя и URL
                try:
                    sleep_time = random.randint(time_a, time_b)
                    response = requests.get(url, cookies=cookies, headers=headers)
                    src = response.text
                    soup = BeautifulSoup(src, 'lxml')
                    scripts_json = soup.find_all('script', type="application/ld+json")
                    for script in scripts_json:
                        data = json.loads(script.text)
                        if 'offers' in data:
                            price = data.get('offers', {}).get('price', 'Not available')
                            all_product.append((name, price))
                        if 'image' in data:
                            url_image = data['image']
                            img_filename = os.path.join(image_path, f"{name}.jpeg")
                            if not os.path.exists(img_filename):
                                response = requests.get(url_image)
                                if response.status_code == 200:
                                    with open(img_filename, 'wb') as img_file:
                                        img_file.write(response.content)
                                    print(f'Saved {img_filename}, sleep for {sleep_time} seconds')
                                    time.sleep(random.randint(time_a, time_b))
                except Exception as e:
                    print(f"An error occurred: {e}")
                    continue

    # После сбора всех данных записываем их в CSV файл
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(all_product)



if __name__ == '__main__':
    get_img()
