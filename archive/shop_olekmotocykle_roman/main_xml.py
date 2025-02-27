import json
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from ftplib import FTP
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
image_directory = current_directory / "image"
configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
image_directory.mkdir(parents=True, exist_ok=True)

xml_output = data_directory / "output.xml"
xlsx_output = data_directory / "output.xlsx"
json_output = data_directory / "url_img.json"
proxies_file = configuration_directory / "proxies.json"

# Блокировка для безопасного логирования из разных потоков
log_lock = Lock()
# Загрузка прокси из файла
def load_proxies():
    try:
        with open(proxies_file, 'r') as f:
            proxy_data = json.load(f)
            
        proxy_list = []
        login = proxy_data['login']
        password = proxy_data['password']
        http_port = proxy_data['http_port']
        
        for ip in proxy_data['proxies']:
            proxy_url = f"http://{login}:{password}@{ip}:{http_port}"
            proxy_list.append({'http': proxy_url, 'https': proxy_url})
            
        return proxy_list
    except Exception as e:
        logger.error(f"Ошибка при загрузке прокси: {str(e)}")
        return []
    
"""Скачать XML файл"""


def get_xml():
    logger.info("Качаем файл XML")
    url = "https://pim.olekmotocykle.com/xml?id=85&hash=be0525b9258c18c3452ee7bd80bcf32e591b48a4ca3574f2fd0d80b8a3f450b6"
    with requests.get(url,timeout=30, stream=True) as response:
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


# """Парсим CSV file"""


# def parse_csv_file():
#     # download_csv_from_ftp()
#     csv_file_path = data_directory / "Olekmotocykle.csv"
#     try:
#         df = pd.read_csv(csv_file_path, sep="\t")
#         product_list = df[["kod", "cena"]].to_dict(orient="records")
#         logger.info("Успешно спарсен CSV файл в список словарей")
#         return product_list
#     except Exception as e:
#         logger.error(f"Ошибка при чтении CSV файла: {str(e)}")
#         return []


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


def parse_xml():
    # Загрузка XML из файла
    tree = ET.parse(xml_output)
    root = tree.getroot()

    # Список для хранения данных о продуктах
    products = []

    # Обход всех продуктов
    for product in root.findall("product"):
        product_data = {
            "id": product.get("id"),
            "symbol": product.find("symbol").text,
            "kod": product.find("kod").text,
            "ean": product.find("ean").text,
            "name": product.find("name").text,
            "marka": product.find("marka").text,
            "category": product.find("category").text.strip(),
            "price": float(product.find("price").text),
            "quantity": int(product.find("quantity").text),
        }
        products.append(product_data)

    # Создание DataFrame из списка продуктов
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
        kod = product.find("kod").text if product.find("kod") is not None else ""
        imgs = product.find("imgs")
        img_urls = (
            [i.attrib["url"] for i in imgs.findall("i")] if imgs is not None else []
        )

        product_data = {"kod": kod, "i url": img_urls}
        products_list.append(product_data)

    # Сохранение в JSON файл
    with open(json_output, "w", encoding="utf-8") as json_file:
        json.dump(products_list, json_file, ensure_ascii=False, indent=4)

    logger.info(f"JSON файл сохранен {json_output}")


# # Функция для скачивания изображений с поддержкой повторных попыток
# def download_image_with_retries(url, image_path, image_name, max_retries=3):
#     attempts = 0
#     while attempts < max_retries:
#         try:
#             response = requests.get(url,headers=headers, timeout=30, stream=True)
#             if response.status_code == 200:
#                 with open(image_path, "wb") as file:
#                     for chunk in response.iter_content(1024):
#                         file.write(chunk)
#                 logger.info(f"Изображение сохранено как {image_name}")

#                 # Пауза от 1 до 5 секунд после успешного скачивания
#                 time.sleep(random.randint(1, 5))
#                 break  # Успешно скачали, выходим из цикла
#             else:
#                 logger.error(
#                     f"Ошибка при загрузке изображения по ссылке {url}: {response.status_code}"
#                 )
#                 # Пауза 10 секунд при ошибке
#                 time.sleep(10)
#                 attempts += 1

#         except Exception as e:
#             logger.error(f"Ошибка при скачивании изображения: {str(e)}")
#             # Пауза 10 секунд при ошибке
#             time.sleep(10)
#             attempts += 1

#     if attempts == max_retries:
#         logger.error(
#             f"Не удалось скачать изображение после {max_retries} попыток: {url}"
#         )


# # Функция для формирования имени файла
# def format_image_name(kod, index, url):
#     if not kod:
#         # Извлекаем оригинальное имя файла из URL, если ean отсутствует
#         original_filename = os.path.basename(url)
#         return (
#             f"{os.path.splitext(original_filename)[0]}_{index}.jpg"
#             if index > 0
#             else original_filename
#         )
#     else:
#         # Заменяем символ '/' на '-' в ean
#         sanitized_kod = re.sub(r"/", " ", kod)
#         return f"{sanitized_kod}_{index}.jpg" if index > 0 else f"{sanitized_kod}.jpg"

# # Основная функция для загрузки изображений из JSON
# def download_images_from_json():
#     # Чтение JSON файла
#     try:
#         with open(json_output, "r", encoding="utf-8") as json_file:
#             products_list = json.load(json_file)
#     except Exception as e:
#         logger.error(f"Не удалось прочитать файл JSON: {e}")
#         return

#     # Проход по каждому продукту в JSON
#     for product in products_list:
#         kod = product.get("kod")  # Используем get для безопасного доступа
#         image_urls = product.get(
#             "i url", []
#         )  # Используем get с пустым списком на случай отсутствия

#         for index, url in enumerate(image_urls):
#             # Формируем имя файла
#             image_name = format_image_name(kod, index, url)

#             # Полный путь к файлу изображения
#             image_path = image_directory / image_name

#             # Проверяем, существует ли файл
#             if image_path.exists():
#                 logger.info(f"Файл {image_name} уже существует, пропускаем скачивание.")
#                 continue

#             # Вызов функции для скачивания с поддержкой повторных попыток
#             download_image_with_retries(url, image_path, image_name)

# Функция для скачивания изображений с поддержкой повторных попыток и прокси
def download_image_with_retries(url, image_path, image_name, proxy, max_retries=10):
    attempts = 0
    
    # Базовые заголовки для запроса
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://google.com/',
    }
    
    
    while attempts < max_retries:
        try:
            with log_lock:
                logger.info(f"Загрузка {url} через прокси {proxy['http']} (попытка {attempts+1})")
                
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxy, 
                timeout=30, 
                stream=True
            )
            
            if response.status_code == 200:
                with open(image_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                        
                with log_lock:
                    logger.info(f"Изображение сохранено как {image_name}")

                # Пауза от 1 до 5 секунд после успешного скачивания
                time.sleep(random.randint(1, 5))
                return True  # Успешно скачали
                
            else:
                with log_lock:
                    logger.error(f"Ошибка при загрузке изображения по ссылке {url}: {response.status_code}")
                # Пауза 10 секунд при ошибке
                time.sleep(10)
                attempts += 1

        except Exception as e:
            with log_lock:
                logger.error(f"Ошибка при скачивании изображения {url}: {str(e)}")
            # Пауза 10 секунд при ошибке
            time.sleep(10)
            attempts += 1

    if attempts == max_retries:
        with log_lock:
            logger.error(f"Не удалось скачать изображение после {max_retries} попыток: {url}")
    return False

# Функция для формирования имени файла
def format_image_name(kod, index, url):
    if not kod:
        # Извлекаем оригинальное имя файла из URL, если kod отсутствует
        original_filename = os.path.basename(url)
        return (
            f"{os.path.splitext(original_filename)[0]}_{index}.jpg"
            if index > 0
            else original_filename
        )
    else:
        # Заменяем символ '/' на пробел в kod
        sanitized_kod = re.sub(r"/", " ", kod)
        return f"{sanitized_kod}_{index}.jpg" if index > 0 else f"{sanitized_kod}.jpg"

# Функция для обработки одного изображения (для использования в пуле потоков)
def process_image(item):
    product, proxy = item
    kod = product.get("kod")
    image_urls = product.get("i url", [])
    
    for index, url in enumerate(image_urls):
        # Формируем имя файла
        image_name = format_image_name(kod, index, url)

        # Полный путь к файлу изображения
        image_path = image_directory / image_name

        # Проверяем, существует ли файл
        if image_path.exists():
            with log_lock:
                logger.info(f"Файл {image_name} уже существует, пропускаем скачивание.")
            continue

        # Вызов функции для скачивания с поддержкой повторных попыток
        download_image_with_retries(url, image_path, image_name, proxy)

# Основная функция для загрузки изображений из JSON в многопоточном режиме
def download_images_from_json_multithreaded(max_workers=5):
    # Загрузка прокси
    proxies = load_proxies()
    if not proxies:
        logger.error("Не удалось загрузить прокси, прерываем выполнение.")
        return
    
    # Чтение JSON файла
    try:
        with open(json_output, "r", encoding="utf-8") as json_file:
            products_list = json.load(json_file)
    except Exception as e:
        logger.error(f"Не удалось прочитать файл JSON: {e}")
        return

    logger.info(f"Загружено {len(products_list)} товаров для обработки")
    
    # Подготовка задач для пула потоков
    tasks = []
    for product in products_list:
        # Случайно выбираем прокси для каждого товара
        random_proxy = random.choice(proxies)
        tasks.append((product, random_proxy))
    
    # Запуск обработки в пуле потоков
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        logger.info(f"Запуск многопоточной загрузки с {max_workers} потоками")
        list(executor.map(process_image, tasks))
    
    logger.info("Загрузка изображений завершена")
if __name__ == "__main__":
    while True:
        # Запрос ввода от пользователя
        print(
            "\nВведите 1 для получения Excel файла"
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
            parse_xml()
            generate_json()
        elif user_input == 2:
            generate_json()
        elif user_input == 3:
            download_images_from_json_multithreaded(max_workers=10) 
        elif user_input == 0:
            print("\nПрограмма завершена.")
            break  
        else:
            print("\nНеверный ввод, пожалуйста, введите корректный номер действия.")
