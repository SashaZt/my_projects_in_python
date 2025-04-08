import json
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import gspread
import numpy as np
import pandas as pd
import requests
from google.oauth2.service_account import Credentials
from loguru import logger
from lxml import etree

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"
config_directory = current_directory / "config"

config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
config_file_path = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def load_json_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def save_json_data(data, file_path):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")
        return False


config = load_json_data(config_file_path)
URLS = config.get("competitor_www", [])
MY_URL = config.get("my_www")
HEADERS = config.get("headers", {})
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]


def get_google_sheet(sheet_one):
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(sheet_one)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


def update_sheet_with_data(sheet, data, total_rows=50000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Добавление пустых строк до общего количества total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A2:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")
    logger.info(f"Обновлено {len(data)} строк в Google Sheets")


def download_xml(url, headers):
    """
    Скачивает XML файл по указанному URL.

    Args:
        url (str): URL для скачивания XML файла
        headers (dict): Заголовки для HTTP запроса
        xml_dir (Path, optional): Директория для сохранения файлов. По умолчанию xml_directory.

    Returns:
        Path or None: Путь к сохраненному файлу или None в случае ошибки
    """
    try:
        if (
            url
            == "https://hdsport.com.ua/index.php?route=extension/feed/unixml/allprice"
        ):
            xml_file_path = xml_directory / "all.xml"
        else:
            # Извлечение имени файла из URL
            filename = urlparse(url).path.split("/")[-1]

            # Если имя файла пустое, используем домен
            if not filename:
                filename = urlparse(url).netloc.replace(".", "_")

            # Добавляем расширение .xml если его нет
            if not filename.endswith(".xml"):
                xml_file_path = xml_directory / f"{filename}.xml"
            else:
                xml_file_path = xml_directory / filename

        logger.info(f"Скачиваем XML файл: {url}")

        response = requests.get(
            url,
            headers=headers,
            timeout=100,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(xml_file_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Исключение при скачивании файла {url}: {e}")
        return None


def download_all_xml_files():
    """
    Скачивает все XML файлы на основе конфигурации.

    Args:
        config_file_path (str): Путь к файлу конфигурации

    Returns:
        dict: Результаты скачивания {url: путь_к_файлу_или_None}
    """
    # Загрузка конфигурации

    results = {}

    # Скачивание файлов конкурентов
    for url in URLS:
        results[url] = download_xml(url, HEADERS)

    # Скачивание собственного файла
    if MY_URL:
        results[MY_URL] = download_xml(MY_URL, HEADERS)

    return results


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

            # return urls

        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            print(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")


def parsin_xml():
    # Словарь для хранения данных по sku
    data_dict = {}
    # Дополнительный словарь для хранения данных по ean для быстрого поиска
    ean_dict = {}
    # Словарь для сопоставления SKU без префикса INS
    normalized_sku_dict = {}

    # Для хранения данных в разных категориях
    matched_data = []  # Данные, которые были сопоставлены
    unmatched_data = []  # Данные, которые не были сопоставлены

    # Сначала обрабатываем файл "all", чтобы собрать sku и ean
    for xml_file in xml_directory.glob("*.xml"):
        name_file = xml_file.stem

        if name_file == "all":
            tree = etree.parse(xml_file)
            root = tree.getroot()
            offers = root.xpath("//offer")

            for offer in offers:
                price_my_site = extract_xml_value(offer, "price")
                sku = (
                    offer.xpath('param[@name="sku"]/text()')[0]
                    if offer.xpath('param[@name="sku"]')
                    else None
                )

                ean = (
                    offer.xpath('param[@name="ean"]/text()')[0]
                    if offer.xpath('param[@name="ean"]')
                    else None
                )

                if sku:  # Используем sku как ключ
                    data_dict[sku] = {
                        "Мой сайт sku": sku,
                        "Мой сайт ean": ean,
                        "Мой сайт цена": price_my_site,
                        "insportline vendor_code": None,
                        "insportline цена": None,
                        "xcore_sku": None,
                        "xcore_price": None,
                        "matched": False,  # Флаг для отслеживания сопоставленных записей
                    }

                    # Если есть EAN, создаем ссылку на запись в data_dict
                    if ean:
                        ean_dict[ean] = sku

                    # Создаем нормализованную версию SKU (без префикса INS)
                    normalized_sku = normalize_sku(sku)
                    normalized_sku_dict[normalized_sku] = sku

    # Теперь обрабатываем остальные файлы для получения insportline (vendorCode)
    for xml_file in xml_directory.glob("*.xml"):
        name_file = xml_file.stem

        if name_file in ["export_yandex_market", "yml_dualprice"]:
            tree = etree.parse(xml_file)
            root = tree.getroot()
            offers = root.xpath("//offer")

            for offer in offers:
                vendor_code = extract_xml_value(offer, "vendorCode")
                insportline_price = extract_xml_value(offer, "price")

                if not vendor_code:
                    continue

                match_found = False

                # Пытаемся найти соответствующую запись по sku
                if vendor_code in data_dict:
                    # Сопоставление по точному совпадению SKU
                    data_dict[vendor_code]["insportline vendor_code"] = vendor_code
                    data_dict[vendor_code]["insportline цена"] = insportline_price
                    data_dict[vendor_code]["matched"] = True
                    match_found = True
                else:
                    # Нормализуем vendor_code для сравнения
                    normalized_vendor = normalize_sku(vendor_code)

                    # Проверяем соответствие по нормализованному SKU
                    if normalized_vendor in normalized_sku_dict:
                        original_sku = normalized_sku_dict[normalized_vendor]
                        data_dict[original_sku]["insportline vendor_code"] = vendor_code
                        data_dict[original_sku]["insportline цена"] = insportline_price
                        data_dict[original_sku]["matched"] = True
                        match_found = True
                    else:
                        # Попробуем сопоставить по EAN
                        ean_value = extract_xml_value(
                            offer, "barcode"
                        ) or extract_xml_value(offer, "ean")

                        if ean_value and ean_value in ean_dict:
                            # Нашли соответствие по EAN
                            matching_sku = ean_dict[ean_value]
                            data_dict[matching_sku][
                                "insportline vendor_code"
                            ] = vendor_code
                            data_dict[matching_sku][
                                "insportline цена"
                            ] = insportline_price
                            data_dict[matching_sku]["matched"] = True
                            match_found = True

                if not match_found:
                    # Если нет соответствия ни по SKU, ни по EAN, добавляем новую запись
                    new_key = f"insportline_{vendor_code}"
                    data_dict[new_key] = {
                        "Мой сайт sku": None,
                        "Мой сайт ean": None,
                        "Мой сайт цена": None,
                        "insportline vendor_code": vendor_code,
                        "insportline цена": insportline_price,
                        "xcore_sku": None,
                        "xcore_price": None,
                        "matched": False,  # Это несопоставленная запись
                    }

    # Обработка JSON файла xcore_com_ua.json
    try:
        with open("data/xcore_com_ua.json", "r", encoding="utf-8") as f:
            xcore_data = json.load(f)

        for item in xcore_data:
            xcore_sku = item.get("Артику")
            xcore_price = item.get("Ціна")

            if not xcore_sku:
                continue

            match_found = False

            # Сначала проверяем точное совпадение SKU
            if xcore_sku in data_dict:
                data_dict[xcore_sku]["xcore_sku"] = xcore_sku
                data_dict[xcore_sku]["xcore_price"] = xcore_price
                data_dict[xcore_sku]["matched"] = True
                match_found = True
            else:
                # Нормализуем xcore_sku для сравнения
                normalized_xcore = normalize_sku(xcore_sku)

                # Проверяем соответствие по нормализованному SKU
                if normalized_xcore in normalized_sku_dict:
                    original_sku = normalized_sku_dict[normalized_xcore]
                    data_dict[original_sku]["xcore_sku"] = xcore_sku
                    data_dict[original_sku]["xcore_price"] = xcore_price
                    data_dict[original_sku]["matched"] = True
                    match_found = True

            if not match_found:
                # Если не нашли соответствие, добавляем новую запись
                new_key = f"xcore_{xcore_sku}"
                data_dict[new_key] = {
                    "Мой сайт sku": None,
                    "Мой сайт ean": None,
                    "Мой сайт цена": None,
                    "insportline vendor_code": None,
                    "insportline цена": None,
                    "xcore_sku": xcore_sku,
                    "xcore_price": xcore_price,
                    "matched": False,  # Это несопоставленная запись
                }

        print(f"Обработано {len(xcore_data)} товаров из xcore_com_ua.json")
    except Exception as e:
        print(f"Ошибка при обработке xcore_com_ua.json: {e}")

    # Разделяем данные на сопоставленные и несопоставленные
    for key, value in data_dict.items():
        # Удаляем служебное поле matched, которое не нужно передавать в result
        matched = value.pop("matched", False)

        # Запись считается сопоставленной, если в ней есть данные хотя бы из двух разных источников
        sources_count = 0
        if value["Мой сайт sku"] is not None:
            sources_count += 1
        if value["insportline vendor_code"] is not None:
            sources_count += 1
        if value["xcore_sku"] is not None:
            sources_count += 1

        if sources_count >= 2:
            matched_data.append(value)
        else:
            unmatched_data.append(value)

    # Выводим для отладки количество сопоставленных и несопоставленных записей
    print(f"Сопоставлено записей: {len(matched_data)}")
    print(f"Не сопоставлено записей: {len(unmatched_data)}")

    # Соединяем сначала сопоставленные, затем несопоставленные записи
    result = matched_data + unmatched_data

    # # Для примера выведем первые несколько сопоставленных записей
    # print("\nПримеры сопоставленных записей:")
    # for i, item in enumerate(matched_data[:5]):  # Первые 5 записей для примера
    #     print(
    #         f"{i+1}. SKU: {item['Мой сайт sku']}, "
    #         + f"Insportline: {item['insportline vendor_code']}, "
    #         + f"Xcore: {item['xcore_sku']}, "
    #         + f"Цены: {item['Мой сайт цена']} / {item['insportline цена']} / {item['xcore_price']}"
    #     )

    # Получаем лист и обновляем данные
    sheet_name = "Data"
    sheet = get_google_sheet(sheet_name)
    update_sheet_with_data(sheet, result)

    return result  # Возвращаем результат для дальнейшего использования
    # # Преобразуем словарь в список для записи
    # result = list(data_dict.values())

    # # Получаем лист и обновляем данные
    # sheet_name = "Data"
    # sheet = get_google_sheet(sheet_name)
    # update_sheet_with_data(sheet, result)


def normalize_sku(sku):
    """
    Нормализует SKU, удаляя префикс 'INS' если он есть.
    Например: 'INS9410-3' -> '9410-3'
    """
    if sku and isinstance(sku, str):
        if sku.startswith("INS"):
            return sku[3:]  # Удаляем первые 3 символа (INS)
    return sku


def extract_xml_value(element, tag_name):
    """Извлекает значение тега из XML элемента или возвращает 'N/A', если тег не найден."""
    node = element.find(tag_name)
    return node.text if node is not None else None


def get_sheet_data(sheet_name):
    """Извлекает данные из указанного листа Google таблицы и возвращает их в виде pandas DataFrame."""
    try:
        # Получаем лист
        worksheet = get_google_sheet(sheet_name)

        # Получаем все записи из листа
        data = worksheet.get_all_records()

        # Преобразуем в DataFrame
        df = pd.DataFrame(data)

        logger.info(
            f"Успешно получены данные из листа '{sheet_name}'. Строк: {len(df)}"
        )
        return df
    except Exception as e:
        logger.error(f"Ошибка при получении данных из листа '{sheet_name}': {e}")
        raise


def process_prices(source_sheet_name, result_sheet_name="result"):
    """
    Обрабатывает данные из исходного листа, сравнивает цены и загружает
    результаты в лист результатов.

    :param source_sheet_name: Имя исходного листа с данными
    :param result_sheet_name: Имя листа для результатов (по умолчанию "result")
    :return: DataFrame с результатами
    """
    try:
        # Получаем данные в DataFrame
        df = get_sheet_data(source_sheet_name)

        # Переименуем колонки для удобства (уберем пробелы)
        df.columns = [col.replace(" ", "_") for col in df.columns]

        # Создаем DataFrame для результатов
        result_df = pd.DataFrame(
            columns=[
                "Артикул",
                "стара_ціна",
                "нова_ціна",
                "Ціна_Xcore",
                "Ціна_Insportline",
            ]
        )

        # Обрабатываем каждую строку
        for _, row in df.iterrows():
            # Проверяем совпадение артикулов (один из трех вариантов)
            my_sku = str(row["Мой_сайт_sku"])
            insportline_code = str(row.get("insportline_vendor_code", ""))
            xcore_sku = str(row.get("xcore_sku", ""))

            # Дополнительная проверка для префиксов MBS/MS
            if my_sku.startswith("MBS-") and xcore_sku.startswith("MS-"):
                my_sku_normalized = my_sku.replace("MBS-", "")
                xcore_sku_normalized = xcore_sku.replace("MS-", "")
                is_prefix_match = my_sku_normalized == xcore_sku_normalized
            elif my_sku.startswith("MS-") and xcore_sku.startswith("MBS-"):
                my_sku_normalized = my_sku.replace("MS-", "")
                xcore_sku_normalized = xcore_sku.replace("MBS-", "")
                is_prefix_match = my_sku_normalized == xcore_sku_normalized
            else:
                is_prefix_match = False

            # Проверяем, что хотя бы один из вариантов совпадения артикулов есть
            is_match = (
                (my_sku and insportline_code and xcore_sku)  # вариант 1: все артикулы
                or (
                    my_sku and my_sku == xcore_sku
                )  # вариант 2: Мой сайт sku и xcore_sku
                or (
                    my_sku and my_sku == insportline_code
                )  # вариант 3: Мой сайт sku и insportline
                or is_prefix_match  # вариант 4: совпадение с учетом префиксов MBS/MS
            )

            if not is_match:
                continue

            # Получаем текущую цену на сайте
            try:
                my_price = (
                    float(row["Мой_сайт_цена"])
                    if pd.notna(row.get("Мой_сайт_цена"))
                    else 0
                )
            except (ValueError, TypeError):
                my_price = 0

            # Получаем цены поставщиков
            try:
                insportline_price = (
                    float(row.get("insportline_цена", 0))
                    if pd.notna(row.get("insportline_цена"))
                    else 0
                )
            except (ValueError, TypeError):
                insportline_price = 0

            try:
                xcore_price = (
                    float(row.get("xcore_price", 0))
                    if pd.notna(row.get("xcore_price"))
                    else 0
                )
            except (ValueError, TypeError):
                xcore_price = 0

            # Проверяем валидность цен (игнорируем цены 1 или 2)
            valid_prices = []

            if xcore_price > 2:
                valid_prices.append(xcore_price)

            if insportline_price > 2:
                valid_prices.append(insportline_price)

            # Проверяем наличие валидных цен
            if not valid_prices:
                continue

            # Находим минимальную валидную цену с учетом условий
            filtered_prices = valid_prices.copy()

            # Фильтруем цены, если разница между ними более 50%
            if len(valid_prices) > 1:
                min_price = min(valid_prices)
                max_price = max(valid_prices)

                # Проверяем разницу между минимальной и максимальной ценой
                if max_price / min_price > 1.5:  # разница более 50%
                    # Определяем, какую цену исключить
                    if (
                        xcore_price in valid_prices
                        and insportline_price in valid_prices
                    ):
                        # Если обе цены валидны, удаляем выброс
                        if xcore_price / insportline_price > 1.5:
                            filtered_prices.remove(xcore_price)
                        elif insportline_price / xcore_price > 1.5:
                            filtered_prices.remove(insportline_price)
            # Проверяем случай, когда цена конкурента ниже нашей на 30% и более
            if my_price > 0:
                for price in valid_prices[:]:  # Создаем копию для безопасной итерации
                    if (
                        price / my_price < 0.7
                    ):  # Цена поставщика ниже нашей более чем на 30%
                        if price in filtered_prices:
                            filtered_prices.remove(price)

            # Если после фильтрации остались цены
            # Теперь работаем с отфильтрованным списком
            if filtered_prices:
                min_supplier_price = min(filtered_prices)

                # Проверяем, является ли наша текущая цена самой низкой
                if my_price > 0 and my_price < min_supplier_price:
                    # Если наша цена ниже минимальной цены поставщиков, оставляем нашу цену
                    new_price = my_price
                else:
                    # Рассчитываем новую цену с небольшим случайным отклонением
                    discount_factor = round(random.uniform(0.95, 0.97), 2)
                    new_price = min_supplier_price * discount_factor

                # Добавляем результат
                result_df = result_df._append(
                    {
                        "Артикул": my_sku,
                        "стара_ціна": my_price,
                        "нова_ціна": round(new_price, 2),
                        "Ціна_Xcore": xcore_price if xcore_price > 2 else "-",
                        "Ціна_Insportline": (
                            insportline_price if insportline_price > 2 else "-"
                        ),
                    },
                    ignore_index=True,
                )
            else:
                # Если после фильтрации не осталось валидных цен, используем нашу цену
                new_price = my_price

        # Выгружаем результаты в лист "result" используя функцию update_sheet_with_data
        try:
            # Получаем лист для результатов
            result_sheet = get_google_sheet(result_sheet_name)

            # Преобразуем DataFrame в список словарей для передачи в функцию update_sheet_with_data
            # Переименуем столбцы обратно для правильного отображения в таблице
            result_df_renamed = result_df.rename(
                columns={
                    "Артикул": "Артикул",
                    "стара_ціна": "стара ціна",
                    "нова_ціна": "нова ціна",
                    "Ціна_Xcore": "Ціна Xcore",
                    "Ціна_Insportline": "Ціна Insportline",
                }
            )

            # Преобразуем DataFrame в список словарей
            result_data = result_df_renamed.to_dict("records")

            # Используем готовую функцию для обновления листа
            update_sheet_with_data(result_sheet, result_data)

            logger.info(
                f"Обработано {len(result_df)} товаров. Результаты выгружены в лист '{result_sheet_name}'."
            )
        except Exception as e:
            logger.error(
                f"Ошибка при выгрузке результатов в лист '{result_sheet_name}': {e}"
            )
            raise

        return result_df

    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {e}")
        raise


if __name__ == "__main__":
    download_all_xml_files()
    parsin_xml()
    source_sheet = "Data"  # Имя листа с исходными данными
    result_sheet = "result"  # Имя листа для результатов
    results = process_prices(source_sheet, result_sheet)
