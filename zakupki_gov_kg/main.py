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

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_files_page_directory = current_directory / "html_files_page"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_page_directory.mkdir(parents=True, exist_ok=True)

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


# # Асинхронная функция для сохранения HTML и получения ссылок по XPath
# async def single_html_one(url):
#     proxies = load_proxies()
#     proxy = random.choice(proxies) if proxies else None
#     if not proxies:
#         logger.info("Прокси не найдено, работа будет выполнена локально.")
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
#             # Пауза на 5 секунд
#             await asyncio.sleep(5)
#             # Поиск элемента с нужными классами
#             element = await page.query_selector(
#                 "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
#             )
#             page_number = None
#             if element:
#                 # Извлекаем текст из элемента
#                 element_text = await element.inner_text()

#                 # Преобразуем текст и сохраняем в переменную page
#                 page_number_raw = element_text.strip().replace(" ", "_").lower()
#                 page_number = f"page_{page_number_raw.split('_')[-1]}"

#             content = await page.content()
#             html_file_path = html_files_directory / f"0{page_number}.html"
#             with open(html_file_path, "w", encoding="utf-8") as f:
#                 f.write(content)

#             # Цикл для нажатия на кнопку "Next Page", пока она есть на странице
#             while True:
#                 next_button = await page.query_selector(
#                     "a.ui-paginator-next.ui-state-default.ui-corner-all"
#                 )

#                 if next_button:
#                     # Нажимаем на кнопку "Next Page"
#                     await next_button.click()

#                     # Пауза, чтобы подождать загрузку новой страницы
#                     await asyncio.sleep(2)
#                     # Поиск элемента с нужными классами
#                     element = await page.query_selector(
#                         "a.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active"
#                     )
#                     page_number = None
#                     if element:
#                         # Извлекаем текст из элемента
#                         element_text = await element.inner_text()

#                         # Преобразуем текст и сохраняем в переменную page
#                         page_number_raw = element_text.strip().replace(" ", "_").lower()
#                         page_number = f"page_{page_number_raw.split('_')[-1]}"

#                     content = await page.content()
#                     html_file_path = html_files_directory / f"0{page_number}.html"
#                     with open(html_file_path, "w", encoding="utf-8") as f:
#                         f.write(content)

#         await context.close()
#         await browser.close()
#     except Exception as e:
#         logger.error(f"Ошибка при обработке URL: {e}")


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


async def single_html_one(url):
    inns = read_cities_from_csv(csv_output_file)
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
            await asyncio.sleep(2)
            for inn in inns:
                logger.info(inn)
                html_file_path = html_files_directory / f"inn_{inn}.html"
                if html_file_path.exists():
                    continue  # Переходим к следующей итерации цикла
                await page.wait_for_selector(
                    "input[type='text'][name='j_idt66']", timeout=10000
                )
                await page.fill("input[type='text'][name='j_idt66']", inn)
                logger.info(f"Вставили {inn}")
                await page.wait_for_selector(
                    "input[id='j_idt79'][type='submit']", timeout=10000
                )
                await page.click("input[id='j_idt79'][type='submit']")
                await page.wait_for_selector(
                    "table.display-table.public-table", timeout=10000
                )
                first_row_link = await page.query_selector(
                    "table.display-table.public-table tbody tr:first-child a[onclick*='mojarra.jsfcljs']"
                )
                if first_row_link:
                    await first_row_link.click()
                    # Проверяем наличие ошибки на странице
                error_element = await page.query_selector(
                    "p[style='font-size:24px;color:#1785aa;font-weight: bold;']"
                )
                if error_element:
                    logger.warning("Обнаружена ошибка на странице, перезагружаем...")
                    await page.goto(url, timeout=60000, wait_until="networkidle")
                # Находим элемент "Назад" и нажимаем на него
                back_button = await page.wait_for_selector(
                    "//a[@class='button-grey' and text()='Назад']",
                    timeout=30000,
                )
                # await asyncio.sleep(1)
                html_content = await page.content()
                with open(html_file_path, "w", encoding="utf-8") as file:
                    file.write(html_content)
                    logger.info(f"Файл {html_file_path} успешно сохранен.")

                await back_button.click()
                # Очистка поля ввода после сохранения
                await page.fill("input[type='text'][name='j_idt66']", "")

            await context.close()
            await browser.close()

    except Exception as e:
        logger.error(f"Ошибка при выполнении: {e}")


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
                        await asyncio.sleep(5)
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


# Готовое решение потом возьмем данные  из parsed_data.json
def parsing_company():
    # Множество для хранения уникальных itm_value
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        soup = BeautifulSoup(content, "lxml")
        tbody = soup.find("tbody")
        rows = tbody.find_all("tr")

        result = {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                # Если есть ссылка, добавляем её к значению
                link = cells[1].find("a")
                if link:
                    value = f"{value} (ссылка: {link['href']})"
                result[key] = value
        all_data.append(result)
    # logger.info(all_data)
    df = pd.DataFrame(all_data)
    df.to_excel("output.xlsx", index=False)


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
            result = []

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
    df = pd.DataFrame(all_data)
    df[["ИНН организации"]].to_csv(csv_output_file, index=False, encoding="utf-8")


# Функция для выполнения основной логики
def main():
    url = "http://zakupki.gov.kg/popp/view/services/registry/suppliers.xhtml"
    asyncio.run(single_html_one(url))
    # asyncio.run(single_html_page_company(url))


if __name__ == "__main__":
    main()
    # parsing_page()
    # parsing_company()
    # parsing_page_company()
