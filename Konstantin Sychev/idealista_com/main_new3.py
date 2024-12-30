import json

import requests

TOKEN_FILE = "token.json"
DATA_FILE = "extracted_profile_data.json"
PROPERTY_API_URL = "https://allproperty.ai/wp-json/wp/v2/properties"

# Загрузка токена
with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
    token_data = json.load(token_file)
    token = token_data.get("token")

# Загрузка данных из файла
with open(DATA_FILE, "r", encoding="utf-8") as data_file:
    extracted_data = json.load(data_file)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def prepare_payload(property_data):
    """
    Преобразование данных в формат WordPress API для объектов недвижимости.
    """
    payload = {
        "title": property_data.get("title", "Untitled Property"),
        "status": "publish",  # Установить "draft", если публикация не нужна сразу
        "meta": {
            "fave_property_size": property_data.get("area", ""),
            "fave_property_bedrooms": property_data.get("number_of_rooms", ""),
            "fave_property_price": property_data.get("price", "").replace("€", ""),
            "fave_property_address": property_data.get("location", ""),
        },
        "content": generate_property_content(property_data),
        "property_type": property_data.get("category_ids", []),
        "tags": property_data.get("tag_ids", []),
    }
    return payload


def generate_property_content(property_data):
    """
    Формирование содержимого для записи объекта недвижимости.
    """
    description = (
        f"<p>{property_data.get('description', 'No description provided.')}</p>"
    )

    # Добавление галереи изображений
    photos = property_data.get("photos", [])
    if photos:
        description += '<div class="property-gallery">'
        for photo in photos:
            for desc, url in photo.items():
                description += f'<img src="{url}" alt="{desc}" />'
        description += "</div>"

    # Добавление деталей
    details = property_data.get("details", [])
    for section in details:
        title = section.get("title", "Details")
        items = section.get("items", [])
        description += f"<h3>{title}</h3><ul>"
        for item in items:
            description += f"<li>{item}</li>"
        description += "</ul>"

    return description


def upload_properties():
    """
    Загрузка объектов недвижимости в WordPress через REST API.
    """
    for property_data in extracted_data:
        payload = prepare_payload(property_data)
        response = requests.post(PROPERTY_API_URL, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"Property '{property_data['title']}' успешно загружен.")
        else:
            print(f"Ошибка загрузки '{property_data['title']}': {response.text}")


if __name__ == "__main__":
    upload_properties()
