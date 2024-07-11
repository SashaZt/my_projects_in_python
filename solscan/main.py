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
        "cf_clearance": "aLnB.AOkSeez21DWlIW7KyJV1zUS.RrpaFjqNTfoBM0-1720533465-1.0.1.1-_KvQdOv0B3D0nVafkDuNG.uGNzttGv22IPMu9ihqqLCJT2FCJC8ep3aLETAdA1Kq5AS1am2AN3nQUlxDc2_YxQ",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "origin": "https://solscan.io",
        "priority": "u=1, i",
        "referer": "https://solscan.io/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sol-aut": "TdUBfj4Nn=mxGEiB9dls0fKJuLxsZE5CWl5XJwY5",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    for page in range(1, 13):
        params = {
            "address": "878ki1YAVGTW5HM4qLog9PCGM5dogGdVVkTwAkm83xRe",
            "page": page,
            "page_size": "100",
            "remove_spam": "false",
            "exclude_amount_zero": "false",
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
                        "flow": record.get("flow", ""),
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
    get_jsons()
    parsing_json()
