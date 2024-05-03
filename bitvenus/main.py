# -*- mode: python ; coding: utf-8 -*-
from bs4 import BeautifulSoup
import asyncio
import aiofiles
import json
import os
import boto3
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


async def load_contracts(filename):
    """Асинхронно читает JSON файл и возвращает список контрактов."""
    async with aiofiles.open(filename, "r", encoding="utf-8") as file:
        content = await file.read()  # Чтение содержимого файла
        contracts = json.loads(content)  # Декодирование JSON
        return contracts


def convert_pair_name(pair_name):
    matches = re.match(r"([A-Z0-9]+)(USDT)$", pair_name)

    if matches:
        result = f"{matches.group(1).upper()} {matches.group(2).upper()}"
        return result
    return None


async def run_get_index_mark():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    price_path = os.path.join(temp_path, "price")
    funding_rate_record_path = os.path.join(temp_path, "funding_rate_record")
    await create_directories_async([temp_path, price_path, funding_rate_record_path])
    filename_all_contracts = os.path.join(price_path, "all_contracts.json")
    contracts = await load_contracts(filename_all_contracts)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        results = []
        for contract in contracts:
            url_start = f"https://futures.bitvenus.com/en-US/contract/{contract}"
            await page.goto(url_start, wait_until="load")
            await asyncio.sleep(1)
            # Находим элементы с помощью XPath и starts-with для класса
            new_price_element = await page.query_selector(
                "xpath=//div[starts-with(@class, 'newPrice_newPrice')]/span"
            )
            mark_price_element = await page.query_selector(
                "xpath=//div[starts-with(@class, 'newPrice_markPrice')]/span"
            )

            # Извлекаем текст из элементов, если они найдены
            new_price_text = (
                await new_price_element.inner_text()
                if new_price_element
                else "Not found"
            )
            mark_price_text = (
                await mark_price_element.inner_text()
                if mark_price_element
                else "Not found"
            )
            pair = convert_pair_name(contract)
            result = {
                "name": pair,
                "index_price": new_price_text,
                "marking_price": mark_price_text,
            }
            results.append(result)
        await browser.close()
        xml_element = create_xml(results)
        await write_xml_file(xml_element, "bitvenus.xml")
        save_to_xml_and_upload()


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
    filename_xml = os.path.join(current_directory, "bitvenus.xml")
    with open(filename_xml, "rb") as file:
        s3_client.upload_fileobj(file, aws_s3_bucket, filename_xml)


def create_xml(data):
    rss = ET.Element("rss", xmlns="http://base.google.com/", version="2.0")
    for item in data:
        data_element = ET.SubElement(rss, "data")
        ET.SubElement(data_element, "name").text = item.get("name", "")
        ET.SubElement(data_element, "index_price").text = item.get("index_price", "")
        ET.SubElement(data_element, "marking_price").text = item.get(
            "marking_price", ""
        )
        ET.SubElement(data_element, "financing_rate").text = item.get(
            "financing_rate", ""
        )
    return rss


def prettify_xml(element):
    """Возвращает красиво отформатированную XML строку."""
    rough_string = ET.tostring(element, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


async def write_xml_file(xml_element, filename):
    xml_string = prettify_xml(xml_element)
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(xml_string)


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
        url_all_contracts = "https://www.bitvenus.com/openapi/v1/contracts"
        page_all_contracts = await context.new_page()
        filename_all_contracts = os.path.join(price_path, "all_contracts.json")
        await asyncio.gather(
            fetch_and_save_json(
                page_all_contracts, url_all_contracts, filename_all_contracts
            ),
        )

        await browser.close()


# Сохраняем json с mark_price index_price
async def fetch_and_save_json(page, url, filename):
    await page.goto(url)
    json_text = await page.text_content("pre")
    json_data = json.loads(json_text)
    index_data = [item["index"] for item in json_data]
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(index_data, ensure_ascii=False, indent=4))
    print(f"Данные успешно сохранены в файл {filename}.")


async def periodic_task(interval):
    while True:
        await run_get_all_couples()  # Используйте await вместо asyncio.run()
        await run_get_index_mark()  # Используйте await вместо asyncio.run()
        print("Sleeping for", interval, "seconds")
        await asyncio.sleep(interval)  # Ожидание перед следующим запуском


async def main():
    await periodic_task(300)  # Запускать каждые 5 минут (300 секунд)


if __name__ == "__main__":
    asyncio.run(main())
