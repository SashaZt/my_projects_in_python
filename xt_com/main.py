# -*- mode: python ; coding: utf-8 -*-
from bs4 import BeautifulSoup
import asyncio
import aiofiles
import json
import os
<<<<<<< HEAD
import boto3
import sys
=======
import csv
import pandas as pd
import shutil
import sys
from openpyxl import Workbook
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
from glob import glob
import asyncio
from time import sleep
from playwright.async_api import async_playwright
<<<<<<< HEAD
import re
import json
import os
from asyncio import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom


# Создаем директории временные
=======
import aiohttp
import math
import re
import csv
import json
import os
import glob
from asyncio import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom
from selectolax.parser import HTMLParser


async def save_response_json(json_response, url_name, temp_path):
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(temp_path, f"{url_name}.json")
    print(filename)
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


async def run():
    url_start = "https://www.xt.com/ru/trade/5mc_usdt"
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
    # await create_directories_async(
    #     [
    #         temp_path,
    #         path_json_GamePal,
    #         path_json_item,
    #     ]
    # )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(url_start, wait_until="load")
        await asyncio.sleep(10)  # Увеличить задержку при необходимости

        def create_log_response_with_counter(url_name):
            async def log_response(response):

                api_url = "https://www.xt.com/sapi/v4/market/public/ticker/24h"
                request = response.request
                print(request)
                if request.method == "GET" and api_url in request.url:
                    try:
                        json_response = await response.json()
                        await save_response_json(json_response, url_name, temp_path)
                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response

        url_name = "test"
        handler = create_log_response_with_counter(url_name)
        page.on("response", handler)
        await asyncio.sleep(30)
        await browser.close()
        # elements = await page.query_selector_all(
        #     f"xpath=//div[starts-with(@class, 'market_name')]"
        # )

        # # Проходим по всем элементам и извлекаем их текст или другие данные
        # for element in elements:
        #     text = await element.text_content()
        #     print(text)
        # content = await page.content()

        # async with aiofiles.open("test.html", "w", encoding="utf-8") as f:
        #     await f.write(content)


>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


<<<<<<< HEAD
# Записываем пары в новую строку csv
async def save_to_csv(perpetual_pairs, filename):
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as file:
=======
async def save_to_csv(perpetual_pairs, filename):
    # Открываем файл на запись в асинхронном режиме
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as file:
        # Записываем каждую торговую пару в новую строку
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
        for pair in perpetual_pairs:
            await file.write(pair + "\n")  # Добавляем символ новой строки


<<<<<<< HEAD
# Разделяем пары на BTCUSDT на btc_usdt для дальнейших запросов
def convert_pair_name(pair_name):
    matches = re.match(r"([A-Z0-9]+)(USDT)$", pair_name)

    if matches:
=======
def convert_pair_name(pair_name):
    # Разделяем исходную строку на две части: "ORBS" и "USDT"
    matches = re.match(r"([A-Z0-9]+)(USDT)$", pair_name)

    if matches:
        # Формируем новую строку с нижними подчеркиваниями и в нижнем регистре
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
        result = f"{matches.group(1).lower()}_{matches.group(2).lower()}"
        return result
    return None


# Собираем пары, маркер цены и индекс цены
async def run_get_all_couples():
<<<<<<< HEAD
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    price_path = os.path.join(temp_path, "price")
    funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
    await create_directories_async([temp_path, price_path, funding_rate_record_path])
=======

    timeout = 20000
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    price_path = os.path.join(temp_path, "price")
    # if os.path.exists(temp_path) and os.path.isdir(temp_path):
    #     shutil.rmtree(temp_path)
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    # Убедитесь, что папки существуют или создайте их
    await create_directories_async([temp_path, price_path])
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        url_start = "https://www.xt.com/ru/futures/information/trade-rules"
        url_mark_price = "https://www.xt.com/fapi/market/v1/public/q/mark-price"
        url_index_price = "https://www.xt.com/fapi/market/v1/public/q/index-price"
        page_start = await context.new_page()
        page_mark_price = await context.new_page()
        page_index_price = await context.new_page()
        filename_mark_price = os.path.join(price_path, "mark_price.json")
        filename_index_price = os.path.join(price_path, "index_price.json")
        await asyncio.gather(
            fetch_and_save_json(page_mark_price, url_mark_price, filename_mark_price),
            fetch_and_save_json(
                page_index_price, url_index_price, filename_index_price
            ),
        )
        await page_start.goto(url_start, wait_until="load")
<<<<<<< HEAD
        await asyncio.sleep(5)

        pages = 0
        perpetual_pairs = set()
        # Содержит starts-wit часть из class
=======
        await asyncio.sleep(1)
        # json_text = await page_start.text_content(
        #     "pre"
        # )  # Получаем JSON в виде строки из элемента <pre>
        # json_data = json.loads(
        #     json_text
        # )  # Декодируем строку JSON в объект Python (словарь)
        # filename = "mark_price.json"
        # await save_json_data(json_data, filename)  # Сохраняем данные
        # button_next_selector = "xpath=//button[starts-with(@class, 'el-button el-button--default el-button--small is-plain scrollPagination_btn')]"

        # button_next = await page_start.wait_for_selector(
        #     button_next_selector, timeout=timeout
        # )
        pages = 0
        perpetual_pairs = set()
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
        button_selector = "xpath=//button[starts-with(@class, 'el-button el-button--default el-button--small is-plain scrollPagination_btn') and .//i[contains(@class, 'el-icon-arrow-right')]]"

        while True:
            # Проверяем наличие кнопки с disabled
            disabled_button = await page_start.query_selector(
                "button.el-button--disabled"
            )
            if disabled_button:
                print("Кнопка неактивна, останавливаемся.")
                break

            try:
<<<<<<< HEAD
                button_next = await page_start.query_selector(button_selector)

                if button_next is not None:

                    content = await page_start.content()
                    soup = BeautifulSoup(content, "lxml")

                    # Поиск всех div с текстом "Бессрочный "
                    for perpetual_div in soup.find_all("div", string="Бессрочный "):
                        parent_div = perpetual_div.parent
                        trade_pair_div = parent_div.find("div")
                        trade_pair = trade_pair_div.get_text(strip=True)
                        trade_pair_coints = convert_pair_name(trade_pair)
                        perpetual_pairs.add(trade_pair_coints)
=======
                # Ищем активную кнопку со стрелкой вправо
                button_next = await page_start.query_selector(button_selector)

                # button_next = await page.wait_for_selector(
                #     button_selector, timeout=5000  # 5000 мс таймаут
                # )

                if button_next is not None:

                    # Если такая кнопка найдена, кликаем по ней
                    # filename_html = os.path.join(path_coins, f"0{pages}.html")
                    content = await page_start.content()
                    soup = BeautifulSoup(content, "lxml")

                    # Пустой список для хранения торговых пар

                    # Поиск всех div с текстом "Бессрочный "
                    for perpetual_div in soup.find_all("div", string="Бессрочный "):
                        # Доступ к родительскому div, который содержит и торговую пару, и "Бессрочный "
                        parent_div = perpetual_div.parent
                        # В первом child div этого родителя должно быть название торговой пары
                        trade_pair_div = parent_div.find("div")
                        # Получаем текст из этого div, который и является торговой парой
                        trade_pair = trade_pair_div.get_text(strip=True)
                        # print(f"trade_pair {trade_pair}")
                        # Добавляем торговую пару в множество
                        trade_pair_coints = convert_pair_name(trade_pair)
                        if trade_pair_coints is None:
                            print(trade_pair)
                        perpetual_pairs.add(trade_pair_coints)
                    # async with aiofiles.open(filename_html, "w", encoding="utf-8") as f:
                    #     await f.write(content)
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
                    await button_next.click()
                    pages += 1
                else:
                    break  # Прерываем цикл, если кнопка не найдена
            except TimeoutError:
                print(
                    "Таймаут при поиске кнопки, возможно, нужно больше времени для загрузки или кнопки больше нет."
                )
                break

<<<<<<< HEAD
=======
            # Ожидаем, чтобы избежать слишком быстрой перегрузки страницы
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
            await page_start.wait_for_timeout(1000)

        await browser.close()
        # Сохраняем данные в CSV файл
        filename_trading_pairs = os.path.join(price_path, "trading_pairs.csv")
        await save_to_csv(perpetual_pairs, filename_trading_pairs)
        print(f"Данные успешно сохранены в файл {filename_trading_pairs}.")


<<<<<<< HEAD
# Сохраняем json с mark_price index_price
=======
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
async def fetch_and_save_json(page, url, filename):
    await page.goto(url)
    json_text = await page.text_content("pre")
    json_data = json.loads(json_text)
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
    print(f"Данные успешно сохранены в файл {filename}.")


<<<<<<< HEAD
# Читаем и возвращем список пар из csv
async def read_csv_file(price_path):

    filename_trading_pairs = os.path.join(price_path, "trading_pairs.csv")
    results = []
    async with aiofiles.open(
        filename_trading_pairs, mode="r", encoding="utf-8"
    ) as file:
        async for line in file:
            results.append(line.strip())
    return results


# Основная функция Ставка финансирования
async def funding_rate_record():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    price_path = os.path.join(temp_path, "price")
    trading_pairs = await read_csv_file(price_path)
    funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
=======
# Читаем и возвращем список пар
async def read_csv_file():
    filename = "trading_pairs.csv"
    results = []
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as file:
        async for line in file:
            # Предполагается, что каждая строка содержит одно значение без дополнительного разделителя
            results.append(line.strip())  # Удаляем пробельные символы и перевод строки
    return results


async def funding_rate_record():
    trading_pairs = await read_csv_file()
    timeout = 20000
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    path_coins = os.path.join(temp_path, "coins")
    funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
    # if os.path.exists(temp_path) and os.path.isdir(temp_path):
    #     shutil.rmtree(temp_path)
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    # Убедитесь, что папки существуют или создайте их
    await create_directories_async([temp_path, path_coins, funding_rate_record_path])

>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page_start = await context.new_page()
        for pair in trading_pairs:
            url_start = f"https://www.xt.com/fapi/market/v1/public/q/funding-rate-record?symbol={pair}&direction=NEXT&limit=1"
            filename = os.path.join(funding_rate_record_path, f"{pair}.json")
            await save_json_funding_rate_record(page_start, url_start, filename)
        await browser.close()


<<<<<<< HEAD
# сохраняем json Ставка финансирования
=======
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
async def save_json_funding_rate_record(page, url, filename):
    await page.goto(url, wait_until="load")

    json_text = await page.text_content("pre")
    json_data = json.loads(json_text)
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
<<<<<<< HEAD
=======
    print(f"Данные успешно сохранены в файл {filename}.")
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62


# Собраем всю информацию в один json
def get_xml():
    async def read_and_process_json(filename):
        """Асинхронно читает JSON файл и извлекает специфическое значение."""
        async with aiofiles.open(filename, "r", encoding="utf-8") as file:
            content = await file.read()
            data = json.loads(content)
            funding_rate = data["result"]["items"][0]["fundingRate"]
            return funding_rate

    async def read_csv_file(filename):
        """Асинхронно читает CSV файл и возвращает список торговых пар."""
        pairs = []
        async with aiofiles.open(filename, mode="r", encoding="utf-8") as file:
            async for line in file:
                pairs.append(line.strip())
        return pairs

    async def read_json_file(filename):
        """Асинхронно читает JSON файл и возвращает данные."""
        async with aiofiles.open(filename, mode="r", encoding="utf-8") as file:
            content = await file.read()
            return json.loads(content)

    async def find_prices(trading_pairs, index_data, mark_data):
        """Формирует список словарей с данными по ценам для каждой торговой пары."""
        results = []
        for pair in trading_pairs:
            index_price = next(
                (item["p"] for item in index_data["result"] if item["s"] == pair), None
            )
            mark_price = next(
                (item["p"] for item in mark_data["result"] if item["s"] == pair), None
            )
            results.append(
                {"pair": pair, "index_price": index_price, "mark_price": mark_price}
            )
        return results

    async def main():
        current_directory = os.getcwd()
        temp_path = os.path.join(current_directory, "temp")
        price_path = os.path.join(temp_path, "price")
        funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
        filename_mark_price = os.path.join(price_path, "mark_price.json")
        filename_index_price = os.path.join(price_path, "index_price.json")
        filename_trading_pairs = os.path.join(price_path, "trading_pairs.csv")

        trading_pairs = await read_csv_file(filename_trading_pairs)
        tasks = [
            read_and_process_json(
                os.path.join(funding_rate_record_path, f"{pair}.json")
            )
            for pair in trading_pairs
        ]

        funding_rates = await asyncio.gather(*tasks)
        index_data = await read_json_file(filename_index_price)
        mark_data = await read_json_file(filename_mark_price)
        prices_info = await find_prices(trading_pairs, index_data, mark_data)

        results = [
            {
                "pair": pair,
                "funding_rate": rate.replace(".", ","),
                "index_price": info["index_price"].replace(".", ","),
                "mark_price": info["mark_price"].replace(".", ","),
            }
            for pair, rate, info in zip(trading_pairs, funding_rates, prices_info)
        ]
<<<<<<< HEAD
        await write_xml_file(results, os.path.join(current_directory, "xt.xml"))
=======
        # await write_json_file(results, os.path.join(temp_path, "prices_info.json"))
        await write_xml_file(results, os.path.join(temp_path, "prices_info.xml"))

    async def write_json_file(data, filename):
        """Асинхронно записывает данные в JSON файл."""
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(json.dumps(data, ensure_ascii=False, indent=4))
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62

    def create_xml_element(data):
        rss = ET.Element("rss", xmlns="http://base.google.com/", version="2.0")
        for item in data:
            data_element = ET.SubElement(rss, "data")
            ET.SubElement(data_element, "name").text = (
                item["pair"].replace("_", " ").upper()
            )
            ET.SubElement(data_element, "index_price").text = str(item["index_price"])
            ET.SubElement(data_element, "marking_price").text = str(item["mark_price"])
            ET.SubElement(data_element, "financing_rate").text = item["funding_rate"]
        return rss

    def prettify_xml_element(element):
        rough_string = ET.tostring(element, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    async def write_xml_file(data, filename):
        element = create_xml_element(data)
        xml_string = prettify_xml_element(element)
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(xml_string)

    asyncio.run(main())


<<<<<<< HEAD
def save_to_xml_and_upload():
    key_id = "key_id"
    access_key = "access_key"
    # Создание клиента S3
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=key_id,
        aws_secret_access_key=access_key,
    )
    aws_s3_bucket = "dataxmlsparsers"  # Замените на имя вашего бакета
    current_directory = os.getcwd()
    filename_xml = os.path.join(current_directory, "xt.xml")
    with open(filename_xml, "rb") as file:
        s3_client.upload_fileobj(file, aws_s3_bucket, filename_xml)


if __name__ == "__main__":
    asyncio.run(run_get_all_couples())
    asyncio.run(funding_rate_record())
    get_xml()
    save_to_xml_and_upload()
=======
if __name__ == "__main__":
    # asyncio.run(run())
    # asyncio.run(run_get_all_couples())
    # asyncio.run(funding_rate_record())
    get_xml()
>>>>>>> f4a2e8aa8f71791dbd71d22aa827a1c7858b0f62
