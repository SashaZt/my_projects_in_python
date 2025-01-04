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
import threading
from functions.authorization import start_file_check


# Создание временных папок
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
json_product = os.path.join(temp_path, "json_product")
json_list = os.path.join(temp_path, "json_list")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(json_product, exist_ok=True)
os.makedirs(json_list, exist_ok=True)

# Получение текущей рабочей директории
log_directory = os.getcwd()
log_file_path = os.path.join(log_directory, "info_{time:YYYY-MM-DD_HH-mm-ss}.log")

logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="1 hour",  # Ротация каждый час
    retention="7 days",  # Сохранять логи в течение 7 дней
    compression="zip",  # Архивация старых логов
    enqueue=True,  # Безопасная очередь для ротации
    backtrace=True,  # Включение трассировки для подробных логов
)

logger.info("Логирование настроено и работает корректно.")


# Загрузка конфига
def get_config():

    # Загрузка данных из файла config.json
    with open("config.json", "r") as file:
        config_data = json.load(file)

    # Получение данных из загруженного JSON
    price_range_from = config_data["price_range"]["price_range_from"]
    price_range_to = config_data["price_range"]["price_range_to"]
    return price_range_from, price_range_to


# Загрузка конфига
def get_authorization():
    start_file_check()
    # Загрузка данных из файла authorization.json
    destination_file_path = os.path.join(os.getcwd(), "authorization.json")
    with open(destination_file_path, "r") as file:
        config_data = json.load(file)

    # Получение данных из загруженного JSON
    authorization = config_data["Authorization"]
    return authorization


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
    for offer_id in list_offer_id:
        authorization = get_authorization()
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
        url = "https://sls.g2g.com/offer/"
        filename_to_check = os.path.join(json_product, f"{offer_id}_params.json")
        data_json = None

        filename_to_check = os.path.join(json_product, f"{offer_id}_params.json")
        data_json = None

        # Проверка наличия файла
        # if not os.path.exists(filename_to_check):
        response = requests.get(f"{url}{offer_id}", params=params, headers=headers)
        data_json = response.json()
        filename_all_data, filename_params = receiving_data(data_json)
        if filename_params is None:
            print(f"ПРОВЕРИТЬ {offer_id}!!!")
            continue
        # time.sleep(1)
        # else:
        #     filename_params = filename_to_check

        # Выполняем оставшиеся функции в любом случае
        filename_list = get_list_product(filename_params)
        price_study(filename_list, authorization)


# Парсинг json продуктов
def receiving_data(data):
    try:
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
    except KeyError as e:
        logger.critical(f"Проверь товар: отсутствует ключ {e}")
        return None, None
    except Exception as e:
        logger.critical(f"Произошла ошибка: {e}")
        return None, None


# Получение списка конкурентов
def get_list_product(filename_params):
    # authorization = get_authorization()

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        # "authorization": authorization,
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
    price_range_from, price_range_to = get_config()
    price_rang = random.uniform(price_range_to, price_range_from)
    price_rang = round(price_rang, 6)
    return price_rang


# Проверка цены конкурентов
def price_study(filename_list, authorization):
    filename = filename_list.split("\\")[-1]  # Получаем последнюю часть пути
    identifier = filename.split("_")[0]  # Разделяем по '_' и берем первую часть
    with open(filename_list, encoding="utf-8") as f:
        data = json.load(f)

    # try:
    #     with open(filename_list, encoding="utf-8") as f:
    #         data = json.load(f)

    #     # Используем метод get с указанием значений по умолчанию
    #     payload = data.get("payload", {})
    #     results = payload.get("results", [])

    #     if results:
    #         json_data = results[0]
    #     else:
    #         json_data = None

    # except FileNotFoundError:
    #     logger.info(f"Файл {filename_list} не найден.")
    #     json_data = None
    # except json.JSONDecodeError:
    #     logger.info("Ошибка декодирования JSON.")
    #     json_data = None
    # except Exception as e:
    #     logger.info(f"Произошла ошибка: {e}")
    #     json_data = None
    # try:
    #     username = json_data["username"]
    # except:
    #     return
    # try:
    #     title = json_data["title"]
    # except:
    #     return
    # unit_price = float(json_data["unit_price"])
    # if username != "Allbestfory":
    #     unit_price = float(json_data["unit_price"])
    #     if unit_price > 999:
    #         unit_price = float(json_data["display_price"])
    try:
        with open(filename_list, encoding="utf-8") as f:
            data = json.load(f)

        # Используем метод get с указанием значений по умолчанию
        payload = data.get("payload", {})
        results = payload.get("results", [])

        if not results:
            return None

        for i in range(min(2, len(results))):  # Обходим не более двух результатов
            json_data = results[i]

            try:
                username = json_data["username"]
                title = json_data["title"]
                unit_price = float(json_data["unit_price"])
            except KeyError as e:
                logger.info(f"Ключ {e} отсутствует в JSON.")
                return None
            except ValueError:
                logger.info("Ошибка преобразования значения в float.")
                return None

            if username != "Allbestfory":
                if unit_price > 999:
                    unit_price = float(json_data["display_price"])
                elif unit_price < 1:
                    logger.info("Цена меньше 1, пробуем следующий элемент.")
                    continue  # Переходим к следующему элементу в results

                # Изменяем цену
                price_rang = get_random_price_range()
                new_price = unit_price - price_rang
                new_price = round(new_price, 6)
                logger.info(f"Цена {unit_price} конкурента {username} на товар {title}")
                price_change_request(identifier, new_price, authorization)
                # return  # Завершаем выполнение после успешного изменения цены

        # Если Allbestfory первый в списке
        logger.info(f"Allbestfory первый в списке товара {identifier}")

    except FileNotFoundError:
        logger.info(f"Файл {filename_list} не найден.")
    except json.JSONDecodeError:
        logger.info("Ошибка декодирования JSON.")
    except Exception as e:
        logger.info(f"Произошла ошибка: {e}")


# Изменение цены
def price_change_request(identifier, new_price, authorization):
    # authorization = get_authorization()
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
    else:
        now = datetime.now()
        logger.critical(f"Проверь товар {identifier}")
        logger.critical(f"{response.status_code}  в {formatted_datetime}")
        logger.critical("ОБНОВИ authorization !!!!!")


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
