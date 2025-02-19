import json
import os
import sys
from io import BytesIO
from pathlib import Path

import requests
from dotenv import load_dotenv
from loguru import logger
from PIL import Image

current_directory = Path.cwd()
json_directory = current_directory / "json"
config_directory = current_directory / "config"
log_directory = current_directory / "log"
img_directory = current_directory / "img"

config_directory.mkdir(parents=True, exist_ok=True)
img_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

output_json = log_directory / "output.json"
log_file_path = log_directory / "log_message.log"
env_file_path = config_directory / ".env"

load_dotenv(env_file_path)
category = os.getenv("category")
logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "origin": "https://www.vistaprint.com",
    "priority": "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}


def get_json():
    for i in range(0, 5):
        offset = i * 96
        params = {
            "attributes": [
                "corners_standard corners",
                "finish_none",
                "substrate_matte",
            ],
            "bypassApproval": "false",
            "facetCategories": [
                "1",
                "1299",
                "377",
            ],
            "useRealisationEngineService": "false",
            "limit": "96",
            "offset": offset,
            "requestor": "gallery-6-client",
            "noCache": "false",
            "useConstraints": "true",
            "experimentFlags[global_ranking_p4]": "2",
            "designCreationTypes": "Static",
            "debug": "false",
            "includeCategoryAndKeywordData": "true",
            "mpvId": "standardBusinessCards",
            "filterAltTextCompatibleTagging": "true",
        }
        response = requests.get(
            f"https://gallery-content-query.dd.vpsvc.com/api/v2/Galleries/{category}/Culture/en-us/Content",
            params=params,
            headers=headers,
            timeout=30,
        )
        json_file_path = json_directory / f"{category}_{i}.json"
        if json_file_path.exists():
            logger.warning(f"Файл {json_file_path} уже существует")
            continue
        try:
            data = response.json()
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
            logger.info(json_file_path)
        except ValueError:
            logger.error("Ошибка: ответ не содержит JSON")


def process_data():
    all_data = []
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        json_datas = data["results"]["content"]
        for json_data in json_datas:
            name = json_data["altText"]
            url_img = f'https:{json_data["previewUrls"]["size2x"]}'
            all_data.append({"name": name, "url_img": url_img})
    with open(output_json, "w", encoding="utf-8") as f:  # Записываем в файл
        json.dump(all_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    logger.info("Данные успешно записаны в файл data.json")
    logger.info(f"Количество данных: {len(all_data)}")


def download_images():
    with open(output_json, "r", encoding="utf-8") as file:
        data = json.load(file)
    for item in data:
        name = item["name"]
        url_img = item["url_img"]
        img_path = img_directory / f"{name}.jpg"
        if img_path.exists():
            logger.warning(f"Изображение {name} уже существует")
            continue
        img_response = requests.get(url_img, headers=headers, timeout=30)
        if img_response.status_code == 200:
            image = Image.open(BytesIO(img_response.content))

            # Сохраняем изображение в формате JPEG
            if image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(img_path, "JPEG")
            logger.info(f"Изображение {name} успешно скачано")
        else:
            logger.error(f"Ошибка при скачивании изображения {name}")


if __name__ == "__main__":
    get_json()
    process_data()
    download_images()
