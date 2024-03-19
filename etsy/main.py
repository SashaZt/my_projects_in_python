import getpass
import glob
import json
import os
import random
import re
import shutil
import time
import sys
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials


current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
json_path = os.path.join(temp_path, "json")
json_product = os.path.join(temp_path, "json_product")
json_tags = os.path.join(temp_path, "json_tags")
json_statistic = os.path.join(temp_path, "json_statistic")
html_path = os.path.join(temp_path, "html")


"""
Функция читает файл конфигурации из внешнего файла
Применимо даже при формирование exe файла
"""


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")

    with open(filename_config, "r") as config_file:
        config = json.load(config_file)

    return config


"""
Функция читает файл cookies из внешнего файла
Применимо даже при формирование exe файла
"""


def get_cookies():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_cookies = os.path.join(application_path, "cookies.json")

    with open(filename_cookies, "r", encoding="utf-8") as f:
        data_json = json.load(f)

    shops_json = data_json["shops"]
    shops_cookies = []

    for s in shops_json:
        # Собираем информацию о каждом магазине
        shop_info = {"id_shop": s["id_shop"], "cookies": s["cookies"]}
        # Добавляем информацию о магазине в список
        shops_cookies.append(shop_info)

    # Возвращаем список с информацией о всех магазинах и их cookies
    return shops_cookies


"""
Функция читает файл access.json из внешнего файла
Применимо даже при формирование exe файла
"""


def get_google():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    creds_file = os.path.join(application_path, "access.json")
    config = load_config()
    spreadsheet_id = config.get("spreadsheet_id", "")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


"""
Функция для создание временных директорий
"""


def creative_temp_folders():
    for folder in [temp_path, json_path, json_product, json_tags, json_statistic]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    shops_cookies = get_cookies()
    for s in shops_cookies:
        shop = s["id_shop"]
        for folder in [json_path, json_product, json_tags, json_statistic]:
            shop_folder = os.path.join(folder, shop)
            if not os.path.exists(shop_folder):
                os.makedirs(shop_folder)


"""
Функция для удаление временных директорий
"""


def delete_temp_directory():
    # Проверка существования директории и её удаление
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        try:
            shutil.rmtree(temp_path)
            print(f"The directory {temp_path} has been deleted successfully.")
        except Exception as e:
            print(f"Failed to delete the directory {temp_path}. Reason: {e}")
    else:
        print(f"The directory {temp_path} does not exist or is not a directory.")


"""
Убираем знаки пунктуации и разбиваем по пробелам, приводя всё к нижнему регистру
"""


def split_into_words(text):
    return re.findall(r"\b\w+\b", text.lower())


"""
Получаем файлы статистики
"""


def get_page_statistic(date_range):
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")
    shops_cookies = get_cookies()
    for s in shops_cookies:
        shop = s["id_shop"]
        print(f"Збираємо статистику з магазину {shop}")
        cookies = s["cookies"]
        params = {
            "date_range": date_range,
            "channel": "etsy-retail",
            "limit": "5",
            "offset": "0",
            "sort_direction": "DESC",
            "sort_by": "visits",
            "selected_listings_filter": "all",
        }
        filename_tender_statistic = os.path.join(json_statistic, shop, "statistic.json")
        if not os.path.exists(filename_tender_statistic):
            response = requests.get(
                f"https://www.etsy.com/api/v3/ajax/bespoke/shop/{shop}/shop-analytics-stats/listings",
                params=params,
                cookies=cookies,
                headers=headers,
            )
            json_data = response.json()
            if json_data.get("error"):
                print(f"Помилка в магазині {shop} - {json_data.get('error')}")
                print(f"Перевірте кукі магазину {shop}!!!!!!!!!!!!!!!!!!!!!!!")
                continue
            else:
                with open(filename_tender_statistic, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
        with open(filename_tender_statistic, "r", encoding="utf-8") as f:
            data_json = json.load(f)
        json_data = data_json
        pagination = json_data.get("pagination", None)
        pages = int(pagination.get("total_pages", None))
        print(f"Всього сторінок {pages}")
        pages = pages + 1
        offset = 5
        for _ in range(2, pages):
            params = {
                "date_range": date_range,
                "channel": "etsy-retail",
                "limit": "5",
                "offset": offset,
                "sort_direction": "DESC",
                "sort_by": "visits",
                "selected_listings_filter": "all",
            }
            filename_tender_statistic = os.path.join(
                json_statistic, shop, f"statistic_{offset}.json"
            )
            if not os.path.exists(filename_tender_statistic):
                response = requests.get(
                    f"https://www.etsy.com/api/v3/ajax/bespoke/shop/{shop}/shop-analytics-stats/listings",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()
                with open(filename_tender_statistic, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                sleep_time = random.randint(time_a, time_b)
                # print(f'Сторінка {p}')

                time.sleep(sleep_time)
            offset += 5


"""
Получаем файлы товаров
"""


def get_product(date_range):
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")
    shops_cookies = get_cookies()
    for s in shops_cookies:
        shop = s["id_shop"]
        all_products_keys = parsing_statistic(shop)
        print(f"Збираємо продукти з магазину {shop}")
        cookies = s["cookies"]
        for a in all_products_keys:
            params = {"date_range": date_range, "channel": "etsy-retail"}
            product = a
            filename_tender = os.path.join(
                json_product, shop, f"product_{product}.json"
            )
            if not os.path.exists(filename_tender):
                response = requests.get(
                    f"https://www.etsy.com/api/v3/ajax/bespoke/shop/{shop}/stats/dashboard-listing/{product}",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()
                with open(filename_tender, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                sleep_time = random.randint(time_a, time_b)
                time.sleep(sleep_time)


"""
Получаем файлы тегов
"""


def get_tags():
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")
    shops_cookies = get_cookies()
    for s in shops_cookies:

        shop = s["id_shop"]
        print(f"Збираємо теги з магазину {shop}")
        search_pattern = os.path.join(json_product, shop, "product_*.json")
        matching_files = glob.glob(search_pattern)
        # Подсчёт количества найденных файлов
        number_of_files = (len(matching_files) // 40) + 1
        cookies = s["cookies"]
        offset = 0
        for p in range(0, number_of_files):
            params = {
                "limit": "40",
                "offset": offset,
                "sort_field": "ending_date",
                "sort_order": "descending",
                "state": "active",
                "language_id": "0",
                "query": "",
                "shop_section_id": "",
                "listing_tag": "",
                "is_featured": "",
                "shipping_profile_id": "",
                "return_policy_id": "",
                "production_partner_id": "",
                "is_retail": "true",
                "is_retail_only": "",
                "is_pattern": "",
                "is_pattern_only": "",
                "is_digital": "",
                "channels": "",
                "is_waitlisted": "",
                "has_video": "",
            }
            filename_tender = os.path.join(json_tags, shop, f"tags_{offset}.json")
            if not os.path.exists(filename_tender):
                response = requests.get(
                    f"https://www.etsy.com/api/v3/ajax/shop/{shop}/listings/search",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                json_data = response.json()

                # Проверяем, является ли json_data словарем и нет ли в нем ключа "error"
                if isinstance(json_data, dict) and "error" not in json_data:
                    with open(filename_tender, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
                elif isinstance(json_data, dict) and "error" in json_data:
                    # Если json_data является словарем и содержит ключ "error"
                    error_message = json_data["error"]
                    print(f"Помилка в магазині {shop} - {error_message}")
                    print(f"Перевірте кукі магазину {shop}!!!!!!!!!!!!!!!!!!!!!!!")
                else:
                    # Если json_data не является словарем (например, является списком), сохраняем его
                    with open(filename_tender, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)

                    
                sleep_time = random.randint(time_a, time_b)
                time.sleep(sleep_time)
            offset += 40

def safe_get(dct, keys, default=None):
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError, IndexError):
            return default
    return dct
"""
Парсим файлы товаров
"""


def pars_product():
    config = load_config()
    spreadsheet_id = config.get("spreadsheet_id", "")
    shops_cookies = get_cookies()
    for s in shops_cookies:
        shop = s["id_shop"]
        
        filename_tender = os.path.join(json_product, shop, "product*.json")
        filenames = glob.glob(filename_tender)
        all_objects = []
        all_tags = par_tags(shop)
        if not filenames:
            print(f"Даних по магазину {shop} немає")
        else:
            print(f"Завантажуємо інформацію по магазину {shop} в Google таблицю")
            for filename in filenames:
                # print(filename)
                with open(filename, "r", encoding="utf-8") as f:
                    data_json = json.load(f)
                    # Ваш код с использованием безопасного извлечения
                    json_data = data_json.get("pages", [])

                    # Безопасное извлечение данных по списку ключей
                    listing_id = safe_get(json_data, [0, "list", 0, "stacked_graphs_view", 0, "inventory_detail", "datasets", 0, "entries", 0, "listing", "listing_id"], None)
                    listing_title = safe_get(json_data, [0, "list", 0, "stacked_graphs_view", 0, "inventory_detail", "datasets", 0, "entries", 0, "listing", "title"], None)
                    img_url = safe_get(json_data, [0, "list", 0, "stacked_graphs_view", 0, "inventory_detail", "datasets", 0, "entries", 0, "listing", "image", "url"], None)
                    url_product = safe_get(json_data, [0, "list", 0, "stacked_graphs_view", 0, "inventory_detail", "datasets", 0, "entries", 0, "listing", "url"], None)

                    all_data_table_01_data = safe_get(json_data, [0, "list", 2, "filters", 0, "options"], [])
                    all_data_table_02_data = safe_get(json_data, [0, "list", 3, "stacked_graphs_view", 0, "donut_chart", "datasets", 0, "entries"], [])
                    paginated_view = safe_get(json_data, [0, "list", 4, "paginated_view"], [])

                    # Использование безопасного извлечения данных для словарей таблиц
                    dict_table_01 = {entry.get("label"): entry.get("total", "").replace("USD ", "").replace(".", ",") for entry in all_data_table_01_data}
                    dict_table_02 = {entry.get("label"): entry.get("value") for entry in all_data_table_02_data}
                    dict_table_03 = {}

                    for item in paginated_view:
                        entries = safe_get(item, ["horizontal_line_chart", "datasets", 0, "entries"], [])
                        for entry in entries:
                            label = entry.get("label")
                            value = entry.get("value")
                            if label is not None and value is not None:
                                dict_table_03[label] = value

                    # Формирование итогового объекта
                    img_url_for_google = f'=IMAGE("{img_url}")' if img_url else None
                    current_object = {
                        "object": {
                            "listing_id": listing_id,
                            "title": listing_title,
                            "img_url_for_google": img_url_for_google,
                            "url_product": url_product,
                        },
                        "dict_table_01": dict_table_01,
                        "dict_table_02": dict_table_02,
                        "dict_table_03": dict_table_03,
                    }

                    all_objects.append(current_object)
                
                
                

                
                # json_data = data_json["pages"]
                # listing_id = json_data[0]["list"][0]["stacked_graphs_view"][0]["inventory_detail"
                # ]["datasets"][0]["entries"][0]["listing"]["listing_id"]
                # listing_title = json_data[0]["list"][0]["stacked_graphs_view"][0][
                #     "inventory_detail"
                # ]["datasets"][0]["entries"][0]["listing"]["title"]

                # # Данные по таблицам

                # all_data_table_01_data = json_data[0]["list"][2]["filters"][0]["options"]
                # all_data_table_02_data = json_data[0]["list"][3]["stacked_graphs_view"][0][
                #     "donut_chart"
                # ]["datasets"][0]["entries"]
                # all_data_table_03_data = json_data[0]["list"][4]["paginated_view"][0]
                # # Итерация по списку entries для получения количества элементов и их обработки

                # # Словари по таблицам
                # dict_table_01 = {
                #     entry["label"]: entry["total"] for entry in all_data_table_01_data
                # }
                # dict_table_01["Revenue"] = (
                #     dict_table_01["Revenue"].replace("USD ", "").replace(".", ",")
                # )

                # dict_table_02 = {
                #     entry["label"]: entry["value"] for entry in all_data_table_02_data
                # }
                # dict_table_03 = {}

                # for item in json_data[0]["list"][4]["paginated_view"]:
                #     # Проверяем, есть ли нужные ключи и данные
                #     if (
                #         "horizontal_line_chart" in item
                #         and "datasets" in item["horizontal_line_chart"]
                #         and len(item["horizontal_line_chart"]["datasets"]) > 0
                #     ):

                #         # Получаем список 'entries'
                #         entries = item["horizontal_line_chart"]["datasets"][0]["entries"]

                #         # Итерация по каждому 'entry' для заполнения словаря
                #         for entry in entries:
                #             # Проверяем, есть ли 'label' и 'value' в 'entry'
                #             if "label" in entry and "value" in entry:
                #                 # Добавляем пару в словарь
                #                 dict_table_03[entry["label"]] = entry["value"]

                # img_url = json_data[0]["list"][0]["stacked_graphs_view"][0][
                #     "inventory_detail"
                # ]["datasets"][0]["entries"][0]["listing"]["image"]["url"]
                # url_product = json_data[0]["list"][0]["stacked_graphs_view"][0][
                #     "inventory_detail"
                # ]["datasets"][0]["entries"][0]["listing"]["url"]
                # img_url_for_google = f'=IMAGE("{img_url}")'
                # current_object = {
                #     "object": {
                #         "listing_id": listing_id,
                #         "title": listing_title,
                #         "img_url_for_google": img_url_for_google,
                #         "url_product": url_product,
                #     },
                #     "dict_table_01": dict_table_01,
                #     "dict_table_02": dict_table_02,
                #     "dict_table_03": dict_table_03,
                # }

                # all_objects.append(current_object)
            values = []

            for index, item in enumerate(all_objects, start=2):
                # Найдите теги, соответствующие текущему listing_id
                tags = next(
                    (
                        tag_item["object"]["tags"]
                        for tag_item in all_tags
                        if tag_item["listing_id"] == item["object"]["listing_id"]
                    ),
                    None,
                )

                # Преобразуйте список тегов в строку, если теги найдены
                tags_str = ", ".join(tags) if tags else ""
                dict_to_tags = (
                    ", ".join([f"{k}: {v}" for k, v in item["dict_table_03"].items()])
                    if item["dict_table_03"]
                    else ""
                )
                # Извлекаем числовые значения, обрабатываем случай отсутствия данных
                visits_str = item["dict_table_01"].get("Visits", "0").replace(",", "")
                visits = int(visits_str)

                # if visits > 0:
                #     visits = visits.replace(",", "")
                #     visits = float(visits)
                

                # Пример с удалением запятой перед преобразованием
                total_views_str = item["dict_table_01"].get(
                    "Total Views", "0"
                )  # Получаем строку
                if total_views_str == "0":
                    continue
                total_views_str = total_views_str.replace(",", "")  # Удаляем запятые
                total_views = float(
                    total_views_str
                )  # Преобразуем в число с плавающей точкой

                orders_str = item["dict_table_01"].get("Orders", 0).replace(",", ".")
                orders = float(orders_str)

                # Обработка деления с проверкой на ноль и округлением
                orders_to_visits_ratio = (
                    ((round(orders / visits, 4)) * 100) if visits else None
                )
                visits_to_total_views_ratio = (
                    ((round(visits / total_views, 4)) * 100) if total_views else None
                )

                row_data = [
                    item["object"]["img_url_for_google"],
                    item["object"]["url_product"],
                    str(item["dict_table_01"].get("Visits", "")),
                    str(item["dict_table_01"].get("Total Views", "")),
                    str(item["dict_table_01"].get("Orders", "")),
                    str(item["dict_table_01"].get("Revenue", "")),
                    orders_to_visits_ratio,  # Используем обработанные значения
                    visits_to_total_views_ratio,  # Используем обработанные значения
                    item["dict_table_02"]["Direct & other traffic"],
                    item["dict_table_02"]["Etsy app & other Etsy pages"],
                    item["dict_table_02"]["Etsy Ads"],
                    item["dict_table_02"]["Etsy marketing & SEO"],
                    item["dict_table_02"]["Social media"],
                    item["dict_table_02"]["Etsy search"],
                    item["object"]["title"],
                    dict_to_tags,  # Используйте преобразованный словарь
                    tags_str,
                ]
                values.append(row_data)
            new_values = []
            for v in values:
                matched_in_tags_set = set()
                unmatched_in_tags_set = set()
                matched_in_title_set = set()
                unmatched_in_title_set = set()
                matched_in_search_set_tag = set()
                matched_in_search_set_title = set()
                
                # B - Title
                title = v[14]
                title_words = set(split_into_words(title))
                
                # P - Search Terms
                dict_to_tags = v[15]
                tags_words = re.sub(": \d+", "", dict_to_tags)
                words = re.findall(r"\w+", tags_words.lower())
                unique_words_search_terms = set(words)
                # Q - Tags
                tags_listing = v[16]
                tags_to_list = set(split_into_words(tags_listing))

                # Только проверка тегов
                for product_info in tags_to_list:
                    product_name = product_info.split(" : ")[0]

                    # print(f"\nАнализируем продукт: {product_name}")
                    # Определяем product_words заранее
                    product_words = split_into_words(product_name)

                    product_name = product_name.lower()
                    # Шаг 1
                    # if product_name.lower() in title.lower():
                    #     print("\nНайдено целиком в заголовке.")
                    # else:
                    #     print("\nНе найдено целиком в заголовке.")
                    # Шаг 2
                    product_words = [
                        re.sub(r"\d+", "", word)
                        for word in product_words
                        if re.sub(r"\d+", "", word)
                    ]
                    # Шаг 3
                    matched_in_tags = [
                        word for word in product_words if word in unique_words_search_terms
                    ]
                    unmatched_in_tags = [
                        word
                        for word in product_words
                        if word not in unique_words_search_terms and word
                    ]
                    matched_in_tags_set.update(matched_in_tags)
                    unmatched_in_tags_set.update(unmatched_in_tags)

                for title in title_words:
                    title__words = split_into_words(title)
                    matched_in_title = [
                        word for word in title__words if word in unique_words_search_terms
                    ]
                    unmatched_in_title = [
                        word
                        for word in title__words
                        if word not in unique_words_search_terms and word
                    ]
                    matched_in_title_set.update(matched_in_title)
                    unmatched_in_title_set.update(unmatched_in_title)
                

                common_words_tag = unique_words_search_terms.difference(tags_to_list)
                matched_in_search_set_tag.update(common_words_tag)
               
                common_words_title = unique_words_search_terms.difference(title_words)
                matched_in_search_set_title.update(common_words_title)

                matched_in_tags_str = ", ".join(list(matched_in_tags_set))
                unmatched_in_tags_str = ", ".join(list(unmatched_in_tags_set))
                
                matched_in_title_str = ", ".join(list(matched_in_title_set))
                unmatched_in_title_str = ", ".join(list(unmatched_in_title_set))
                
                matched_in_search_str_tag = ", ".join(list(matched_in_search_set_tag))
                matched_in_search_str_title = ", ".join(list(matched_in_search_set_title))
                
                new_row = v + [
                    matched_in_tags_str,
                    unmatched_in_tags_str,
                    matched_in_title_str,
                    unmatched_in_title_str,
                    matched_in_search_str_tag,
                    matched_in_search_str_title,
                ]
                
                new_values.append(new_row)

            client, spreadsheet_id = get_google()
            sheet = client.open_by_key(spreadsheet_id)

            new_headers = [
                [
                    "Title Photo",
                    "Link",
                    "Visits",
                    "Total Views",
                    "Orders",
                    "Revenue",
                    "Conversion Rate",
                    "Сlick Rate",
                    "Direct & other traffic",
                    "Etsy app & other Etsy pages",
                    "Etsy Ads",
                    "Etsy marketing & SEO",
                    "Social media",
                    "Etsy search",
                    "Title",
                    "Search Terms",
                    "Tags",
                    "Working Tags",
                    "Non-Working Tags",
                    "Working Title Words",
                    "Non-Working Title Words",
                    "Tagging ideas (Tags)",
                    "Tagging ideas (Title)",
                ]
            ]
            # Преобразование списка списков в одну большую строку
            # all_values_as_string = ''.join([''.join(map(str, row)) for row in new_values])

            # # Подсчет количества символов в строке
            # total_characters = len(all_values_as_string)
            # print(total_characters)
            try:
                worksheet = sheet.worksheet(shop)
            except gspread.WorksheetNotFound:
                worksheet = sheet.add_worksheet(title=shop, rows="100", cols="20")

            # Очистка всего листа
            worksheet.clear()
            time.sleep(5)
            # Запись только заголовков
            try:
                worksheet.update(new_headers, "A1")
            except Exception as e:
                print(f"Произошла ошибка при обновлении Google Sheets: {e}")
            time.sleep(5)
            # Запись всех данных
            try:
                worksheet.update(new_values, "A2", value_input_option="USER_ENTERED")
            except Exception as e:
                print(f"Произошла ошибка при обновлении Google Sheets: {e}")


"""
Парсим файлы тегов
"""


def par_tags(shop):
    filename_tags = os.path.join(json_tags, shop, "tags*.json")
    filenames = glob.glob(filename_tags)
    all_objects = []  # список для хранения всех словарей
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as f:
            data_json = json.load(f)
        json_data = data_json
        all_tags = []
        for i, entry in enumerate(json_data):
            listing_id = entry["listing_id"]
            title = entry["title"]
            tags = entry["tags"]
            current_object = {
                "listing_id": listing_id,
                "object": {
                    "title": title,
                    "tags": tags,
                    # Обратите внимание, что здесь должно быть "tags": entry['tags'], а не просто tags: entry['tags']
                },
            }
            all_objects.append(current_object)
    return all_objects
    # with open('all_tags.json', 'w', encoding='utf-8') as f:
    #     json.dump(all_objects, f, ensure_ascii=False, indent=4)  # Записываем в файл
    # print(all_objects)
    # Добавляем словарь в список
    #     all_objects.append(current_object)
    #     values = [listing_id, title, tags]
    #     all_tags.extend(values)
    #     # all_products.update(dict_table_04)
    # print(all_tags)


"""
Парсим файлы статистики
"""


def parsing_statistic(shop):
    filename_tender = os.path.join(json_statistic, shop, "statistic*.json")
    filenames = glob.glob(filename_tender)
    all_products = {}
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as f:
            data_json = json.load(f)

        json_data = data_json
        dict_table_04 = {entry["id"]: entry["title"] for entry in json_data["listings"]}
        all_products.update(dict_table_04)
    all_products_keys = list(all_products.keys())
    return all_products_keys


if __name__ == "__main__":
    while True:
        print(
            "\nОчистити тимчасові файли - натисніть 9"
            "\nЯкий беремо період?"
            "\nОстанні 7 днів - натисніть 1"
            "\nОстанні 30 днів - натисніть 2"
            "\nЦей рік - натисніть 3"
            "\nЗа весь час - натисніть 4"
            "\nЦей місяць - натисніть 5"
            "\nОстанній рік - натисніть 6"
            "\nЗакрити програму - натисніть 0"
        )

        date_range = input()  # Используйте input() без преобразования к int здесь
        if date_range.isdigit():  # Проверка, является ли ввод числом
            date_range = int(
                date_range
            )  # Преобразование ввода в число, если это возможно
            if date_range == 1:
                date_range = "last_7"
            elif date_range == 2:
                date_range = "last_30"
            elif date_range == 3:
                date_range = "this_year"
            elif date_range == 4:
                date_range = "all_time"
            elif date_range == 5:
                date_range = "this_month"
            elif date_range == 6:
                date_range = "last_year"
            elif date_range == 9:
                """
                Удаление старых файлов
                """
                delete_temp_directory()
                creative_temp_folders()
                print("Старі файли видалено. Продовжуйте вибір.")
                continue  # Переходимо назад до початку циклу

            elif date_range == 0:
                print("Програма завершена.")
                break
            else:
                print("Невірний ввід, будь ласка, введіть коректний номер дії.")
                continue  # Для возврата к началу цикла, если ввод некорректен

            creative_temp_folders()
            get_page_statistic(date_range)
            get_product(date_range)
            get_tags()
            pars_product()
        else:
            print("Невірний ввід, будь ласка, введіть коректний номер дії.")
