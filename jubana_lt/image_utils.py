import logging
from pathlib import Path
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from logger import logger

cookies = {
    'PHPSESSID': 'veilud4s6c3a6eae33ncp3m222',
    'user_id': '5b387233db63876c1540ef24c9b1aacd',
    'cc_cookie': '%7B%22categories%22%3A%5B%22necessary%22%2C%22functionality%22%2C%22analytics%22%2C%22marketing%22%5D%2C%22revision%22%3A0%2C%22data%22%3Anull%2C%22consentTimestamp%22%3A%222025-04-07T11%3A32%3A21.849Z%22%2C%22consentId%22%3A%22d27c5c74-1482-479b-a878-a4ee2a6dba3b%22%2C%22services%22%3A%7B%22necessary%22%3A%5B%5D%2C%22functionality%22%3A%5B%5D%2C%22analytics%22%3A%5B%5D%2C%22marketing%22%3A%5B%5D%7D%2C%22lastConsentTimestamp%22%3A%222025-04-07T11%3A32%3A21.849Z%22%2C%22expirationTime%22%3A1759750341849%7D',
    'session': 'mzl6kWsidKIbqO%2B4XsA4ui83%2BSNgV5Kf2UjrppYitmmXHM%2B%2F4m%2F4YELGdcxIgz4cQKmfLfWylBGJOtmG7KENYPzIn3oYp%2FbahxaTAdPevNL2yNupajluOZ2O5R21b6faa%2Fcu601vMcxF%2B0evQW9PrspL0GhJNUuyd9PVk6lRFcY54DQD3j8Qxw8hJ%2BJw%2BnREeZyC6QMtVN9o313JRFONR8C9OPdoBjJjpt8E%2BgtUubvNxCncaAY55oh%2FS%2FbGgDJH6Lxx%2Fnv04Gprw49675h47U7fJSzmdY36Hefclc5X%2BFvGrcoH8vec6pgLFWpyX2yurxfb5hdk6yrZk4uMJ13TVPrpW7LyihwEbEvJy59DaLNg6lXRS4qtZhkpqR1V0IJhuQSqaokNW6uzB0wR4ujJTgkD0JfqRpEcdYHdzOrSxhE%3D',
    'hl': 'en',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'dnt': '1',
    'priority': 'u=0, i',
    'referer': 'https://www.jubana.lt/en/starters/starter-parts',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}
def extract_product_images(html_content: str) -> str:
    """
    Извлекает ссылки на все изображения продукта в максимальном качестве из HTML.

    Args:
        html_content (str): HTML содержимое страницы

    Returns:
        str: Список URL изображений в максимальном качестве, разделенных запятыми
    """
    try:
        soup = BeautifulSoup(html_content, "lxml")
        best_image_urls = []
        
        # Ищем все изображения в галерее продукта
        gallery_images = soup.select(".gallery-container .product-gallery-element")
        
        # Если галерея пуста, ищем любые подходящие изображения
        if not gallery_images:
            gallery_images = soup.select("img[data-src], img[src]")
        
        for img in gallery_images:
            best_url = ""
            max_resolution = 0
            
            # Проверяем data-src (обычно там более высокое качество)
            img_url = img.get("data-src", "")
            
            # Если data-src пуст, используем обычный src
            if not img_url:
                img_url = img.get("src", "")
            
            # Начинаем с этого URL как базового
            best_url = img_url
            
            # Проверяем источник изображения высокого разрешения
            source_parent = img.parent.find("source") if img.parent else None
            if source_parent and source_parent.has_attr("srcset"):
                srcset = source_parent["srcset"]
                # Разбираем srcset на отдельные изображения разных размеров
                srcset_parts = srcset.split(",")
                
                for part in srcset_parts:
                    part = part.strip()
                    if part:
                        # Обычно формат: URL 1x или URL 2x или URL 3x
                        url_resolution = part.split(" ")
                        if len(url_resolution) >= 2:
                            url = url_resolution[0]
                            resolution_str = url_resolution[1].replace("x", "")
                            try:
                                resolution = float(resolution_str)
                                # Ищем изображение с максимальным разрешением
                                if resolution > max_resolution:
                                    max_resolution = resolution
                                    best_url = url
                            except ValueError:
                                pass
            
            # Если нашли хороший URL, добавляем его в список
            if best_url and best_url not in best_image_urls:
                best_image_urls.append(best_url)
        
        # Объединяем все URL через запятую
        return ",".join(best_image_urls)
    
    except Exception as e:
        logger.error(f"Ошибка при извлечении фотографий продукта: {e}")
        return ""


def download_product_images(
    image_info: Union[List[Dict[str, str]], Dict[str, Any]],
    output_dir: str,
    product_id: str = None,
) -> List[str]:
    """
    Скачивает фотографии продукта по информации из extract_product_images.

    Args:
        image_info: Информация об изображениях (из extract_product_images)
        output_dir (str): Директория для сохранения изображений
        product_id (str, optional): ID продукта для именования файлов

    Returns:
        List[str]: Список путей к скачанным изображениям
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    try:
        # Проверяем, получили ли мы словарь с main_images и thumbnails или только список изображений
        if isinstance(image_info, dict) and "main_images" in image_info:
            images = image_info["main_images"]
        else:
            images = image_info

        for idx, img_data in enumerate(images):
            # Используем data_src если доступен, иначе src
            img_url = img_data.get("data_src") or img_data.get("src")

            if not img_url:
                continue

            # Проверяем, является ли URL относительным
            if not img_url.startswith(("http://", "https://")):
                # Для относительных URL нужно добавить базовый URL сайта
                # Предполагаем, что базовый URL - jubana.lt
                base_url = "https://www.jubana.lt"
                if not img_url.startswith("/"):
                    img_url = "/" + img_url
                img_url = base_url + img_url

            # Получаем расширение файла из URL
            path_parts = urlparse(img_url).path.split("/")
            if "." in path_parts[-1]:
                ext = path_parts[-1].split(".")[-1]
                if "?" in ext:  # Удаляем параметры запроса из расширения
                    ext = ext.split("?")[0]
            else:
                ext = "jpg"  # По умолчанию jpg

            # Формируем имя файла
            if product_id:
                filename = f"{product_id}_{idx+1}.{ext}"
            else:
                # Если product_id не указан, используем часть URL или title/alt
                name_base = (
                    img_data.get("title") or img_data.get("alt") or f"product_{idx+1}"
                )
                # Очищаем имя файла от недопустимых символов
                name_base = "".join(
                    c for c in name_base if c.isalnum() or c in [" ", "_", "-"]
                )
                name_base = name_base.replace(" ", "_")
                filename = f"{name_base}.{ext}"

            file_path = output_path / filename
            if file_path.exists():
                continue
            # Скачиваем изображение
            try:
                response = requests.get(img_url,cookies=cookies,headers=headers, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded_files.append(str(file_path))
                    logger.info(f"Скачано изображение: {file_path}")
                else:
                    logger.warning(
                        f"Не удалось скачать изображение {img_url}. Код ответа: {response.status_code}"
                    )
            except Exception as e:
                logger.error(f"Ошибка при скачивании изображения {img_url}: {e}")

       

        return downloaded_files
    except Exception as e:
        logger.error(f"Ошибка при скачивании изображений: {e}")
        return downloaded_files
