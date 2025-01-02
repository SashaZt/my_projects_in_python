import json
import os
import re
import shutil
from math import log
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

current_directory = Path.cwd()

data_directory = current_directory / "data"
html_directory = current_directory / "html"
photo_directory = current_directory / "photo"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
photo_directory.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = "token.json"  # Файл для сохранения токена
output_file = Path("extracted_profile_data.json")


def extract_photo(soup):
    all_data = []
    # Ищем теги <script> с данными
    script_tags = soup.find_all("script")

    for script in script_tags:
        if "fullScreenGalleryPics" in script.text:
            # Извлекаем содержимое с помощью регулярного выражения
            match = re.search(r"fullScreenGalleryPics\s*:\s*(\[[^\]]*\])", script.text)
            if match:
                gallery_data = match.group(1)
                # logger.info(f"Найденные данные match:\n{gallery_data}")
                try:
                    # Исправляем кавычки
                    gallery_data = gallery_data.replace("'", '"')

                    # Исправляем кавычки перед "https"
                    gallery_data = re.sub(r'""https://', r'"https://', gallery_data)

                    # Добавляем кавычки к ключам
                    gallery_data = re.sub(r"([{,])\s*(\w+):", r'\1 "\2":', gallery_data)

                    # Преобразуем в JSON
                    full_screen_gallery_pics = json.loads(gallery_data)
                    # logger.info(f"Данные из файла {html_file.name}:")

                    # Логируем ключевую информацию
                    for idx, pic in enumerate(full_screen_gallery_pics, start=1):
                        description = pic.get("hoverText", "Нет данных")
                        url = pic.get("imageDataService", "Нет данных")
                        dimensions = (
                            f"{pic.get('width', 'нет')}x{pic.get('height', 'нет')}"
                        )
                        tag = pic.get("tag", "Нет данных")
                        photos = {f"{description}_{idx}": url}
                        all_data.append(photos)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка {e} декодирования JSON в файле")

    return all_data


def extract_details(soup):
    details_list = []

    # Находим все секции с классом details-property-feature-
    feature_sections = soup.find_all(
        "div", class_=lambda x: x and x.startswith("details-property-feature-")
    )

    for section in feature_sections:
        section_data = {}

        # Извлекаем заголовок секции
        header = section.find("h2", class_="details-property-h2")
        if header:
            section_title = header.text.strip()
            section_data["title"] = section_title

        # Извлекаем элементы списка <ul>
        features = section.find_all("ul")
        section_items = []
        for feature in features:
            items = feature.find_all("li")
            for item in items:
                # Обрабатываем текст элементов списка
                text = item.get_text(separator=" ", strip=True)
                section_items.append(text)

        section_data["items"] = section_items
        details_list.append(section_data)

    return details_list


def extract_bathrooms_year(details):
    bathrooms_count = None
    year_built = None

    for detail_group in details:
        for item in detail_group.get("items", []):
            # Проверяем на наличие "bathroom" или "bathrooms"
            bathroom_match = re.search(r"(\d+)\s+bathrooms?", item, re.IGNORECASE)
            if bathroom_match:
                bathrooms_count = int(bathroom_match.group(1))

            # Проверяем на наличие "Built in <year>"
            year_match = re.search(r"Built in (\d{4})", item, re.IGNORECASE)
            if year_match:
                year_built = int(year_match.group(1))

    return bathrooms_count, year_built


def parsing_html():

    extracted_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
        soup = BeautifulSoup(content, "lxml")
        title = None
        location = None
        price = None
        description = None
        area = None
        number_of_rooms = None
        imgs_title = None
        # Извлечение данных
        title = soup.find("span", class_="main-info__title-main")
        location = soup.find("span", class_="main-info__title-minor")
        price = soup.find("span", class_="info-data-price")
        description = soup.find(
            "div", class_="adCommentsLanguage expandable is-expandable"
        )

        title = title.get_text(strip=True) if title else None
        location = location.get_text(strip=True) if location else None
        price = price.get_text(strip=True) if price else None
        description = description.get_text(strip=True) if description else None

        list_items = soup.find_all("li", {"class": "header-map-list"})

        values = [item.get_text(strip=True) for item in list_items]

        location = ", ".join(values)

        # Извлечение характеристик (площадь, комнаты)
        info_features = soup.find("div", class_="info-features")
        if info_features:
            spans = info_features.find_all("span")
            if len(spans) >= 2:
                area = spans[0].get_text(strip=True)
                number_of_rooms = spans[1].get_text(strip=True).split()[0]

        imgs_title_raw = soup.find(
            "img", attrs={"class", "image-focus show image-focus show"}
        )
        if imgs_title_raw:
            imgs_title = imgs_title_raw.get("src")

        photos = extract_photo(soup)
        details = extract_details(soup)
        bathrooms, year = extract_bathrooms_year(details)

        all_data = {
            "status": "publish",
            "type": "property",
            "title": {"rendered": title},
            "imgs_title": [imgs_title],
            "photos": photos,
            # "price": price,
            "content": description,
            "location": location,
            # "area": area,
            # "number_of_rooms": number_of_rooms,
            "details": details,
            "property_meta": {
                "fave_property_images": [],
                "fave_property_bedrooms": number_of_rooms,
                "fave_property_price": price,
                "fave_property_size": area,
                "fave_property_bathrooms": bathrooms,
                "fave_property_year": year,
            },
        }
        extracted_data.append(all_data)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)


"--------------------------------------------"
# Конфигурация
BASE_URL = "https://allproperty.ai"  # Замените на URL вашего сайта
TOKEN_FILE = "token.json"  # Файл для сохранения токена
SCHEME_FILE = "scheme.json"  # Файл для сохранения токена
USERNAME = "apiuser"  # Имя пользователя
PASSWORD = "mkXh8jHOnDmiYB8qSyGKO77H"  # Пароль пользователя


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
            timeout=30,
        )

        # Проверка, что запрос выполнен успешно
        if response.status_code == 200:
            data = response.json()
            token_jwt = {"token": data["token"]}
            # Сохранение токена в файл
            with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
                json.dump(token_jwt, token_file, indent=4)

        else:
            print(f"Ошибка при получении токена: {response.status_code}")
            print("Ответ сервера:", response.text)

    except requests.RequestException as e:
        print(f"Произошла ошибка при выполнении запроса: {e}")


def load_headers():
    # Загрузка токена
    with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
        token_data = json.load(token_file)
        token = token_data.get("token")

    # Заголовки для запроса
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    return headers


# # Функция для создания записи
# def create_post(token):
#     url = f"{BASE_URL}/wp-json/wp/v2/posts"
#     payload = {
#         "title": "Новая запись 2 ",
#         "content": "Это содержимое записи.",
#         "status": "publish",
#     }
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     }

#     response = requests.post(url, json=payload, headers=headers)

#     if response.status_code == 201:
#         data = response.json()
#         print("Запись успешно создана:", data.get("link"))
#     else:
#         print("Ошибка создания записи:", response.status_code, response.text)


# def get_post_schema(token):
#     headers = {
#         "Content-Type": "application/json",
#         # "Authorization": f"Bearer {token}",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     }
#     response = requests.options(
#         "https://allproperty.ai/wp-json/wp/v2/posts", headers=headers
#     )
#     if response.status_code == 200:
#         schema = response.json()
#         # Сохранение токена в файл
#         with open(SCHEME_FILE, "w") as token_file:
#             json.dump(schema, token_file, indent=4)

#     else:
#         print(f"Ошибка при получении схемы: {response.status_code}")


# def creative_new_post(token):
#     # Load the extracted data and WordPress schema
#     extracted_data_path = "extracted_profile_data.json"
#     scheme_path = "scheme.json"

#     with open(extracted_data_path, "r", encoding="utf-8") as file:
#         extracted_data = json.load(file)

#     # WordPress REST API settings
#     wordpress_url = "https://allproperty.ai/wp-json/wp/v2/posts"

#     # Prepare the headers with the token
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     }

#     # Helper function to format and upload data
#     def create_wordpress_post(data):
#         # Extract fields from the data
#         post_title = data.get("title", "Untitled Post")
#         content = f"<p>{data.get('description', '')}</p>"

#         # Add image gallery if available
#         photos = data.get("photos", [])
#         gallery_content = ""
#         if photos:
#             gallery_content = '[gallery ids="'
#             for photo in photos:
#                 for _, url in photo.items():  # Assuming each photo dict has one URL
#                     # Here, you would ideally upload the image and get its ID
#                     # For this example, we'll simulate this by using a placeholder ID
#                     # You need to implement actual image uploading to Media Library
#                     gallery_content += "1,"  # Replace with real ID after uploading
#             gallery_content = gallery_content.rstrip(",") + '"]'
#             content += gallery_content

#         # Add details if available
#         details = data.get("details", [])
#         if details:
#             for detail in details:
#                 title = detail.get("title", "Details")
#                 items = detail.get("items", [])
#                 content += f"<h2>{title}</h2><ul>"
#                 for item in items:
#                     content += f"<li>{item}</li>"
#                 content += "</ul>"

#         # Prepare the payload for WordPress
#         payload = {
#             "title": post_title,
#             "content": content,
#             "status": "publish",  # Change to "draft" if you want to review before publishing
#             "format": "gallery",  # Setting the format to gallery
#         }

#         # Make the POST request to WordPress
#         response = requests.post(wordpress_url, json=payload, headers=headers)

#         if response.status_code == 201:
#             print(f"Post '{post_title}' created successfully.")
#         else:
#             print(f"Failed to create post '{post_title}'. Error: {response.text}")

#     # Process each item in the extracted data
#     for item in extracted_data:
#         create_wordpress_post(item)


# def generate_post_content(item):
#     content = f"<h1>{item.get('title', 'Untitled Post')}</h1>"
#     content += f"<p>{item.get('description', '')}</p>"

#     # Галерея изображений
#     photos = item.get("photos", [])
#     if photos:
#         content += "<div class='gallery'>"
#         for photo in photos:
#             for description, url in photo.items():
#                 content += f'<figure><img src="{url}" alt="{description}"><figcaption>{description}</figcaption></figure>'
#         content += "</div>"

#     # Детали
#     details = item.get("details", [])
#     for detail in details:
#         title = detail.get("title", "Details")
#         items = detail.get("items", [])
#         content += f"<h2>{title}</h2><ul>"
#         for item in items:
#             content += f"<li>{item}</li>"
#         content += "</ul>"

#     return content


# def load_posts_to_wordpress(token):
#     data_path = "extracted_profile_data.json"
#     scheme_path = "scheme.json"
#     # Загрузка данных
#     with open(data_path, "r", encoding="utf-8") as file:
#         extracted_data = json.load(file)
#     with open(scheme_path, "r", encoding="utf-8") as file:
#         wp_schema = json.load(file)

#     # URL WordPress REST API
#     wordpress_url = "https://allproperty.ai/wp-json/wp/v2/posts"

#     # Заголовки авторизации
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     }

#     for item in extracted_data:
#         # Сопоставление данных со схемой
#         payload = {
#             "title": item.get("title", "Untitled Post"),  # Заголовок
#             "content": generate_post_content(
#                 item
#             ),  # Описание и галерея, формируемая с помощью отдельной функции
#             "status": "publish",  # Статус публикации
#             "meta": {
#                 "location": item.get("location", ""),  # Местоположение
#                 "price": item.get("price", ""),  # Цена
#                 "area": item.get("area", ""),  # Площадь
#                 "number_of_rooms": item.get("number_of_rooms", ""),  # Количество комнат
#             },
#             # Если WordPress поддерживает специальные категории или метки, можно добавить их
#             "categories": ["Real Estate", "Barcelona"],  # Пример категорий
#             "tags": ["Flat", "Apartment", "Sale"],  # Пример тегов
#             # Медиа-файлы
#             "photos": [
#                 {"description": list(photo.keys())[0], "url": list(photo.values())[0]}
#                 for photo in item.get("photos", [])
#             ],
#             # Дополнительные детали, если их нужно указать в мета-полях
#             "details": [
#                 {
#                     "title": detail.get("title", "Details"),
#                     "items": detail.get("items", []),
#                 }
#                 for detail in item.get("details", [])
#             ],
#         }

#         # Отправка данных на WordPress
#         response = requests.post(wordpress_url, headers=headers, json=payload)

#         if response.status_code == 201:
#             print(f"Post '{item['title']}' успешно создан.")
#         else:
#             print(f"Ошибка создания поста '{item['title']}': {response.text}")


def get_categories(token):
    """
    Получает категории из WordPress REST API.

    :param token: строка, токен авторизации.
    :return: словарь {название категории: ID категории}.
    """
    categories_url = "https://allproperty.ai/wp-json/wp/v2/categories"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(categories_url, headers=headers, timeout=30)

    if response.status_code == 200:
        categories = response.json()
        return {item["name"]: item["id"] for item in categories}
    else:
        print(f"Ошибка получения категорий: {response.status_code} - {response.text}")
        return {}


def get_tags(token):
    """
    Получает теги из WordPress REST API.

    :param token: строка, токен авторизации.
    :return: словарь {название тега: ID тега}.
    """
    tags_url = "https://allproperty.ai/wp-json/wp/v2/tags"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(tags_url, headers=headers, timeout=30)

    if response.status_code == 200:
        tags = response.json()
        return {item["name"]: item["id"] for item in tags}
    else:
        print(f"Ошибка получения тегов: {response.status_code} - {response.text}")
        return {}


def make_get_request(url, headers):
    """
    Универсальная функция для GET-запросов.

    :param url: URL для GET-запроса.
    :param token: строка, токен авторизации.
    :return: результат запроса в виде JSON или None в случае ошибки.
    """

    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        logger.info(response.json())
        return response.json()
    else:
        logger.error(f"Ошибка GET-запроса: {response.status_code} - {response.text}")
        return None


def make_post_request(url, payload):
    """
    Универсальная функция для POST-запросов.

    :param url: URL для POST-запроса.
    :param payload: словарь с данными для отправки.
    :return: результат запроса в виде JSON или None в случае ошибки.
    """
    headers = load_headers()  # Получение заголовков авторизации

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code in [200, 201]:
            pass
            # logger.info(f"Запрос успешен. Ответ: {response.json()}")
            # return response.json()
        else:
            logger.error(
                f"Ошибка POST-запроса: {response.status_code} - {response.text}"
            )
            return None
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса: {e}")
        return None


def get_property():
    # URL для вашего WordPress REST API
    api_url = "https://allproperty.ai/wp-json/wp/v2/properties"
    with open(output_file, "r", encoding="utf-8") as token_file:
        property_datas = json.load(token_file)
    for property_data in property_datas:
        make_post_request(api_url, property_data)


def update_property(id_property):
    # URL для вашего WordPress REST API
    api_url = f"https://allproperty.ai/wp-json/wp/v2/properties/{id_property}"

    # Данные для обновления
    property_data = {
        "content": "Ку",
        "property_meta": {  # Используем стандартное поле meta
            "fave_property_garage": ["1", "1"],
            "fave_property_year": ["2016", "2016"],
            "fave_property_map_address": [
                "3047 W Argyle St, Chicago, IL 60625, USA",
            ],
            "fave_property_size": [
                "1200",
            ],
            "fave_property_id": ["HZ33", "HZ33"],
            "additional_features": [],
            "property_country": [65],
        },
    }

    # Выполнение запроса
    make_post_request(api_url, property_data)


if __name__ == "__main__":
    # get_token()

    # load_posts_to_wordpress(token)

    # creative_new_post(token)
    parsing_html()
    get_property()
    # id_property = "17760"
    # update_property(id_property)
