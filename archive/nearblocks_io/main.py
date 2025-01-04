import requests
import json
import os

# headers = {
#     "accept": "*/*",
#     "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
#     "content-type": "application/json",
#     "dnt": "1",
#     "if-none-match": 'W/"358f4-He+oIgaJNPM1V/rd56YyxEakroY"',
#     "origin": "https://nearblocks.io",
#     "priority": "u=1, i",
#     "referer": "https://nearblocks.io/",
#     "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-site",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
# }

# params = {
#     "order": "desc",
#     "sort": "onchain_market_cap",
#     "page": "1",
#     "per_page": "50",
# }

# response = requests.get(
#     "https://api3.nearblocks.io/v1/fts", params=params, headers=headers
# )
# json_data = response.json()
# with open(f'token.json', 'w', encoding='utf-8') as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

# Загрузка содержимого JSON файла
with open(f"token.json", "r", encoding="utf-8") as file:
    datas = json.load(file)

json_data = datas["tokens"]
for js in json_data[:1]:
    contract = js["contract"]
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    contract_path = os.path.join(temp_path, contract)

    # Создание директории, если она не существует
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(contract_path, exist_ok=True)
    url = f"https://api3.nearblocks.io/v1/fts/{contract}/holders"
    headers = {
        "accept": "*/*",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "content-type": "application/json",
        "dnt": "1",
        "if-none-match": 'W/"795-5yAJcVcTyC4LcvVwWqFVV5BtSIs"',
        "origin": "https://nearblocks.io",
        "priority": "u=1, i",
        "referer": "https://nearblocks.io/",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    for page in range(1, 201):
        params = {
            "page": page,
            "per_page": "25",
        }

        # response = requests.get(
        #     url,
        #     params=params,
        #     headers=headers,
        # )
        print(params)
        exit()
        filename = os.path.join(contract_path, f"{contract}_0{page}.json")
        json_data = response.json()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
