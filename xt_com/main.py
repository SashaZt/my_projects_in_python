# -*- mode: python ; coding: utf-8 -*-
from bs4 import BeautifulSoup
import asyncio
import aiofiles
import json
import os
import boto3
import sys
from glob import glob
import asyncio
from time import sleep
from playwright.async_api import async_playwright
import re
import json
import os
from asyncio import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom


# Создаем директории временные
async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


# Записываем пары в новую строку csv
async def save_to_csv(perpetual_pairs, filename):
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as file:
        for pair in perpetual_pairs:
            await file.write(pair + "\n")  # Добавляем символ новой строки


# Разделяем пары на BTCUSDT на btc_usdt для дальнейших запросов
def convert_pair_name(pair_name):
    matches = re.match(r"([A-Z0-9]+)(USDT)$", pair_name)

    if matches:
        result = f"{matches.group(1).lower()}_{matches.group(2).lower()}"
        return result
    return None


# Собираем пары, маркер цены и индекс цены
async def run_get_all_couples():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    price_path = os.path.join(temp_path, "price")
    funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
    await create_directories_async([temp_path, price_path, funding_rate_record_path])

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
        await asyncio.sleep(5)

        pages = 0
        perpetual_pairs = set()
        # Содержит starts-wit часть из class
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
                    await button_next.click()
                    pages += 1
                else:
                    break  # Прерываем цикл, если кнопка не найдена
            except TimeoutError:
                print(
                    "Таймаут при поиске кнопки, возможно, нужно больше времени для загрузки или кнопки больше нет."
                )
                break

            await page_start.wait_for_timeout(1000)

        await browser.close()
        # Сохраняем данные в CSV файл
        filename_trading_pairs = os.path.join(price_path, "trading_pairs.csv")
        await save_to_csv(perpetual_pairs, filename_trading_pairs)
        print(f"Данные успешно сохранены в файл {filename_trading_pairs}.")


# Сохраняем json с mark_price index_price
async def fetch_and_save_json(page, url, filename):
    await page.goto(url)
    json_text = await page.text_content("pre")
    json_data = json.loads(json_text)
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
    print(f"Данные успешно сохранены в файл {filename}.")


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
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page_start = await context.new_page()
        for pair in trading_pairs:
            url_start = f"https://www.xt.com/fapi/market/v1/public/q/funding-rate-record?symbol={pair}&direction=NEXT&limit=1"
            filename = os.path.join(funding_rate_record_path, f"{pair}.json")
            await save_json_funding_rate_record(page_start, url_start, filename)
        await browser.close()


# сохраняем json Ставка финансирования
async def save_json_funding_rate_record(page, url, filename):
    await page.goto(url, wait_until="load")

    json_text = await page.text_content("pre")
    json_data = json.loads(json_text)
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))


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
        await write_xml_file(results, os.path.join(current_directory, "xt.xml"))

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


async def periodic_task(interval):
    while True:
        await run_get_all_couples()
        await funding_rate_record()
        get_xml()  # Предполагается, что это синхронная функция
        save_to_xml_and_upload()  # Предполагается, что это синхронная функция
        print("Sleeping for", interval, "seconds")
        await asyncio.sleep(interval)  # Ожидание перед следующим запуском

async def main():
    await periodic_task(300)  # Запускать каждые 5 минут (300 секунд)

if __name__ == "__main__":
    asyncio.run(main())
