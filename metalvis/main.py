# -*- mode: python ; coding: utf-8 -*-

import aiofiles
import asyncio
import sys
from time import sleep
from playwright.async_api import async_playwright

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser
import csv
from openpyxl import Workbook
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


async def read_csv_values():
    current_directory = os.getcwd()
    filename_csv = os.path.join(current_directory, "list_sku.csv")
    values = []
    async with aiofiles.open(filename_csv, mode="r", encoding="utf-8") as file:
        async for line in file:
            values.append(line.strip())
    return values


async def read_json_and_get_urls(filename):
    async with aiofiles.open(filename, "r", encoding="utf-8") as file:
        content = await file.read()
        data = json.loads(content)
        return data


async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


write_lock = asyncio.Lock()


def chunk_list(lst, n):
    """Разделяет lst на n равных частей"""
    k, m = divmod(len(lst), n)
    return (lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


async def process_urls(values, playwright_instance, browsers_path):
    browser = await playwright_instance.chromium.launch(headless=False)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()
    all_hrefs = []

    for value_first in values:
        first_value = value_first.split(";")[0].strip()
        if first_value:
            url_start = f"https://metalvis.ua/uk/Search?_vt=0&_search={first_value}"
            await page.goto(url_start)
            try:
                xpath_begin_search = '//section[@id="GPageBody"]//div[@class="h3"]/a'
                await page.wait_for_selector(
                    f"xpath={xpath_begin_search}", state="visible", timeout=3000
                )
                element_handle = await page.query_selector(
                    f"xpath={xpath_begin_search}"
                )
                if element_handle:
                    href_value = await element_handle.get_attribute("href")
                    url_ua = f"https://metalvis.ua{href_value}"
                    url_ru = f"https://metalvis.ua{href_value.replace('/uk/', '/ru/')}"
                    all_hrefs.append(
                        {"sku": first_value, "url_ua": url_ua, "url_ru": url_ru}
                    )
                await asyncio.sleep(random.randint(1, 3))
            except Exception as e:
                print(f"Ошибка: {e}")

    await browser.close()
    return all_hrefs


async def get_urls():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")

    json_file_path = "all_urls.json"
    # Проверяем и удаляем файл, если он уже существует
    if os.path.exists(json_file_path):
        os.remove(json_file_path)
    # Удаляем папку temp полностью
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        shutil.rmtree(temp_path)

    values = await read_csv_values()
    num_threads = 5  # Количество "потоков"
    # Разделяем список values на num_threads частей
    chunk_size = len(values) // num_threads
    tasks = []
    current_directory = os.getcwd()
    browsers_path = os.path.join(current_directory, "pw-browsers")

    async with async_playwright() as playwright:
        for i in range(num_threads):
            chunk = values[i * chunk_size : (i + 1) * chunk_size]
            task = process_urls(chunk, playwright, browsers_path)
            tasks.append(task)
        if len(values) % num_threads != 0:  # Если есть остаток
            chunk = values[num_threads * chunk_size :]
            task = process_urls(chunk, playwright, browsers_path)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        # Объединяем все результаты
        all_hrefs = [item for sublist in results for item in sublist]
        filename = "all_urls.json"
        # Записываем результаты
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(all_hrefs, ensure_ascii=False, indent=4))


async def get_html_files():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    rus_path = os.path.join(temp_path, "rus")
    ua_path = os.path.join(temp_path, "ua")
    datas = await read_json_and_get_urls("all_urls.json")
    await create_directories_async(
        [
            temp_path,
            rus_path,
            ua_path,
        ]
    )
    session = AsyncSession()
    count = 0
    for data in datas:
        count += 1
        url_ua = data["url_ua"]
        url_ru = data["url_ru"]
        sku = data["sku"]

        filename_html_ua = os.path.join(ua_path, f"{sku}.html")
        filename_html_ru = os.path.join(rus_path, f"{sku}.html")
        download_performed = False  # Флаг, указывающий на выполнение загрузки

        if not os.path.exists(filename_html_ua):
            response_ua = await session.get(url_ua, headers=headers, cookies=cookies)
            html_ua = response_ua.text
            with open(filename_html_ua, "w", encoding="utf-8") as f:
                f.write(html_ua)
            download_performed = True  # Обновляем флаг после загрузки

        if not os.path.exists(filename_html_ru):
            response_ru = await session.get(url_ru, headers=headers, cookies=cookies)
            html_ru = response_ru.text
            with open(filename_html_ru, "w", encoding="utf-8") as f:
                f.write(html_ru)
            download_performed = True  # Обновляем флаг после загрузки

        # Если была выполнена загрузка, ждем указанное время
        if download_performed:
            sleep_time = random.randint(1, 2)
            await asyncio.sleep(sleep_time)
    await session.close()


def parsin_html():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
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
    with open("all_products_ua.json", "w", encoding="utf-8") as json_file:
        json.dump(all_products_ua, json_file, ensure_ascii=False, indent=4)

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
                properties["Название товара на русском"] = product_name_node.text(
                    strip=True
                )

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

    print("Данные о всех товарах сохранены")


def write_csv_ua():
    # Читаем данные из JSON файла
    with open("all_products_ua.json", "r", encoding="utf-8") as file:
        products = json.load(file)

    # Заголовки для CSV файла на Украинском языке
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

    print("Данные успешно сохранены в CSV-файл. для Украинского языка")


def write_csv_ru():
    # Читаем данные из JSON файла
    with open("all_products_ru.json", "r", encoding="utf-8") as file:
        products = json.load(file)

    # Заголовки для CSV файла на Русском языке
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

    print("Данные успешно сохранены в CSV-файл. для Русского языка")


def two_csv_in_xlsx():
    # Шаг 1: Считываем products_ua.csv и строим словарь артикулов и наименований
    ua_products = {}
    with open("products_ua.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            ua_products[row["Артикул"]] = row["Наименование"]

    # Шаг 2: Читаем products_ru.csv, обновляем наименования и сохраняем изменения
    updated_rows = []
    with open("products_ru.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        fieldnames = reader.fieldnames  # сохраняем названия столбцов

        for row in reader:
            # Обновляем наименование, если находим совпадение артикула
            if row["Артикул"] in ua_products:
                row["Наименование"] = ua_products[row["Артикул"]]
            updated_rows.append(row)

    # Перезаписываем products_ru.csv с обновленными данными
    with open("products_ru.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
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
        with open(filename, newline="", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                sheet.append(row)

    # Загружаем данные из CSV файлов
    load_csv_to_sheet("products_ua.csv", ws_ua)
    load_csv_to_sheet("products_ru.csv", ws_ru)

    # Сохраняем Excel файл
    wb.save("products_combined.xlsx")
    print("Файл products_combined сохранен. Все готово")


while True:
    print("Введите 1 запуска программы\nВведите 0 для закрытия программы")
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        asyncio.run(get_urls())
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(get_html_files())
        parsin_html()
        write_csv_ua()
        write_csv_ru()
        two_csv_in_xlsx()
    elif user_input == 0:
        print("Программа завершена.")
        sys.exit(1)

    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
