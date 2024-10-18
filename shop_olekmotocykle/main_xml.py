import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
from pathlib import Path
import json
from configuration.logger_setup import logger
import os
import random
import re
from ftplib import FTP
from tqdm import tqdm

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
    with requests.get(url, stream=True) as response:
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        with tqdm(
            total=total_size, desc="Загрузка XML файла", unit="B", unit_scale=True
        ) as pbar:
            if response.status_code == 200:
                with open(xml_output, "wb") as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        pbar.update(len(data))
                logger.info("Качаем файл XML успешно сохранен")
            else:
                logger.error(f"Ошибка при загрузке XML: {response.status_code}")


"""Скачать csv файл"""


def download_csv_from_ftp():
    ftp_server = "ftp.olekmotocykle.pl"
    ftp_user = "daneeverhandel@olekmotocykle.pl"
    ftp_password = "32hdy5xaE1q2w3e4r"
    file_name = "Olekmotocykle.csv"
    local_file_path = data_directory / file_name

    try:
        ftp = FTP(ftp_server)
        ftp.login(user=ftp_user, passwd=ftp_password)
        logger.info(f"Подключен к FTP серверу {ftp_server}")

        with open(local_file_path, "wb") as file:
            ftp.retrbinary(f"RETR {file_name}", file.write)
        logger.info(f"Файл {file_name} скачан и сохранен в {local_file_path}")

    except Exception as e:
        logger.error(f"Ошибка при подключении к FTP серверу: {str(e)}")
    finally:
        if "ftp" in locals():
            ftp.quit()
            logger.info(f"Соединение с FTP сервером {ftp_server} закрыто")


"""Парсим CSV file"""


def parse_csv_file():
    download_csv_from_ftp()
    csv_file_path = data_directory / "Olekmotocykle.csv"
    try:
        df = pd.read_csv(csv_file_path, sep="\t")
        product_list = df[["kod", "cena"]].to_dict(orient="records")
        logger.info(f"Успешно спарсен CSV файл в список словарей")
        return product_list
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV файла: {str(e)}")
        return []


"""Парсим XML file"""


# Function to parse product element
def parse_product(product, list_tovarov):
    imgs = product.find("imgs")
    img_urls = ";".join([i.attrib["url"] for i in imgs.findall("i")]) if imgs else ""

    kod = product.find("kod").text
    cena = next(
        (item["cena"] for item in list_tovarov if str(item["kod"]) == kod), None
    )

    data = {
        "id": product.attrib["id"],
        "symbol": product.find("symbol").text,
        "kod": kod,
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
        "cena": cena,
    }
    return data


def parsing_xml():
    # Загрузка XML из файла
    tree = ET.parse(xml_output)
    root = tree.getroot()
    # Загрузка списка товаров из CSV файла
    list_tovarov = parse_csv_file()
    # Extract data from XML
    products = []
    for product in tqdm(root.findall("product"), desc="Обработка товаров"):
        products.append(parse_product(product, list_tovarov))
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
    if not ean:
        # Извлекаем оригинальное имя файла из URL, если ean отсутствует
        original_filename = os.path.basename(url)
        if len(image_urls) > 1 and index > 0:
            return f"{os.path.splitext(original_filename)[0]}_{index + 1}.jpg"
        else:
            return original_filename
    else:
        # Заменяем символ '/' на '-' в ean
        sanitized_ean = re.sub(r"/", "-", ean)
        if len(image_urls) > 1 and index > 0:
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


if __name__ == "__main__":
    while True:
        # Запрос ввода от пользователя
        print(
            "\nВведите 1 для получения Excel файла и фото"
            "\nВведите 2 для получения только Excel файла"
            "\nВведите 3 для скачивания фото"
            "\nВведите 0 для закрытия программы"
        )
        try:
            user_input = int(input("\u0412ыберите действие: "))
        except ValueError:
            print("\nНеверный ввод, пожалуйста, введите цифру.")
            continue

        if user_input == 1:
            get_xml()
            parsing_xml()
            generate_json()
        elif user_input == 2:
            get_xml()
            parsing_xml()
            generate_json()
        elif user_input == 3:
            download_images_from_json()
        elif user_input == 0:
            print("\nПрограмма завершена.")
            break  # Выход из цикла, завершение программы
        else:
            print("\nНеверный ввод, пожалуйста, введите корректный номер действия.")
