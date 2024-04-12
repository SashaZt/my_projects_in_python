# -*- mode: python ; coding: utf-8 -*-
# Скачивание PDF файлов
import aiofiles
import asyncio
import sys
from time import sleep
from playwright.async_api import async_playwright

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser
import csv
from openpyxl import Workbook


# import aiohttp
# import aiofiles
import re

# import aiomysql
import json

import time
import glob
import string
import shutil
import random
import os
import glob
from asyncio import sleep

# from bs4 import BeautifulSoup
import json

cookies = {
    "cacheID": "d304c0ef-923b-48ec-a42d-b2a0db7a4f99",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "referer": "https://metalvis.ua/ru/catalog/sku-anker-t88v-1080-shurup/",
    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
}

# Выкачка PDF файлов
# async def download_file(session, url, cookies_dict, filename_pdf):
#     headers = {
#         "authority": "www.assessedvalues2.com",
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
#         "cache-control": "no-cache",
#         # 'cookie': 'ASP.NET_SessionId=w1lubbprygi3wq5hdfiwa0tl; CookieTest=Testme; sucuri_cloudproxy_uuid_0766875d6=399c6876557455524af4b491910baaac; SearchList2=; SearchList3=; SearchList=000101',
#         "dnt": "1",
#         "pragma": "no-cache",
#         "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": '"Windows"',
#         "sec-fetch-dest": "document",
#         "sec-fetch-mode": "navigate",
#         "sec-fetch-site": "same-origin",
#         "sec-fetch-user": "?1",
#         "upgrade-insecure-requests": "1",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
#     }

#     async with session.get(url, headers=headers, cookies=cookies_dict) as response:
#         if response.status == 200:
#             async with aiofiles.open(filename_pdf, "wb") as out_file:
#                 while True:
#                     chunk = await response.content.read(1024)
#                     if not chunk:
#                         break
#                     await out_file.write(chunk)
#         else:
#             print(f"Ошибка при загрузке файла: {response.status}")


# Запись логов
# async def write_log(message, filename):
#     current_directory = os.getcwd()
#     temp_path = os.path.join(current_directory, "temp")
#     log_path = os.path.join(temp_path, "log")
#     for folder in [
#         temp_path,
#         log_path,
#     ]:
#         if not os.path.exists(folder):
#             os.makedirs(folder)
#     filename_log = os.path.join(log_path, f"{filename}.txt")
#     async with aiofiles.open(filename_log, "a", encoding="utf-8") as log_file:
#         await log_file.write(message + "\n")


# Прочитать файл
# async def read_csv_values():
#     current_directory = os.getcwd()
#     filename_csv = os.path.join(current_directory, "list_keyno.csv")
#     values = []
#     async with aiofiles.open(filename_csv, mode="r", encoding="utf-8") as file:
#         async for line in file:
#             values.append(line.strip())
#     return values


async def read_csv_values():
    current_directory = os.getcwd()
    filename_csv = os.path.join(current_directory, "list_sku.csv")
    values = []
    async with aiofiles.open(filename_csv, mode="r", encoding="utf-8") as file:
        async for line in file:
            values.append(line.strip())
    return values


async def write_json_all_hrefs(all_hrefs):
    async with aiofiles.open("all_urls.json", "w", encoding="utf-8") as file:
        await file.write(json.dumps(all_hrefs, ensure_ascii=False, indent=4))


async def read_json_and_get_urls(filename):
    async with aiofiles.open(filename, "r", encoding="utf-8") as file:
        content = await file.read()
        data = json.loads(content)
        return data


# Основная функция получение PDF
async def get_urls():
    current_directory = os.getcwd()
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    temp_path = os.path.join(current_directory, "temp")
    log_path = os.path.join(temp_path, "log")
    rus_path = os.path.join(temp_path, "rus")
    ua_path = os.path.join(temp_path, "ua")
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, rus_path, ua_path, log_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удаление папки log_path вместе со всем содержимым
    shutil.rmtree(log_path, ignore_errors=True)
    values_csv = await read_csv_values()
    async with async_playwright() as playwright:
        timeout = 3000
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        all_hrefs = []
        for value_first in values_csv:
            parts = value_first.split(";")  # Разделяем строку на части
            first_value = re.sub(r"\s+", " ", parts[0]).strip()

            if first_value:  # Проверяем, что строка не пустая
                url_start = f"https://metalvis.ua/uk/Search?_vt=0&_search={first_value}"
                await page.goto(url_start)
                try:
                    xpath_begin_search = (
                        '//section[@id="GPageBody"]//div[@class="h3"]/a'
                    )
                    await page.wait_for_selector(
                        f"xpath={xpath_begin_search}", state="visible", timeout=timeout
                    )
                except:
                    continue

                # Исправленный метод для поиска элементов по XPath
                element_handle = await page.query_selector(
                    f"xpath={xpath_begin_search}"
                )
                if element_handle:
                    href_value_ua = await element_handle.get_attribute("href")
                    href_value_rus = await element_handle.get_attribute("href")
                    url_ua = f"https://metalvis.ua{href_value_ua}"
                    url_ru = (
                        f"https://metalvis.ua{href_value_rus.replace('/uk/', '/ru/')}"
                    )
                    all_hrefs.append(
                        {"sku": first_value, "url_ua": url_ua, "url_ru": url_ru}
                    )

                sleep_time = random.randint(5, 10)

                await asyncio.sleep(sleep_time)

        await browser.close()
        await write_json_all_hrefs(all_hrefs)


async def get_html_files():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    rus_path = os.path.join(temp_path, "rus")
    ua_path = os.path.join(temp_path, "ua")
    datas = await read_json_and_get_urls("all_urls.json")
    session = AsyncSession()
    for data in datas:
        url_ua = data["url_ua"]
        url_ru = data["url_ru"]
        sku = data["sku"]

        filename_html_ua = os.path.join(ua_path, f"{sku}.html")
        filename_html_ru = os.path.join(rus_path, f"{sku}.html")
        if not os.path.exists(filename_html_ua):
            response_ua = await session.get(url_ua, headers=headers, cookies=cookies)
            html_ua = response_ua.text
            with open(filename_html_ua, "w", encoding="utf-8") as f:
                f.write(html_ua)
        if not os.path.exists(filename_html_ru):
            response_ru = await session.get(url_ru, headers=headers, cookies=cookies)
            html_ru = response_ru.text
            with open(filename_html_ru, "w", encoding="utf-8") as f:
                f.write(html_ru)
        sleep_time = random.randint(5, 10)

        await asyncio.sleep(sleep_time)
    await session.close()


def parsin_html():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    log_path = os.path.join(temp_path, "log")

    rus_path = os.path.join(temp_path, "rus")
    ua_path = os.path.join(temp_path, "ua")
    folder_ua = os.path.join(ua_path, "*.html")
    folder_ru = os.path.join(rus_path, "*.html")

    files_html_ua = glob.glob(folder_ua)
    files_html_ru = glob.glob(folder_ru)
    all_products_ua = []
    all_products_ru = []
    for item in files_html_ua:
        with open(item, encoding="utf-8") as file:
            src = file.read()
            filename = os.path.basename(item)

            # Извлекаем часть имени файла до расширения
            sku = os.path.splitext(filename)[0]

            # Создаем парсер для прочитанного HTML
            parser = HTMLParser(src)

            # Словарь для хранения свойств текущего продукта
            properties = {}
            # Извлекаем наименование продукта из тега <h1>
            product_name_node = parser.css_first('h1.product_name[itemprop="name"]')
            if product_name_node:
                properties["Наименование"] = product_name_node.text(strip=True)

            # Находим блок с информацией о продукте
            properties_block = parser.css_first(".Properties-block")
            if properties_block:
                # Итерация по всем строкам с описанием свойств внутри блока
                for row in properties_block.css(".description-row"):
                    property_node = row.css_first(".Property")
                    if property_node is None:
                        continue

                    property_name = property_node.text(strip=True)
                    value_node = row.css_first(".value")
                    if value_node is None:
                        continue

                    property_value = (
                        value_node.text(strip=True).replace("\n", " ").strip()
                    )

                    # Добавляем свойство в словарь текущего продукта
                    properties[property_name] = property_value
            properties["Артикул"] = sku
            # Добавляем словарь текущего продукта в список всех продуктов
            if properties:
                all_products_ua.append(properties)
    for item in files_html_ru:
        with open(item, encoding="utf-8") as file:
            src = file.read()
            filename = os.path.basename(item)

            # Извлекаем часть имени файла до расширения
            sku = os.path.splitext(filename)[0]

            # Создаем парсер для прочитанного HTML
            parser = HTMLParser(src)

            # Словарь для хранения свойств текущего продукта
            properties = {}
            # Извлекаем наименование продукта из тега <h1>
            product_name_node = parser.css_first('h1.product_name[itemprop="name"]')
            if product_name_node:
                properties["Название товара на русском"] = product_name_node.text(strip=True)

            # Находим блок с информацией о продукте
            properties_block = parser.css_first(".Properties-block")
            if properties_block:
                # Итерация по всем строкам с описанием свойств внутри блока
                for row in properties_block.css(".description-row"):
                    property_node = row.css_first(".Property")
                    if property_node is None:
                        continue

                    property_name = property_node.text(strip=True)
                    value_node = row.css_first(".value")
                    if value_node is None:
                        continue

                    property_value = (
                        value_node.text(strip=True).replace("\n", " ").strip()
                    )

                    # Добавляем свойство в словарь текущего продукта
                    properties[property_name] = property_value
            properties["Артикул"] = sku
            # Добавляем словарь текущего продукта в список всех продуктов
            if properties:
                all_products_ru.append(properties)

    # Записываем список словарей в файл JSON
    with open("all_products_ru.json", "w", encoding="utf-8") as json_file:
        json.dump(all_products_ru, json_file, ensure_ascii=False, indent=4)
    with open("all_products_ua.json", "w", encoding="utf-8") as json_file:
        json.dump(all_products_ua, json_file, ensure_ascii=False, indent=4)

    print("Данные сохранены")
    # # Находим все блоки описания
    # for row in parser.css('.Properties-block'):
    #     print(row)
    #     # Извлекаем название свойства
    #     property_name = row.css_first('.Property').text(strip=True)

    #     # Извлекаем значение свойства
    #     # Учитываем, что значение может содержать вложенные элементы, такие как <span>
    #     value_node = row.css_first('.value')
    #     # Если внутри .value есть вложенные элементы, извлекаем содержимое, исключая вложенные теги
    #     property_value = " ".join(value_node.text(deep=True, separator=' ').split())

    #     # Добавляем пару ключ-значение в словарь
    #     properties[property_name] = property_value

    # # Выводим полученный словарь
    # for key, value in properties.items():
    #     print(f"{key}: {value}")


def write_csv_ua():
    # Читаем данные из JSON файла
    with open("all_products_ua.json", "r", encoding="utf-8") as file:
        products = json.load(file)

    # Заголовки для CSV файла
    headers = [
        "Артикул",
        "Наименование",
        "ВИРОБНИК",
        "СТАНДАРТ (ГРУПА)",
        "МАТЕРІАЛ",
        "КЛАС МІЦНОСТІ",
        "ПОКРИТТЯ",
        "ГОЛОВКА",
        "МОДЕЛЬ (МАРКА)",
        "КОЛІР",
        "ВИД НАРІЗІ",
        "ШЛІЦ",
        "ТИП НАРІЗІ",
        "ГРУПА КРІПЛЕННЯ",
        "ГАЛУЗЬ ЗАСТОСУВАННЯ",
        "ДІАМЕТР, ММ",
        "КРОК НАРІЗІ, ММ",
        "ДОВЖИНА, ММ",
        "ДОВЖИНА НАРІЗІ (МАКС.), ММ",
        "РОЗМІР ПІД КЛЮЧ, ММ",
        "РОЗМІР ПІД БІТУ",
        "ТИП ГАЙКИ",
        "ДЛЯ ЯКОЇ ОСНОВИ?",
        "ТОВЩИНА МАТЕРІАЛУ, ЩО ЗАКРІПЛЮЄТЬСЯ (MIN), ММ",
        "ЗОВНІШНІЙ ДІАМЕТР, ММ",
        "ТОВЩИНА МАТЕРІАЛУ, ЩО ЗАКРІПЛЮЄТЬСЯ (MAX), ММ",
        "ТОВЩИНА, ММ",
        "ШИРИНА, ММ",
        "ВИСОТА, ММ",
        "ТОВЩИНА БАЗОВОГО МАТЕРІАЛУ (MIN), ММ",
        "ТОВЩИНА БАЗОВОГО МАТЕРІАЛУ (MAX), ММ",
        "ДІАМЕТР ОТВОРУ, ММ",
        "ЄМНІСТЬ (ОБСЯГ, РОЗМІР)",
        "ТЕМПЕРАТУРА МОНТАЖУ",
        "ПІД ДЮБЕЛЬ N (P, NB) ДІАМЕТРОМ, ММ",
        "ПІД ШУРУП ДІАМЕТРОМ, ММ",
        "РОБОЧА ДОВЖИНА, ММ",
        "ПРОДУКТОВА ЛІНІЙКА",
        "БРЕНД",
        "ХВОСТОВИК",
        "МІСЦЕ ЗАСТОСУВАННЯ",
        "ВАШ ІНСТРУМЕНТ",
        "ПОТУЖНІСТЬ, ВТ",
        "НАПРУГА, В",
        "ЧИСЛО ОБЕРТІВ, ОБ / ХВ",
        "ЧИСЛО УДАРІВ, УД / ХВ",
        "ЧИСЛО ХОДІВ, ХІД / ХВ",
        "КРОК ЗУБІВ, ММ",
        "ДЛЯ ЯКОЇ ПОВЕРХНІ?",
        "ПІД ФАРБУВАННЯ",
    ]

    # Создаем CSV файл
    with open("products_ua.csv", "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter=";")
        writer.writeheader()

        for product in products:
            # Создаем словарь для каждой строки, где ключи соответствуют заголовкам
            row = {}
            product_upper = {key.upper(): value for key, value in product.items()}
            for header in headers:
                if header in product:
                    row[header] = product[header]
                elif header in product_upper:  # Проверяем верхний регистр
                    row[header] = product_upper[header]
                else:
                    row[header] = (
                        ""  # Если совпадение не найдено, вставляем пустую строку
                    )

            writer.writerow(row)

    print("Данные успешно сохранены в CSV-файл.")


def write_csv_ru():
    # Читаем данные из JSON файла
    with open("all_products_ru.json", "r", encoding="utf-8") as file:
        products = json.load(file)

    # Заголовки для CSV файла
    headers = [
        "Артикул",
        "Наименование",
        "Название товара на русском",
        "ПРОИЗВОДИТЕЛЬ",
        "СТАНДАРТ (ГРУППА)",
        "МАТЕРИАЛ",
        "КЛАСС ПРОЧНОСТИ",
        "ПОКРЫТИЕ",
        "ГОЛОВКА",
        "МОДЕЛЬ (МАРКА)",
        "ЦВЕТ",
        "ВИД РЕЗЬБЫ",
        "ШЛИЦ",
        "ТИП РЕЗЬБЫ",
        "ГРУППА КРЕПЕЖА",
        "ОБЛАСТЬ ПРИМЕНЕНИЯ",
        "ДИАМЕТР, ММ",
        "ШАГ РЕЗЬБЫ, ММ",
        "ДЛИНА, ММ",
        "ДЛИНА РЕЗЬБЫ (МАКС.), ММ",
        "РАЗМЕР ПОД КЛЮЧ, ММ",
        "РАЗМЕР ПОД БИТУ",
        "ТИП ГАЙКИ",
        "ДЛЯ КАКОГО ОСНОВАНИЯ?",
        "ТОЛЩИНА ЗАКРЕПЛЯЕМОГО МАТЕРИАЛА (MIN), ММ",
        "НАРУЖНЫЙ ДИАМЕТР, ММ",
        "ТОЛЩИНА ЗАКРЕПЛЯЕМОГО МАТЕРИАЛА (MAX), ММ",
        "ТОЛЩИНА, ММ",
        "ШИРИНА, ММ",
        "ВЫСОТА, ММ",
        "ТОЛЩИНА БАЗОВОГО МАТЕРИАЛА (MIN), ММ",
        "ТОЛЩИНА БАЗОВОГО МАТЕРИАЛА (MAX), ММ",
        "ДИАМЕТР ОТВЕРСТИЯ, ММ",
        "ЁМКОСТЬ (ОБЪЁМ, РАЗМЕР)",
        "ТЕМПЕРАТУРА МОНТАЖА",
        "ПОД ДЮБЕЛЬ N (P, NB) ДИАМЕТРОМ, ММ",
        "ПОД ШУРУП ДИАМЕТРОМ, ММ",
        "РАБОЧАЯ ДЛИНА, ММ",
        "ПРОДУКТОВАЯ ЛИНЕЙКА",
        "БРЕНД",
        "ХВОСТОВИК",
        "МЕСТО ПРИМЕНЕНИЯ",
        "ВАШ ИНСТРУМЕНТ",
        "МОЩНОСТЬ, ВТ",
        "НАПРЯЖЕНИЕ, В",
        "ЧИСЛО ОБОРОТОВ, ОБ/МИН",
        "ЧИСЛО УДАРОВ, УД/МИН",
        "ЧИСЛО ХОДОВ, ХОД/МИН",
        "ШАГ ЗУБЬЕВ, ММ",
        "ДЛЯ КАКОЙ ПОВЕРХНОСТИ?",
        "ПОД ОКРАСКУ",
    ]

    # Создаем CSV файл
    with open("products_ru.csv", "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter=";")
        writer.writeheader()

        for product in products:
            # Создаем словарь для каждой строки, где ключи соответствуют заголовкам
            row = {}
            product_upper = {key.upper(): value for key, value in product.items()}
            for header in headers:
                if header in product:
                    row[header] = product[header]
                elif header in product_upper:  # Проверяем верхний регистр
                    row[header] = product_upper[header]
                else:
                    row[header] = (
                        ""  # Если совпадение не найдено, вставляем пустую строку
                    )

            writer.writerow(row)

    print("Данные успешно сохранены в CSV-файл.")

def two_csv_in_xlsx():
    # Шаг 1: Считываем products_ua.csv и строим словарь артикулов и наименований
    ua_products = {}
    with open('products_ua.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            ua_products[row['Артикул']] = row['Наименование']

    # Шаг 2: Читаем products_ru.csv, обновляем наименования и сохраняем изменения
    updated_rows = []
    with open('products_ru.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        fieldnames = reader.fieldnames  # сохраняем названия столбцов

        for row in reader:
            # Обновляем наименование, если находим совпадение артикула
            if row['Артикул'] in ua_products:
                row['Наименование'] = ua_products[row['Артикул']]
            updated_rows.append(row)

    # Перезаписываем products_ru.csv с обновленными данными
    with open('products_ru.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(updated_rows)

    # Шаг 3: Записываем обновленные данные в Excel
    # Создаем новый Excel файл и листы
    wb = Workbook()
    ws_ua = wb.active
    ws_ua.title = "Укр"

    # Добавляем второй лист
    ws_ru = wb.create_sheet("Рус")

    # Функция для загрузки данных из CSV в лист Excel
    def load_csv_to_sheet(filename, sheet):
        with open(filename, newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                sheet.append(row)

    # Загружаем данные из CSV файлов
    load_csv_to_sheet('products_ua.csv', ws_ua)
    load_csv_to_sheet('products_ru.csv', ws_ru)

    # Сохраняем Excel файл
    wb.save('products_combined.xlsx')


# async def save_html(html, filename):
#     print(filename)
#     # Сохраняем HTML-код страницы в файл
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(html)
#     sleep_time = random.randint(5, 10)

#     await asyncio.sleep(sleep_time)


# async def get_search_info_json(page_content_soup, jurcode, keyno, search_results_path):

#     # Парсинг HTML с помощью BeautifulSoup
#     soup = BeautifulSoup(page_content_soup, "lxml")

#     headers = [th.get_text().strip() for th in soup.find_all("th")]
#     # Первый ряд пропускаем, т.к. это заголовки

#     rows = soup.find_all("tr")[1:]
#     all_data = []
#     for row in rows:
#         values = [td.get_text().strip() for td in row.find_all("td")]
#         pdf_link = row.find("a")["href"] if row.find("a") else None
#         data_dict = dict(zip(headers, values))
#         pdf_link = f"https://www.assessedvalues2.com{pdf_link}"
#         if pdf_link:
#             data_dict["Card_PDF"] = pdf_link
#         all_data.append(data_dict)
#     # Сохраняем полученные данные в JSON файл
#     filename_json_search_info = os.path.join(
#         search_results_path, f"{jurcode}_{keyno}.json"
#     )
#     if not os.path.exists(filename_json_search_info):
#         async with aiofiles.open(
#             filename_json_search_info, mode="w", encoding="utf-8"
#         ) as f:
#             await f.write(json.dumps(all_data, ensure_ascii=False, indent=4))


# def load_config():
#     if getattr(sys, "frozen", False):
#         # Если приложение 'заморожено' с помощью PyInstaller
#         application_path = os.path.dirname(sys.executable)
#     else:
#         # Обычный режим выполнения (например, во время разработки)
#         application_path = os.path.dirname(os.path.abspath(__file__))

#     filename_config = os.path.join(application_path, "config.json")
#     if not os.path.exists(filename_config):
#         print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
#         time.sleep(3)
#         sys.exit(1)
#     else:
#         with open(filename_config, "r") as config_file:
#             config = json.load(config_file)

#     return config


# def convert_card_pdf_url(old_url):
#     # Проверяем наличие '?' в URL
#     if "?" in old_url:
#         # Разбиваем URL на части и извлекаем параметры
#         _, query_string = old_url.split("?")
#         params = dict(param.split("=") for param in query_string.split("&"))

#         # Формируем новый URL
#         new_url = f"https://www.assessedvalues2.com/pdfs/{params['jurcode']}/{params['pdf']}.pdf"
#         return new_url
#     else:
#         # Возвращаем исходный URL, если в нем нет '?'
#         return old_url


# async def insert_data_into_table():
#     current_directory = os.getcwd()
#     # Создайте полный путь к папке temp
#     temp_path = os.path.join(current_directory, "temp")
#     search_results_path = os.path.join(temp_path, "search_results")
#     config = load_config()
#     db_config = config["db_config"]
#     conn = await aiomysql.connect(
#         host=db_config["host"],
#         port=3306,
#         user=db_config["user"],
#         password=db_config["password"],
#         db=db_config["database"],
#     )
#     cursor = await conn.cursor()

#     json_files = glob.glob(f"{search_results_path}/*.json")
#     for json_file_path in json_files:
#         filename = os.path.basename(json_file_path)
#         keyno, card = filename.rstrip(".json").split("_")
#         with open(json_file_path, "r", encoding="utf-8") as json_file:
#             data = json.load(json_file)
#         if not data:  # Пропускаем пустые json файлы
#             continue

#         await cursor.execute("SHOW COLUMNS FROM search_results")
#         columns_info = await cursor.fetchall()
#         column_can_be_null = {col[0]: (col[2] == "YES") for col in columns_info}

#         for record in data:
#             if "Card_PDF" in record:
#                 record["Card_PDF"] = convert_card_pdf_url(record["Card_PDF"])

#             filtered_record = {
#                 k: v for k, v in record.items() if k in column_can_be_null
#             }
#             columns_str = ", ".join(filtered_record.keys())
#             placeholders = ", ".join(["%s"] * len(filtered_record))
#             values = list(filtered_record.values())
#             if not columns_str:
#                 continue

#             insert_query = (
#                 f"INSERT INTO search_results ({columns_str}) VALUES ({placeholders})"
#             )
#             await cursor.execute(insert_query, values)

#         await conn.commit()
#         print(f"Данные успешно вставлены в таблицу search_results из файла {filename}.")

#     await cursor.close()
#     conn.close()


# async def fetch_db_data():
#     config = load_config()
#     db_config = config["db_config"]
#     async with aiomysql.connect(
#         host=db_config["host"],
#         port=3306,
#         user=db_config["user"],
#         password=db_config["password"],
#         db=db_config["database"],
#     ) as conn:
#         async with conn.cursor() as cur:
#             await cur.execute("SELECT Keyno, Card_PDF FROM search_results")
#             db_data = await cur.fetchall()
#     return db_data


# def extract_keyno_from_filename(filename):
#     match = re.search(r"_([0-9]+)_", filename)
#     if match:
#         return match.group(1)
#     return None


# async def find_missing_pdf_files():
#     current_directory = os.getcwd()
#     # Создайте полный путь к папке temp
#     temp_path = os.path.join(current_directory, "temp")
#     search_results_path = os.path.join(temp_path, "search_results")
#     # Извлекаем данные из БД
#     db_data = await fetch_db_data()
#     db_keynos = {str(keyno): pdf for keyno, pdf in db_data}

#     # Извлекаем Keyno из имен файлов
#     file_paths = glob.glob(os.path.join(search_results_path, "*.json"))
#     file_keynos = set(
#         extract_keyno_from_filename(os.path.basename(path)) for path in file_paths
#     )

#     # Находим недостающие Card_PDF
#     missing_pdfs = {db_keynos[keyno] for keyno in db_keynos if keyno not in file_keynos}
#     print(missing_pdfs)
#     return missing_pdfs


if __name__ == "__main__":

    # asyncio.run(get_urls())
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # asyncio.run(get_html_files())
    # parsin_html()
    # write_csv_ua()
    # write_csv_ru()
    two_csv_in_xlsx()


# while True:
#     print(
#         "Введите 1 для запуска парсинга\nВведите 3 для загрузки данных в БД \nВведите 0 для закрытия программы"
#     )
#     user_input = int(input("Выберите действие: "))

#     if user_input == 1:
#         asyncio.run(run())
#     elif user_input == 0:
#         print("Программа завершена.")
#         sys.exit(1)
#     elif user_input == 3:
#         asyncio.run(insert_data_into_table())

#     else:
#         print("Неверный ввод, пожалуйста, введите корректный номер действия.")
