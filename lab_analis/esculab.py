import csv
import json

import requests


def get_esculab():
    headers = {
        'authority': 'esculab.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/json;charset=UTF-8',
        'dnt': '1',
        'origin': 'https://esculab.com',
        'pragma': 'no-cache',
        'referer': 'https://esculab.com/analysis',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    json_data = {
        'idreg': '3201',
    }

    response = requests.post('https://esculab.com/api/customers/getPriceByRegionLocal/ua', headers=headers,
                             json=json_data)
    json_data = response.json()
    with open(f'esculab_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def parsing_esculab():
    file_name = 'esculab_data.json'
    with open(file_name, encoding='utf-8') as f:
        data = json.load(f)
    heandler = ['code', 'name', 'nameRu', 'duration_day', 'price']
    with open('esculab.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in data:
            for child in item['childAnalyzes']:
                code = child['code']
                name = child['name']
                nameRu = child['nameRu']
                price = child['price']
                duration_day = child['duration_day']
                values = [code, name, nameRu, duration_day, price]
                writer.writerow(values)


if __name__ == '__main__':
    get_esculab()
    parsing_esculab()
