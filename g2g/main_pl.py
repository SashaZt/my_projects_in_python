# -*- mode: python ; coding: utf-8 -*-
import asyncio
import aiofiles
import json
import os
import csv
import pandas as pd
import shutil
import sys
from openpyxl import Workbook
from glob import glob
import asyncio
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import math
import re
import csv
import json
import os
import glob
from asyncio import sleep
from selectolax.parser import HTMLParser


async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


async def save_response_json(json_response, file_path):
    """Асинхронно сохраняет JSON-данные в файл."""
    async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


# Скачивание файлов json
async def fetch_and_save_json(href, session, file_path):
    async with session.get(href) as response:
        # Проверяем статус ответа
        if response.status == 200:
            json_data = await response.json()
            # Сохраняем полученный JSON в файл
            async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
                await f.write(json.dumps(json_data, ensure_ascii=False, indent=4))
        else:
            print(f"Ошибка при запросе {href}: {response.status}")


# Создание задание на скачивание
async def process_hrefs(all_hrefs, session, type_pars):
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")
    tasks = []
    for href in all_hrefs:
        match = re.search(r"/([^/?]+)\?", href)
        if match:
            id_product = match.group(1)
            filename = f"{id_product}.json"
            if type_pars == 1:
                file_path = os.path.join(path_json_GamePal, filename)
            elif type_pars == 0:
                file_path = os.path.join(path_json_item, filename)
            # Создаем задачу для асинхронного выполнения
            task = fetch_and_save_json(href, session, file_path)
            tasks.append(task)
    # Выполняем все задачи асинхронно
    await asyncio.gather(*tasks)


# Основаная функция
async def run(url_start, type_pars):
    timeout = 20000
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        shutil.rmtree(temp_path)
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    # Убедитесь, что папки существуют или создайте их
    await create_directories_async(
        [
            temp_path,
            path_json_GamePal,
            path_json_item,
        ]
    )
    async with async_playwright() as playwright, aiohttp.ClientSession() as session:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(url_start)
        await sleep(5)
        xpath_about_results = '//div[@class="text-secondary"]'
        await page.wait_for_selector(f"xpath={xpath_about_results}", timeout=timeout)
        text_about_results = await page.text_content(xpath_about_results)
        count_url = int(
            re.search(r"(\d+)", text_about_results.replace(",", "")).group(0)
        )

        url_in_page = 48
        list_pages = math.ceil(count_url / url_in_page)

        xpath_about_results = '//div[@class="text-secondary"]'
        await page.wait_for_selector(f"xpath={xpath_about_results}", timeout=timeout)

        # Items
        if type_pars == 0:
            all_hrefs = []

            for pages in range(1, list_pages + 1):

                await page.goto(f"{url_start}&page={pages}")
                xpath_href = (
                    '//div[@class="full-height full-width position-relative"]/a'
                )
                await page.wait_for_selector(xpath_href, timeout=10000)
                href_elements = await page.query_selector_all(xpath_href)
                current_page_hrefs = [
                    await element.get_attribute("href") for element in href_elements
                ]

                for current in current_page_hrefs:
                    match = re.search(r"/([^/?]+)\?", current)
                    if match:
                        id_product = match.group(1)
                        all_hrefs.append(
                            f"https://sls.g2g.com/offer/{id_product}?currency=USD&country=UA&include_out_of_stock=1"
                        )
            async with aiohttp.ClientSession() as session:
                await process_hrefs(all_hrefs, session, type_pars)
            await browser.close()
        # GamePal
        elif type_pars == 1:
            all_hrefs = []
            counter = 0
            for pages in range(1, list_pages + 1):
                counter += 1

                # Устанавливаем обработчик для сбора и сохранения данных ответов
                def create_log_response_with_counter(file_path, session):
                    async def log_response(response):
                        # Паттерн для поиска в URL ответа.
                        pattern_service_id = re.compile(
                            r"https://sls\.g2g\.com/offer/search\?service_id=[^&]+"
                        )

                        request = response.request
                        if request.method == "GET" and pattern_service_id.search(
                            request.url
                        ):
                            updated_url = request.url.replace(
                                "currency=EUR", "currency=USD"
                            )
                            try:
                                # Используем переданную сессию для выполнения запроса к обновленному URL.
                                async with session.get(updated_url) as new_response:
                                    if new_response.status == 200:
                                        json_response = await new_response.json()
                                        await save_response_json(
                                            json_response, file_path
                                        )
                                    else:
                                        print(
                                            f"Ошибка запроса к {updated_url}: HTTP статус {new_response.status}"
                                        )
                            except Exception as e:
                                print(f"Ошибка при запросе к {updated_url}: {e}")
                        pattern_seo_term = re.compile(
                            r"https://sls\.g2g\.com/offer/search\?seo_term=[^&]+"
                        )
                        if request.method == "GET" and pattern_seo_term.search(
                            request.url
                        ):
                            updated_url = request.url.replace(
                                "currency=EUR", "currency=USD"
                            )
                            try:
                                # Используем переданную сессию для выполнения запроса к обновленному URL.
                                async with session.get(updated_url) as new_response:
                                    if new_response.status == 200:
                                        json_response = await new_response.json()
                                        await save_response_json(
                                            json_response, file_path
                                        )
                                    else:
                                        print(
                                            f"Ошибка запроса к {updated_url}: HTTP статус {new_response.status}"
                                        )
                            except Exception as e:
                                print(f"Ошибка при запросе к {updated_url}: {e}")

                    return log_response

                # for href in all_hrefs:
                #     match = re.search(r"/([^/?]+)\?", href)
                #     if match:
                #         id_product = match.group(1)
                # if type_pars == 1:
                filename = f"{counter}.json"
                file_path = os.path.join(path_json_GamePal, filename)

                handler = create_log_response_with_counter(file_path, session)

                page.on("response", handler)

                previous_handler = handler
                if previous_handler:
                    page.remove_listener("response", previous_handler)
                handler = create_log_response_with_counter(file_path, session)

                page.on("response", handler)
                previous_handler = handler
                await page.goto(f"{url_start}&page={pages}")
                await sleep(5)
                if previous_handler:
                    page.remove_listener("response", previous_handler)
        await browser.close()


async def save_hrefs_to_json(all_hrefs):
    # Откройте файл в асинхронном режиме и запишите данные
    async with aiofiles.open("all_hrefs.json", "w") as file:
        # Конвертируйте список в JSON и запишите в файл
        await file.write(json.dumps(all_hrefs, indent=4))


async def run_html(url_start, type_pars):
    timeout = 20000
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        shutil.rmtree(temp_path)
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    # Убедитесь, что папки существуют или создайте их
    await create_directories_async(
        [
            temp_path,
            path_json_GamePal,
            path_json_item,
        ]
    )
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        cookies = [
            {
                "domain": ".www.g2g.com",
                "httpOnly": False,
                "name": "g2g_regional",
                "path": "/",
                "secure": True,
                "value": "%7B%22country%22%3A%22UA%22%2C%22currency%22%3A%22USD%22%2C%22language%22%3A%22en%22%7D",
            }
        ]
        await context.add_cookies(cookies)

        await page.goto(url_start)
        await sleep(5)
        xpath_about_results = '//div[@class="text-secondary"]'
        await page.wait_for_selector(f"xpath={xpath_about_results}", timeout=timeout)
        text_about_results = await page.text_content(xpath_about_results)
        count_url = int(
            re.search(r"(\d+)", text_about_results.replace(",", "")).group(0)
        )

        url_in_page = 48
        list_pages = math.ceil(count_url / url_in_page)

        xpath_about_results = '//div[@class="text-secondary"]'
        await page.wait_for_selector(f"xpath={xpath_about_results}", timeout=timeout)

        # Items
        if type_pars == 0:
            all_hrefs = []

            for pages in range(1, list_pages + 1):

                await page.goto(f"{url_start}&page={pages}")
                await page.wait_for_selector(
                    "div.full-height.full-width.position-relative > a"
                )

                # Получите все элементы a внутри div
                link_elements = await page.query_selector_all(
                    "div.full-height.full-width.position-relative > a"
                )

                # Извлеките из каждого элемента атрибут href и сохраните в список
                for link_element in link_elements:
                    href = await link_element.get_attribute("href")
                    # Проверяем, начинается ли ссылка с http:// или https://
                    if href.startswith("http://") or href.startswith("https://"):
                        all_hrefs.append(href)  # Ссылка уже полная, добавляем как есть
                    else:
                        all_hrefs.append(
                            f"https://www.g2g.com{href}"
                        )  # Добавляем префикс, если это относительная ссылка

            await save_hrefs_to_json(all_hrefs)
            await browser.close()
        # GamePal
        elif type_pars == 1:
            all_hrefs = []
            counter = 0
            for pages in range(1, list_pages + 1):
                await page.goto(f"{url_start}&page={pages}")
                await page.wait_for_selector(
                    "div.full-height.full-width.position-relative > a"
                )

                # Получите все элементы a внутри div
                link_elements = await page.query_selector_all(
                    "div.full-height.full-width.position-relative > a"
                )

                # Извлеките из каждого элемента атрибут href и сохраните в список
                for link_element in link_elements:
                    href = await link_element.get_attribute("href")
                    all_hrefs.append(f"https://www.g2g.com{href}")
            await save_hrefs_to_json(all_hrefs)

            await browser.close()


async def save_page_content_html(page, file_path):
    # current_directory = os.getcwd()
    # temp_path = os.path.join(current_directory, "temp")
    # path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    # path_json_item = os.path.join(temp_path, "json_Item")
    # part_url = url.split("/")[-1].split("?")[-2]
    # filename = f"{part_url}.html"

    # # Определение пути сохранения в зависимости от типа разбора
    # if type_pars == 1:
    #     file_path = os.path.join(path_json_GamePal, filename)
    # else:
    #     file_path = os.path.join(path_json_item, filename)

    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)


write_lock = asyncio.Lock()


async def read_hrefs_from_json():
    async with aiofiles.open("all_hrefs.json", "r") as file:
        data = await file.read()
        all_hrefs = json.loads(data)
    return all_hrefs


def divide_data(data, n):
    """Разделяем данные на n равных частей"""
    k, m = divmod(len(data), n)
    return (data[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


async def process_urls_html(urls, playwright_instance, type_pars):
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")

    # Определение пути сохранения в зависимости от типа разбора

    """Функция для обработки списка URL"""
    browser = await playwright_instance.chromium.launch(headless=False)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()

    for url in urls:
        part_url = url.split("/")[-1].split("?")[-2]
        filename = f"{part_url}.html"
        if type_pars == 1:
            file_path = os.path.join(path_json_GamePal, filename)
        else:
            file_path = os.path.join(path_json_item, filename)
            # Обезательно ждать загрузки всей страницы
        if not os.path.exists(file_path):
            await page.goto(url, wait_until="networkidle")
            await save_page_content_html(page, file_path)
    await browser.close()


async def main_html(type_pars):
    current_directory = os.getcwd()
    n = 5
    all_hrefs = await read_hrefs_from_json()
    divided_hrefs = list(divide_data(all_hrefs, n))
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    async with async_playwright() as playwright_instance:
        tasks = [
            asyncio.create_task(
                process_urls_html(chunk, playwright_instance, type_pars)
            )
            for chunk in divided_hrefs
        ]
        await asyncio.gather(*tasks)


def parsin_html(type_pars, file_name_csv):
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")
    folder_GamePal = os.path.join(path_json_GamePal, "*.html")
    folder_item = os.path.join(path_json_item, "*.html")
    if type_pars == 1:
        files_html = glob.glob(folder_GamePal)
    elif type_pars == 0:
        files_html = glob.glob(folder_item)
    all_product = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
            # Создаем парсер для прочитанного HTML
            parser = HTMLParser(src)

            # Извлекаем наименование продукта
            try:
                product_name = parser.css_first("div.q-mb-md > h1").text().strip()
            except:
                product_name = None

            try:
                # Извлекаем все количество
                available_node = (
                    parser.css_first(
                        "div.row.items-center.justify-center.q-mt-md.q-mb-md > div"
                    )
                    .text()
                    .split()
                )
                available = available_node[0]
            except:
                available = None
            try:
                # Прайс
                price = (
                    parser.css_first("span.text-h6.text-weight-medium").text().strip()
                )
            except:
                price = None

            try:
                value_01 = (
                    parser.css_first(
                        "div:nth-child(4) > div:nth-child(1) > div > div.product-info__content.self-start.text-body1 > span"
                    )
                    .text()
                    .strip()
                )
            except:
                value_01 = None
            try:

                value_02 = (
                    parser.css_first(
                        "div:nth-child(4) > div:nth-child(2) > div > div.product-info__content.self-start.text-body1 > span"
                    )
                    .text()
                    .strip()
                )
            except:
                value_02 = None
            try:
                value_03 = (
                    parser.css_first(
                        "div:nth-child(4) > div:nth-child(3) > div > div.product-info__content.self-start.text-body1 > span"
                    )
                    .text()
                    .strip()
                )
            except:
                value_03 = None

            product = {
                "product_name": product_name,
                "available": available,
                "price": price,
                "header_01": value_01,
                "header_02": value_02,
                "header_03": value_03,
            }
            all_product.append(product)

    with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as csvfile:
        # Определяем заголовки на основе ключей первого словаря в списке
        fieldnames = all_product[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Запись заголовков
        writer.writeheader()

        # Запись строк данных
        for item in all_product:
            writer.writerow(item)
    # Загрузка данных из файла CSV
    data = pd.read_csv(f"{file_name_csv}.csv", encoding="utf-8")

    # Сохранение данных в файл XLSX
    data.to_excel(f"{file_name_csv}.xlsx", index=False, engine="openpyxl")
    print(f"успешно добавлен файл {file_name_csv}")
    # Открыть после тестов
    excel_file_path = os.path.join(current_directory, f"{file_name_csv}.xlsx")
    if os.path.exists(excel_file_path):
        if os.path.exists(temp_path) and os.path.isdir(temp_path):
            shutil.rmtree(temp_path)
    print(f"Временные файлы удалены")


# Основная функция паринга
async def run_parsing(type_pars, file_name_csv):
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_json_GamePal = os.path.join(temp_path, "json_GamePal")
    path_json_item = os.path.join(temp_path, "json_Item")
    header_order = [
        "price",
        "unit_price",
        "name",
        "region",
        "checkout_devlivery",
        "stock",
        "Server",
        "ServiceType",
        "description",
    ]
    await async_write_csv(f"{file_name_csv}.csv", "w", header_order, is_header=True)

    if type_pars == 1:
        file_path = os.path.join(path_json_GamePal, "*.json")
    elif type_pars == 0:
        file_path = os.path.join(path_json_item, "*.json")

    files_json = glob.glob(file_path)
    await process_files(files_json, file_name_csv, header_order, type_pars)
    # Теперь записываем уникальные заголовки в первую строку CSV файла в заданном порядке
    with open(f"{file_name_csv}.csv", "r", newline="", encoding="utf-8") as f:
        lines = f.readlines()
    lines[0] = ",".join(header_order) + "\n"

    with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as f:
        f.writelines(lines)

    # Загрузка данных из файла CSV
    data = pd.read_csv(f"{file_name_csv}.csv", encoding="utf-8")

    # Сохранение данных в файл XLSX
    data.to_excel(f"{file_name_csv}.xlsx", index=False, engine="openpyxl")
    print(f"успешно добавлен файл {file_name_csv}")
    # # Открыть после тестов
    # if os.path.exists(temp_path) and os.path.isdir(temp_path):
    #     shutil.rmtree(temp_path)


# Запись csv
async def async_write_csv(filename, mode, data, is_header=False):
    async with aiofiles.open(filename, mode=mode, newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_header:
            await file.write(",".join(data) + "\n")
        else:
            await writer.writerow(data)


async def process_files(files_json, file_name_csv, header_order, type_pars):
    if type_pars == 1:
        unique_headers = set(header_order)

        for item in files_json:
            async with aiofiles.open(item, "r", encoding="utf-8") as f:
                data_json = json.loads(await f.read())
            data_results = data_json["payload"]["results"]

            for dr in data_results:

                title = dr["title"]
                unit_price = str(dr["converted_unit_price"]).replace(".", ",")
                available_qty = dr["available_qty"]
                min_qty = dr["min_qty"]
                display_price = str(unit_price * min_qty).replace(".", ",")

                region_id = dr["region_id"]

                if region_id == "dfced32f-2f0a-4df5-a218-1e068cfadffa":
                    region_id = "US"
                if region_id == "ac3f85c1-7562-437e-b125-e89576b9a38e":
                    region_id = "EU"
                description = dr["description"]
                values = [
                    display_price,
                    unit_price,
                    title,
                    region_id,
                    available_qty,
                    min_qty,
                    description,
                ]
                offer_attributes = dr["offer_attributes"]
                for o in offer_attributes:
                    pattern = re.compile(r"lgc_\d+_(\w+)")
                    # Используем pattern.search, чтобы проверить, соответствует ли collection_id паттерну
                    match = pattern.search(o["collection_id"])
                    if match:
                        collection_id = match.group(1)  # Извлекаем collection_id
                        value = o["value"]
                        # Добавляем collection_id в множество уникальных заголовков
                        unique_headers.add(collection_id)
                        # Добавляем значение в список значений
                        values.append(value)
                await async_write_csv(f"{file_name_csv}.csv", "a", values)

    elif type_pars == 0:
        unique_headers = set(header_order)

        for item in files_json:
            async with aiofiles.open(item, "r", encoding="utf-8") as f:
                data_json = json.loads(await f.read())
            datas = data_json["payload"]

            # for g in datas:
            title = datas["title"]
            description = datas["description"]
            description = description.replace("\\n", " ")
            unit_price = str(datas["converted_unit_price"]).replace(".", ",")
            available_qty = datas["available_qty"]
            min_qty = datas["min_qty"]
            display_price = str(unit_price * min_qty).replace(".", ",")

            region_id = datas["region_id"]

            if region_id == "dfced32f-2f0a-4df5-a218-1e068cfadffa":
                region_id = "US"
            if region_id == "ac3f85c1-7562-437e-b125-e89576b9a38e":
                region_id = "EU"
            values = [
                display_price,
                unit_price,
                title,
                region_id,
                available_qty,
                min_qty,
                description,
            ]
            offer_attributes = datas["offer_attributes"]
            for o in offer_attributes:
                pattern = re.compile(r"lgc_\d+_(\w+)")
                # Используем pattern.search, чтобы проверить, соответствует ли collection_id паттерну
                match = pattern.search(o["collection_id"])
                if match:
                    collection_id = match.group(1)  # Извлекаем collection_id
                    value = o["value"]
                    # Добавляем collection_id в множество уникальных заголовков
                    unique_headers.add(collection_id)
                    # Добавляем значение в список значений
                    values.append(value)

            await async_write_csv(f"{file_name_csv}.csv", "a", values)

    # Теперь записываем уникальные заголовки в первую строку CSV файла в заданном порядке
    async with aiofiles.open(f"{file_name_csv}.csv", "r", encoding="utf-8") as f:
        lines = await f.readlines()
    lines[0] = ",".join(header_order) + "\n"

    async with aiofiles.open(f"{file_name_csv}.csv", "w", encoding="utf-8") as f:
        await f.writelines(lines)


if __name__ == "__main__":

    while True:
        print("Вставьте ссылку (или введите 'exit' для выхода):")
        url_start = input()
        # url_start = "https://www.g2g.com/categories/fallout-76-items?seller=FO76STORE"
        if url_start.lower() == "exit":
            print("Программа завершена.")
            break

        print("Название файла:")
        file_name_csv = input()
        # file_name_csv = "1"

        while True:
            print(
                "1 - для скачивания данных json\n"
                "3 - для скачивания данных html\n"
                "2 - парсинг данных\n"
                "0 - для возврата к вводу новых данных\n"
                "exit - для закрытия программы"
            )
            user_input = input("Выберите действие: ")

            if user_input.lower() == "exit":
                print("Программа завершена.")
                sys.exit(0)
            elif user_input == "0":
                break  # Выход из внутреннего цикла к вводу новых данных

            match = re.search(r"-(\w+)\?", url_start)
            if not match:
                print(
                    "Ссылка не содержит ожидаемых данных. Пожалуйста, проверьте ссылку и попробуйте снова."
                )
                continue

            type_pars_str = match.group(1)
            if type_pars_str == "item":
                type_pars = 0  # Items
            else:
                type_pars = 1  # GamePal

            if user_input == "1":
                asyncio.run(run(url_start, type_pars))
            elif user_input == "3":
                asyncio.run(run_html(url_start, type_pars))
                asyncio.run(main_html(type_pars))
                parsin_html(type_pars, file_name_csv)
            elif user_input == "2":
                asyncio.run(run_parsing(type_pars, file_name_csv))
            else:
                print("Неверный ввод, пожалуйста, введите корректный номер действия.")
