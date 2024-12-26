import json

import requests

# Конфигурация
BASE_URL = "https://your-site.com"  # Замените на URL вашего сайта
TOKEN_FILE = "token.json"  # Файл для сохранения токена
USERNAME = "apiuser"  # Имя пользователя
PASSWORD = "your-password"  # Пароль пользователя


# Функция для получения токена
def get_token():
    url = f"{BASE_URL}/wp-json/jwt-auth/v1/token"
    payload = {"username": USERNAME, "password": PASSWORD}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            # Сохраняем токен в файл
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f, indent=4)
            print("Токен успешно получен и сохранён в файл.")
            return data["data"].get("token")
        else:
            print("Ошибка:", data.get("message"))
    else:
        print("Ошибка HTTP:", response.status_code, response.text)
    return None


# Функция для создания записи
def create_post(token):
    url = f"{BASE_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": "Новая запись",
        "content": "Это содержимое записи.",
        "status": "publish",
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print("Запись успешно создана:", data.get("link"))
    else:
        print("Ошибка создания записи:", response.status_code, response.text)


# Основной скрипт
if __name__ == "__main__":
    # Получаем токен
    token = None
    try:
        with open(TOKEN_FILE, "r") as f:
            token = json.load(f).get("data", {}).get("token")
            print("Токен загружен из файла.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Файл токена не найден или повреждён, запрашиваем новый токен.")
        token = get_token()

    if token:
        # Создаём запись
        create_post(token)
