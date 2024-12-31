import json

import requests

# Загрузка токена
TOKEN_FILE = "token.json"
with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
    token_data = json.load(token_file)
    token = token_data.get("token")

# Заголовки
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
# api_url = "https://allproperty.ai/wp-json/wp/v2/properties"

# # Проверка, что изображение существует
# media_id = "17548"
# media_url = f"https://allproperty.ai/wp-json/wp/v2/media/{media_id}"
# media_response = requests.get(media_url, headers=headers)

# if media_response.status_code == 200:
#     print(
#         f"Изображение с ID {media_id} найдено. Отправляем запрос на создание объекта недвижимости."
#     )
#     # Формирование данных объекта недвижимости
#     property_data = {
#         "status": "publish",
#         "type": "property",
#         "title": "Flat / apartment for sale in calle de Tòquio",
#         "content": "<p>Описание объекта недвижимости...</p>",
#         "excerpt": "<p>Краткое описание...</p>",
#         "meta": {"fave_property_images": [{"id": media_id}]},
#     }

#     # Отправка запроса
#     response = requests.post(api_url, headers=headers, json=property_data)

#     # Обработка результата
#     if response.status_code == 201:
#         print("Объект недвижимости успешно создан!")
#         print(response.json())
#     else:
#         print(
#             f"Ошибка создания объекта недвижимости. Код статуса: {response.status_code}"
#         )
#         print(response.text)
# else:
#     print(
#         f"Изображение с ID {media_id} не найдено. Проверьте ID или загрузите изображение."
#     )
#     print(media_response.text)

# ID объекта недвижимости
property_id = 17570

# Данные для обновления
update_data = {
    "meta_input": {
        "fave_property_images": [
            "16107",
            "16106",
            "16105",
            "16108",
            "16109",
            "16110",
            "16111",
            "16124",
            "16112",
        ]
    }
}

# URL для обновления объекта недвижимости
update_url = f"https://allproperty.ai/wp-json/wp/v2/properties/{property_id}"

# Отправка запроса на обновление
response = requests.post(update_url, headers=headers, json=update_data)

# Проверка ответа
if response.status_code == 200:
    print("Поле `fave_property_images` успешно добавлено в `property_meta`.")
    print(response.json())
else:
    print(f"Ошибка при обновлении объекта. Код статуса: {response.status_code}")
    print(response.text)
