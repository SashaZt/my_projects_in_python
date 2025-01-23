import requests
import json

def get_token():
    # URL для API
    url = "https://my.easyms.co/api/integration/auth"

    # Данные для запроса
    payload = {
        "password": "Lvbnhyte123",
        "username": "smart@smartkasa.od.ua"
        }

    # Заголовки для запроса
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }

    # Выполнение POST-запроса
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    # Проверка ответа
    if response.status_code == 200:
        # Парсим JSON из ответа
        json_data = response.json()
        # Извлекаем access_token
        access_token = json_data.get("data", {}).get("access_token")
        if access_token:
            print("Access Token:", access_token)
            # Сохраняем access_token в JSON-файл
            with open("access_token.json", "w",encoding="utf-8") as file:
                json.dump({"access_token": access_token}, file, indent=4)
            print("Access token saved to access_token.json")
        else:
            print("Access token not found in the response.")
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")

def get_access_token_from_file(file_path: str) -> str:
    """
    Читает access_token из JSON-файла.
    """
    try:
        with open(file_path, "r",encoding="utf-8") as file:
            data = json.load(file)
            return data.get("access_token")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
    return None
def fetch_users(organization_id: int, token_file: str):
    """
    Выполняет GET-запрос для получения списка пользователей с использованием токена.
    """
    # Извлекаем токен из файла
    access_token = get_access_token_from_file(token_file)
    if not access_token:
        print("Access token not found or invalid.")
        return

    # URL для запроса
    url = f"https://my.easyms.co/api/integration/users?organizationId={organization_id}"

    # Заголовки для запроса
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {access_token}"
    }

    # Выполнение GET-запроса
    response = requests.get(url, headers=headers,timeout=30)

    # Проверка ответа
    if response.status_code == 200:
        print("Users fetched successfully:")
        print(response.json())
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")

# Пример использования функции
if __name__ == "__main__":
    get_token()
    # Укажите ID организации и путь к файлу с токеном
    organization_id = 62
    token_file = "access_token.json"
    fetch_users(organization_id, token_file)