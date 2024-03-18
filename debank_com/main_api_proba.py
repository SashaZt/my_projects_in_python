import json
import os

import requests

def get_token():
    with open('token.txt', 'r') as file:
        first_value = file.readline().strip()
        return first_value

def main():
    # Определите текущую директорию, где находится скрипт
    current_directory = os.getcwd()

    # Задайте имя папки data_json
    data_json_directory = 'data_json'

    # Создайте полный путь к папке data_json
    data_json_path = os.path.join(current_directory, data_json_directory)

    # Проверьте, существует ли папка data_json, и если нет, создайте ее
    if not os.path.exists(data_json_path):
        os.makedirs(data_json_path)
    filename = f'test.json'
    file_path = os.path.join(data_json_path, filename)
    token = get_token()
    headers = {
        'accept': 'application/json',
        'AccessKey': token,
    }

    params = {
        'id': '0x0aecfad9e8dbf4ef04b3aadd8f24c8c29007447a',
        'chain_id': 'eth',
    }

    response = requests.get('https://pro-openapi.debank.com/v1/user/complex_protocol_list', params=params,
                            headers=headers)
    json_data = response.json()
    # Определите текущую директорию, где находится скрипт

    with open(file_path, 'w',
              encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


if __name__ == '__main__':
    main()
