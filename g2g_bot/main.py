import requests
import json
import os
import requests
import requests
import os
import json
from urllib.parse import urlencode
import time
import glob
import re
import random
from loguru import logger
from datetime import datetime, timedelta
import csv
from playwright.async_api import async_playwright
import asyncio


# Создание временных папок
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
json_product = os.path.join(temp_path, "json_product")
json_list = os.path.join(temp_path, "json_list")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(json_product, exist_ok=True)
os.makedirs(json_list, exist_ok=True)

logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",  # Формат сообщения
    level="DEBUG",  # Уровень логирования
    encoding="utf-8",  # Кодировка
    mode="w",  # Перезапись файла при каждом запуске
)


# Загрузка конфига
def get_config():

    # Загрузка данных из файла config.json
    with open("config.json", "r") as file:
        config_data = json.load(file)

    # Получение данных из загруженного JSON
    authorization = config_data["headers"]["authorization"]
    price_range_from = config_data["price_range"]["price_range_from"]
    price_range_to = config_data["price_range"]["price_range_to"]
    return authorization, price_range_from, price_range_to


# Получение списка offer_id
def get_offer_id():
    # Открытие CSV файла и чтение данных
    all_data = []
    with open("offer_id.csv", newline="") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            all_data.append(row[0])
    return all_data


# Получение товаров
def get_product(list_offer_id):
    authorization, price_range_from, price_range_to = get_config()
    # list_offer_id = get_offer_id()
    # list_offer_id = ["G1712365749453ZN", "G1711459979838ZA"]
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": authorization,
        "origin": "https://www.g2g.com",
        "priority": "u=1, i",
        "referer": "https://www.g2g.com/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    params = {
        "currency": "USD",
        "country": "UA",
        "include_out_of_stock": "1",
        "include_inactive": "1",
    }
    for offer_id in list_offer_id:
        url = "https://sls.g2g.com/offer/"
        filename_to_check = os.path.join(json_product, f"{offer_id}_params.json")
        data_json = None

        filename_to_check = os.path.join(json_product, f"{offer_id}_params.json")
        data_json = None

        # Проверка наличия файла
        if not os.path.exists(filename_to_check):
            response = requests.get(f"{url}{offer_id}", params=params, headers=headers)
            data_json = response.json()
            filename_all_data, filename_params = receiving_data(data_json)
            # time.sleep(1)
        else:
            filename_params = filename_to_check

        # Выполняем оставшиеся функции в любом случае
        filename_list = get_list_product(filename_params)
        price_study(filename_list)


# Парсинг json продуктов
def receiving_data(data):
    json_data = data["payload"]
    offer_id = json_data["offer_id"]
    unit_price = json_data["unit_price"]
    title = json_data["title"]
    pattern = r"\*([^*]+)\*"
    matches = re.findall(pattern, title)
    q = matches[0]
    service_id = json_data["service_id"]
    brand_id = json_data["brand_id"]
    seo_term = None
    if brand_id == "lgc_game_29076":
        seo_term = "wow-classic-item"
    elif brand_id == "lgc_game_27816":
        seo_term = "wow-classic-era-item"
    region_id = json_data["region_id"]
    filter_attr_row = json_data["offer_attributes"][1]
    collection_id = filter_attr_row["collection_id"]
    dataset_id = filter_attr_row["dataset_id"]
    filter_attr = f"{collection_id}:{dataset_id}"
    all_data = {
        "offer_id": offer_id,
        "unit_price": unit_price,
    }
    params = {
        "seo_term": seo_term,
        "region_id": region_id,
        "q": q,
        "filter_attr": filter_attr,
    }
    filename_all_data = os.path.join(json_product, f"{offer_id}_all_data.json")
    with open(filename_all_data, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    filename_params = os.path.join(json_product, f"{offer_id}_params.json")
    with open(filename_params, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=4)
    # logger.info(f"Сохранил данные товара {offer_id}")
    return filename_all_data, filename_params


# Получение списка конкурентов
def get_list_product(filename_params):
    authorization, price_range_from, price_range_to = get_config()

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": authorization,
        "origin": "https://www.g2g.com",
        "priority": "u=1, i",
        "referer": "https://www.g2g.com/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    filename = filename_params.split("\\")[-1]  # Получаем последнюю часть пути
    identifier = filename.split("_")[0]  # Разделяем по '_' и берем первую часть
    with open(filename_params, encoding="utf-8") as f:
        params = json.load(f)
    # Добавление новых значений в словарь
    params["page_size"] = 48
    params["sort"] = "lowest_price"
    params["currency"] = "USD"
    params["country"] = "UA"
    base_url = "https://sls.g2g.com/offer/search"
    # Создание полного URL с параметрами
    encoded_params = urlencode(params)
    full_url = f"{base_url}?{encoded_params}"
    response = requests.get(
        full_url,
        headers=headers,
    )
    json_data = response.json()
    filename_list = os.path.join(json_list, f"{identifier}_list.json")
    with open(filename_list, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    # time.sleep(1)
    # logger.info(f"Сохранил данные списка по товару {identifier}")
    return filename_list


# Случайная цена
def get_random_price_range():
    authorization, price_range_from, price_range_to = get_config()
    # price_range_from = 0.005
    # price_range_to = 0.001
    price_rang = random.uniform(price_range_to, price_range_from)
    price_rang = round(price_rang, 3)
    return price_rang


# Проверка цены конкурентов
def price_study(filename_list):
    filename = filename_list.split("\\")[-1]  # Получаем последнюю часть пути
    identifier = filename.split("_")[0]  # Разделяем по '_' и берем первую часть
    with open(filename_list, encoding="utf-8") as f:
        data = json.load(f)
    json_data = data["payload"]["results"][0]
    username = json_data["username"]
    title = json_data["title"]
    if username != "Allbestfory":
        unit_price = float(json_data["unit_price"])

        price_rang = get_random_price_range()
        new_price = unit_price - price_rang
        new_price = round(new_price, 3)
        logger.info(f"Цена {unit_price} конкурента {username}на товар {title}")
        price_change_request(identifier, new_price)
    else:
        logger.info(f"Allbestfory первый в списке товара {identifier}")


# Изменение цены
def price_change_request(identifier, new_price):
    authorization, price_range_from, price_range_to = get_config()
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": authorization,
        "content-type": "application/json",
        "priority": "u=1, i",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    json_data = {
        "unit_price": new_price,
        "seller_id": "5688923",
    }

    response = requests.put(
        f"https://sls.g2g.com/offer/{identifier}", headers=headers, json=json_data
    )
    now = datetime.now()
    # Форматирование даты и времени
    formatted_datetime = now.strftime("%H:%M:%S %d.%m.%Y")
    if response.status_code == 200:

        logger.info(f"Установили новую цену {new_price} на товар {identifier}")
        # time.sleep(30)
    else:
        now = datetime.now()
        logger.critical(f"Проверь товар {identifier}")
        logger.critical(f"{response.status_code}  в {formatted_datetime}")
        logger.critical("ОБНОВИ authorization !!!!!")


async def main_get_cookies():
    url = "https://www.g2g.com/login"
    timeout_selector = 10000
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

        # Логирование сетевых событий
        page.on("request", lambda request: print(f"Запрос: {request.url}"))
        page.on(
            "response",
            lambda response: print(f"Ответ: {response.url} - {response.status}"),
        )

        # Устанавливаем обработчик для сбора и сохранения данных ответов
        def create_log_response_with_counter():
            async def log_response(response):
                api_url = "ttps://sls.g2g.com/offer/search_result_count"
                request = response.request
                print(request)
                if (
                    request.method == "GET" and api_url in request.url
                ):  # Подставьте актуальное условие URL
                    try:
                        json_response = await response.json()
                        # await save_response_json(json_response, url_name)

                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response

        await page.goto(url)  # Замените URL на актуальный
        await asyncio.sleep(1)
        # Ввод данных в поле username
        await page.fill("input[data-attr='username-input']", "palpatin031@gmail.com")

        # Ввод данных в поле password
        await page.fill("input[type='password']", "Gaetepke29)1")

        # Нажатие на кнопку Login
        login_button = page.locator(
            "span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row:has-text('Login')"
        )
        await login_button.click()
        await asyncio.sleep(45)
        # Сохранение куки
        await save_cookies(context, "cookies.json")
        # Итерация по страницам
        handler = create_log_response_with_counter()
        page.on("response", handler)
        await asyncio.sleep(1)
        await browser.close()


# if __name__ == "__main__":
#     asyncio.run(main())
#     get_offer_id()
#     get_product()
#     get_list_product()
#     price_study()


if __name__ == "__main__":
    while True:
        # Получение текущей даты и времени
        now = datetime.now()
        # Форматирование даты и времени
        formatted_datetime = now.strftime("%H:%M:%S %d.%m.%Y")
        logger.info(f"Начинаем проверять в {formatted_datetime}")

        list_offer_id = get_offer_id()
        get_product(list_offer_id)

        # get_list_product()

        # price_study()
        # Добавление 5 минут
        future_time = now + timedelta(minutes=5)
        # Форматирование даты и времени
        formatted_datetime = future_time.strftime("%H:%M:%S %d.%m.%Y")
        logger.info(f"Закончили проверять, продолжим в {formatted_datetime}")
        # time.sleep(300)  # Пауза на 5 минут (300 секунд)
