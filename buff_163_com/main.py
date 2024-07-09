import glob
import requests
import pandas as pd
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import random
import time
import logging
import asyncio
import aiofiles
import sys
from playwright.async_api import async_playwright
from natsort import natsorted
import shutil


# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)

# Создание временных папок
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
sell_min_price_path = os.path.join(temp_path, "sell_min_price")
price_path = os.path.join(temp_path, "price")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(sell_min_price_path, exist_ok=True)
os.makedirs(price_path, exist_ok=True)


def load_config_cookies():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "cookies.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    # headers = config["headers"]
    # cookies = config["cookies"]

    # # Генерация строки кукисов из конфигурации
    # if "cookies" in config:
    #     cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
    #     headers["Cookie"] = cookies_str
    return config


def load_config_01():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config_01.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    # headers = config["headers"]
    # cookies = config["cookies"]

    # # Генерация строки кукисов из конфигурации
    # if "cookies" in config:
    #     cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
    #     headers["Cookie"] = cookies_str
    return config


def load_config_02():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config_02.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    # headers = config["headers"]
    # cookies = config["cookies"]

    # # Генерация строки кукисов из конфигурации
    # if "cookies" in config:
    #     cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
    #     headers["Cookie"] = cookies_str
    return config


# Функция сохранения куки
async def save_cookies(context, file_path):
    cookies = await context.cookies()
    with open(file_path, "w") as f:
        json.dump(cookies, f)


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


async def get_cookies():
    proxies = load_proxies()
    proxy_gen = proxy_generator(proxies)
    async with async_playwright() as playwright:
        proxy = next(proxy_gen)
        proxy_server = {
            "server": f"http://{proxy[0]}:{proxy[1]}",
            "username": proxy[2],
            "password": proxy[3],
        }
        print(proxy_server)
        browser = await playwright.chromium.launch(headless=False, proxy=proxy_server)
        # browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )

        # Логирование сетевых событий
        page.on("request", lambda request: print(f"Запрос: {request.url}"))
        page.on(
            "response",
            lambda response: print(f"Ответ: {response.url} - {response.status}"),
        )

        try:
            await page.goto(
                "https://buff.163.com", wait_until="networkidle", timeout=1200000
            )  # Увеличен тайм-аут до 20 минут
        except Exception as e:
            print(f"Ошибка при переходе на сайт: {e}")
            await browser.close()
            return

        await asyncio.sleep(100)  # Дождитесь завершения авторизации

        # Сохранение куки
        await save_cookies(context, "cookies.json")

        # Закрываем браузер
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


# Функция загрузки куки
async def load_cookies(page, file_path):
    with open(file_path, "r") as f:
        cookies = json.load(f)
        await page.context.add_cookies(cookies)


# Функция для проверки наличия более одного значения в колонке
def has_multiple_values(cell):
    return len(str(cell).split("/")) > 1


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Функция для второго скрипта
async def get_price():

    config = load_config_cookies()
    cny_usd = 0.1375
    # Преобразование куки в формат, подходящий для requests
    cookies = {
        cookie["name"]: cookie["value"]
        for cookie in config
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

    data_config_02 = load_config_02()
    params = data_config_02["params"][0]
    time_sleep = int(data_config_02["pause"][0]["sleep"])
    # Загрузка данных из Excel файла
    file_path = "output_sell_min_price.xlsx"
    df = pd.read_excel(file_path)
    df = pd.read_excel(file_path, dtype={"sell_min_price": str})

    # Фильтрация строк
    filtered_df = df[df["float"].apply(has_multiple_values)]

    # Создание списка словарей
    data_list = []
    for index, row in filtered_df.iterrows():
        data_list.append(
            {
                "index": index,
                "product_id": row["product_id"],
                "float": row["float"],
                "sell_min_price": row["sell_min_price"],
            }
        )

    for dl in data_list:
        index_row = dl["index"]
        product_id = dl["product_id"]
        product_floats = str(dl["float"]).split("/")  # Разделение значений
        sell_min_price = str(dl["sell_min_price"])  # Начальное значение sell_min_price

        # Вложенный цикл для обработки каждого значения 'float', начиная со второго
        for product_float in product_floats[1:]:
            # Замена запятой на точку
            product_float = product_float.replace(",", ".")

            params["max_paintwear"] = product_float  # Обновление max_paintwear
            params["goods_id"] = str(product_id)
            proxies = load_proxies()
            proxy_gen = proxy_generator(proxies)
            proxy_server = next(proxy_gen)
            # Создание строки для аутентификации
            proxy_auth = f"{proxy_server[2]}:{proxy_server[3]}@{proxy_server[0]}:{proxy_server[1]}"

            # Настройка прокси для HTTP и HTTPS
            proxies_socks5 = {
                "http": f"socks5://{proxy_auth}",
                "https": f"socks5://{proxy_auth}",
            }
            proxies_http = {
                "http": f"http://{proxy_auth}",
                "https": f"http://{proxy_auth}",
            }
            # if check_proxy(proxies):
            response = requests.get(
                "https://buff.163.com/api/market/goods/sell_order",
                params=params,
                cookies=cookies,
                headers=headers,
                proxies=proxies_http,
            )
            if response.status_code == 200:
                json_data = response.json()
                try:
                    datas_json = json_data["data"]["items"][0]
                except:
                    datas_json = json_data["error"]
                    print(datas_json)
                    continue

                datas_json = json_data["data"]["items"]

                price = float(datas_json["price"])
                price = round(price * cny_usd, 1)

                # Добавление цены к sell_min_price
                sell_min_price += f"/{price}"
            # else:
            #     print("Прокси-сервер недоступен. Пожалуйста, попробуйте другой прокси.")

            time.sleep(time_sleep)

        # Обновление sell_min_price в data_list
        dl["sell_min_price"] = sell_min_price

    # Обновление значений в DataFrame
    for dl in data_list:
        df.at[dl["index"], "sell_min_price"] = dl["sell_min_price"]

    # Сохранение обновленного DataFrame обратно в Excel файл
    updated_file_path = "output_sell_min_price_updated.xlsx"
    df.to_excel(updated_file_path, index=False)

    print(f"Обновленные данные сохранены в файл: {updated_file_path}")


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


def check_proxy(proxy):
    try:
        test_url = "http://httpbin.org/ip"
        response = requests.get(test_url, proxies=proxy, timeout=10)
        if response.status_code == 200:
            ip = response.json().get("origin")
            print(f"Прокси-сервер доступен. Ваш IP: {ip}")
            return True
        else:
            print("Не удалось получить IP-адрес через прокси.")
            return False
    except requests.RequestException as e:
        print(f"Ошибка при проверке прокси: {e}")
        return False


# Функция первого скрипта
def get_sell_min_price_path():

    data_config_01 = load_config_01()
    params = data_config_01["params"][0]
    category_group = data_config_01["params"][0]["category_group"]
    total_pages = data_config_01["total_pages"][0]["pages"]
    time_sleep = int(data_config_01["pause"][0]["sleep"])
    config = load_config_cookies()
    # Фильтрация куки по заданным именам
    cookies = {
        cookie["name"]: cookie["value"]
        for cookie in config
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

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for page_num in range(1, total_pages + 1):
        # Обновление значения page_num в params
        params["page_num"] = str(page_num)
        url = "https://buff.163.com/api/market/goods/all"
        # print(params, cookies, headers)
        # exit()
        proxies = load_proxies()
        proxy_gen = proxy_generator(proxies)
        proxy_server = next(proxy_gen)
        # Создание строки для аутентификации
        proxy_auth = (
            f"{proxy_server[2]}:{proxy_server[3]}@{proxy_server[0]}:{proxy_server[1]}"
        )

        proxies_socks5 = {
            "http": f"socks5://{proxy_auth}",
            "https": f"socks5://{proxy_auth}",
        }
        proxies_http = {"http": f"http://{proxy_auth}", "https": f"http://{proxy_auth}"}
        # if check_proxy(proxies):
        try:
            response = requests.get(
                url,
                params=params,
                cookies=cookies,
                headers=headers,
                proxies=proxies_http,
                verify=False,
            )
            category_group_path = os.path.join(sell_min_price_path, category_group)
            os.makedirs(category_group_path, exist_ok=True)
            filename = os.path.join(category_group_path, f"0{page_num}.json")
            if response.status_code == 200:
                json_data = response.json()

                with open(filename, "w", encoding="utf-8") as file:
                    json.dump(json_data, file, indent=4, ensure_ascii=False)
                logging.info(f"Файл сохранен {filename}")
                time.sleep(time_sleep)
            else:
                print(response.status_code)
            # Обработка ответа
        except requests.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
        # else:
        #     print("Прокси-сервер недоступен. Пожалуйста, попробуйте другой прокси.")


# Функция для получения даты создания папки
def get_creation_time(path):
    return os.path.getctime(path)


def delete_all_in_directory():
    """
    Удаляет все подкаталоги и файлы в указанной папке без подтверждения.
    """
    for root, dirs, files in os.walk(sell_min_price_path):
        for name in files:
            file_path = os.path.join(root, name)
            os.remove(file_path)
        for name in dirs:
            dir_path = os.path.join(root, name)
            shutil.rmtree(dir_path)


# Функция формирование ексель файла
def parsing_products_sell_min_price_path():
    # Загрузка данных из Excel файла
    file_path = "output_sell_min_price.xlsx"

    # Проверка наличия файла
    if os.path.exists(file_path):
        # Загрузка данных из Excel файла
        df_start = pd.read_excel(file_path, dtype={"sell_min_price": str})

        # Установка 'product_id' в качестве индекса
        df_start.set_index("product_id", inplace=True)
    else:
        # Если файла нет, выводим сообщение
        print(f"Файл {file_path} не найден.")
        df_start = pd.DataFrame(
            columns=["product_id", "product_name", "float", "sell_min_price"]
        )
        df_start.set_index("product_id", inplace=True)

    float_default = {
        "(Factory New)": 0.07,
        "(Minimal Wear)": 0.15,
        "(Field-Tested)": 0.38,
        "(Well-Worn)": 0.45,
        "(Battle-Scarred)": 1.00,
    }
    cny_usd = 0.1375

    # Список для хранения всех найденных JSON файлов
    all_json_files = []

    # Получаем список всех подкаталогов
    subdirs = [
        os.path.join(sell_min_price_path, d)
        for d in os.listdir(sell_min_price_path)
        if os.path.isdir(os.path.join(sell_min_price_path, d))
    ]

    # Сортируем подкаталоги по дате создания
    subdirs.sort(key=get_creation_time)

    all_datas = []

    # Проход по всем подкаталогам в порядке их создания
    for subdir in subdirs:
        logging.info(subdir)
        # Использование glob для поиска всех JSON файлов в текущем каталоге
        json_files = glob.glob(os.path.join(subdir, "*.json"))
        json_files = natsorted(json_files)

        # Обработка всех найденных JSON файлов
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                logging.info(f"Processing file: {json_file}")

                datas_json = json_data.get("data", {}).get("items", [])
                if not datas_json:
                    datas_json = json_data.get("error", [])
                    print(f"Error in file {json_file}: {datas_json}")

                for data_json in datas_json:
                    product_id = data_json["id"]
                    sell_min_price = float(data_json["sell_min_price"])
                    product_name = data_json["name"]
                    sell_min_price = round(sell_min_price * cny_usd, 1)

                    # Поиск состояния в названии продукта
                    product_float = None
                    for condition in float_default:
                        if condition in product_name:
                            product_float = float_default[condition]
                            break  # Выход из цикла, если состояние найдено

                    # Формирование данных для записи
                    if product_id in df_start.index:
                        existing_sell_min_price = df_start.loc[
                            product_id, "sell_min_price"
                        ]
                        parts = existing_sell_min_price.split("/", 1)
                        new_sell_min_price = (
                            f"{sell_min_price}/{parts[1]}"
                            if len(parts) > 1
                            else str(sell_min_price)
                        )
                    else:
                        new_sell_min_price = str(sell_min_price)
                    all_data = {
                        "product_id": product_id,
                        "product_name": product_name,
                        "float": product_float,
                        "sell_min_price": new_sell_min_price,
                    }
                    all_datas.append(all_data)

            except json.JSONDecodeError as e:
                logging.info(f"JSONDecodeError in file {json_file}: {e}")
            except Exception as e:
                logging.info(f"Error processing file {json_file}: {e}")

    # Преобразование списка словарей в DataFrame
    df_finish = pd.DataFrame(all_datas)

    # Установка 'product_id' в качестве индекса для df_finish
    df_finish.set_index("product_id", inplace=True)

    if df_start.empty:
        # Если df_start пустой, просто сохраняем df_finish в файл
        df_finish.reset_index(inplace=True)
        df_finish.to_excel(file_path, index=False)
    else:
        # Обновление df_start данными из df_finish по product_id и добавление новых данных
        for product_id in df_finish.index:
            if product_id in df_start.index:
                existing_sell_min_price = df_start.loc[product_id, "sell_min_price"]
                parts = existing_sell_min_price.split("/", 1)
                # Заменяем только первую часть строки
                new_sell_min_price = (
                    f"{df_finish.at[product_id, 'sell_min_price']}"
                    if len(parts) > 1
                    else str(df_finish.at[product_id, "sell_min_price"])
                )
                logging.info(
                    f"{product_id}, {existing_sell_min_price}, {new_sell_min_price}"
                )
                df_start.at[product_id, "sell_min_price"] = new_sell_min_price
                df_start.at[product_id, "product_name"] = df_finish.at[
                    product_id, "product_name"
                ]
                df_start.at[product_id, "float"] = df_finish.at[product_id, "float"]
            else:
                df_start.loc[product_id] = df_finish.loc[product_id]

        # Сброс индекса для df_start (если необходимо)
        df_start.reset_index(inplace=True)

        # Сохранение обновленного DataFrame обратно в Excel файл
        df_start.to_excel(file_path, index=False)


# #     parsing_products_price()
while True:
    print(
        "Введите 1 для получения куки"
        "\nВведите 2 для запуска первого скрипта"
        "\nВведите 3 для запуска формирования xlsx файла"
        "\nВведите 4 для запуска второго скрипта"
        "\nВведите 5 удалить временные файлы"
    )
    user_input = int(input("Выберите действие: "))
    if user_input == 1:
        asyncio.run(get_cookies())
    elif user_input == 2:
        get_sell_min_price_path()
    elif user_input == 3:
        parsing_products_sell_min_price_path()
    elif user_input == 4:
        asyncio.run(get_price())
    elif user_input == 5:
        delete_all_in_directory()
