import requests
from selectolax.parser import HTMLParser
import asyncio
import json
import aiofiles
from playwright.async_api import async_playwright
import time
import os
from datetime import datetime
import csv

"""
await page.goto(url, wait_until="domcontentloaded", timeout=60000)
load: Ожидание завершения события загрузки страницы. Это событие срабатывает, когда вся страница и все ее ресурсы полностью загружены.
domcontentloaded: Ожидание завершения события DOMContentLoaded. Это событие срабатывает, когда начальная структура документа была полностью загружена и обработана, без ожидания завершения загрузки стилей, изображений и подрамок.
networkidle: Ожидание, пока сеть станет "пустой" (idle), то есть когда не будет более 0 сетевых соединений на протяжении как минимум 500 мс. Это полезно для ожидания завершения всех сетевых запросов.
commit: Ожидание подтверждения навигации в контексте текущей страницы. Это самое раннее событие, которое может сработать при переходе на новую страницу.
"""


def parsing():
    filename = f"61745.html"
    # src = response.text
    # with open(filename, "w", encoding="utf-8") as file:
    #     file.write(src)
    with open(filename, encoding="utf-8") as file:
        src = file.read()
    parser = HTMLParser(src)
    product_name_nodes = parser.css("h1.details_title > span.text-wrap")
    product_name = " ".join([node.text() for node in product_name_nodes])
    link_node = parser.css_first('meta[property="og:image"]')

    # Извлекаем значение атрибута href
    image_url = link_node.attrs.get("content")
    category_node = parser.css_first('li[itemprop="category"]')
    category = category_node.text(strip=True)
    # product_info_nodes = parser.css("#product-info > li")

    # Извлекаем текст всех найденных li элементов
    # product_info = [node.text(strip=True) for node in product_info_nodes]

    # for info in product_info:
    #     print(info)
    # date_node = parser.css_first(
    #     "table > tbody > tr:nth-child(2) > td:nth-child(2) > span > span:nth-child(1)"
    # )
    price_node = parser.css_first(
        "table > tbody > tr:nth-child(2) > td:nth-child(5) > span"
    )
    in_stock_node = parser.css_first(
        "table > tbody > tr:nth-child(2) > td:nth-child(2) > span > span:nth-child(1)"
    )

    # Извлекаем текстовые значения
    # date = date_node.text(strip=True)
    price = price_node.text(strip=True)
    in_stock = in_stock_node.text(strip=True)
    # print(date)
    values = {
        "product_name": product_name,
        "image_url": image_url,
        "category": category,
        "price": price,
        "in_stock": in_stock,
    }
    print(values)


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html_path")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)


async def read_csv_values():
    current_directory = os.getcwd()
    filename_csv = os.path.join(current_directory, "list.csv")
    values = []
    async with aiofiles.open(filename_csv, mode="r", encoding="utf-16") as file:
        # Read the entire file content
        content = await file.read()
        # Use csv.reader to parse the content
        reader = csv.reader(content.splitlines(), delimiter="\t")
        for row in reader:
            values.append(row)
    return values


async def read_all_href():
    async with aiofiles.open("all_href_sku.json", "r", encoding="utf-8") as f:
        contents = await f.read()
        all_href = json.loads(contents)
    return all_href


async def get_all_href_sku(url):
    timeout_selector = 10000
    values = await read_csv_values()
    all_href = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Проверка наличия элемента с селектором #headerSearchSmall
        for v in values[1:10]:
            sku = v[0].replace(" ", "")
            brand = v[1]
            if await page.query_selector("#headerSearchSmall"):
                # Ввод значения "OC47"
                await page.fill("#headerSearchSmall", sku)
                await page.press("#headerSearchSmall", "Enter")
                # Ожидание появления первого элемента с классом .search-results-row
                try:
                    await page.wait_for_selector("#oemP", timeout=timeout_selector)
                except:
                    continue
                # Поиск всех элементов #oemP > div
                search_results = await page.query_selector_all("#oemP > div")

                for result in search_results:
                    # Проверка наличия элемента span с нужным data-brand
                    brand_span = await result.query_selector(
                        f'span[data-brand="{brand}"]'
                    )
                    if brand_span:
                        # Получение родительского элемента a и значения href с помощью evaluate
                        parent_a_href = await brand_span.evaluate(
                            '(element) => element.closest("a").href'
                        )
                        all_href.append(parent_a_href)
                        # print(f"Найдено значение href: {parent_a_href}")
                    else:
                        continue

            else:
                print("Элемент не найден.")
    # Сохранение результатов в JSON файл
    with open("all_href_sku.json", "w", encoding="utf-8") as f:
        json.dump(all_href, f, ensure_ascii=False, indent=4)


async def get_html_files():
    timeout_selector = 10000
    values = await read_all_href()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Проверка наличия элемента с селектором #headerSearchSmall
        for v in values[:1]:
            await page.goto(v, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector(
                    "#CloseStoreSelector", timeout=timeout_selector
                )
            except:
                continue
            page_content = await page.content()
            parser = HTMLParser(page_content)
            product_name_nodes = parser.css("h1.details_title > span.text-wrap")
            product_name = " ".join([node.text() for node in product_name_nodes])
            print(product_name)

            link_node = parser.css_first('meta[property="og:image"]')

            # Извлекаем значение атрибута href
            image_url = link_node.attrs.get("content")
            print(image_url)
            product_info_nodes = parser.css("#product-info > li")

            # Извлекаем текст всех найденных li элементов
            product_info = [node.text(strip=True) for node in product_info_nodes]

            for info in product_info:
                print(info)
            date_node = parser.css_first(
                "table > tbody > tr:nth-child(2) > td:nth-child(2) > span > span:nth-child(1)"
            )
            price_node = parser.css_first(
                "table > tbody > tr:nth-child(2) > td:nth-child(5) > span"
            )

            # Извлекаем текстовые значения
            date = date_node.text(strip=True)
            price = price_node.text(strip=True)
            print(date)
            print(price)


if __name__ == "__main__":
    parsing()
    url = "https://auto1.by/"
    # asyncio.run(get_all_href_sku(url))
    # asyncio.run(get_html_files())
