# -*- mode: python ; coding: utf-8 -*-
# Скачивание PDF файлов
import asyncio
import sys
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
import aiomysql
import json
import time
import glob
import asyncio
import string
import shutil
import random
import os
import glob
from asyncio import sleep
from bs4 import BeautifulSoup
import json


# Выкачка PDF файлов
async def download_file(session, url, cookies_dict, filename_pdf):
    headers = {
        "authority": "www.assessedvalues2.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'ASP.NET_SessionId=w1lubbprygi3wq5hdfiwa0tl; CookieTest=Testme; sucuri_cloudproxy_uuid_0766875d6=399c6876557455524af4b491910baaac; SearchList2=; SearchList3=; SearchList=000101',
        "dnt": "1",
        "pragma": "no-cache",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    async with session.get(url, headers=headers, cookies=cookies_dict) as response:
        if response.status == 200:
            async with aiofiles.open(filename_pdf, "wb") as out_file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await out_file.write(chunk)
        else:
            print(f"Ошибка при загрузке файла: {response.status}")


# Запись логов
async def write_log(message, filename):
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    log_path = os.path.join(temp_path, "log")
    for folder in [
        temp_path,
        log_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    filename_log = os.path.join(log_path, f"{filename}.txt")
    async with aiofiles.open(filename_log, "a", encoding="utf-8") as log_file:
        await log_file.write(message + "\n")


# Прочитать файл
async def read_csv_values():
    current_directory = os.getcwd()
    filename_csv = os.path.join(current_directory, "list_keyno.csv")
    values = []
    async with aiofiles.open(filename_csv, mode="r", encoding="utf-8") as file:
        async for line in file:
            values.append(line.strip())
    return values


# Основная функция получение PDF
async def run():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    log_path = os.path.join(temp_path, "log")

    # Удаление папки log_path вместе со всем содержимым
    shutil.rmtree(log_path, ignore_errors=True)

    print("Вставьте код город")
    code_sity = str(input())
    url_start = f"https://www.assessedvalues2.com/SearchPage.aspx?jurcode={code_sity}"
    print("Собираем по улицам - 1\nСобираем по кодам  - 2\nСобираем по ключам - 3")
    collection_method = int(input())
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    pdf_path = os.path.join(temp_path, "pdf")
    search_results_path = os.path.join(temp_path, "search_results")
    # Убедитесь, что папки существуют или создайте их
    for folder in [
        temp_path,
        pdf_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Сбор по кодам
    if collection_method == 2:

        print("Введите диапозон поиска по кодам, от")
        range_a = int(input())
        print("Введите диапозон поиска по кодам, до")
        range_b = int(input())

        timeout = 3000
        current_directory = os.getcwd()
        browsers_path = os.path.join(current_directory, "pw-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        async with async_playwright() as playwright, aiohttp.ClientSession() as session:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            await page.goto(url_start)
            match = re.search(r"jurcode=(\d+)", url_start)
            jurcode = match.group(1)

            # Имя лог-файла
            filename_log = f"{code_sity}_range"

            # Ждем появление кнопки поиска и нажимаем на нее
            xpath_begin_search = '//input[@id="ctl00_MainContent_BtnSearch"]'
            # Дожидаемся появления кнопки с заданным текстом и кликаем по ней
            await page.wait_for_selector(f"xpath={xpath_begin_search}", timeout=timeout)
            await page.click(xpath_begin_search)
            await asyncio.sleep(1)
            # Ждем появление поля ввода, вводим значение из переменной current и нажимаем Enter
            xpath_keyno = '//input[@id="ctl00_MainContent_TxtKey"]'

            await page.wait_for_selector(f"xpath={xpath_keyno}", timeout=timeout)

            # # Получение Search_info
            # page_content_soup = await page.content()
            # # Парсинг HTML с помощью BeautifulSoup
            # soup = BeautifulSoup(page_content_soup, "lxml")
            # # Продолжаем работать с soup, как показано в предыдущем примере
            # headers = [th.get_text().strip() for th in soup.find_all("th")]
            # rows = soup.find_all("tr")[1:]  # Первый ряд пропускаем, т.к. это заголовки

            # all_data = []
            # for row in rows:
            #     values = [td.get_text().strip() for td in row.find_all("td")]
            #     pdf_link = row.find("a")["href"] if row.find("a") else None
            #     data_dict = dict(zip(headers, values))
            #     if pdf_link:
            #         data_dict["Card_PDF"] = pdf_link
            #     all_data.append(data_dict)
            # # Сохраняем полученные данные в JSON файл
            # async with aiofiles.open("data.json", mode="w", encoding="utf-8") as f:
            #     await f.write(json.dumps(all_data, ensure_ascii=False, indent=4))

            # # Получение Search_info
            # page_content_soup = await page.content()
            # await get_search_info_json(page_content_soup, jurcode, keyno, search_results_path)

            folder_pdf = os.path.join(pdf_path, "*.pdf")
            files_pdf = glob.glob(folder_pdf)
            found_parts = []

            # Обход всех файлов и сбор номеров в заданном диапазоне
            for item in files_pdf:
                filename = os.path.basename(item)
                parts = filename.split("_")
                if len(parts) >= 2:
                    try:
                        part_number = int(parts[1])  # Извлекаем номер
                        if range_a <= part_number <= range_b:
                            found_parts.append(part_number)
                    except ValueError:
                        # Если part2 не является числом, пропускаем этот файл
                        continue

            # Определяем отсутствующие номера в диапазоне
            missing_parts = [
                n for n in range(range_a, range_b + 1) if n not in found_parts
            ]

            # Определяем номер, с которого начать обработку
            # Если в missing_parts есть элементы, берем первый как начальный номер для обработки
            current = missing_parts[0] if missing_parts else range_b + 1

            while current <= range_b:
                if current in found_parts:
                    current += 1
                    continue

                await page.fill(xpath_keyno, str(current))
                await page.press(xpath_keyno, "Enter")

                # Получение Search_info
                page_content_soup = await page.content()
                # вместо keyno используем current
                await get_search_info_json(
                    page_content_soup, jurcode, current, search_results_path
                )

                sleep_time = random.randint(7, 11)
                await asyncio.sleep(sleep_time)
                # Получаем куки из контекста браузера
                cookies = await context.cookies()
                cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                # Ждем появление ссылки и получаем с нее href
                try:
                    xpath_href = '//a[@target="_blank"]'
                    await page.wait_for_selector(f"xpath={xpath_href}", timeout=timeout)
                    url_href = await page.get_attribute(xpath_href, "href")

                    pattern = r"pdf=([^&]+)"
                    match = re.search(pattern, url_href)

                    if match:
                        extracted_part = match.group(1)
                        keyno_match = re.search(r"K(\d+)N", extracted_part)
                        keyno = keyno_match.group(1) if keyno_match else None
                    else:
                        print("Совпадение не найдено.")
                    url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"

                    filename_pdf = os.path.join(
                        pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
                    )
                    await download_file(session, url, cookies_dict, filename_pdf)
                    current += 1
                except:
                    await write_log(f"Нет данных для {current}", filename_log)
                    current += 1
                    continue

            print("Все скачано")
            await sleep(5)
            await browser.close()
    # Сбор по улицам
    elif collection_method == 1:
        lowercase_letters_list = list(string.ascii_lowercase)
        for letter_streed in lowercase_letters_list:

            current_directory = os.getcwd()
            # Создайте полный путь к папке temp
            temp_path = os.path.join(current_directory, "temp")
            pdf_path = os.path.join(temp_path, "pdf")
            # Убедитесь, что папки существуют или создайте их
            for folder in [
                temp_path,
                pdf_path,
            ]:
                if not os.path.exists(folder):
                    os.makedirs(folder)

            timeout = 5000
            current_directory = os.getcwd()
            browsers_path = os.path.join(current_directory, "pw-browsers")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
            async with async_playwright() as playwright, aiohttp.ClientSession() as session:
                browser = await playwright.chromium.launch(
                    headless=False
                )  # Для отладки можно использовать headless=False
                context = await browser.new_context(accept_downloads=True)
                page = await context.new_page()

                await page.goto(url_start)
                match = re.search(r"jurcode=(\d+)", url_start)

                jurcode = match.group(1)
                filename_log = f"{jurcode}_letter"
                await write_log(f"Поиск по букве {letter_streed}", filename_log)
                # Ждем появление кнопки поиска и нажимаем на нее
                xpath_begin_search = '//input[@id="ctl00_MainContent_BtnSearch"]'
                # Дожидаемся появления кнопки с заданным текстом и кликаем по ней
                await page.wait_for_selector(
                    f"xpath={xpath_begin_search}", timeout=timeout
                )
                await page.click(xpath_begin_search)
                await asyncio.sleep(1)
                # Получаем куки из контекста браузера
                cookies = await context.cookies()
                cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

                # Ждем появление поля ввода, вводим значение из переменной current и нажимаем Enter
                xpath_txtstreet = '//input[@id="ctl00_MainContent_TxtStreet"]'
                await page.wait_for_selector(
                    f"xpath={xpath_txtstreet}", timeout=timeout
                )
                await page.fill(xpath_txtstreet, str(letter_streed))
                await page.press(xpath_txtstreet, "Enter")

                xpath_error_message = '//span[@id="ctl00_MainContent_lblMaxRec"]'
                xpath_href = '//a[@target="_blank"]'

                # Пытаемся найти элемент с сообщением об ошибке
                error_message_element = await page.query_selector(xpath_error_message)

                if error_message_element:
                    error_message_text = await error_message_element.text_content()
                    if error_message_text == "No records found using chosen criteria!":
                        await write_log(
                            f"Нет записей, соответствующих критериям - {letter_streed}",
                            filename_log,
                        )
                    elif (
                        error_message_text
                        == "Search results are limited to the first 300 records!"
                    ):

                        # Добавляем вторую букву
                        lowercase_letters_list = list(string.ascii_lowercase)
                        for letter in lowercase_letters_list:
                            find_letter = f"{letter_streed}{letter}"
                            await asyncio.sleep(1)
                            await page.fill(xpath_txtstreet, find_letter)
                            await page.press(xpath_txtstreet, "Enter")
                            await asyncio.sleep(1)

                            # Получение Search_info
                            page_content_soup = await page.content()
                            # Вместо keyno использую две буквы
                            await get_search_info_json(
                                page_content_soup,
                                jurcode,
                                find_letter,
                                search_results_path,
                            )

                            # Обновляем состояние элемента с сообщением об ошибке
                            error_message_element = await page.query_selector(
                                xpath_error_message
                            )
                            if error_message_element:
                                error_message_text = (
                                    await error_message_element.text_content()
                                )
                                if (
                                    error_message_text
                                    == "No records found using chosen criteria!"
                                ):
                                    await write_log(
                                        f"Нет записей, пропускаем {find_letter}",
                                        filename_log,
                                    )
                                    continue  # Пропускаем текущую итерацию и переходим к следующей букве
                                elif (
                                    error_message_text
                                    == "Search results are limited to the first 300 records!"
                                ):
                                    # Добавляем 3ю букву для поиска
                                    lowercase_letters_list_3 = list(
                                        string.ascii_lowercase
                                    )
                                    for letter_3 in lowercase_letters_list_3:
                                        find_letter_3 = (
                                            f"{letter_streed}{letter}{letter_3}"
                                        )
                                        await asyncio.sleep(1)
                                        await page.fill(xpath_txtstreet, find_letter_3)
                                        await page.press(xpath_txtstreet, "Enter")
                                        await asyncio.sleep(1)

                                        # Получение Search_info
                                        page_content_soup = await page.content()
                                        await get_search_info_json(
                                            page_content_soup,
                                            jurcode,
                                            find_letter_3,
                                            search_results_path,
                                        )

                                        xpath_href = '//a[@target="_blank"]'
                                        links_elements = await page.query_selector_all(
                                            f"xpath={xpath_href}"
                                        )
                                        urls = [
                                            await link_element.get_attribute("href")
                                            for link_element in links_elements
                                        ]
                                        await write_log(
                                            f"Собираем {find_letter_3}", filename_log
                                        )
                                        # Создаем список словарей, где каждый словарь содержит jurcode, extracted_part и keyno для каждого URL
                                        jurcode_extracted_list = []
                                        pattern = re.compile(
                                            r"jurcode=(\d+)&pdf=([^&]+)"
                                        )

                                        for url in urls:
                                            match = pattern.search(url)
                                            if match:
                                                jurcode, extracted_part = match.groups()
                                                keyno_match = re.search(
                                                    r"K(\d+)N", extracted_part
                                                )
                                                keyno = (
                                                    keyno_match.group(1)
                                                    if keyno_match
                                                    else None
                                                )

                                                # Создаем словарь для каждого найденного совпадения и добавляем его в список
                                                jurcode_extracted_dict = {
                                                    "jurcode": jurcode,
                                                    "extracted_part": extracted_part,
                                                    "keyno": keyno,
                                                }
                                                jurcode_extracted_list.append(
                                                    jurcode_extracted_dict
                                                )
                                        await write_log(
                                            f"качаем {find_letter_3} количество {len(jurcode_extracted_list)}",
                                            filename_log,
                                        )
                                        # Выводим полученный список словарей
                                        for item in jurcode_extracted_list:
                                            jurcode = item["jurcode"]
                                            extracted_part = item["extracted_part"]
                                            keyno = item["keyno"]
                                            url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"

                                            filename_pdf = os.path.join(
                                                pdf_path,
                                                f"{jurcode}_{keyno}_{extracted_part}.pdf",
                                            )

                                            # await asyncio.sleep(1)
                                            # #Открыть потом
                                            if not os.path.exists(filename_pdf):
                                                await download_file(
                                                    session,
                                                    url,
                                                    cookies_dict,
                                                    filename_pdf,
                                                )
                                        # print(f'Ручная проверка запроса\n {find_letter}!!!!!!!!!!!!!!!!!!')
                            else:
                                # Качаем две буквы
                                await write_log(f"Собираем {find_letter}", filename_log)

                            xpath_href = '//a[@target="_blank"]'
                            links_elements = await page.query_selector_all(
                                f"xpath={xpath_href}"
                            )
                            urls = [
                                await link_element.get_attribute("href")
                                for link_element in links_elements
                            ]
                            # Создаем список словарей, где каждый словарь содержит jurcode, extracted_part и keyno для каждого URL
                            jurcode_extracted_list = []
                            pattern = re.compile(r"jurcode=(\d+)&pdf=([^&]+)")

                            for url in urls:
                                match = pattern.search(url)
                                if match:
                                    jurcode, extracted_part = match.groups()
                                    keyno_match = re.search(r"K(\d+)N", extracted_part)
                                    keyno = (
                                        keyno_match.group(1) if keyno_match else None
                                    )

                                    # Создаем словарь для каждого найденного совпадения и добавляем его в список
                                    jurcode_extracted_dict = {
                                        "jurcode": jurcode,
                                        "extracted_part": extracted_part,
                                        "keyno": keyno,
                                    }
                                    jurcode_extracted_list.append(
                                        jurcode_extracted_dict
                                    )
                            await write_log(
                                f"качаем {find_letter} количество {len(jurcode_extracted_list)}",
                                filename_log,
                            )
                            # Выводим полученный список словарей
                            for item in jurcode_extracted_list:
                                jurcode = item["jurcode"]
                                extracted_part = item["extracted_part"]
                                keyno = item["keyno"]
                                url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
                                filename_pdf = os.path.join(
                                    pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
                                )

                                # # Получение Search_info
                                # page_content_soup = await page.content()
                                # await get_search_info_json(page_content_soup, jurcode, keyno, search_results_path)
                                # await asyncio.sleep(1)
                                # Открыть потом
                                if not os.path.exists(filename_pdf):
                                    await download_file(
                                        session, url, cookies_dict, filename_pdf
                                    )
                # Качаем одну букву
                else:
                    print(f"качаем {letter_streed}")

                    # Получение Search_info
                    page_content_soup = await page.content()
                    # Вместо keyno использую букву
                    await get_search_info_json(
                        page_content_soup, jurcode, letter_streed, search_results_path
                    )

                    # Если элемент с сообщением об ошибке не найден, собираем все ссылки
                    links_elements = await page.query_selector_all(xpath_href)
                    pattern = re.compile(r"jurcode=(\d+)&pdf=([^&]+)")

                    urls = [
                        await link_element.get_attribute("href")
                        for link_element in links_elements
                    ]
                    # Создаем список словарей, где каждый словарь содержит jurcode, extracted_part и keyno для каждого URL
                    jurcode_extracted_list = []

                    for url in urls:
                        match = pattern.search(url)
                        if match:
                            jurcode, extracted_part = match.groups()
                            keyno_match = re.search(r"K(\d+)N", extracted_part)
                            keyno = keyno_match.group(1) if keyno_match else None

                            # Создаем словарь для каждого найденного совпадения и добавляем его в список
                            jurcode_extracted_dict = {
                                "jurcode": jurcode,
                                "extracted_part": extracted_part,
                                "keyno": keyno,
                            }
                            jurcode_extracted_list.append(jurcode_extracted_dict)

                    print(f"качаем {letter_streed}")
                    # Выводим полученный список словарей
                    await write_log(
                        f"качаем {letter_streed} количество {len(jurcode_extracted_list)}",
                        filename_log,
                    )
                    for item in jurcode_extracted_list:
                        jurcode = item["jurcode"]
                        extracted_part = item["extracted_part"]
                        keyno = item["keyno"]
                        url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
                        filename_pdf = os.path.join(
                            pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
                        )
                        # await asyncio.sleep(1)
                        # Открыть потом
                        if not os.path.exists(filename_pdf):

                            await download_file(
                                session, url, cookies_dict, filename_pdf
                            )

                print("Все скачано")
                await sleep(5)
                await browser.close()
    # Поиск по ключам из файла list_keyno.csv
    elif collection_method == 3:
        timeout = 3000
        url_start = (
            f"https://www.assessedvalues2.com/SearchPage.aspx?jurcode={code_sity}"
        )

        current_directory = os.getcwd()
        temp_path = os.path.join(current_directory, "temp")
        pdf_path = os.path.join(temp_path, "pdf")
        for folder in [
            temp_path,
            pdf_path,
        ]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        browsers_path = os.path.join(current_directory, "pw-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        async with async_playwright() as playwright, aiohttp.ClientSession() as session:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            await page.goto(url_start)

            # Ждем появление кнопки поиска и нажимаем на нее
            xpath_begin_search = '//input[@id="ctl00_MainContent_BtnSearch"]'
            await page.wait_for_selector(f"xpath={xpath_begin_search}", timeout=timeout)
            await page.click(xpath_begin_search)
            await asyncio.sleep(1)

            # Ждем появление поля ввода, вводим значение из переменной current и нажимаем Enter
            xpath_keyno = '//input[@id="ctl00_MainContent_TxtKey"]'
            await page.wait_for_selector(f"xpath={xpath_keyno}", timeout=timeout)
            values = await read_csv_values()

            match = re.search(r"jurcode=(\d+)", url_start)
            jurcode = match.group(1)

            # Имя лог-файла
            filename_log = f"{code_sity}_key"
            for v in values:

                await page.fill(xpath_keyno, str(v))
                await page.press(xpath_keyno, "Enter")
                sleep_time = random.randint(7, 11)
                await asyncio.sleep(sleep_time)

                # Получаем куки из контекста браузера
                cookies = await context.cookies()
                cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                # Ждем появление ссылки и получаем с нее href

                try:
                    xpath_href = '//a[@target="_blank"]'
                    await page.wait_for_selector(f"xpath={xpath_href}", timeout=timeout)
                    url_href = await page.get_attribute(xpath_href, "href")

                    pattern = r"pdf=([^&]+)"
                    match = re.search(pattern, url_href)

                    if match:
                        extracted_part = match.group(1)
                        keyno_match = re.search(r"K(\d+)N", extracted_part)
                        keyno = keyno_match.group(1) if keyno_match else None
                    else:
                        print("Совпадение не найдено.")
                    url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
                    filename_pdf = os.path.join(
                        pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
                    )
                    # Получение Search_info
                    page_content_soup = await page.content()
                    await get_search_info_json(
                        page_content_soup, jurcode, keyno, search_results_path
                    )
                    # # Парсинг HTML с помощью BeautifulSoup
                    # soup = BeautifulSoup(page_content_soup, "lxml")

                    # headers = [th.get_text().strip() for th in soup.find_all("th")]
                    # # Первый ряд пропускаем, т.к. это заголовки

                    # rows = soup.find_all("tr")[1:]
                    # all_data = []
                    # for row in rows:
                    #     values = [td.get_text().strip() for td in row.find_all("td")]
                    #     pdf_link = row.find("a")["href"] if row.find("a") else None
                    #     data_dict = dict(zip(headers, values))
                    #     pdf_link = f"https://www.assessedvalues2.com{pdf_link}"
                    #     if pdf_link:
                    #         data_dict["Card_PDF"] = pdf_link
                    #     all_data.append(data_dict)
                    # # Сохраняем полученные данные в JSON файл
                    # filename_json_search_info = os.path.join(
                    #     search_results_path, f"{jurcode}_{keyno}.json"
                    # )
                    # async with aiofiles.open(
                    #     filename_json_search_info, mode="w", encoding="utf-8"
                    # ) as f:
                    #     await f.write(
                    #         json.dumps(all_data, ensure_ascii=False, indent=4)
                    #     )

                    if not os.path.exists(filename_pdf):
                        await download_file(session, url, cookies_dict, filename_pdf)
                except:
                    await write_log(f"Нет данных для {v}", filename_log)
                    continue

            print("Все скачано")
            await sleep(5)
            await browser.close()


async def get_search_info_json(page_content_soup, jurcode, keyno, search_results_path):

    # Парсинг HTML с помощью BeautifulSoup
    soup = BeautifulSoup(page_content_soup, "lxml")

    headers = [th.get_text().strip() for th in soup.find_all("th")]
    # Первый ряд пропускаем, т.к. это заголовки

    rows = soup.find_all("tr")[1:]
    all_data = []
    for row in rows:
        values = [td.get_text().strip() for td in row.find_all("td")]
        pdf_link = row.find("a")["href"] if row.find("a") else None
        data_dict = dict(zip(headers, values))
        pdf_link = f"https://www.assessedvalues2.com{pdf_link}"
        if pdf_link:
            data_dict["Card_PDF"] = pdf_link
        all_data.append(data_dict)
    # Сохраняем полученные данные в JSON файл
    filename_json_search_info = os.path.join(
        search_results_path, f"{jurcode}_{keyno}.json"
    )
    if not os.path.exists(filename_json_search_info):
        async with aiofiles.open(
            filename_json_search_info, mode="w", encoding="utf-8"
        ) as f:
            await f.write(json.dumps(all_data, ensure_ascii=False, indent=4))


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


def convert_card_pdf_url(old_url):
    # Проверяем наличие '?' в URL
    if "?" in old_url:
        # Разбиваем URL на части и извлекаем параметры
        _, query_string = old_url.split("?")
        params = dict(param.split("=") for param in query_string.split("&"))

        # Формируем новый URL
        new_url = f"https://www.assessedvalues2.com/pdfs/{params['jurcode']}/{params['pdf']}.pdf"
        return new_url
    else:
        # Возвращаем исходный URL, если в нем нет '?'
        return old_url


async def insert_data_into_table():
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    search_results_path = os.path.join(temp_path, "search_results")
    config = load_config()
    db_config = config["db_config"]
    conn = await aiomysql.connect(
        host=db_config["host"],
        port=3306,
        user=db_config["user"],
        password=db_config["password"],
        db=db_config["database"],
    )
    cursor = await conn.cursor()

    json_files = glob.glob(f"{search_results_path}/*.json")
    for json_file_path in json_files:
        filename = os.path.basename(json_file_path)
        keyno, card = filename.rstrip(".json").split("_")
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        if not data:  # Пропускаем пустые json файлы
            continue

        await cursor.execute("SHOW COLUMNS FROM search_results")
        columns_info = await cursor.fetchall()
        column_can_be_null = {col[0]: (col[2] == "YES") for col in columns_info}

        for record in data:
            if "Card_PDF" in record:
                record["Card_PDF"] = convert_card_pdf_url(record["Card_PDF"])

            filtered_record = {
                k: v for k, v in record.items() if k in column_can_be_null
            }
            columns_str = ", ".join(filtered_record.keys())
            placeholders = ", ".join(["%s"] * len(filtered_record))
            values = list(filtered_record.values())
            if not columns_str:
                continue

            insert_query = (
                f"INSERT INTO search_results ({columns_str}) VALUES ({placeholders})"
            )
            await cursor.execute(insert_query, values)

        await conn.commit()
        print(f"Данные успешно вставлены в таблицу search_results из файла {filename}.")

    await cursor.close()
    conn.close()


async def fetch_db_data():
    config = load_config()
    db_config = config["db_config"]
    async with aiomysql.connect(
        host=db_config["host"],
        port=3306,
        user=db_config["user"],
        password=db_config["password"],
        db=db_config["database"],
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT Keyno, Card_PDF FROM search_results")
            db_data = await cur.fetchall()
    return db_data


def extract_keyno_from_filename(filename):
    match = re.search(r"_([0-9]+)_", filename)
    if match:
        return match.group(1)
    return None


async def find_missing_pdf_files():
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    search_results_path = os.path.join(temp_path, "search_results")
    # Извлекаем данные из БД
    db_data = await fetch_db_data()
    db_keynos = {str(keyno): pdf for keyno, pdf in db_data}

    # Извлекаем Keyno из имен файлов
    file_paths = glob.glob(os.path.join(search_results_path, "*.json"))
    file_keynos = set(
        extract_keyno_from_filename(os.path.basename(path)) for path in file_paths
    )

    # Находим недостающие Card_PDF
    missing_pdfs = {db_keynos[keyno] for keyno in db_keynos if keyno not in file_keynos}
    print(missing_pdfs)
    return missing_pdfs


while True:
    print(
        "Введите 1 для запуска парсинга\nВведите 3 для загрузки данных в БД \nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        asyncio.run(run())
    elif user_input == 0:
        print("Программа завершена.")
        sys.exit(1)
    elif user_input == 3:
        asyncio.run(insert_data_into_table())

    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
