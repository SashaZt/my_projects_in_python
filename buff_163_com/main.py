import glob
import requests
import pandas as pd
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import asyncio
import aiofiles
from playwright.async_api import async_playwright


# from selectolax.parser import HTMLParser


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
sell_min_price_path = os.path.join(temp_path, "sell_min_price")
price_path = os.path.join(temp_path, "price")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(sell_min_price_path, exist_ok=True)
os.makedirs(price_path, exist_ok=True)


# Функция сохранения куки
async def save_cookies(context, file_path):
    cookies = await context.cookies()
    with open(file_path, "w") as f:
        json.dump(cookies, f)


# Функция получения куки
async def get_cookies():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )
        await page.goto("https://buff.163.com", wait_until="networkidle", timeout=60000)

        # Здесь выполните действия по авторизации
        # Например, введите логин и пароль и нажмите кнопку входа

        await asyncio.sleep(60)  # Дождитесь завершения авторизации

        # Сохранение куки
        await save_cookies(context, "cookies.json")

        await browser.close()


# Функция извлечение категории из url
def extract_category_group(url):
    # Разбираем URL
    parsed_url = urlparse(url)
    # Извлекаем параметры
    query_params = parse_qs(parsed_url.query)
    # Получаем значение параметра category_group
    category_group = query_params.get("category_group", [None])[0]
    return category_group


async def save_response_json_sell_min_price_path(json_response, category_group):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(sell_min_price_path, f"{category_group}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


async def save_response_json_price(json_response, filename):
    """Асинхронно сохраняет JSON-данные в файл."""
    # filename = os.path.join(price_path, f"{category_group}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


async def load_cookies(page, file_path):
    with open(file_path, "r") as f:
        cookies = json.load(f)
        await page.context.add_cookies(cookies)


# async def get_sell_min_price_path(url):

#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=False)
#         context = await browser.new_context()
#         page = await context.new_page()

#         # Устанавливаем обработчик для сбора и сохранения данных ответов
#         def create_log_response_with_counter(category_group):
#             async def log_response(response):
#                 api_url = "https://buff.163.com/api/market/goods/all"
#                 request = response.request
#                 if (
#                     request.method == "GET" and api_url in request.url
#                 ):  # Подставьте актуальное условие URL
#                     try:
#                         json_response = await response.json()
#                         await save_response_json_sell_min_price_path(
#                             json_response, category_group
#                         )

#                     except Exception as e:
#                         print(
#                             f"Ошибка при получении JSON из ответа {response.url}: {e}"
#                         )

#             return log_response

#         category_group = extract_category_group(url)
#         await load_cookies(page, "cookies.json")
#         handler = create_log_response_with_counter(category_group)
#         page.on("response", handler)
#         await page.goto(url)
#         # Итерация по страницам

#         await asyncio.sleep(10)
#         await browser.close()


def extract_max_paintwear(url):
    # Разбираем URL
    parsed_url = urlparse(url)
    # Извлекаем параметры из фрагмента
    fragment = parsed_url.fragment
    fragment_params = parse_qs(fragment)
    # Получаем значение параметра max_paintwear
    max_paintwear = fragment_params.get("max_paintwear", [None])[0]
    return max_paintwear


async def get_price():
    product_urls = extract_urls_with_product_id()
    save_product_urls(product_urls)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        # Загрузка куки
        await load_cookies(page, "cookies.json")
        for product_id, urls in product_urls.items():
            for url in urls:

                max_paintwear = extract_max_paintwear(url)
                filename = os.path.join(
                    price_path, f"{product_id}_{max_paintwear}.json"
                )
                if not os.path.exists(filename):

                    # # Загрузка куки
                    # await load_cookies(page, "cookies.json")

                    # Устанавливаем обработчик для сбора и сохранения данных ответов
                    async def log_response(response):
                        api_url = "https://buff.163.com/api/market/goods/sell_order"
                        request = response.request
                        if request.method == "GET" and api_url in request.url:
                            try:
                                json_response = await response.json()
                                await save_response_json_price(json_response, filename)
                            except Exception as e:
                                print(
                                    f"Ошибка при получении JSON из ответа {response.url}: {e}"
                                )

                    page.on("response", log_response)

                    await page.goto(url)
                    await asyncio.sleep(30)

                    # Удаление обработчика после использования
                    page.remove_listener("response", log_response)

        await browser.close()


# def parsing_products_sell_min_price_path():
#     slices = 2
#     float_default = {
#         "(Factory New)": 0.07,
#         "(Minimal Wear)": 0.15,
#         "(Field-Tested)": 0.38,
#         "(Well-Worn)": 0.45,
#         "(Battle-Scarred)": 1.00,
#     }
#     cny_usd = 0.1375
#     folder = os.path.join(sell_min_price_path, "*.json")

#     current_directory = os.getcwd()  # Получение текущей директории

#     files_json = glob.glob(folder)
#     all_datas = []
#     for item in files_json:
#         with open(item, "r", encoding="utf-8") as f:
#             json_data = json.load(f)

#         datas_json = json_data["data"]["items"]
#         for data_json in datas_json:
#             product_id = data_json["id"]
#             sell_min_price = float(data_json["sell_min_price"])
#             product_name = data_json["name"]
#             sell_min_price = round(sell_min_price / cny_usd, 1)
#             # Поиск состояния в названии продукта
#             product_float = None
#             for condition in float_default:
#                 if condition in product_name:
#                     product_float = float_default[condition]

#             # Формирование URL с различными диапазонами min_paintwear и max_paintwear
#             base_url = (
#                 f"https://buff.163.com/goods/{product_id}?from=market#tab=selling"
#             )
#             all_urls_slice = []
#             min_paintwear = 0.15
#             max_paintwear = 0.18
#             for slice in range(1, slices + 1):
#                 all_urls_slice.append(
#                     f"{base_url}&min_paintwear={min_paintwear}&max_paintwear={max_paintwear}&page_num=1"
#                 )
#                 min_paintwear = max_paintwear
#                 max_paintwear = round(min_paintwear + 0.03, 2)

#             url = ";".join(all_urls_slice)
#             all_data = {
#                 "product_id": product_id,
#                 "product_name": product_name,
#                 "float": product_float,
#                 "sell_min_price": sell_min_price,
#                 "url": url,
#             }
#             all_datas.append(all_data)

#     filename = os.path.join(current_directory, "output_sell_min_price.json")
#     with open(filename, "w", encoding="utf-8") as file:
#         json.dump(all_datas, file, indent=4, ensure_ascii=False)

#     # Преобразование списка словарей в DataFrame
#     df = pd.DataFrame(all_datas)

#     # Запись DataFrame в Excel
#     output_file = "output_sell_min_price.xlsx"
#     df.to_excel(output_file, index=False)


def extract_urls_with_product_id():
    json_file = "output_sell_min_price.json"
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    product_urls = {}
    for item in data:
        product_id = item["product_id"]
        urls = item["url"].split(";")
        product_urls[product_id] = urls

    return product_urls


def save_product_urls(product_urls):
    temp_json_file = "temporary_product_urls.json"
    with open(temp_json_file, "w", encoding="utf-8") as file:
        json.dump(product_urls, file, indent=4, ensure_ascii=False)


# Функция для извлечения product_id и product_float из пути
def extract_product_details(item):
    pattern = r".*\\(\d+)_([\d.]+)\.json"
    match = re.match(pattern, item)
    if match:
        product_id = match.group(1)
        product_float = match.group(2)
        return product_id, product_float
    else:
        return None, None


def parsing_products_price():
    cny_usd = 0.1375

    # Загрузка данных из output_sell_min_price.json
    with open("output_sell_min_price.json", "r", encoding="utf-8") as f:
        output_data = json.load(f)
    folder = os.path.join(price_path, "*.json")

    files_json = glob.glob(folder)

    for item in files_json:
        product_id, product_float = extract_product_details(item)

        if product_id is not None and product_float is not None:
            with open(item, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            datas_json = json_data["data"]["items"][0]
            price = float(datas_json["price"])
            price = round(price / cny_usd, 1)
            # Поиск и обновление данных в output_data
            for product in output_data:
                if product["product_id"] == int(product_id):
                    product["float"] = f'{product["float"]} / {product_float}'
                    product["sell_min_price"] = f'{product["sell_min_price"]} / {price}'
                    # Удаление поля "url"
                    if "url" in product:
                        del product["url"]

    # Сохранение обновленных данных
    with open("output_sell_min_price_.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    excel_file = "output_sell_min_price.xlsx"

    df = pd.DataFrame(output_data)
    df.to_excel(excel_file, index=False)


def get_sell_min_price_path(category_group):
    filename_cookies = os.path.join(current_directory, "cookies.json")
    # Чтение куки из файла

    with open(filename_cookies, "r") as f:
        cookies_data = json.load(f)

    # Преобразование куки в формат, подходящий для requests
    cookies = {
        cookie["name"]: cookie["value"]
        for cookie in cookies_data
        if cookie["name"]
        in [
            "Device-Id",
            "Locale-Supported",
            "game",
            "session",
            "client_id",
            "display_appids_v2",
            "csrf_token",
        ]
    }

    # cookies = {
    #     "Device-Id": "bHJpA8wwPJKOJj3HrabQ",
    #     "Locale-Supported": "ru",
    #     "game": "csgo",
    #     "session": "1-Csc8USFmUznZrrAvsYcmXkrkhUdg3fFxSAnlYGz4qIGp2028358427",
    #     "client_id": "VaCQbsNDqdwhGIqoTziolw",
    #     "display_appids_v2": '"[730\\054 570]"',
    #     "csrf_token": "ImJkODY2NDZkYzc1YzdiOGU4ZmFmZjk1YzZhMTRiN2JiOTIxYjFjM2Mi.GWPRpw.gkL7-aknOHrZ5BD05MYRPM5PRi4",
    # }

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://buff.163.com/market/buy_order/to_create?game=csgo&category_group=knife&exterior=wearcategory2",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "game": "csgo",
        "category_group": category_group,
        "exterior": "wearcategory2",
        "page_size": "70",
    }
    url = "https://buff.163.com/api/market/goods/all"
    response = requests.get(
        url, params=params, cookies=cookies, headers=headers, verify=False
    )
    if response.status_code == 200:
        json_data = response.json()
        filename = os.path.join(sell_min_price_path, f"{category_group}.json")
        print(f"Файл сохранен {filename}")
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
    else:
        print(response.status_code)


# РАБОЧИЙ
# def parsing_products_sell_min_price_path():
#     slices = 2
#     float_default = {
#         "(Factory New)": 0.07,
#         "(Minimal Wear)": 0.15,
#         "(Field-Tested)": 0.38,
#         "(Well-Worn)": 0.45,
#         "(Battle-Scarred)": 1.00,
#     }
#     cny_usd = 0.1375
#     folder = os.path.join(sell_min_price_path, "*.json")

#     current_directory = os.getcwd()  # Получение текущей директории

#     files_json = glob.glob(folder)
#     all_datas = []
#     for item in files_json:
#         with open(item, "r", encoding="utf-8") as f:
#             json_data = json.load(f)

#         datas_json = json_data["data"]["items"]
#         for data_json in datas_json:
#             product_id = data_json["id"]
#             sell_min_price = float(data_json["sell_min_price"])
#             product_name = data_json["name"]
#             sell_min_price = round(sell_min_price / cny_usd, 1)
#             # Поиск состояния в названии продукта
#             product_float = None
#             for condition in float_default:
#                 if condition in product_name:
#                     product_float = float_default[condition]

#             # Формирование URL с различными диапазонами min_paintwear и max_paintwear
#             base_url = (
#                 f"https://buff.163.com/goods/{product_id}?from=market#tab=selling"
#             )
#             all_urls_slice = []
#             min_paintwear = 0.15
#             max_paintwear = 0.18
#             for slice in range(1, slices + 1):
#                 all_urls_slice.append(
#                     f"{base_url}&min_paintwear={min_paintwear}&max_paintwear={max_paintwear}&page_num=1"
#                 )
#                 min_paintwear = max_paintwear
#                 max_paintwear = round(min_paintwear + 0.03, 2)

#             url = ";".join(all_urls_slice)
#             all_data = {
#                 "product_id": product_id,
#                 "product_name": product_name,
#                 "float": product_float,
#                 "sell_min_price": sell_min_price,
#                 "url": url,
#             }
#             all_datas.append(all_data)

#     filename = os.path.join(current_directory, "output_sell_min_price.json")
#     with open(filename, "w", encoding="utf-8") as file:
#         json.dump(all_datas, file, indent=4, ensure_ascii=False)

#     # Преобразование списка словарей в DataFrame
#     df = pd.DataFrame(all_datas)


#     # Запись DataFrame в Excel
#     output_file = "output_sell_min_price.xlsx"
#     df.to_excel(output_file, index=False)
def parsing_products_sell_min_price_path():
    float_default = {
        "(Factory New)": 0.07,
        "(Minimal Wear)": 0.15,
        "(Field-Tested)": 0.38,
        "(Well-Worn)": 0.45,
        "(Battle-Scarred)": 1.00,
    }
    cny_usd = 0.1375
    folder = os.path.join(sell_min_price_path, "*.json")

    current_directory = os.getcwd()  # Получение текущей директории

    files_json = glob.glob(folder)
    all_datas = []
    for item in files_json:
        with open(item, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        datas_json = json_data["data"]["items"]
        for data_json in datas_json:
            product_id = data_json["id"]
            sell_min_price = float(data_json["sell_min_price"])
            product_name = data_json["name"]
            sell_min_price = round(sell_min_price / cny_usd, 1)
            # Поиск состояния в названии продукта
            product_float = None
            for condition in float_default:
                if condition in product_name:
                    product_float = float_default[condition]

            # Формирование URL с различными диапазонами min_paintwear и max_paintwear
            all_data = {
                "product_id": product_id,
                "product_name": product_name,
                "float": product_float,
                "sell_min_price": sell_min_price,
            }
            all_datas.append(all_data)

    filename = os.path.join(current_directory, "output_sell_min_price.json")
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(all_datas, file, indent=4, ensure_ascii=False)

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Запись DataFrame в Excel
    output_file = "output_sell_min_price.xlsx"
    df.to_excel(output_file, index=False)


if __name__ == "__main__":
    # asyncio.run(get_cookies())
    # category_group = str(input("Введите категорию:  "))
    # get_sell_min_price_path(category_group)
    parsing_products_sell_min_price_path()
# asyncio.run(get_cookies())
# asyncio.run(get_sell_min_price_path())
#
# asyncio.run(get_price())


# #     parsing_products_price()
# while True:
#     print(
#         "Введите 1 для получения куки"
#         "\nВведите 2 для запуска первого скрипта"
#         "\nВведите 3 для запуска второго скрипта"
#         "\nВведите 0 для закрытия программы"
#     )
#     user_input = int(input("Выберите действие: "))
#     if user_input == 1:
#         asyncio.run(get_cookies())
#     elif user_input == 2:
#         # url = str((input("Вставьте ссылку на срипт 1: ")))
#         # asyncio.run(get_sell_min_price_path(url))
#         slices = 1
#         parsing_products_sell_min_price_path()
#     elif user_input == 3:
#         asyncio.run(get_price())
#         parsing_products_price()
