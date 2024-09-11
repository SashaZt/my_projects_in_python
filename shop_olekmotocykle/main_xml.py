from email.mime import image
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
from pathlib import Path
import json
from configuration.logger_setup import logger
import time
import os
import random
import requests

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
image_directory = current_directory / "image"
data_directory.mkdir(parents=True, exist_ok=True)
image_directory.mkdir(parents=True, exist_ok=True)

xml_output = data_directory / "output.xml"
xlsx_output = data_directory / "output.xlsx"
json_output = data_directory / "url_img.json"

"""Скачать XML файл"""


def get_xml():
    logger.info("Качаем файл XML")
    url = "https://pim.olekmotocykle.com/xml?id=109&hash=2427e6499332bca0f4a0f2687025cc520421d0a727cfe165875974fad723eb69"
    response = requests.get(url)
    if response.status_code == 200:
        with open(xml_output, "wb") as file:
            file.write(response.content)
        logger.info("XML файл успешно сохранен")
    else:
        logger.error("Ошибка при загрузке XML:", response.status_code)


"""Парсим файл XML"""


# Function to parse product element
def parse_product(product):
    imgs = product.find("imgs")
    img_urls = ";".join([i.attrib["url"] for i in imgs.findall("i")]) if imgs else ""

    data = {
        "id": product.attrib["id"],
        "symbol": product.find("symbol").text,
        "kod": product.find("kod").text,
        "ean": product.find("ean").text if product.find("ean") is not None else "",
        "name": product.find("name").text,
        "marka": product.find("marka").text,
        "imgs": img_urls,
        "category": (
            product.find("category").text.strip()
            if product.find("category") is not None
            else ""
        ),
        "price": float(product.find("price").text),
        "quantity": int(product.find("quantity").text),
    }
    return data


def parsing_xml():
    # Загрузка XML из файла
    tree = ET.parse(xml_output)
    root = tree.getroot()
    # Extract data from XML
    products = []
    for product in root.findall("product"):
        products.append(parse_product(product))
    # Преобразование данных в DataFrame
    df = pd.DataFrame(products)

    # Запись данных в .xlsx файл
    df.to_excel(xlsx_output, index=False)
    logger.info(f"Файл сохранен {xlsx_output}")


"""Формирование JSON файла с ean и ссылками на изображения"""


def generate_json():
    # Загрузка XML из файла
    tree = ET.parse(xml_output)
    root = tree.getroot()

    products_list = []

    for product in root.findall("product"):
        ean = product.find("ean").text if product.find("ean") is not None else ""
        imgs = product.find("imgs")
        img_urls = [i.attrib["url"] for i in imgs.findall("i")] if imgs else []

        product_data = {"ean": ean, "i url": img_urls}

        products_list.append(product_data)

    # Сохранение в JSON файл
    with open(json_output, "w", encoding="utf-8") as json_file:
        json.dump(products_list, json_file, ensure_ascii=False, indent=4)

    logger.info(f"JSON файл сохранен {json_output}")


# Функция для скачивания изображений с поддержкой повторных попыток
def download_image_with_retries(url, image_path, image_name, max_retries=3):
    attempts = 0
    while attempts < max_retries:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(image_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                logger.info(f"Изображение сохранено как {image_name}")

                # Пауза от 1 до 5 секунд после успешного скачивания
                time.sleep(random.randint(1, 5))
                break  # Успешно скачали, выходим из цикла
            else:
                logger.error(
                    f"Ошибка при загрузке изображения по ссылке {url}: {response.status_code}"
                )
                # Пауза 10 секунд при ошибке
                time.sleep(10)
                attempts += 1

        except Exception as e:
            logger.error(f"Ошибка при скачивании изображения: {str(e)}")
            # Пауза 10 секунд при ошибке
            time.sleep(10)
            attempts += 1

    if attempts == max_retries:
        logger.error(
            f"Не удалось скачать изображение после {max_retries} попыток: {url}"
        )


# Функция для формирования имени файла
def format_image_name(ean, index, image_urls, url):
    if ean is None:
        # Извлекаем оригинальное имя файла из URL, если ean отсутствует
        original_filename = os.path.basename(url)
        if len(image_urls) > 1:
            return f"{os.path.splitext(original_filename)[0]}_{index + 1}.jpg"
        else:
            return original_filename
    else:
        # Заменяем символ '/' на '-' в ean
        sanitized_ean = re.sub(r"/", "-", ean)
        if len(image_urls) > 1:
            return f"{sanitized_ean}_{index + 1}.jpg"
        else:
            return f"{sanitized_ean}.jpg"


# Основная функция для загрузки изображений из JSON
def download_images_from_json():
    # Чтение JSON файла
    with open(json_output, "r", encoding="utf-8") as json_file:
        products_list = json.load(json_file)

    # Проход по каждому продукту в JSON
    for product in products_list:
        ean = product.get("ean")  # Используем get для безопасного доступа
        image_urls = product.get(
            "i url", []
        )  # Используем get с пустым списком на случай отсутствия

        for index, url in enumerate(image_urls):
            # Формируем имя файла
            image_name = format_image_name(ean, index, image_urls, url)

            # Полный путь к файлу изображения
            image_path = image_directory / image_name

            # Проверяем, существует ли файл
            if image_path.exists():
                logger.info(f"Файл {image_name} уже существует, пропускаем скачивание.")
                continue

            # Вызов функции для скачивания с поддержкой повторных попыток
            download_image_with_retries(url, image_path, image_name)


# if __name__ == "__main__":
#     get_xml()
#     parsing_xml()
#     generate_json()
#     download_images_from_json()

while True:
    # Запрос ввода от пользователя
    print(
        "Введите 1 для получения ексель файла и фото"
        "\nВведите 2 для получения только ексель файла"
        "\nВведите 3 для скачивания фото"
        "\nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        get_xml()
        parsing_xml()
        generate_json()
        download_images_from_json()
    elif user_input == 2:
        get_xml()
        parsing_xml()
    elif user_input == 3:
        download_images_from_json()
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
