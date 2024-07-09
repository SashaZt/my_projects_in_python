import requests
import json
import time
import os
import pandas as pd
import glob


# Создание временных папок
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
json_path = os.path.join(temp_path, "json")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)


def get_jsons():

    cookies = {
        "cf_clearance": "b8n0m3wfRg8.Grp8P8sFMNluKkMDUuh3pjCdzV_gL9Y-1720417336-1.0.1.1-FR8708pseb97.uQG.E.Lzs4y3BmzGOOA4A4qSye9DEQ4tk0KuMThiJO.ft3XFGGp6we0rMSjryo_g8x3g5GQMw",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        # 'cookie': 'cf_clearance=b8n0m3wfRg8.Grp8P8sFMNluKkMDUuh3pjCdzV_gL9Y-1720417336-1.0.1.1-FR8708pseb97.uQG.E.Lzs4y3BmzGOOA4A4qSye9DEQ4tk0KuMThiJO.ft3XFGGp6we0rMSjryo_g8x3g5GQMw',
        "dnt": "1",
        "origin": "https://solscan.io",
        "priority": "u=1, i",
        "referer": "https://solscan.io/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sol-aut": "B9dls0fKBm=1x0mByg7gjF9RY2NFKh6SA=miZ=R7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    for page in range(1, 101):
        params = {
            "address": "urJq11QoCV4Zk4ivxaKXeJAfvHBHqDhYfJMm4yZLUUS",
            "page": page,
            "page_size": "100",
            "remove_spam": "false",
            "exclude_amount_zero": "false",
            "token": "So11111111111111111111111111111111111111111",
        }

        response = requests.get(
            "https://api-v2.solscan.io/v2/account/transfer",
            params=params,
            cookies=cookies,
            headers=headers,
        )
        json_data = response.json()
        filename = os.path.join(json_path, f"0{page}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        time.sleep(5)


def parsing_json():
    # Получение списка всех JSON файлов в директории
    folder = os.path.join(json_path, "*.json")
    files_json = glob.glob(folder)

    # Список для хранения всех данных
    all_data = []

    # Чтение данных из каждого JSON файла и добавление их в список
    for item in files_json:
        with open(item, encoding="utf-8") as f:
            data = json.load(f)
            if "data" in data:
                for record in data["data"]:
                    # Извлечение нужных полей
                    filtered_record = {
                        "trans_id": record.get("trans_id", ""),
                        "from_address": record.get("from_address", ""),
                        "token_address": record.get("token_address", ""),
                        "token_decimals": record.get("token_decimals", ""),
                        "amount": str(
                            record.get("amount", "")
                        ),  # Преобразование amount в строку
                    }
                    all_data.append(filtered_record)

    # Преобразование списка данных в DataFrame
    df = pd.DataFrame(all_data)

    # Преобразование колонки 'amount' в строковый формат
    df["amount"] = df["amount"].astype(str)

    # Запись DataFrame в Excel
    output_path = os.path.join(json_path, "output.xlsx")
    df.to_excel(output_path, index=False)


if __name__ == "__main__":
    # get_jsons()
    parsing_json()
