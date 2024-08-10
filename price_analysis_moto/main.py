import re
import json
import os
import csv
from tkinter import N
import requests
import aiofiles
import time
from selectolax.parser import HTMLParser
import glob
import asyncio
from configuration.logger_setup import logger


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)


# Создание директорий согласно out.json
def get_dir_json():
    # Загрузка данных из out.json
    with open("out.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Обработка каждого ключа верхнего уровня (например, motostyle_ua, motodom_ua)
    for key in data.keys():
        # Создание директории с именем ключа внутри папки temp
        dir_path = os.path.join(temp_path, key)
        os.makedirs(dir_path, exist_ok=True)

        # Создание нового JSON-файла в соответствующей папке внутри temp
        with open(os.path.join(dir_path, "out.json"), "w", encoding="utf-8") as outfile:
            # Запись данных в новый JSON-файл
            json.dump({key: data[key]}, outfile, ensure_ascii=False, indent=4)

    logger.info("Данные успешно разделены и сохранены в соответствующих папках.")
    load_json_files_from_subdirectories()


def load_json_files_from_subdirectories():
    dir_path = os.path.join(os.getcwd(), "temp")
    json_data = {}

    # Итерация по всем элементам в указанной директории
    for root, dirs, files in os.walk(dir_path):
        for directory in dirs:
            # Полный путь к поддиректории
            subdir_path = os.path.join(root, directory)

            # Путь к файлу out.json в этой поддиректории
            json_file_path = os.path.join(subdir_path, "out.json")
            csv_file_path = os.path.join(subdir_path, "out.csv")

            # Проверка на существование файла out.json
            all_links = []
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    try:
                        # Загрузка данных JSON
                        data = json.load(json_file)
                        json_data[directory] = data
                        # Получение всех ссылок из ключа "motodom_ua"
                        links = data.get("motodom_ua", [])
                        for l in links:
                            all_links.append(l["link"])
                            id_link = l["id"]
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при загрузке {json_file_path}: {e}")
            else:
                logger.error(f"Файл {json_file_path} не найден.")

            # Запись ссылок в CSV
            with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for link in all_links:
                    writer.writerow([link])

    logger.info("Все ссылки успешно записаны в CSV файлы.")


def create_html_and_read_csv():

    dir_path = os.path.join(os.getcwd(), "temp")

    # Получение списка поддиректорий на верхнем уровне
    subdirs = [
        d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))
    ]

    for directory in subdirs:
        if directory == "motodom_ua":

            # Полный путь к поддиректории
            subdir_path = os.path.join(dir_path, directory)
            # Создание новой папки html в каждой поддиректории, если она еще не создана
            html_path = os.path.join(subdir_path, "html")
            if not os.path.exists(html_path):
                os.makedirs(html_path)

            json_file_path = os.path.join(subdir_path, "out.json")

            # Проверка на существование файла out.json
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    # Загрузка данных JSON
                    data = json.load(json_file)
                    # Получение всех ссылок из ключа "motodom_ua"
                    links = data.get(directory, [])
                    for l in links:
                        url = l["link"]
                        id_link = l["id"]
                        file_name_html = os.path.join(html_path, f"{id_link}.html")
                        get_html_motodom_ua(url, file_name_html)
        elif directory == "tireshop_ua":
            # Полный путь к поддиректории
            subdir_path = os.path.join(dir_path, directory)
            # Создание новой папки html в каждой поддиректории, если она еще не создана
            html_path = os.path.join(subdir_path, "html")
            if not os.path.exists(html_path):
                os.makedirs(html_path)

            json_file_path = os.path.join(subdir_path, "out.json")

            # Проверка на существование файла out.json
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    # Загрузка данных JSON
                    data = json.load(json_file)
                    # Получение всех ссылок из ключа "motodom_ua"
                    links = data.get(directory, [])
                    for l in links:
                        url = l["link"]
                        id_link = l["id"]
                        file_name_html = os.path.join(html_path, f"{id_link}.html")
                        get_html_motodom_ua(url, file_name_html)


def get_html_motodom_ua(url, file_name_html):

    if not os.path.exists(file_name_html):
        cookies = {
            "jrv": "55750",
            "PHPSESSID": "5pfnuqtt1bh94bqaqs9qfv5ctu",
            "default": "imrum01m616km4mgu38a4b0vpr",
            "currency": "UAH",
            "cf_clearance": "u7PFikBy.dJRMui6wRUUCmWA4Wbdu1nvD5FgD36KfvY-1723014419-1.0.1.1-QMhdwCrE.tZv_sGpWTNOXRP_x3OLH_jgX5.QlhvoSNGdK_JOqyi3V2oRHsp7_DbTqy11voEP.pI0u2DVX0V0Gg",
            "language_url": "ru",
            "language": "ru-ru",
        }

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }
        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
        )
        # Проверка кода ответа
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_name_html, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Файл сохраненн {file_name_html}")
            time.sleep(5)
        else:
            logger.error(response.status_code)


def get_html_tireshop_ua(url, file_name_html):

    if not os.path.exists(file_name_html):
        cookies = {
            "language": "ru",
            "_ms": "37997b6d-db6c-4452-b320-cf43fa925144",
            "PHPSESSID": "3t80nt1grucdo6pfdatcin5su2",
            "currency": "UAH",
        }

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "cache-control": "no-cache",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }
        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
        )
        # Проверка кода ответа
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_name_html, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Файл сохраненн {file_name_html}")
            time.sleep(5)
        else:
            logger.error(response.status_code)


# Основная функция парсера
async def parse_html_file():
    dir_path = os.path.join(os.getcwd(), "temp")

    subdirs = [
        d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))
    ]

    for directory in subdirs:
        if directory == "motodom_ua":
            await parser_motodom_ua(dir_path, directory)
        elif directory == "tireshop_ua":
            await parser_tireshop_ua(dir_path, directory)


# Парсер motodom_ua
async def parser_motodom_ua(dir_path, directory):
    subdir_path = os.path.join(dir_path, directory)
    json_out = os.path.join(subdir_path, "out.json")

    async with aiofiles.open(json_out, "r", encoding="utf-8") as file:
        content = await file.read()
        json_data = json.loads(content)

    html_path = os.path.join(subdir_path, "html")
    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)

    for item in files_html:
        id_product = os.path.splitext(os.path.basename(item))[0]
        async with aiofiles.open(item, "r", encoding="utf-8") as file:
            html_content = await file.read()

        tree = HTMLParser(html_content)
        available = None
        price = None
        stock_text_node = tree.css_first("#product > div.product-stats")

        if stock_text_node:
            stock_li_nodes = stock_text_node.css("li")
            for li_node in stock_li_nodes:
                if "Наличие:" in li_node.text():
                    stock_text_node = li_node.css_first("span")
                    if stock_text_node:
                        available = stock_text_node.text(strip=True)

        available = True if available == "В наличии" else False

        price_selector = "div.price-group > div.product-price"
        price = extract_price_motodom_ua(tree, price_selector)

        if price == "Элемент не найден":
            price_selector = "div.price-group > div.product-price-new"
            price = extract_price_motodom_ua(tree, price_selector)

        # price = int(price)
        err = None
        data = {
            "id": id_product,
            "available": available,
            "price": price,
            "err": err,
        }
        # logger.info(data)
        result(subdir_path, data)


# Парсер motodom_ua
async def parser_tireshop_ua(dir_path, directory):
    subdir_path = os.path.join(dir_path, directory)
    json_out = os.path.join(subdir_path, "out.json")

    async with aiofiles.open(json_out, "r", encoding="utf-8") as file:
        content = await file.read()
        json_data = json.loads(content)

    html_path = os.path.join(subdir_path, "html")
    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)

    for item in files_html:
        # logger.info(item)
        id_product = os.path.splitext(os.path.basename(item))[0]
        async with aiofiles.open(item, "r", encoding="utf-8") as file:
            html_content = await file.read()

        tree = HTMLParser(html_content)
        available = None
        price = None
        # Извлечение текста
        available_text_node = tree.css_first(
            "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div:nth-child(4) > div:nth-child(2) > div"
        )

        if available_text_node:
            extracted_text = available_text_node.text(strip=True)
            if "В наличии в Киеве" in extracted_text:
                available = extracted_text
        #     else:
        #         logger.info("Text not found.")
        # else:
        #     logger.info("Element not found.")

        available = True if available == "В наличии в Киеве" else False

        # Попытка извлечения цены с использованием различных селекторов
        selectors = [
            "div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div.product__item-sale > div.product__card-price.price-grn",
            "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div:nth-child(1) > div",
            "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4 > div.product__card-total-price.price-grn.gray",
        ]

        price = None

        for selector in selectors:
            price = extract_price_motodom_ua(tree, selector)
            if price != "Элемент не найден":
                break

        if price != "Элемент не найден":
            pass

        err = None
        data = {
            "id": id_product,
            "available": available,
            "price": price,
            "err": err,
        }
        # logger.info(data)
        result(subdir_path, data)


# Формирование резултата motodom_ua
def result(subdir_path, data):
    out_path = os.path.join(subdir_path, "out.json")
    result_path = os.path.join(subdir_path, "result.json")

    # Чтение данных из out.json
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        # Обновление данных
        updated = False
        for key, items in json_data.items():
            for item in items:
                if item["id"] == data["id"]:
                    # logger.info(f"Updating item with ID: {item['id']}")
                    item["available"] = data["available"]
                    item["price"] = data["price"]
                    item["err"] = data["err"]
                    updated = True

        # Если данные обновлены, сохранение их в файл out.json
        if updated:
            with open(out_path, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            # logger.info(f"Data updated in {out_path}")

            # Также сохранить обновленные данные в файл result.json
            with open(result_path, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            # logger.info(f"Data also saved in {result_path}")
        else:
            logger.warning(f"ID {data['id']} not found in {out_path}")
    else:
        logger.error(f"File {out_path} does not exist.")


# Функция для извлечения цены
def extract_price_motodom_ua(tree, selector):
    try:
        node = tree.css_first(selector)
        if node:
            price = node.text(strip=True).replace(" ", "")
            price = price.replace(" грн.", "")
            return int(price)
        else:
            return "Элемент не найден"
    except Exception as e:
        return f"Ошибка извлечения: {e}"


if __name__ == "__main__":
    # get_dir_json()
    # create_html_and_read_csv()
    asyncio.run(parse_html_file())
