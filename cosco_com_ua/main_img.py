import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from PIL import Image

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
urls_csv = current_directory / "urls.csv"
img_files = current_directory / "img"
img_files.mkdir(parents=True, exist_ok=True)


def extract_filename_from_url(url):
    """
    Извлекает имя файла из URL после 'uploads' и заменяет '/' на '_', с заменой расширения на .jpg.

    :param url: str - URL-адрес
    :return: str - Имя файла с расширением .jpg
    """
    match = re.search(r"uploads/([\w/.-]+)", url)
    if match:
        return (
            match.group(1).replace("/", "_").rsplit(".", 1)[0] + ".jpg"
        )  # Сохраняем с расширением .jpg
    raise ValueError(f"URL '{url}' не содержит 'uploads'.")


def download_image(url, save_directory):
    """
    Скачивает изображение по URL и сохраняет его в указанной директории в формате JPG.

    :param url: str - URL изображения
    :param save_directory: Path - Путь к папке для сохранения изображения
    """
    try:
        # Извлекаем имя файла
        filename = extract_filename_from_url(url)
        save_path = save_directory / filename

        # Проверяем, существует ли файл
        if save_path.exists():
            print(f"Файл уже существует: {save_path}")
            return

        # Запрос к изображению
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Конвертируем изображение в JPG
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img.save(save_path, format="JPEG")

        print(f"Изображение сохранено: {save_path}")
    except Exception as e:
        print(f"Ошибка при загрузке изображения из {url}: {e}")


def read_cities_from_csv(input_csv_file):
    """
    Считывает список URL из CSV-файла.

    :param input_csv_file: Path - Путь к CSV-файлу
    :return: list - Список URL
    """
    try:
        df = pd.read_csv(input_csv_file)
        return df["url"].tolist()
    except Exception as e:
        print(f"Ошибка при чтении CSV-файла {input_csv_file}: {e}")
        return []


# Основной код
urls = read_cities_from_csv(urls_csv)

for url in urls:
    download_image(url, img_files)
