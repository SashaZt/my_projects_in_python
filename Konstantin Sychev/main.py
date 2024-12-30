import json

import requests

# Конфигурация
BASE_URL = "https://allproperty.ai"  # Замените на URL вашего сайта
TOKEN_FILE = "token.json"  # Файл для сохранения токена
SCHEME_FILE = "scheme.json"  # Файл для сохранения токена
USERNAME = "apiuser"  # Имя пользователя
PASSWORD = "lHvAkp3u9rR2EFQzlSwvtmAz"  # Пароль пользователя


# Функция для получения токена
def get_token():
    # Данные для аутентификации
    auth_data = {"username": USERNAME, "password": PASSWORD}

    # Заголовки для запроса
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    try:
        # Отправка POST-запроса
        response = requests.post(
            "https://allproperty.ai/wp-json/jwt-auth/v1/token",
            headers=headers,
            json=auth_data,
        )

        # Проверка, что запрос выполнен успешно
        if response.status_code == 200:
            data = response.json()
            token = data["token"]
            # Сохранение токена в файл
            with open(TOKEN_FILE, "w") as token_file:
                json.dump(data["token"], token_file, indent=4)
            return token
        else:
            print(f"Ошибка при получении токена: {response.status_code}")
            print("Ответ сервера:", response.text)

    except requests.RequestException as e:
        print(f"Произошла ошибка при выполнении запроса: {e}")


# Функция для создания записи
def create_post(token):
    url = f"{BASE_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": "Новая запись 2 ",
        "content": "Это содержимое записи.",
        "status": "publish",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print("Запись успешно создана:", data.get("link"))
    else:
        print("Ошибка создания записи:", response.status_code, response.text)


def get_post_schema(token):
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = requests.options(
        "https://allproperty.ai/wp-json/wp/v2/posts", headers=headers
    )
    if response.status_code == 200:
        schema = response.json()
        # Сохранение токена в файл
        with open(SCHEME_FILE, "w") as token_file:
            json.dump(schema, token_file, indent=4)

    else:
        print(f"Ошибка при получении схемы: {response.status_code}")


def creative_new_post(token):
    # Load the extracted data and WordPress schema
    extracted_data_path = "extracted_profile_data.json"
    scheme_path = "scheme.json"

    with open(extracted_data_path, "r", encoding="utf-8") as file:
        extracted_data = json.load(file)

    with open(scheme_path, "r", encoding="utf-8") as file:
        wp_schema = json.load(file)

    # WordPress REST API settings
    wordpress_url = "https://allproperty.ai/wp-json/wp/v2/posts"

    # Prepare the headers with the token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    # Helper function to format and upload data
    def create_wordpress_post(data):
        # Extract fields from the data
        post_title = data.get("title", "Untitled Post")
        content = f"<p>{data.get('description', '')}</p>"

        # Add image gallery if available
        photos = data.get("photos", [])
        if photos:
            content += "<ul>"
            for photo in photos:
                for description, url in photo.items():
                    content += f'<li><img src="{url}" alt="{description}" /></li>'
            content += "</ul>"

        # Add details if available
        details = data.get("details", [])
        if details:
            for detail in details:
                title = detail.get("title", "Details")
                items = detail.get("items", [])
                content += f"<h2>{title}</h2><ul>"
                for item in items:
                    content += f"<li>{item}</li>"
                content += "</ul>"

        # Prepare the payload for WordPress
        payload = {
            "title": post_title,
            "content": content,
            "status": "publish",  # Change to "draft" if you want to review before publishing
        }

        # Make the POST request to WordPress
        response = requests.post(wordpress_url, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"Post '{post_title}' created successfully.")
        else:
            print(f"Failed to create post '{post_title}'. Error: {response.text}")

    # Process each item in the extracted data
    for item in extracted_data:
        create_wordpress_post(item)


# Основной скрипт
if __name__ == "__main__":
    # Получаем токен
    token = get_token()
    # create_post(token)
    creative_new_post(token)
    # token = None
    # try:
    #     with open(TOKEN_FILE, "r") as f:
    #         token = json.load(f).get("data", {}).get("token")
    #         print("Токен загружен из файла.")
    #         # get_post_schema(token)
    #         # creative_new_post(token)

    # except (FileNotFoundError, json.JSONDecodeError):
    #     print("Файл токена не найден или повреждён, запрашиваем новый токен.")

    # if token:
    #     # Создаём запись
    #     get_post_schema(token)
    #     # create_post(token)
