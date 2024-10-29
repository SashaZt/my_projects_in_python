import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from configuration.logger_setup import logger
import json
import os
from bs4 import BeautifulSoup
import re
import aiofiles
import csv

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_files_page_directory = current_directory / "html_files_page"
configuration_directory = current_directory / "configuration"
json_directory = current_directory / "json"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_page_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
csv_output_file = current_directory / "inn_data.csv"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


# Функция загрузки списка прокси
def load_proxies():
    if os.path.exists(file_proxy):
        with open(file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


# Функция для парсинга прокси
def parse_proxy(proxy):
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html_one(url):
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")
    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )
            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            # Пауза на 5 секунд
            await asyncio.sleep(5)
            # Поиск элемента с нужными классами
            element = await page.query_selector(
                "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
            )
            page_number = None
            if element:
                # Извлекаем текст из элемента
                element_text = await element.inner_text()

                # Преобразуем текст и сохраняем в переменную page
                page_number_raw = element_text.strip().replace(" ", "_").lower()
                page_number = f"page_{page_number_raw.split('_')[-1]}"

            content = await page.content()
            html_file_path = html_files_directory / f"0{page_number}.html"
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Цикл для нажатия на кнопку "Next Page", пока она есть на странице
            while True:
                next_button = await page.query_selector(
                    "a.ui-paginator-next.ui-state-default.ui-corner-all"
                )

                if next_button:
                    # Нажимаем на кнопку "Next Page"
                    await next_button.click()

                    # Пауза, чтобы подождать загрузку новой страницы
                    await asyncio.sleep(2)
                    # Поиск элемента с нужными классами
                    element = await page.query_selector(
                        "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
                    )
                    page_number = None
                    if element:
                        # Извлекаем текст из элемента
                        element_text = await element.inner_text()

                        # Преобразуем текст и сохраняем в переменную page
                        page_number_raw = element_text.strip().replace(" ", "_").lower()
                        page_number = f"page_{page_number_raw.split('_')[-1]}"

                    content = await page.content()
                    html_file_path = html_files_directory / f"0{page_number}.html"
                    with open(html_file_path, "w", encoding="utf-8") as f:
                        f.write(content)

        await context.close()
        await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


async def single_html_one_contact(url):
    # Парсим контакты
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")
    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )
            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            # Ждем, пока появится активный элемент пагинации, чтобы страница полностью загрузилась
            await page.wait_for_selector(
                "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
            )
            await process_page(page)

            # Цикл для нажатия на кнопку "Next Page", пока не найдется нужный элемент
            attempts = 0
            max_attempts = 5

            while attempts < max_attempts:
                next_button = await page.query_selector(
                    "a.ui-paginator-next.ui-state-default.ui-corner-all"
                )
                if not next_button:
                    logger.warning(
                        "Кнопка 'Next Page' не найдена. Попытка {}/{}.".format(
                            attempts + 1, max_attempts
                        )
                    )
                    attempts += 1
                    await asyncio.sleep(2)
                    continue

                # Получаем текущий номер страницы перед переходом
                current_page_number = await page.query_selector(
                    "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
                )
                current_page_number_text = (
                    await current_page_number.inner_text()
                    if current_page_number
                    else None
                )

                if not current_page_number_text:
                    logger.error(
                        "Не удалось получить текущий номер страницы. Попытка {}/{}.".format(
                            attempts + 1, max_attempts
                        )
                    )
                    attempts += 1
                    await asyncio.sleep(2)
                    continue

                logger.info(f"Текущая страница: {current_page_number_text}")

                # Нажимаем на кнопку "Next Page"
                await next_button.click()
                logger.info("Нажата кнопка 'Next Page'.")

                # Небольшая пауза для гарантированной подгрузки контента, если необходимо
                await asyncio.sleep(2)

                # Ждем, пока номер страницы изменится
                try:
                    await page.wait_for_function(
                        f"""
                        () => {{
                            const activePage = document.querySelector('a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active');
                            return activePage && activePage.innerText !== '{current_page_number_text}';
                        }}
                        """,
                        timeout=10000,  # Время ожидания 10 секунд
                    )
                    logger.info("Номер страницы изменился, переход успешно выполнен.")
                    attempts = 0  # Сбрасываем счетчик попыток, так как переход успешен
                except Exception as e:
                    attempts += 1
                    logger.warning(
                        f"Не удалось дождаться изменения номера страницы (попытка {attempts}/{max_attempts}): {str(e)}. Возможно, загрузка не произошла."
                    )
                    await asyncio.sleep(2)
                    continue

                # Обрабатываем текущую страницу
                await process_page(page)

            # Если максимальное количество попыток исчерпано
            if attempts == max_attempts:
                logger.error(
                    f"Максимальное количество попыток ({max_attempts}) достигнуто. Остановка выполнения."
                )

        await context.close()
        await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


async def write_inn_to_csv(inn):
    logger.warning("Пишем")
    async with aiofiles.open("inns.csv", mode="a") as file:
        await file.write(f"{inn}\n")
        await file.flush()  # Принудительно записываем данные в файл


# async def single_html_one(url):
#     inns = read_cities_from_csv(csv_output_file)
#     # Парсим поставщиков
#     proxies = load_proxies()
#     proxy = random.choice(proxies) if proxies else None
#     if not proxies:
#         logger.info("Прокси не найдено, работа будет выполнено локально.")
#     try:
#         proxy_config = parse_proxy(proxy) if proxy else None
#         async with async_playwright() as p:
#             browser = (
#                 await p.chromium.launch(proxy=proxy_config, headless=False)
#                 if proxy
#                 else await p.chromium.launch(headless=False)
#             )
#             context = await browser.new_context(accept_downloads=True)
#             page = await context.new_page()

#             # Отключаем медиа
#             await page.route(
#                 "**/*",
#                 lambda route: (
#                     route.abort()
#                     if route.request.resource_type in ["image", "media"]
#                     else route.continue_()
#                 ),
#             )

#             # Переход на страницу и ожидание полной загрузки
#             await page.goto(url, timeout=60000, wait_until="networkidle")
#             await asyncio.sleep(2)
#             for inn in inns:
#                 # if not inn.isdigit():
#                 #     logger.warning(f"Некорректное значение ИНН: {inn}, пропускаем.")
#                 #     logger.info("Запись")
#                 #     await write_inn_to_csv(inn)

#                 #     continue

#                 logger.info(inn)
                # html_file_path = html_files_directory / f"inn_{inn}.html"
                # if html_file_path.exists():
                #     continue  # Переходим к следующей итерации цикла
#                 await page.wait_for_selector(
#                     "input[type='text'][name='j_idt66']", timeout=10000
#                 )
#                 await page.fill("input[type='text'][name='j_idt66']", inn)
#                 logger.info(f"Вставили {inn}")
#                 await page.wait_for_selector(
#                     "input[id='j_idt79'][type='submit']", timeout=10000
#                 )
#                 await page.click("input[id='j_idt79'][type='submit']")
#                 await page.wait_for_selector(
#                     "table.display-table.public-table", timeout=10000
#                 )
#                 first_row_link = await page.query_selector(
#                     "table.display-table.public-table tbody tr:first-child a[onclick*='mojarra.jsfcljs']"
#                 )
#                 if first_row_link:
#                     await first_row_link.click()
#                     # Проверяем наличие ошибки на странице
#                 error_element = await page.query_selector(
#                     "p[style='font-size:24px;color:#1785aa;font-weight: bold;']"
#                 )
#                 if error_element:
#                     logger.warning("Обнаружена ошибка на странице, перезагружаем...")
#                     await page.goto(url, timeout=60000, wait_until="networkidle")
#                     continue

#                 # ТЕСТОВО
#                 # # Находим элемент "Назад" и нажимаем на него
#                 # back_button = await page.wait_for_selector(
#                 #     "//a[@class='button-grey' and text()='Назад']",
#                 #     timeout=30000,
#                 # )
#                 await asyncio.sleep(1)
#                 html_content = await page.content()
#                 with open(html_file_path, "w", encoding="utf-8") as file:
#                     file.write(html_content)
#                     logger.info(f"Файл {html_file_path} успешно сохранен.")

#                 # Тестово проверим возможно быстрее будет
#                 await page.goto(url, timeout=60000, wait_until="networkidle")

#                 # await back_button.click()
#                 # # Очистка поля ввода после сохранения
#                 # await page.fill("input[type='text'][name='j_idt66']", "")

#             await context.close()
#             await browser.close()

#     except Exception as e:
#         logger.error(f"Ошибка при выполнении: {e}")


async def single_html_page_company(url):

    # Парсим поставщиков
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнено локально.")
    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            # Дожидаемся появления выпадающего списка и выбираем значение "50"
            await asyncio.sleep(3)
            while True:
                # Находим все ссылки внутри ячеек и кликаем по очереди
                await page.wait_for_selector("//td[@role='gridcell']//a", timeout=30000)
                links = await page.locator("//td[@role='gridcell']//a").all()
                if not links:
                    break
                await process_page_company(page)

                next_button = await page.query_selector(
                    "#table_paginator_bottom .ui-paginator-next.ui-state-default.ui-corner-all"
                )
                if next_button and await next_button.is_visible():
                    try:
                        await next_button.click()
                        await asyncio.sleep(3)
                    except Exception as e:
                        logger.error(f"Ошибка при клике на кнопку 'Next Page': {e}")
                else:
                    logger.info(
                        "Кнопка 'Next Page' не найдена или не видна, завершаем обработку."
                    )
                    break
            await context.close()
            await browser.close()

    except Exception as e:
        logger.error(f"Ошибка при выполнении: {e}")


async def process_page(page, html_file_path):
    try:
        # inn_element = await page.wait_for_selector(
        #     "//tr[td[text()='ИНН организации']]/td[2]", timeout=30000
        # )
        # inn = await inn_element.inner_text()
        content = await page.content()

        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Ошибка при обработке страницы: {e}")


async def process_page_company(page):
    try:
        # Поиск элемента с нужными классами
        element = await page.query_selector(
            "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
        )
        page_number = None
        if element:
            element_text = await element.inner_text()
            page_number_raw = element_text.strip().replace(" ", "_").lower()
            page_number = f"page_{page_number_raw.split('_')[-1]}"

        if page_number:
            content = await page.content()
            html_file_path = html_files_page_directory / f"0{page_number}.html"
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(html_file_path)
        else:
            logger.warning("Не удалось определить номер страницы.")
    except Exception as e:
        logger.error(f"Ошибка при обработке страницы: {e}")


async def process_page_contact(page):
    try:
        # Поиск элемента с нужными классами
        element = await page.query_selector(
            "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
        )
        page_number = None
        if element:
            element_text = await element.inner_text()
            page_number_raw = element_text.strip().replace(" ", "_").lower()
            page_number = f"page_{page_number_raw.split('_')[-1]}"

        if page_number:
            content = await page.content()
            html_file_path = html_files_page_directory / f"0{page_number}.html"
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            logger.warning("Не удалось определить номер страницы.")
    except Exception as e:
        logger.error(f"Ошибка при обработке страницы: {e}")


def parsing_page():
    # Множество для хранения уникальных itm_value
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content: str = file.read()
            # Создать объект BeautifulSoup
            serial_number = None
            ad_number = None
            name_of_purchase = None
            winners_names = None
            lot_number = None
            contract_price = None
            contract_number = None
            contract_signing_date = None
            soup = BeautifulSoup(content, "lxml")
            table_ad = soup.find(
                "tbody", attrs={"class": "ui-datatable-data ui-widget-content"}
            )

            if table_ad:
                all_ad = table_ad.find_all(
                    "tr", class_=re.compile(r"ui-widget-content ui-datatable*")
                )
                if all_ad:
                    for ad in all_ad:
                        # Находим все ячейки в строке
                        td_elements = ad.find_all("td")

                        # Извлекаем данные
                        serial_number = (
                            td_elements[0].get_text(strip=True).replace("№", "").strip()
                        )
                        ad_number = (
                            td_elements[1]
                            .get_text(strip=True)
                            .replace("Номер объявления", "")
                            .strip()
                        )
                        name_of_purchase = (
                            td_elements[2]
                            .get_text(strip=True)
                            .replace("Наименование закупки", "")
                            .strip()
                        )
                        winners_names = (
                            td_elements[3]
                            .get_text(strip=True)
                            .replace("Наименования победителя", "")
                            .strip()
                        )
                        lot_number = (
                            td_elements[4]
                            .get_text(" ", strip=True)
                            .replace("Номер лота", "")
                            .strip()
                        )
                        contract_price = (
                            td_elements[6]
                            .get_text(" ", strip=True)
                            .replace("Цена предложенная участником", "")
                            .replace("\xa0", " ")
                            .strip()
                        )

                        texts = [
                            text.strip()
                            for text in td_elements[6].find_all(
                                string=True, recursive=False
                            )
                        ]
                        contract_price = ", ".join(
                            text.replace("\xa0", " ") for text in texts
                        )
                        contract_price = contract_price.lstrip(", ")
                        # Разбиваем текст по "<br><br>" и объединяем через запятую, если значений больше одного
                        # prices = [
                        #     price.strip()
                        #     for price in contract_price.split("  ")
                        #     if price
                        # ]

                        # # Объединяем значения через запятую
                        # contract_price_cleaned = ", ".join(prices)
                        # logger.info(price)
                        contract_number = (
                            td_elements[8]
                            .get_text(strip=True)
                            .replace("Номер контракта", "")
                            .strip()
                        )
                        contract_signing_date = (
                            td_elements[9]
                            .get_text(strip=True)
                            .replace("Дата подписания контракта", "")
                            .strip()
                        )

                        datas = {
                            "№": serial_number,
                            "Номер объявления": ad_number,
                            "Наименование закупки": name_of_purchase,
                            "Наименования победителя": winners_names,
                            "Номер лота": lot_number,
                            "Цена контракта": contract_price,
                            "Номер контракта": contract_number,
                            "Дата подписания контракта": contract_signing_date,
                        }
                        all_data.append(datas)
    # logger.info(all_data)
    df = pd.DataFrame(all_data)
    df.to_excel("output.xlsx", index=False)


def parsing_company():
    # Множество для хранения уникальных itm_value
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        # Извлекаем ИНН из имени файла
        inn_match = re.search(r"inn_(\d+)\.html", html_file.name)
        if inn_match:
            inn = inn_match.group(1)
        else:
            continue
        soup = BeautifulSoup(content, "lxml")
        tbody = soup.find("tbody")
        rows = tbody.find_all("tr")

        result = {
            "ИНН организации": None,
            "Наименование организации": None,
            "Организационно-правовая форма": None,
            "Населённый пункт": None,
            "Фактический адрес": None,
            "Рабочий телефон": None,
            "Банк": None,
            "Р/счет": None,
            "БИК": None,
            "Официальное информационное письмо по банковскому реквизиту": None,
            "ФИО пользователя": None,
            "Должность": None,
            "Роль": None,
            "Электронная почта": None,
        }

        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                # Если есть ссылка, добавляем её к значению
                link = cells[1].find("a")
                if link:
                    value = f"{value} (ссылка: {link['href']})"
                if key in result:
                    result[key] = value
                # Если ключ равен "ИНН организации", сохраняем его значение как inn_from_content
                if key == "ИНН организации":
                    inn_from_content = value
                    if inn_from_content == inn:
                        logger.info("ИНН сходится")
                    else:
                        logger.info(f"Разные, файл {inn}, внутри {inn_from_content}")
        write_inn_to_csv_inn(inn_from_content)

        # logger.info(result)
        json_output_file = json_directory / f"output_{inn_from_content}.json"
        with open(json_output_file, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)


def write_inn_to_csv_inn(inn):
    csv_file_successful = current_directory / "inns_successful.csv"
    with open(csv_file_successful, mode="a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([inn])


# Готовое решение потом возьмем данные  из parsed_data.json
def parsing_company_():
    # Множество для хранения уникальных itm_value
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        # Извлекаем ИНН из имени файла
        inn_match = re.search(r"inn_(\d+)\.html", html_file.name)
        if inn_match:
            inn = inn_match.group(1)
        else:
            continue
        soup = BeautifulSoup(content, "lxml")
        tbody = soup.find("tbody")
        rows = tbody.find_all("tr")

        result = {
            "ИНН организации": None,
            "Наименование организации": None,
            "Организационно-правовая форма": None,
            "Населённый пункт": None,
            "Фактический адрес": None,
            "Рабочий телефон": None,
            "Банк": None,
            "Р/счет": None,
            "БИК": None,
            "Официальное информационное письмо по банковскому реквизиту": None,
            "ФИО пользователя": None,
            "Должность": None,
            "Роль": None,
            "Электронная почта": None,
        }

        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                # Если есть ссылка, добавляем её к значению
                link = cells[1].find("a")
                if link:
                    value = f"{value} (ссылка: {link['href']})"
                if key in result:
                    result[key] = value
                # Если ключ равен "ИНН организации", сохраняем его значение как inn_from_content
                if key == "ИНН организации":
                    inn_from_content = value
                    if inn_from_content == inn:
                        logger.info("ИНН сходится")
                    else:
                        logger.info(f"Разные, файл {inn}, внутри {inn_from_content}")

        # logger.info(result)
        exit()
        all_data.append(result)
    output_file = "output_html.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)
    # # Создание DataFrame из данных, полученных из HTML
    # html_df = pd.DataFrame(all_data)

    # # Объединение DataFrame из JSON и HTML по столбцу "ИНН организации", оставляя только совпадающие значения
    # merged_df = pd.merge(json_df, html_df, on="ИНН организации", how="inner")

    # # Запись объединённых данных в Excel
    # merged_df.to_excel("output.xlsx", index=False)

    # # logger.info(all_data)
    # df = pd.DataFrame(all_data)
    # df.to_excel("output.xlsx", index=False)
    # Записать список словарей в JSON файл


def parsing_page_company():
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_page_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        soup = BeautifulSoup(content, "lxml")
        table = soup.find("table", attrs={"class": "display-table public-table"})
        if table:
            rows = table.find("tbody").find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                data = {
                    "ИНН организации": cells[0].get_text(strip=True),
                    "Наименование организации": cells[1].get_text(strip=True),
                    "Организационно-правовая форма": cells[2].get_text(strip=True),
                    "Статус": cells[3].get_text(strip=True),
                    "Дата регистрации": cells[4].get_text(strip=True),
                }
                all_data.append(data)
    # Записать все данные в JSON файл
    output_file = "parsed_data.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)
    # Записать ИНН каждой организации в CSV файл
    # Записать ИНН каждой организации в CSV файл с использованием pandas
    # df = pd.DataFrame(all_data)
    # df[["ИНН организации"]].to_csv(csv_output_file, index=False, encoding="utf-8")
    # # Создание DataFrame и запись уникальных значений ИНН организации в CSV
    df = pd.DataFrame(all_data)
    unique_inn_df = df[["ИНН организации"]].drop_duplicates()
    unique_inn_df.to_csv(csv_output_file, index=False, encoding="utf-8")


# Функция для выполнения основной логики
def main():
    url = "http://zakupki.gov.kg/popp/view/services/registry/suppliers.xhtml"
    asyncio.run(single_html_one(url))
    # asyncio.run(single_html_page_company(url))


def get_write_json():
    # Загрузка данных из JSON файлов
    with open("output_html.json", "r", encoding="utf-8") as f:
        output_html = json.load(f)

    with open("inn_company.json", "r", encoding="utf-8") as f:
        inn_company = json.load(f)

    # Создаем словарь для быстрого поиска по ИНН из inn_company.json
    inn_dict = {entry["ИНН организации"]: entry for entry in inn_company}

    # Обновление данных в output_html.json
    for company in output_html:
        inn = company.get("ИНН организации")
        if inn in inn_dict:
            company.update(
                {
                    "Статус": inn_dict[inn]["Статус"],
                    "Дата регистрации": inn_dict[inn]["Дата регистрации"],
                }
            )

    # Сохранение обновленного списка в JSON файл
    with open("output_html_updated.json", "w", encoding="utf-8") as f:
        json.dump(output_html, f, ensure_ascii=False, indent=4)

    # Загрузка данных из JSON файла
    with open("output_html_updated.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Сбор всех уникальных ключей из всех словарей
    unique_keys = set()
    for item in data:
        unique_keys.update(item.keys())

    # Создание списка всех уникальных ключей
    unique_keys = sorted(unique_keys)

    # Преобразование списка словарей в DataFrame с учетом всех ключей
    normalized_data = []
    for item in data:
        normalized_item = {key: item.get(key, None) for key in unique_keys}
        normalized_data.append(normalized_item)

    df = pd.DataFrame(normalized_data)

    # Запись данных в Excel файл
    output_excel = "output_html_updated.xlsx"
    df.to_excel(output_excel, index=False, sheet_name="Data")


def delet_html():
    # Путь к файлу CSV и папке с HTML-файлами
    csv_file_path = "inns_successful.csv"
    html_files_folder = "html_files"

    # Чтение значений ИНН из файла CSV
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        inns_successful = set(row[0].strip() for row in reader)

    # Получение списка файлов в папке html_files
    html_files = os.listdir(html_files_folder)

    # Итерация по файлам и удаление тех, которые отсутствуют в inns_successful
    for filename in html_files:
        # Проверяем, что имя файла соответствует шаблону "inn_XXXXXXXXXXXXX.html"
        if filename.startswith("inn_") and filename.endswith(".html"):
            # Извлекаем ИНН из имени файла (без 'inn_' и '.html')
            inn_from_file = filename[4:-5]
            # Удаляем файл, если ИНН не в списке успешных
            if inn_from_file not in inns_successful:
                file_path = os.path.join(html_files_folder, filename)
                os.remove(file_path)
                print(f"Удален файл: {file_path}")


if __name__ == "__main__":
    # main()
    # parsing_page()
    # parsing_company()
    # get_write_json()
    # parsing_page_company()
    delet_html()
