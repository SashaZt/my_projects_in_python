import os
import re
from io import BytesIO

import requests
from configuration.logger_setup import logger
from PIL import Image

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def sanitize_filename(filename):
    """
    Убирает запрещённые символы из имени файла.
    """
    return re.sub(r'[\\/:*?"<>|]', "_", filename)


def search_image(query, api_key, cx, min_resolution=(500, 500), max_results=10):
    """
    Поиск изображения через Google Custom Search API.
    Возвращает URL изображения, соответствующего минимальному разрешению.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cx,
        "key": api_key,
        "searchType": "image",
        "num": max_results,
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            return None

        # Проверяем разрешение изображений
        for item in data["items"]:
            image_url = item["link"]
            try:
                img_response = requests.get(image_url, stream=True, timeout=10)
                img_response.raise_for_status()
                img = Image.open(BytesIO(img_response.content))
                if (
                    img.size[0] >= min_resolution[0]
                    and img.size[1] >= min_resolution[1]
                ):
                    return image_url
            except Exception as e:
                logger.warning(
                    f"Не удалось проверить изображение: {image_url}, ошибка: {e}"
                )

        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при поиске изображения: {e}")
        return None


def download_image(image_url, save_path):
    """
    Скачивает изображение по URL и сохраняет его на диск.
    """
    try:
        response = requests.get(image_url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        logger.info(f"Изображение сохранено: {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при скачивании изображения: {e}")
        return False


# Введите свой API-ключ и CX
API_KEY = "API_KEY"
CX = "CX"

# Пример запроса
# product_name = "AKTYWNA PIANA DO MYCIA NAPĘDU ROWEROWEGO"
skus = [
    "FPT124 1012",
    "1327B021226",
    "640367/23",
    "24385B",
    "JTF577.15",
    "CASQN312KAKIMAT",
    "FPJ056 6142",
    "FJT226 1010",
    "CAI599184/22",
]

# # Поиск по названию товара
# image_by_name_url = search_image(product_name, API_KEY, CX)
# if image_by_name_url:
#     print(f"Изображение по названию: {image_by_name_url}")
#     download_image(image_by_name_url, os.path.join(os.getcwd(), "image_by_name.jpg"))
# Пример использования
# Основной процесс
for sku in skus:
    attempts = 0
    image_saved = False
    while attempts < 3:  # Максимум 3 попытки для каждого SKU
        image_url = search_image(sku, API_KEY, CX)
        if image_url:
            logger.info(f"Изображение по SKU: {image_url}")

            # Очищаем имя файла
            sanitized_sku = sanitize_filename(sku)
            file_path = os.path.join(os.getcwd(), f"image_by_{sanitized_sku}.jpg")
            # Проверяем наличие файла
            if os.path.exists(file_path):
                logger.info(f"Файл уже существует: {file_path}. Пропускаем загрузку.")
                break  # Переходим к следующему SKU
            # Скачивание изображения
            if download_image(image_url, file_path):
                image_saved = True
                break  # Успешно скачано, выходим из цикла
            else:
                logger.warning(
                    f"Попытка {attempts + 1}: Не удалось скачать изображение по SKU: {sku}"
                )
        else:
            logger.error(
                f"Попытка {attempts + 1}: Не удалось найти изображение для SKU: {sku}"
            )
        attempts += 1

    if not image_saved:
        logger.error(
            f"Не удалось найти или скачать изображение для SKU: {sku} после 3 попыток."
        )
