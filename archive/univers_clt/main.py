from urllib.parse import urlparse, parse_qs
import requests
from selectolax.parser import HTMLParser
import os
import json
import asyncio
import aiofiles
import glob
from curl_cffi.requests import AsyncSession
from bd import initialize_db
from configuration.config import database
from typing import List, Dict
from configuration.logging_config import logger
from sqlalchemy.exc import SQLAlchemyError
import shutil

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
data_path = os.path.join(current_directory, "data")
logging_path = os.path.join(current_directory, "logging")
view_property_C_path = os.path.join(temp_path, "view_property_C")
view_property_R_path = os.path.join(temp_path, "view_property_R")


def сreation_temp_directory():
    # Создание директории, если она не существует
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(data_path, exist_ok=True)
    os.makedirs(view_property_C_path, exist_ok=True)
    os.makedirs(view_property_R_path, exist_ok=True)


# Функция для удаления папки и её содержимого
def remove_temp_directory():
    try:
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            logger.info(f"Папка {temp_path} успешно удалена.")
        else:
            logger.warning(f"Папка {temp_path} не существует.")
    except Exception as e:
        logger.error(f"Ошибка при удалении папки {temp_path}: {e}")


def get_all_url():
    cookies = {
        "PHPSESSID": "li2h6f073blagdq5h70ehh2n71",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    data = {
        "paging_off": "View All Results",
    }
    filename = os.path.join(data_path, "all_url.html")
    response = requests.post(
        "https://gilford.univers-clt.com/index.php",
        cookies=cookies,
        headers=headers,
        data=data,
        verify=False,  # запрос без проверки SSL-сертификата.
    )
    if response.status_code == 200:
        html = response.content

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html.decode("utf-8"))
        logger.info(f"Скачал файл {filename} где находятся все ссылки")
    else:
        logger.error(f"Статус {response.status_code} !!!")


# Функция для безопасного извлечения значения атрибута href из элемента a
def safe_extract_href(element, default=None):
    return (
        f"https://gilford.univers-clt.com/{element.attributes.get('href', default)}"
        if element
        else default
    )


# Функция для сохранения ссылок в JSON-файл
async def save_hrefs_to_json(hrefs):
    filename = os.path.join(data_path, "all_url.json")
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(hrefs, ensure_ascii=False, indent=4))
    logger.info(f"Сохранил файл {filename} где находятся все {len(hrefs)} ссылки")


# Основная функция для извлечения данных
async def extract_url():
    filename = os.path.join(data_path, "all_url.html")
    async with aiofiles.open(filename, encoding="utf-8") as file:
        content = await file.read()

    parser = HTMLParser(content)

    # Извлекаем таблицу по селектору
    details_table = parser.css_first("body > div > table:nth-child(6) > tbody")
    hrefs = []
    if details_table:
        # Находим все td, содержащие текст "View Details"
        details_tds = details_table.css("td")
        for td in details_tds:
            a_tag = td.css_first("a")
            if a_tag and "View Details" in a_tag.text():
                hrefs.append(safe_extract_href(a_tag))

    # Сохраняем ссылки в JSON-файл
    await save_hrefs_to_json(hrefs)


# Функция для выполнения запроса
async def fetch_url(url, sem):
    cookies = {
        "PHPSESSID": "li2h6f073blagdq5h70ehh2n71",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    async with sem:
        async with AsyncSession() as session:
            view_property_C_path = os.path.join(temp_path, "view_property_C")
            view_property_R_path = os.path.join(temp_path, "view_property_R")
            path = urlparse(url).path
            view_property = path.split("/")[-1].split(".")[0]
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            accnum = query_params.get("account_no", [None])[0]
            series_card = query_params.get("series_card", [None])[0]

            if view_property == "view_property_C":
                filename_html = os.path.join(
                    view_property_C_path, f"{accnum}_{series_card}.html"
                )
            else:
                filename_html = os.path.join(
                    view_property_R_path, f"{accnum}_{series_card}.html"
                )

            if not os.path.exists(filename_html):
                try:
                    response = await session.get(
                        url,
                        cookies=cookies,
                        headers=headers,
                        verify=False,
                    )
                    response.raise_for_status()
                    src = response.text
                    with open(filename_html, "w", encoding="utf-8") as f:
                        f.write(src)
                    logger.info(f"Скаченно: {filename_html}")
                except Exception as e:
                    logger.error(f"Ошибка {url}: {e}")
                await asyncio.sleep(1)
            else:
                logger.error(f"Файл уже есть {filename_html}")


# Основная функция для распределения URL и запуска задач
async def get_html():
    tasks = []
    # Устанавливаем ограничение на количество одновременно выполняемых задач
    sem = asyncio.Semaphore(10)  # Ограничение на 10 одновременно выполняемых задач
    filename = os.path.join(data_path, "all_url.json")
    # Чтение JSON файла
    with open(filename, "r", encoding="utf-8") as f:
        urls_data = json.load(f)
    # Получение списка URL
    urls = urls_data if isinstance(urls_data, list) else []

    for url in urls:
        tasks.append(fetch_url(url, sem))

    await asyncio.gather(*tasks)


async def save_view_property_C_to_json(data):
    filename = os.path.join(data_path, "view_property_C.json")
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))
    logger.info(
        f"Сохранил файл {filename} где находятся все ссылки с {len(data)} словарями"
    )


async def save_view_property_R_to_json(data):
    filename = os.path.join(data_path, "view_property_R.json")
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))
    logger.info(
        f"Сохранили файл {filename} где находятся все ссылки с {len(data)} словарями"
    )


# Функция парсинга view_property_C_path
async def extract_view_property_C():
    folder = os.path.join(view_property_C_path, "*.html")
    all_datas = []
    files_html = glob.glob(folder)
    for item in files_html:
        async with aiofiles.open(item, encoding="utf-8") as file:
            content = await file.read()

        parser = HTMLParser(content)

        data = {}

        # Функция для безопасного извлечения текста из элемента
        def safe_extract(element, default=None):
            return element.text(strip=True) if element else default

        # Извлекаем заголовки и значения из указанной таблицы
        table_selector = "body > div > table:nth-child(4) > tbody"
        header_row_selector = f"{table_selector} > tr:nth-child(2)"
        value_row_selector = f"{table_selector} > tr:nth-child(3)"

        header_row = parser.css_first(header_row_selector)
        value_row = parser.css_first(value_row_selector)

        if header_row and value_row:
            headers = [cell.text(strip=True) for cell in header_row.css("td.form-h2")]
            values = [cell.text(strip=True) for cell in value_row.css("td.form-input")]

            # Убедимся, что у нас есть все нужные данные
            if len(headers) >= 7 and len(values) >= 7:
                data["accnum"] = values[0]
                data["card"] = values[1]
                data["mapblocklot"] = values[2]
                data["locat"] = values[3]
                data["zoning"] = values[4]
                data["stateclass"] = values[5]
                data["acres"] = values[6]
        # Извлекаем информацию о владельце по новому селектору
        owner_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(1) > tbody"
        )
        if owner_info_table:
            owner_info_rows = owner_info_table.css("tr")
            owner_data = [
                safe_extract(row.css_first("td.form-input"))
                for row in owner_info_rows
                if row.css_first("td.form-input")
            ]
            if len(owner_data) >= 3:
                data["ownername"] = owner_data[0]
                data["owneradd1"] = owner_data[1]
                data["owneradd2"] = owner_data[2]

        # Извлекаем информацию о документе по новому селектору
        deed_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(3) > tbody"
        )
        if deed_info_table:
            deed_info_rows = deed_info_table.css("tr")
            for row in deed_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                label_text = safe_extract(label_cell)
                input_text = safe_extract(input_cell)
                if label_text == "Book/Page:":
                    data["bookpage"] = input_text
                elif label_text == "Deed Date:":
                    data["deeddate"] = input_text

        # Извлекаем информацию о здании по новому селектору
        building_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(5) > tbody"
        )
        if building_info_table:
            building_info_rows = building_info_table.css("tr")
            for row in building_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                label_text = safe_extract(label_cell)
                input_text = safe_extract(input_cell)
                if label_text == "Building No:":
                    data["buildingno"] = input_text
                elif label_text == "Year Built:":
                    data["yearbuilt"] = input_text
                elif label_text == "No of Units:":
                    data["noofunits"] = input_text
                elif label_text == "Structure Type:":
                    data["structuretype"] = input_text
                elif label_text == "Grade:":
                    data["grade"] = input_text
                elif label_text == "Identical Units:":
                    data["identicalunits"] = input_text

        # Извлекаем информацию о стоимости по новому селектору
        valuation_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(7) > tbody"
        )
        if valuation_info_table:
            valuation_info_rows = valuation_info_table.css("tr")
            for row in valuation_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                label_text = safe_extract(label_cell)
                input_text = safe_extract(input_cell)
                if label_text == "Land:":
                    data["land"] = input_text
                elif label_text == "Building:":
                    data["building"] = input_text
                elif label_text == "Total:":
                    data["total"] = input_text
                elif label_text == "Net Assessment:":
                    data["netassessment"] = input_text

        # Извлекаем информацию о продажах по новому селектору
        sales_history_table = parser.css_first(
            "body > div > table:nth-child(7) > tbody"
        )
        if sales_history_table:
            sales_history_rows = sales_history_table.css("tr")
            sales_data = []
            for row in sales_history_rows:
                input_cells = row.css("td.form-input")
                if input_cells:
                    sale_entry = {
                        "bookpage": safe_extract(input_cells[0]),
                        "date": safe_extract(input_cells[1]),
                        "price": safe_extract(input_cells[2]),
                        "type": safe_extract(input_cells[3]),
                        "validity": safe_extract(input_cells[4]),
                    }
                    sales_data.append(sale_entry)
                    if len(sales_data) >= 2:
                        break  # Останавливаемся после извлечения данных из первых двух строк

            # Добавляем данные в общий словарь, добавляя суффиксы 1 и 2
            for i, sale in enumerate(sales_data, start=1):
                data[f"bookpage{i}"] = sale["bookpage"]
                data[f"date{i}"] = sale["date"]
                data[f"price{i}"] = sale["price"]
                data[f"type{i}"] = sale["type"]
                data[f"validity{i}"] = sale["validity"]

        # Извлекаем информацию о внешних строениях по новому селектору
        out_building_info_table = parser.css_first(
            "body > div > table:nth-child(9) > tbody"
        )
        if out_building_info_table:
            out_building_info_rows = out_building_info_table.css("tr")
            out_building_data = []
            for row in out_building_info_rows:
                input_cells = row.css("td.form-input")
                if input_cells:
                    out_building_entry = {
                        "structurecode": safe_extract(input_cells[0]),
                        "width": safe_extract(input_cells[1]),
                        "lgth_sf": safe_extract(input_cells[2]),
                        "year": safe_extract(input_cells[3]),
                        "rcnld": safe_extract(input_cells[4]),
                    }
                    out_building_data.append(out_building_entry)
                    if len(out_building_data) >= 2:
                        break  # Останавливаемся после извлечения данных из первых двух строк

            # Добавляем данные в общий словарь, добавляя суффиксы 1 и 2
            for i, building in enumerate(out_building_data, start=1):
                data[f"structurecode{i}"] = building["structurecode"]
                data[f"width{i}"] = building["width"]
                data[f"lgth_sf{i}"] = building["lgth_sf"]
                data[f"year{i}"] = building["year"]
                data[f"rcnld{i}"] = building["rcnld"]

        # Извлекаем информацию об экстерьере/интерьере по новому селектору
        exterior_interior_info_table = parser.css_first(
            "body > div > table:nth-child(11) > tbody"
        )
        if exterior_interior_info_table:
            exterior_interior_info_rows = exterior_interior_info_table.css("tr")
            exterior_interior_data = []
            for row in exterior_interior_info_rows:
                input_cells = row.css("td.form-input")
                if input_cells:
                    exterior_interior_entry = {
                        "levels": safe_extract(input_cells[0]),
                        "size": safe_extract(input_cells[1]),
                        "usetype": safe_extract(input_cells[2]),
                        "extwalls": safe_extract(input_cells[3]),
                        "consttype": safe_extract(input_cells[4]),
                        "partitions": safe_extract(input_cells[5]),
                        "heating": safe_extract(input_cells[6]),
                        "aircond": safe_extract(input_cells[7]),
                        "plumbing": safe_extract(input_cells[8]),
                        "condition": safe_extract(input_cells[9]),
                        "funcutility": safe_extract(input_cells[10]),
                        "unadjrcnld": safe_extract(input_cells[11]),
                    }
                    exterior_interior_data.append(exterior_interior_entry)
                    if len(exterior_interior_data) >= 5:
                        break  # Останавливаемся после извлечения данных из первых пяти строк

            # Добавляем данные в общий словарь, добавляя суффиксы 1, 2, 3, 4, 5
            for i, ext_int in enumerate(exterior_interior_data, start=1):
                data[f"levels{i}"] = ext_int["levels"]
                data[f"size{i}"] = ext_int["size"]
                data[f"usetype{i}"] = ext_int["usetype"]
                data[f"extwalls{i}"] = ext_int["extwalls"]
                data[f"consttype{i}"] = ext_int["consttype"]
                data[f"partitions{i}"] = ext_int["partitions"]
                data[f"heating{i}"] = ext_int["heating"]
                data[f"aircond{i}"] = ext_int["aircond"]
                data[f"plumbing{i}"] = ext_int["plumbing"]
                data[f"condition{i}"] = ext_int["condition"]
                data[f"funcutility{i}"] = ext_int["funcutility"]
                data[f"unadjrcnld{i}"] = ext_int["unadjrcnld"]
        all_datas.append(data)
    await save_view_property_C_to_json(all_datas)


# Функция парсинга view_property_R_path
async def extract_view_property_R():
    folder = os.path.join(view_property_R_path, "*.html")
    all_datas = []
    files_html = glob.glob(folder)
    for item in files_html:
        async with aiofiles.open(item, encoding="utf-8") as file:
            content = await file.read()

        parser = HTMLParser(content)

        data = {}

        # Функция для безопасного извлечения текста из элемента
        def safe_extract(element, default=None):
            return element.text(strip=True) if element else default

        # Извлекаем заголовки и значения из указанной таблицы
        table_selector = "body > div > table:nth-child(4) > tbody"
        header_row_selector = f"{table_selector} > tr:nth-child(2)"
        value_row_selector = f"{table_selector} > tr:nth-child(3)"

        header_row = parser.css_first(header_row_selector)
        value_row = parser.css_first(value_row_selector)

        if header_row and value_row:
            headers = [cell.text(strip=True) for cell in header_row.css("td.form-h2")]
            values = [cell.text(strip=True) for cell in value_row.css("td.form-input")]

            # Убедимся, что у нас есть все нужные данные
            if len(headers) >= 7 and len(values) >= 7:
                data["accnum"] = values[0]
                data["card"] = values[1]
                data["mapblocklot"] = values[2]
                data["locat"] = values[3]
                data["zoning"] = values[4]
                data["stateclass"] = values[5]
                data["acres"] = values[6]
        # Извлекаем информацию о владельце по новому селектору
        owner_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(1) > tbody"
        )
        if owner_info_table:
            owner_info_rows = owner_info_table.css("tr")
            owner_data = [
                safe_extract(row.css_first("td.form-input"))
                for row in owner_info_rows
                if row.css_first("td.form-input")
            ]
            if len(owner_data) >= 3:
                data["ownername"] = owner_data[0]
                data["owneradd1"] = owner_data[1]
                data["owneradd2"] = owner_data[2]

        # Извлекаем информацию о документе по новому селектору
        deed_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(3) > tbody"
        )
        if deed_info_table:
            deed_info_rows = deed_info_table.css("tr")
            for row in deed_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                label_text = safe_extract(label_cell)
                input_text = safe_extract(input_cell)
                if label_text == "Book/Page:":
                    data["bookpage"] = input_text
                elif label_text == "Deed Date:":
                    data["deeddate"] = input_text

        # Извлечение информации о жилье по новому селектору
        dwelling_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(5) > tbody"
        )
        if dwelling_info_table:
            dwelling_info_rows = dwelling_info_table.css("tr")
            for row in dwelling_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                if label_cell and input_cell:
                    label_text = label_cell.text(strip=True)
                    input_text = input_cell.text(strip=True)
                    if label_text == "Style:":
                        data["style"] = input_text
                    elif label_text == "Story Height:":
                        data["story"] = input_text
                    elif label_text == "Attic:":
                        data["attic"] = input_text
                    elif label_text == "Basement:":
                        data["basement"] = input_text
                    elif label_text == "Year Built:":
                        data["yearbuilt"] = input_text
                    elif label_text == "Ground Flr Area:":
                        data["groundflrarea"] = input_text
                    elif label_text == "Tot Living Area:":
                        data["totlivingarea"] = input_text
                    elif label_text == "Rooms:":
                        data["rooms"] = input_text
                    elif label_text == "Bedrooms:":
                        data["bedrooms"] = input_text
                    elif label_text == "Full Baths:":
                        data["fullbaths"] = input_text
                    elif label_text == "Half Baths:":
                        data["halfbaths"] = input_text
        # Извлекаем информацию о стоимости по новому селектору
        valuation_info_table = parser.css_first(
            "body > div > table:nth-child(6) > tbody > tr > td:nth-child(1) > table:nth-child(7) > tbody"
        )
        if valuation_info_table:
            valuation_info_rows = valuation_info_table.css("tr")
            for row in valuation_info_rows:
                label_cell = row.css_first("td.form-label")
                input_cell = row.css_first("td.form-input")
                label_text = safe_extract(label_cell)
                input_text = safe_extract(input_cell)
                if label_text == "Land:":
                    data["land"] = input_text
                elif label_text == "Building:":
                    data["building"] = input_text
                elif label_text == "Total:":
                    data["total"] = input_text
                elif label_text == "Net Assessment:":
                    data["netassessment"] = input_text
        # Извлекаем информацию о продажах по новому селектору
        sales_history_table = parser.css_first(
            "body > div > table:nth-child(7) > tbody"
        )
        if sales_history_table:
            sales_history_rows = sales_history_table.css("tr")
            sales_data = []
            for row in sales_history_rows:
                input_cells = row.css("td.form-input")
                if input_cells:
                    sale_entry = {
                        "bookpage": safe_extract(input_cells[0]),
                        "date": safe_extract(input_cells[1]),
                        "price": safe_extract(input_cells[2]),
                        "type": safe_extract(input_cells[3]),
                        "validity": safe_extract(input_cells[4]),
                    }
                    sales_data.append(sale_entry)
                    if len(sales_data) >= 2:
                        break  # Останавливаемся после извлечения данных из первых двух строк

            # Добавляем данные в общий словарь, добавляя суффиксы 1 и 2
            for i, sale in enumerate(sales_data, start=1):
                data[f"bookpage{i}"] = sale["bookpage"]
                data[f"date{i}"] = sale["date"]
                data[f"price{i}"] = sale["price"]
                data[f"type{i}"] = sale["type"]
                data[f"validity{i}"] = sale["validity"]
        # Извлекаем информацию о внешних строениях по новому селектору
        out_building_info_table = parser.css_first(
            "body > div > table:nth-child(9) > tbody"
        )
        if out_building_info_table:
            out_building_info_rows = out_building_info_table.css("tr")
            out_building_data = []
            for row in out_building_info_rows:
                input_cells = row.css("td.form-input")
                if input_cells:
                    out_building_entry = {
                        "outbuildingtype": safe_extract(input_cells[0]),
                        "qty": safe_extract(input_cells[1]),
                        "year": safe_extract(input_cells[2]),
                        "size_1": safe_extract(input_cells[3]),
                        "size_2": safe_extract(input_cells[4]),
                        "grade": safe_extract(input_cells[4]),
                        "cond": safe_extract(input_cells[4]),
                    }
                    out_building_data.append(out_building_entry)
                    if len(out_building_data) >= 2:
                        break  # Останавливаемся после извлечения данных из первых двух строк

            # Добавляем данные в общий словарь, добавляя суффиксы 1 и 2
            for i, building in enumerate(out_building_data, start=1):
                data[f"outbuildingtype{i}"] = building["outbuildingtype"]
                data[f"qty{i}"] = building["qty"]
                data[f"year{i}"] = building["year"]
                data[f"size{i}_1"] = building["size_1"]
                data[f"size{i}_2"] = building["size_2"]
                data[f"grade{i}"] = building["grade"]
                data[f"cond{i}"] = building["cond"]
        all_datas.append(data)
    await save_view_property_R_to_json(all_datas)


# Функция для чтения JSON-файлов и преобразования их в списки словарей
async def read_json_file(file_path: str) -> List[Dict]:
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()
            data = json.loads(content)
            logger.info(f"Количество строк {len(data)} в {file_path}")
            return data
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return []


# Функция для записи данных в таблицу базы данных
async def insert_data_into_db(data: List[Dict], table_name: str):
    # Обновляем каждый словарь в data, добавляя отсутствующие ключи со значением None
    all_keys = {key for item in data for key in item.keys()}
    for item in data:
        for key in all_keys:
            item.setdefault(key, None)

    # Создаем шаблон запроса с учетом всех возможных ключей
    query = f"INSERT INTO {table_name} ({', '.join(all_keys)}) VALUES ({', '.join([':' + key for key in all_keys])})"

    try:
        await database.connect()
        await database.execute_many(query=query, values=data)
    except SQLAlchemyError as e:
        logger.error(f"Error in insert_data_into_db: {e}")
    finally:
        await database.disconnect()


# Функция для очистки таблицы
async def clear_table(table_name: str):
    try:
        await database.connect()
        query = f"DELETE FROM {table_name}"
        await database.execute(query)
        await database.disconnect()
        logger.info(f"Таблица {table_name} очищенна.")
    except SQLAlchemyError as e:
        logger.error(f"Error clearing table {table_name}: {e}")


# Основная функция для обработки файлов и записи данных
async def wr_bd():
    try:
        # Очищаем таблицы перед записью данных
        await clear_table("uni_com_all")
        await clear_table("uni_res_all")
        # Путь к файлу view_property_C.json
        com_file_path = os.path.join(data_path, "view_property_C.json")
        # Обработка view_property_C.json и запись в uni_com_all
        com_data = await read_json_file(com_file_path)
        await insert_data_into_db(com_data, "uni_com_all")

        # Путь к файлу view_property_R.json
        res_file_path = os.path.join(data_path, "view_property_R.json")
        # Обработка view_property_R.json и запись в uni_res_all
        res_data = await read_json_file(res_file_path)
        await insert_data_into_db(res_data, "uni_res_all")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")


while True:
    # Запрос ввода от пользователя
    print(
        "Введите 1 получения всех ссылок"
        "\nВведите 2 для получения всех файлов"
        "\nВведите 3 для парсинга и записи в БД"
        "\nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        remove_temp_directory()
        сreation_temp_directory()
        try:
            initialize_db()
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
        get_all_url()
        asyncio.run(extract_url())

    elif user_input == 2:
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(get_html())
        except Exception as e:
            logger.error(f"Ошибка при выполнении get_html: {e}")
    elif user_input == 3:
        asyncio.run(extract_view_property_C())
        asyncio.run(extract_view_property_R())
        asyncio.run(wr_bd())
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
