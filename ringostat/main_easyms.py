import json

import requests


def get_token():
    url = "https://my.easyms.co/api/integration/auth"

    payload = json.dumps(
        {"password": "Lvbnhyte123", "username": "smart@smartkasa.od.ua"}
    )
    headers = {"accept": "*/*", "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=payload, timeout=30)

    if response.status_code == 200:
        try:
            json_data = response.json()  # Вызов json() как метода
            access_token = json_data.get("data", {}).get("access_token")

            if access_token:
                # Записываем токен в файл access_token.json
                with open("access_token.json", "w", encoding="utf-8") as file:
                    json.dump({"access_token": access_token}, file, indent=4)
                print("Access token успешно записан в access_token.json")
            else:
                print("Access token не найден в ответе")
        except ValueError:
            print("Ошибка при декодировании JSON данных")
    else:
        print(f"Ошибка запроса: {response.status_code}")


if __name__ == "__main__":
    get_token()
