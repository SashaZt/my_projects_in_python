# Функция для скачивания изображения
import json
import os
import re
import shutil
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

current_directory = Path.cwd()

photo_directory = current_directory / "photo"

photo_directory.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = "token.json"  # Файл для сохранения токена


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


# Функция для поиска изображения по slug
def check_existing_image(slug, headers):
    wp_media_url = "https://allproperty.ai/wp-json/wp/v2/media"
    try:
        response = requests.get(
            wp_media_url, headers=headers, params={"slug": slug}, timeout=30
        )
        if response.status_code == 200:
            results = response.json()
            if results:
                # Возвращаем первый найденный ID
                logger.info(
                    f"Изображение {slug} уже существует. ID: {results[0]['id']}"
                )
                return results[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Ошибка при проверке существующего изображения {slug}: {e}")
        return None


# Функция для скачивания изображения
def download_image(url, file_name):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(file_name, "wb") as img_file:
                img_file.write(response.content)
            logger.info(f"Изображение сохранено локально как {file_name}.")
            return file_name
        else:
            logger.error(
                f"Ошибка при скачивании {url}. Код ответа: {response.status_code}"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при скачивании {url}: {e}")
        return None


# Функция для загрузки изображения
def download_and_upload_image(photo, headers):
    wp_media_url = "https://allproperty.ai/wp-json/wp/v2/media"
    for name, url in photo.items():
        file_name = extract_file_name(url)
        slug = file_name.replace(".jpg", "")
        logger.info(f"Проверяем, существует ли {slug} на сервере...")

        # Проверяем, существует ли изображение
        existing_id = check_existing_image(slug, headers)
        if existing_id:
            return existing_id

        logger.info(f"Скачиваем {name} с {url}...")
        file_name = download_image(url, file_name)
        if not file_name:
            logger.error(f"Пропускаем загрузку {name}, файл не скачан.")
            continue

        # Загружаем на сервер
        try:
            with open(file_name, "rb") as img_file:
                upload_headers = headers.copy()
                upload_headers["Content-Type"] = "image/jpeg"
                upload_headers["Content-Disposition"] = (
                    f'attachment; filename="{file_name}"'
                )
                upload_response = requests.post(
                    wp_media_url, headers=upload_headers, data=img_file, timeout=30
                )

            if upload_response.status_code == 201:
                logger.info(f"Изображение {file_name} загружено на сервер.")
                return upload_response.json()["id"]
            else:
                logger.error(
                    f"Ошибка при загрузке {file_name}. Ответ сервера: {upload_response.text}"
                )
        except Exception as e:
            logger.error(f"Ошибка при загрузке {file_name}: {e}")
        finally:
            os.remove(file_name)
            logger.info(f"Локальный файл {file_name} успешно удален.")

    return None


# Функция для извлечения имени файла
def extract_file_name(url):
    match = re.search(r"id\.pro\.es\.image\.master/([\d/]+/\d+\.jpg)", url)
    if match:
        return match.group(1).replace("/", "_")
    return None


# Чтение JSON-файла
def process_images_from_json():
    headers = load_headers()
    output_file = Path("extracted_profile_data.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        title = entry.get("title", "Без названия")
        logger.info(f"Обрабатываем объект: {title}")

        # Обработка изображений из photos
        photos = entry.get("photos", [])
        for photo in photos[:1]:
            image_id = download_and_upload_image(photo, headers)
            logger.info(f"Получен ID изображения: {image_id}")


if __name__ == "__main__":
    process_images_from_json()
