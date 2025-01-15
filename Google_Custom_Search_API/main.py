import os

import requests
from configuration.logger_setup import logger


def search_image(query, api_key, cx):
    """
    Функция для поиска изображения через Google Custom Search API.
    Возвращает URL первого найденного изображения.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,  # Запрос
        "cx": cx,  # Идентификатор поисковой системы
        "key": api_key,  # API-ключ
        "searchType": "image",  # Поиск по изображениям
        "num": 1,  # Количество результатов
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            return data["items"][0]["link"]  # URL первого изображения
        else:
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка: {e}")
        return None


def download_image(image_url, save_path):
    """
    Скачивает изображение по URL и сохраняет его на диск.
    """
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        logger.info(f"Изображение сохранено: {save_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при скачивании изображения: {e}")


# Введите свой API-ключ и CX
API_KEY = "API_KEY"
CX = "CX"

# Пример запроса
# product_name = "AKTYWNA PIANA DO MYCIA NAPĘDU ROWEROWEGO"
skus = "AWR9212,SN5035"

# # Поиск по названию товара
# image_by_name_url = search_image(product_name, API_KEY, CX)
# if image_by_name_url:
#     print(f"Изображение по названию: {image_by_name_url}")
#     download_image(image_by_name_url, os.path.join(os.getcwd(), "image_by_name.jpg"))
for sku in skus:
    # Поиск по SKU
    image_by_sku_url = search_image(sku, API_KEY, CX)
    if image_by_sku_url:
        logger.info(f"Изображение по SKU: {image_by_sku_url}")
        download_image(
            image_by_sku_url, os.path.join(os.getcwd(), f"image_by_{sku}.jpg")
        )
