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

    print("Данные успешно разделены и сохранены в соответствующих папках.")
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
                        print(f"Ошибка при загрузке {json_file_path}: {e}")
            else:
                print(f"Файл {json_file_path} не найден.")

            # Запись ссылок в CSV
            with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for link in all_links:
                    writer.writerow([link])

    print("Все ссылки успешно записаны в CSV файлы.")


def create_html_and_read_csv():
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
        "cache-control": "no-cache",
        # 'cookie': 'jrv=55750; PHPSESSID=5pfnuqtt1bh94bqaqs9qfv5ctu; default=imrum01m616km4mgu38a4b0vpr; currency=UAH; cf_clearance=u7PFikBy.dJRMui6wRUUCmWA4Wbdu1nvD5FgD36KfvY-1723014419-1.0.1.1-QMhdwCrE.tZv_sGpWTNOXRP_x3OLH_jgX5.QlhvoSNGdK_JOqyi3V2oRHsp7_DbTqy11voEP.pI0u2DVX0V0Gg; language_url=ru; language=ru-ru',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    dir_path = os.path.join(os.getcwd(), "temp")

    # Получение списка поддиректорий на верхнем уровне
    subdirs = [
        d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))
    ]

    for directory in subdirs[2:3]:
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
                links = data.get("motodom_ua", [])
                for l in links:
                    url = l["link"]
                    id_link = l["id"]
                    file_name_html = os.path.join(html_path, f"{id_link}.html")
                    if not os.path.exists(file_name_html):
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
                            time.sleep(5)


async def parse_html_file():
    dir_path = os.path.join(os.getcwd(), "temp")

    subdirs = [
        d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))
    ]

    for directory in subdirs[2:3]:
        subdir_path = os.path.join(dir_path, directory)
        json_out = os.path.join(subdir_path, "out.json")
        async with aiofiles.open(json_out, "r", encoding="utf-8") as file:
            content = await file.read()
            json_data = json.loads(content)

        html_path = os.path.join(subdir_path, "html")
        out_path = os.path.join(subdir_path, "out.json")
        folder = os.path.join(html_path, "*.html")
        files_html = glob.glob(folder)

        for item in files_html:
            id_product = os.path.splitext(os.path.basename(item))[0]
            async with aiofiles.open(item, "r", encoding="utf-8") as file:
                html_content = await file.read()

            tree = HTMLParser(html_content)
            # Цвета и размеры
            # # Извлечение цветов и размеров из HTML
            # color_map = {}
            # size_map = {}
            # color_id = None
            # size_id = None

            # # Извлечение цветов и размеров
            # for option_div in tree.css(".form-group.product-option-radio"):
            #     label_element = option_div.css_first(".control-label")
            #     if not label_element:
            #         continue

            #     label = label_element.text().strip().lower()

            #     option_id_element = option_div.css_first("div[id^='input-option']")
            #     if not option_id_element:
            #         continue

            #     option_id = option_id_element.attributes.get("id").replace(
            #         "input-option", ""
            #     )

            #     if "цвет" in label:
            #         color_id = option_id
            #         for radio in option_div.css(".radio"):
            #             input_element = radio.css_first("input[type='radio']")
            #             value = input_element.attributes.get("value")
            #             option_value = radio.css_first(".option-value").text().strip()
            #             color_map[value] = option_value
            #         logger.debug(f"Color ID: {color_id}, Color Map: {color_map}")
            #     elif "размер" in label:
            #         size_id = option_id
            #         for radio in option_div.css(".radio"):
            #             input_element = radio.css_first("input[type='radio']")
            #             value = input_element.attributes.get("value")
            #             option_value = radio.css_first(".option-value").text().strip()
            #             size_map[value] = option_value
            #         logger.debug(f"Size ID: {size_id}, Size Map: {size_map}")

            # # Обработка JSON-данных из скрипта
            # for script_tag in tree.css("script[type='text/javascript']"):
            #     script_content = script_tag.text()
            #     if script_content:
            #         json_match = re.search(
            #             r"ro_params\['ro_data'\] = (.*?]);", script_content, re.DOTALL
            #         )
            #         if json_match:
            #             json_string = json_match.group(1)
            #             data = json.loads(json_string)

            #             # Совместить идентификаторы с названиями цветов и размеров
            #             combined_options = []
            #             for entry in data:
            #                 try:
            #                     for ro_id, ro_info in entry["ro"].items():
            #                         color_value = ro_info["options"].get(color_id)
            #                         size_value = ro_info["options"].get(size_id)

            #                         color_name = color_map.get(
            #                             color_value, "Unknown Color"
            #                         )
            #                         size_name = size_map.get(size_value, "Unknown Size")

            #                         combined_options.append(
            #                             {
            #                                 "related_option_id": ro_id,
            #                                 "color": color_name,
            #                                 "size": size_name,
            #                             }
            #                         )

            #                         logger.debug(f"  Related Option ID: {ro_id}")
            #                         logger.debug(f"    Color: {color_name}")
            #                         logger.debug(f"    Size: {size_name}")
            #                 except Exception as e:
            #                     logger.error(f"Ошибка при обработке продукта: {e}")
            #                     continue

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
                # logger.info(available)

            price_selector = "div.price-group > div.product-price"
            price = extract_text(tree, price_selector)

            if price == "Элемент не найден":
                price_selector = "div.price-group > div.product-price-new"
                price = extract_text(tree, price_selector)

            err = None
            data = {
                "id": id_product,
                "available": available,
                "price": price,
                "err": err,
            }
            logger.info(data)
            update_json_with_price_and_availability(subdir_path, data)


def update_json_with_price_and_availability(subdir_path, data):
    out_path = os.path.join(subdir_path, "out.json")
    result_path = os.path.join(
        subdir_path, "result.json"
    )  # Путь для сохранения результата

    # Чтение данных из out.json
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        # Обновление данных
        updated = False
        for key, items in json_data.items():
            for item in items:
                if item["id"] == data["id"]:
                    item["available"] = data["available"]
                    item["price"] = data["price"]
                    item["err"] = data["err"]
                    updated = True

        # Если данные обновлены, сохранение их в файл result.json
        if updated:
            with open(result_path, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            print(f"Updated data for ID {data['id']} in {result_path}")
        else:
            print(f"ID {data['id']} not found in {out_path}")
    else:
        print(f"File {out_path} does not exist.")


def find_value_by_keyword_size_color(options, keywords):
    for key, value in options.items():
        # Проверяем каждое ключевое слово на соответствие ключу
        for keyword in keywords:
            if re.search(keyword, key, re.IGNORECASE):
                return value
    return None


# Функция для извлечения цены
def extract_text(tree, selector):
    try:
        node = tree.css_first(selector)
        if node:
            price = node.text(strip=True)
            return price.replace(" грн.", "")
        else:
            return "Элемент не найден"
    except Exception as e:
        return f"Ошибка извлечения: {e}"


def find_value_by_keyword(options, keywords):
    for key, value in options.items():
        # Преобразуем ключ в строку, чтобы быть уверенными, что мы работаем с текстом
        if any(re.search(keyword, key) for keyword in keywords):
            return value
    return None


if __name__ == "__main__":
    # get_dir_json()
    # create_html_and_read_csv()
    asyncio.run(parse_html_file())
