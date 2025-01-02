import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

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
            token_jwt = {"token": data["token"]}
            # Сохранение токена в файл
            with open(TOKEN_FILE, "w") as token_file:
                json.dump(token_jwt, token_file, indent=4)
        else:
            print(f"Ошибка при получении токена: {response.status_code}")
            print("Ответ сервера:", response.text)

    except requests.RequestException as e:
        print(f"Произошла ошибка при выполнении запроса: {e}")


def make_get_request(url, token):
    """
    Универсальная функция для GET-запросов.

    :param url: URL для GET-запроса.
    :param token: строка, токен авторизации.
    :return: результат запроса в виде JSON или None в случае ошибки.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка GET-запроса: {response.status_code} - {response.text}")
        return None


def make_post_request(url, token, payload):
    """
    Универсальная функция для POST-запросов.

    :param url: URL для POST-запроса.
    :param token: строка, токен авторизации.
    :param payload: словарь с данными для отправки.
    :return: результат запроса в виде JSON или None в случае ошибки.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30))
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Ошибка POST-запроса: {response.status_code} - {response.text}")
        return None


def get_categories(token):
    categories_url = "https://allproperty.ai/wp-json/wp/v2/categories"
    return make_get_request(categories_url, token)


def get_tags(token):
    tags_url = "https://allproperty.ai/wp-json/wp/v2/tags"
    return make_get_request(tags_url, token)


def generate_post_content(item):
    content = f"<h1>{item.get('title', 'Untitled Post')}</h1>"
    content += f"<p>{item.get('description', '')}</p>"

    # Галерея изображений
    photos = item.get("photos", [])
    if photos:
        content += "<div class='gallery'>"
        for photo in photos:
            for description, url in photo.items():
                content += f'<figure><img src="{url}" alt="{description}"><figcaption>{description}</figcaption></figure>'
        content += "</div>"

    # Детали
    details = item.get("details", [])
    for detail in details:
        title = detail.get("title", "Details")
        items = detail.get("items", [])
        content += f"<h2>{title}</h2><ul>"
        for item in items:
            content += f"<li>{item}</li>"
        content += "</ul>"

    return content


def save_categories_and_tags(token):
    # URL API
    categories_url = "https://allproperty.ai/wp-json/wp/v2/categories"
    tags_url = "https://allproperty.ai/wp-json/wp/v2/tags"

    # Получение категорий и тегов
    categories = make_get_request(categories_url, token)
    tags = make_get_request(tags_url, token)

    # Сохранение категорий в файл
    categories_data = {item["id"]: item["name"] for item in categories}
    with open("categories.json", "w", encoding="utf-8") as file:
        json.dump(categories_data, file, ensure_ascii=False, indent=4)

    # Сохранение тегов в файл
    tags_data = {item["id"]: item["name"] for item in tags}
    with open("tags.json", "w", encoding="utf-8") as file:
        json.dump(tags_data, file, ensure_ascii=False, indent=4)

    print("Категории и теги успешно сохранены.")



# Обновление категории и тегов
def get_tag_category(token):
    categories_url = "https://allproperty.ai/wp-json/wp/v2/categories"
    tags_url = "https://allproperty.ai/wp-json/wp/v2/tags"

    category_ids = get_categories(token)
    # Получение тегов
    tag_ids = get_tags(token)
    # Сохранение категорий в файл
    categories_data = {item["id"]: item["name"] for item in category_ids}
    with open("categories.json", "w", encoding="utf-8") as file:
        json.dump(categories_data, file, ensure_ascii=False, indent=4)

    # Сохранение тегов в файл
    tags_data = {item["id"]: item["name"] for item in tag_ids}
    with open("tags.json", "w", encoding="utf-8") as file:
        json.dump(tags_data, file, ensure_ascii=False, indent=4)
    exit()


if __name__ == "__main__":
    # get_token()
    load_posts_to_wordpress()
