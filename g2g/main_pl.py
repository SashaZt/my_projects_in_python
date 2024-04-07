# -*- mode: python ; coding: utf-8 -*-
# Получаем json в папку list
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


async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


async def save_response_json(json_response, file_path):
    """Асинхронно сохраняет JSON-данные в файл."""
    async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


#Скачивание файлов json
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

#Создание задание на скачивание
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

#Основаная функция 
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
        
        #Items
        if type_pars == 0:
            all_hrefs = []

            for pages in range(1, list_pages + 1):

                await page.goto(f"{url_start}&page={pages}")
                xpath_href = '//div[@class="full-height full-width position-relative"]/a'
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
        #GamePal
        elif type_pars == 1:
            all_hrefs = []
            counter = 0
            for pages in range(1, list_pages + 1):
                counter += 1
                # Устанавливаем обработчик для сбора и сохранения данных ответов
                def create_log_response_with_counter(file_path, session):
                    async def log_response(response):
                        # Паттерн для поиска в URL ответа.
                        pattern = re.compile(
                            r"https://sls\.g2g\.com/offer/search\?service_id=[^&]+"
                        )

                        request = response.request
                        if request.method == "GET" and pattern.search(request.url):
                            updated_url = request.url.replace("currency=EUR", "currency=USD")
                            try:
                                # Используем переданную сессию для выполнения запроса к обновленному URL.
                                async with session.get(updated_url) as new_response:
                                    if new_response.status == 200:
                                        json_response = await new_response.json()
                                        await save_response_json(json_response, file_path)
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
                # elif type_pars == 0:
                #     filename = f"{id_product}.json"
                #     file_path = os.path.join(path_json_item, filename)

                # handler = create_log_response_with_counter(file_path, session)

                # page.on("response", handler)
                # previous_handler = handler
                # if previous_handler:
                #     page.remove_listener("response", previous_handler)
                # handler = create_log_response_with_counter(file_path, session)

                # page.on("response", handler)
                # previous_handler = handler
                # await page.goto(f"{url_start}&page={pages}")
                # await sleep(5)
                # if previous_handler:
                #     page.remove_listener("response", previous_handler)

        # Выполняем переход
        # await page.goto(url_next)
        # await sleep(5)
        # """Нажимаем кнопку next page"""
        # xpath_next_page = '//button[@title="Go to next page"]'
        # await page.wait_for_selector(f"xpath={xpath_next_page}", timeout=timeout)
        # # await page.click(xpath_next_page)

        # counter = 1

        # while True:
        #     # Проверяем, активна ли кнопка "следующая страница"
        #     is_disabled = await page.is_disabled(xpath_next_page)

        #     if is_disabled:
        #         print(f"Button is disabled for letter {letter}, stopping.")
        #         break

        #     # Если кнопка активна, готовимся перехватить ответы сервера
        #     url_name = f"page_180000{counter}_{letter}"
        #     handler = create_log_response_with_counter(url_name)

        #     # Отписываемся от предыдущего обработчика, если он есть
        #     if previous_handler:
        #         page.remove_listener("response", previous_handler)

        #     # Подписываемся на новый обработчик
        #     page.on("response", handler)
        #     previous_handler = handler  # Обновляем предыдущий обработчик

        #     # Нажимаем на кнопку "следующая страница" и ожидаем загрузку
        #     await page.click(xpath_next_page)
        #     await sleep(5)
        #     await page.wait_for_load_state('networkidle')

        #     counter += 1
        # После выхода из всех циклов, отписываемся от последнего обработчика
        # if previous_handler:
        #     page.remove_listener("response", previous_handler)
    


#Основная функция паринга
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
    ]
    await async_write_csv(f"{file_name_csv}.csv", "w", header_order, is_header=True)

    if type_pars == 1:
        file_path = os.path.join(path_json_GamePal, "*.json")
    elif type_pars == 0:
        file_path = os.path.join(path_json_item, "*.json")

    files_json = glob.glob(file_path)
    await process_files(files_json, file_name_csv, header_order,type_pars)
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
    print(f'успешно добавлен файл {file_name_csv}')
    # Открыть после тестов
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        shutil.rmtree(temp_path)

#Запись csv
async def async_write_csv(filename, mode, data, is_header=False):
    async with aiofiles.open(filename, mode=mode, newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_header:
            await file.write(",".join(data) + "\n")
        else:
            await writer.writerow(data)


async def process_files(files_json, file_name_csv, header_order,type_pars):
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
                values = [
                    display_price,
                    unit_price,
                    title,
                    region_id,
                    available_qty,
                    min_qty,
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
    # url_start = 'https://www.g2g.com/categories/gta-5-online-boosting-service?seller=AMELIBOOST'
    # match = re.search(r"-(\w+)\?", url_start)
    # type_pars_str = match.group(1)
    # if type_pars_str == "item":
    #     type_pars = 0  # Items
    # else:
    #     type_pars = 1  # GamePal
    # # asyncio.run(run(url_start, type_pars))
    # file_name_csv = 're'
    # asyncio.run(run_parsing(type_pars, file_name_csv))
    while True:
        print("Вставьте ссылку (или введите 'exit' для выхода):")
        url_start = input()
        if url_start.lower() == 'exit':
            print("Программа завершена.")
            break

        print("Название файла:")
        file_name_csv = input()

        while True:
            print(
                "1 - для скачивания данных\n"
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
                print("Ссылка не содержит ожидаемых данных. Пожалуйста, проверьте ссылку и попробуйте снова.")
                continue

            type_pars_str = match.group(1)
            if type_pars_str == "item":
                type_pars = 0  # Items
            else:
                type_pars = 1  # GamePal

            if user_input == "1":
                asyncio.run(run(url_start, type_pars))
            elif user_input == "2":
                asyncio.run(run_parsing(type_pars, file_name_csv))
            else:
                print("Неверный ввод, пожалуйста, введите корректный номер действия.")

