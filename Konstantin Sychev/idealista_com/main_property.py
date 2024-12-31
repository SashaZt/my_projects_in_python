import json

import requests

TOKEN_FILE = "token.json"
DATA_FILE = "properties_60.json"
PROPERTY_API_URL = "https://allproperty.ai/wp-json/wp/v2/properties"
MEDIA_API_URL = "https://allproperty.ai/wp-json/wp/v2/media"

# Загрузка токена
with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
    token_data = json.load(token_file)
    token = token_data.get("token")

# Загрузка данных из файла
with open(DATA_FILE, "r", encoding="utf-8") as data_file:
    properties_data = json.load(data_file)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def upload_image(image_url):
    """Загрузка изображения на WordPress и возврат его ID."""
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        files = {"file": (image_url.split("/")[-1], response.raw, "image/jpeg")}
        media_response = requests.post(MEDIA_API_URL, headers=headers, files=files)
        if media_response.status_code == 201:
            return media_response.json().get("id")
        else:
            print(f"Ошибка загрузки изображения: {media_response.text}")
    return None


def prepare_payload(property_data):
    """Подготовка данных для загрузки объекта недвижимости."""
    featured_image_id = upload_image(property_data.get("imgs_title", [None])[0])

    payload = {
        "title": property_data.get("title", "Untitled Property"),
        "status": "publish",  # Измените на "draft", если нужно
        "content": property_data.get("description", "No description available."),
        "meta": {
            "fave_property_price": property_data.get("price", ""),
            "fave_property_size": property_data.get("area", ""),
            "fave_property_bedrooms": property_data.get("number_of_rooms", ""),
            "fave_property_location": property_data.get("location", ""),
        },
        "categories": property_data.get("category_ids", []),
        "tags": property_data.get("tag_ids", []),
    }

    if featured_image_id:
        payload["featured_media"] = featured_image_id

    return payload


def upload_properties():
    """Загрузка объектов недвижимости на WordPress через REST API."""
    for property_data in properties_data:
        payload = prepare_payload(property_data)
        response = requests.post(PROPERTY_API_URL, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"Property '{property_data['title']}' успешно загружен.")
        else:
            print(f"Ошибка загрузки '{property_data['title']}': {response.text}")


if __name__ == "__main__":
    upload_properties()
