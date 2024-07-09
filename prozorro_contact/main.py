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


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


def get_jsons():
    cookies = {
        "_ga": "GA1.3.176997764.1720510487",
        "_gat": "1",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "uk",
        "content-type": "application/x-www-form-urlencoded",
        "dnt": "1",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    for page in range(1, 117):
        params = {
            "date[tender][start]": "2023-01-01",
            "cpv[0]": "44810000-1",
            "page": page,
        }
        proxies = load_proxies()
        proxy_gen = proxy_generator(proxies)
        proxy_server = next(proxy_gen)
        proxy_auth = (
            f"{proxy_server[2]}:{proxy_server[3]}@{proxy_server[0]}:{proxy_server[1]}"
        )
        response = requests.post(
            "https://prozorro.gov.ua/api/search/tenders",
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
                for record in data.get("data", []):
                    procuring_entity = record.get("procuringEntity", {})
                    identifier = procuring_entity.get("identifier", {})
                    address = procuring_entity.get("address", {})
                    contact_point = procuring_entity.get("contactPoint", {})

                    name = identifier.get("legalName", "")
                    name_id = identifier.get("id", "")
                    streetAddress = address.get("streetAddress", "")
                    postalCode = address.get("postalCode", "")
                    locality = address.get("locality", "")
                    countryName = address.get("countryName", "")
                    region = address.get("region", "")
                    name_contactPoint = contact_point.get("name", "")
                    telephone_contactPoint = contact_point.get("telephone", "")
                    email_contactPoint = contact_point.get("email", "")

                    datas = {
                        "Найменування": name,
                        "Код ЄДРПОУ": name_id,
                        "Місцезнаходження": f"{streetAddress}, {postalCode}, {locality}, {region}, {countryName}",
                        # "postalCode": postalCode,
                        # "locality": locality,
                        # "countryName": countryName,
                        # "region": region,
                        "name_contactPoint": name_contactPoint,
                        "telephone_contactPoint": telephone_contactPoint,
                        "email_contactPoint": email_contactPoint,
                    }
                    all_data.append(datas)

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_data)

    # Запись DataFrame в Excel
    output_file = "output.xlsx"
    df.to_excel(output_file, index=False)


if __name__ == "__main__":
    # get_jsons()
    parsing_json()
