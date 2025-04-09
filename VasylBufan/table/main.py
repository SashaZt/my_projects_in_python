import json
import random
import shutil
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


def get_json_xcore():
    source_path = "/home/rsa-key-20241114/xcore_com_ua/data/xcore_com_ua.json"
    destination_path = "/home/rsa-key-20241114/table/data/xcore_com_ua.json"

    shutil.copy2(source_path, destination_path)
    logger.info(f"Файл {destination_path} перемещен ")


def extract_xml_value(element, tag_name):
    """Извлекает значение тега из XML элемента или возвращает 'N/A', если тег не найден."""
    node = element.find(tag_name)
    return node.text if node is not None else None


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


# Рабочая функция для обновления данных в Google Sheets
# def update_sheet_with_data(sheet, data, total_rows=50000):
#     """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
#     if not data:
#         raise ValueError("Данные для обновления отсутствуют.")

#     # Заголовки из ключей словаря
#     headers = list(data[0].keys())

#     # Запись заголовков в первую строку
#     sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

#     # Формирование строк для записи
#     rows = [[entry.get(header, "") for header in headers] for entry in data]

#     # Добавление пустых строк до общего количества total_rows
#     if len(rows) < total_rows:
#         empty_row = [""] * len(headers)
#         rows.extend([empty_row] * (total_rows - len(rows)))

#     # Определение диапазона для записи данных
#     end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
#     range_name = f"A2:{end_col}{total_rows + 1}"


#     # Запись данных в лист
#     sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")
#     logger.info(f"Обновлено {len(data)} строк в Google Sheets")
def update_sheet_with_data(sheet, data, total_rows=50000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Получаем имя листа для проверки
    sheet_title = sheet.title

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Определяем стартовую строку в зависимости от имени листа
    start_row = 101 if sheet_title == "Data" else 2

    # Добавление пустых строк до общего количества total_rows
    if start_row + len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows) - start_row + 2))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A{start_row}:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")
    logger.info(
        f"Обновлено {len(data)} строк в Google Sheets, начиная со строки {start_row}"
    )


def create_sku_mapping(df):
    """
    Создает маппинг артикулов с учетом префиксов MBS/MS.

    :param df: DataFrame с данными
    :return: Словарь соответствий артикулов
    """
    sku_mapping = {}

    # Получаем все уникальные артикулы
    my_site_skus = [
        str(sku).strip()
        for sku in df["Мой_сайт_sku"].unique()
        if pd.notna(sku) and str(sku).strip()
    ]
    xcore_skus = [
        str(sku).strip()
        for sku in df["xcore_sku"].unique()
        if pd.notna(sku) and str(sku).strip()
    ]

    logger.info(
        f"Найдено уникальных артикулов: my_site_sku={len(my_site_skus)}, xcore_sku={len(xcore_skus)}"
    )

    # Создаем маппинг артикулов MBS/MS
    for my_sku in my_site_skus:
        if my_sku.startswith("MBS-"):
            # Ищем соответствующий MS- артикул
            ms_sku = "MS-" + my_sku[4:]
            if ms_sku in xcore_skus:
                sku_mapping[my_sku] = ms_sku
                sku_mapping[ms_sku] = my_sku
                logger.info(f"Создано соответствие: {my_sku} <-> {ms_sku}")

    for xcore_sku in xcore_skus:
        if xcore_sku.startswith("MS-"):
            # Ищем соответствующий MBS- артикул
            mbs_sku = "MBS-" + xcore_sku[3:]
            if mbs_sku in my_site_skus:
                sku_mapping[xcore_sku] = mbs_sku
                sku_mapping[mbs_sku] = xcore_sku
                logger.info(f"Создано соответствие: {xcore_sku} <-> {mbs_sku}")

    # Добавляем специальное правило для конкретных артикулов
    sku_mapping["MBS-26339"] = "MS-26339"
    sku_mapping["MS-26339"] = "MBS-26339"

    logger.info(f"Создано {len(sku_mapping)} соответствий артикулов")
    return sku_mapping


# Модифицируем функцию check_sku_match, чтобы использовать маппинг
def check_sku_match(my_sku, xcore_sku, insportline_code, sku_mapping):
    """
    Проверяет совпадение артикулов с учетом различных префиксов и маппинга.
    """
    # Очистка строк от лишних пробелов
    my_sku_clean = my_sku.strip()
    xcore_sku_clean = xcore_sku.strip()
    insportline_code_clean = insportline_code.strip()

    # Логирование для отладки
    logger.info(
        f"Сравниваем артикулы: my_sku='{my_sku_clean}', xcore_sku='{xcore_sku_clean}', insportline='{insportline_code_clean}'"
    )

    # Проверяем стандартные условия совпадения
    if (
        my_sku_clean and insportline_code_clean and xcore_sku_clean
    ):  # вариант 1: все артикулы
        logger.info("Совпадение по варианту 1: есть все артикулы")
        return True
    if (
        my_sku_clean and my_sku_clean == xcore_sku_clean
    ):  # вариант 2: Мой сайт sku и xcore_sku
        logger.info("Совпадение по варианту 2: my_sku == xcore_sku")
        return True
    if (
        my_sku_clean and my_sku_clean == insportline_code_clean
    ):  # вариант 3: Мой сайт sku и insportline
        logger.info("Совпадение по варианту 3: my_sku == insportline_code")
        return True

    # Проверка по маппингу артикулов - исправлено
    if my_sku_clean and my_sku_clean in sku_mapping:
        matched_sku = sku_mapping[my_sku_clean]
        if xcore_sku_clean and matched_sku == xcore_sku_clean:
            logger.info(f"Совпадение по маппингу: {my_sku_clean} -> {xcore_sku_clean}")
            return True
        # Здесь может потребоваться дополнительная логика для поиска строк с совпадающими артикулами

    if xcore_sku_clean and xcore_sku_clean in sku_mapping:
        matched_sku = sku_mapping[xcore_sku_clean]
        if my_sku_clean and matched_sku == my_sku_clean:
            logger.info(f"Совпадение по маппингу: {xcore_sku_clean} -> {my_sku_clean}")
            return True
        # Здесь может потребоваться дополнительная логика для поиска строк с совпадающими артикулами

    return False


def filter_prices(my_price, valid_prices, xcore_price, insportline_price):
    """
    Фильтрует цены с учетом всех условий и ограничений.

    :param my_price: Цена на 'Моем сайте'
    :param valid_prices: Список валидных цен поставщиков
    :param xcore_price: Цена Xcore
    :param insportline_price: Цена Insportline
    :return: Отфильтрованный список цен
    """
    # Создаем копию для безопасной фильтрации
    filtered_prices = valid_prices.copy()

    # Фильтруем цены, если разница между ними более 50%
    if len(filtered_prices) > 1:
        min_price = min(filtered_prices)
        max_price = max(filtered_prices)

        # Проверяем разницу между минимальной и максимальной ценой
        if max_price / min_price > 1.5:  # разница более 50%
            # Определяем, какую цену исключить
            if xcore_price in filtered_prices and insportline_price in filtered_prices:
                # Если обе цены валидны, удаляем выброс
                if xcore_price / insportline_price > 1.5:
                    filtered_prices.remove(xcore_price)
                    logger.info(
                        f"Исключена цена Xcore {xcore_price}, так как она отличается от цены Insportline {insportline_price} более чем на 50%"
                    )
                elif insportline_price / xcore_price > 1.5:
                    filtered_prices.remove(insportline_price)
                    logger.info(
                        f"Исключена цена Insportline {insportline_price}, так как она отличается от цены Xcore {xcore_price} более чем на 50%"
                    )

    # Проверяем случай, когда цена конкурента ниже нашей на 30% и более
    if my_price > 0:
        for price in valid_prices[:]:  # Создаем копию для безопасной итерации
            if price / my_price < 0.7:  # Цена поставщика ниже нашей более чем на 30%
                if price in filtered_prices:
                    filtered_prices.remove(price)
                    logger.info(
                        f"Исключена цена {price}, так как она ниже нашей цены {my_price} более чем на 30%"
                    )

    return filtered_prices


def calculate_new_price(my_price, filtered_prices):
    """
    Рассчитывает новую цену на основе отфильтрованных цен поставщиков.

    :param my_price: Цена на 'Моем сайте'
    :param filtered_prices: Отфильтрованный список цен поставщиков
    :return: Новая цена
    """
    if not filtered_prices:
        # Если после фильтрации не осталось валидных цен, используем нашу цену
        logger.info(
            f"После фильтрации не осталось валидных цен. Используем нашу цену: {my_price}"
        )
        return my_price

    min_supplier_price = min(filtered_prices)

    # Проверяем, является ли наша текущая цена самой низкой
    if my_price > 0 and my_price < min_supplier_price:
        # Если наша цена ниже минимальной цены поставщиков, оставляем нашу цену
        # logger.info(
        #     f"Наша цена {my_price} ниже минимальной цены поставщиков {min_supplier_price}. Оставляем нашу цену."
        # )
        return my_price
    else:
        # Рассчитываем новую цену с небольшим случайным отклонением (3-5% ниже минимальной цены поставщика)
        discount_factor = round(random.uniform(0.95, 0.97), 2)
        new_price = min_supplier_price * discount_factor
        # logger.info(
        #     f"Рассчитана новая цена: {new_price} (коэффициент: {discount_factor} * {min_supplier_price})"
        # )
        return round(new_price, 2)


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

        # Создаем маппинг артикулов с учетом префиксов
        sku_mapping = create_sku_mapping(df)

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

        # Словари для хранения данных по артикулам
        my_site_data = {}  # {sku: price}
        xcore_data = {}  # {sku: price}
        insportline_data = {}  # {sku: price}

        # Шаг 1: Собираем все данные по артикулам
        for _, row in df.iterrows():
            my_sku = str(row["Мой_сайт_sku"]).strip()
            xcore_sku = str(row.get("xcore_sku", "")).strip()
            insportline_code = str(row.get("insportline_vendor_code", "")).strip()

            # Сохраняем данные по моему сайту
            if my_sku:
                try:
                    my_price = (
                        float(row["Мой_сайт_цена"])
                        if pd.notna(row.get("Мой_сайт_цена"))
                        else 0
                    )
                    my_site_data[my_sku] = my_price
                except (ValueError, TypeError):
                    my_site_data[my_sku] = 0

            # Сохраняем данные по Xcore
            if xcore_sku:
                try:
                    xcore_price = (
                        float(row.get("xcore_price", 0))
                        if pd.notna(row.get("xcore_price"))
                        else 0
                    )
                    if xcore_price > 0:
                        xcore_data[xcore_sku] = xcore_price
                except (ValueError, TypeError):
                    pass

            # Сохраняем данные по Insportline
            if insportline_code:
                try:
                    insportline_price = (
                        float(row.get("insportline_цена", 0))
                        if pd.notna(row.get("insportline_цена"))
                        else 0
                    )
                    if insportline_price > 0:
                        insportline_data[insportline_code] = insportline_price
                except (ValueError, TypeError):
                    pass

        logger.info(
            f"Собрано артикулов: my_site={len(my_site_data)}, xcore={len(xcore_data)}, insportline={len(insportline_data)}"
        )

        # Шаг 2: Обрабатываем собранные данные
        processed_count = 0
        matched_count = 0

        for my_sku, my_price in my_site_data.items():
            processed_count += 1

            # Инициализируем цены поставщиков
            xcore_price = 0
            insportline_price = 0

            # Проверяем прямое совпадение для Xcore
            if my_sku in xcore_data:
                xcore_price = xcore_data[my_sku]
                # logger.info(f"Прямое совпадение для {my_sku} с Xcore: {xcore_price}")
            # Проверяем совпадение через маппинг для Xcore
            elif my_sku in sku_mapping and sku_mapping[my_sku] in xcore_data:
                mapped_sku = sku_mapping[my_sku]
                xcore_price = xcore_data[mapped_sku]
                # logger.info(
                #     f"Совпадение через маппинг для {my_sku} -> {mapped_sku} с Xcore: {xcore_price}"
                # )

            # Проверяем прямое совпадение для Insportline
            if my_sku in insportline_data:
                insportline_price = insportline_data[my_sku]
                # logger.info(
                #     f"Прямое совпадение для {my_sku} с Insportline: {insportline_price}"
                # )

            # Определяем, есть ли совпадение хотя бы с одним поставщиком
            is_match = xcore_price > 0 or insportline_price > 0

            if not is_match:
                # logger.info(f"Нет совпадений для артикула {my_sku}")
                continue

            matched_count += 1

            # Проверяем валидность цен (игнорируем цены 1 или 2)
            valid_prices = []

            if xcore_price > 2:
                valid_prices.append(xcore_price)

            if insportline_price > 2:
                valid_prices.append(insportline_price)

            # Проверяем наличие валидных цен
            if not valid_prices:
                logger.info(f"Для артикула {my_sku} нет валидных цен поставщиков")
                continue

            # Фильтруем цены
            filtered_prices = filter_prices(
                my_price, valid_prices, xcore_price, insportline_price
            )

            # Рассчитываем новую цену
            new_price = calculate_new_price(my_price, filtered_prices)

            # Добавляем результат
            result_df = result_df._append(
                {
                    "Артикул": my_sku,
                    "стара_ціна": my_price,
                    "нова_ціна": new_price,
                    "Ціна_Xcore": xcore_price if xcore_price > 2 else "-",
                    "Ціна_Insportline": (
                        insportline_price if insportline_price > 2 else "-"
                    ),
                },
                ignore_index=True,
            )

        logger.info(
            f"Обработано {processed_count} позиций, найдено совпадений: {matched_count}"
        )

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

            logger.info(f"Результаты выгружены в лист '{result_sheet_name}'.")
        except Exception as e:
            logger.error(
                f"Ошибка при выгрузке результатов в лист '{result_sheet_name}': {e}"
            )
            raise

        return result_df

    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {e}")
        raise


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
            timeout=200,
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


def normalize_sku(sku):
    """
    Нормализует SKU, удаляя префикс 'INS' если он есть.
    Например: 'INS9410-3' -> '9410-3'
    """
    if sku and isinstance(sku, str):
        if sku.startswith("INS"):
            return sku[3:]  # Удаляем первые 3 символа (INS)
    return sku


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


# Пример использования
if __name__ == "__main__":
    get_json_xcore()
    download_all_xml_files()
    parsin_xml()
    source_sheet = "Data"  # Имя листа с исходными данными
    result_sheet = "result"  # Имя листа для результатов

    try:
        results = process_prices(source_sheet, result_sheet)
        print(f"Обработано товаров: {len(results)}")
    except gspread.exceptions.APIError as e:
        if "429" in str(e):
            print(
                "Превышена квота API Google Sheets. Пожалуйста, подождите несколько минут и попробуйте снова."
            )
        else:
            print(f"Ошибка API: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
