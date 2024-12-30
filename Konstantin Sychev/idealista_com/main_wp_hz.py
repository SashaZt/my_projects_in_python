import json

import requests

TOKEN_FILE = "token.json"  # Файл для сохранения токена


def generate_post_content(data):
    """
    Формирует содержимое поста для WordPress из данных.
    """
    content = f"<p>{data.get('description', '')}</p>"

    # Добавляем галерею изображений
    photos = data.get("photos", [])
    if photos:
        content += "<ul>"
        for photo in photos:
            for description, url in photo.items():
                content += f'<li><img src="{url}" alt="{description}" /></li>'
        content += "</ul>"

    # Добавляем детали
    details = data.get("details", [])
    if details:
        for detail in details:
            title = detail.get("title", "Details")
            items = detail.get("items", [])
            if items:
                content += f"<h2>{title}</h2><ul>"
                for item in items:
                    content += f"<li>{item}</li>"
                content += "</ul>"

    return content


def import_to_wordpress(token, data):
    """
    Загружает данные в WordPress через REST API.
    """
    wordpress_url = "https://allproperty.ai/wp-json/wp/v2/posts"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    for item in data:
        payload = {
            "title": item.get("title", "Untitled Post"),
            "content": generate_post_content(item),
            "status": "publish",  # Установите "draft", если хотите предварительно проверить посты
            "meta": {
                "location": item.get("location", ""),
                "price": item.get("price", ""),
                "area": item.get("area", ""),
                "number_of_rooms": item.get("number_of_rooms", ""),
            },
            "categories": item.get("category_ids", []),
            "tags": item.get("tag_ids", []),
        }

        response = requests.post(wordpress_url, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"Post '{item['title']}' успешно создан.")
        else:
            print(f"Ошибка создания поста '{item['title']}': {response.text}")


if __name__ == "__main__":
    with open(TOKEN_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    token = data["token"]

    with open("extracted_profile_data.json", "r", encoding="utf-8") as file:
        extracted_data = json.load(file)

    import_to_wordpress(token, extracted_data)
