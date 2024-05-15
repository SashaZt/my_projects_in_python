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

# cookies = {
#     "sid": "iddx1xqd4e4iwzoyl1tbdkiu",
#     "uss": "4e3a002b-b10f-4f5a-83b1-2af3659855ff",
#     "__RequestVerificationToken": "-daFHhNiGck4PTcLDV3OeqSHdp36Up1xo4uy_xDhkrzHV0h7oFsimLxyPC5aT2rMEs3Ee0XR-aiH8jtmOYuH2VLuPRR9ohhmXAxDBwojQr01",
#     "_gcl_au": "1.1.1649775358.1715416861",
#     "_fbp": "fb.1.1715416861473.1152719356",
#     "_tt_enable_cookie": "1",
#     "_ttp": "vkj1jKVoQzkc1sxB-kJG93_LWyo",
#     "_gid": "GA1.2.1206992160.1715578557",
#     "_gat": "1",
#     "_ga_6352MSYKNX": "GS1.1.1715592801.4.1.1715592813.48.0.0",
#     "_dc_gtm_UA-38210263-4": "1",
#     "_gat_UA-238453145-1": "1",
#     "_ga_83HJKTVF69": "GS1.1.1715592801.3.1.1715592813.0.0.0",
#     "_ga": "GA1.1.833406689.1715416861",
#     "_ga_ECXG0392JW": "GS1.1.1715592801.4.1.1715592813.0.0.0",
#     "session_timer_104054": "1",
# }

# headers = {
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#     "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
#     "Cache-Control": "no-cache",
#     "Connection": "keep-alive",
#     # 'Cookie': 'sid=iddx1xqd4e4iwzoyl1tbdkiu; uss=4e3a002b-b10f-4f5a-83b1-2af3659855ff; __RequestVerificationToken=-daFHhNiGck4PTcLDV3OeqSHdp36Up1xo4uy_xDhkrzHV0h7oFsimLxyPC5aT2rMEs3Ee0XR-aiH8jtmOYuH2VLuPRR9ohhmXAxDBwojQr01; _gcl_au=1.1.1649775358.1715416861; _fbp=fb.1.1715416861473.1152719356; _tt_enable_cookie=1; _ttp=vkj1jKVoQzkc1sxB-kJG93_LWyo; _gid=GA1.2.1206992160.1715578557; _gat=1; _ga_6352MSYKNX=GS1.1.1715592801.4.1.1715592813.48.0.0; _dc_gtm_UA-38210263-4=1; _gat_UA-238453145-1=1; _ga_83HJKTVF69=GS1.1.1715592801.3.1.1715592813.0.0.0; _ga=GA1.1.833406689.1715416861; _ga_ECXG0392JW=GS1.1.1715592801.4.1.1715592813.0.0.0; session_timer_104054=1',
#     "DNT": "1",
#     "Pragma": "no-cache",
#     "Referer": "https://auto1.by/",
#     "Sec-Fetch-Dest": "document",
#     "Sec-Fetch-Mode": "navigate",
#     "Sec-Fetch-Site": "same-origin",
#     "Sec-Fetch-User": "?1",
#     "Upgrade-Insecure-Requests": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
#     "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
# }

# params = {
#     "pattern": "OC47",
# }

# response = requests.get(
#     "https://auto1.by/search", params=params, cookies=cookies, headers=headers
# )


# Рабочий!!!!!!!!!!!!
# filename = f"61745.html"
# # src = response.text
# # with open(filename, "w", encoding="utf-8") as file:
# #     file.write(src)
# with open(filename, encoding="utf-8") as file:
#     src = file.read()
# parser = HTMLParser(src)
# product_name_nodes = parser.css("h1.details_title > span.text-wrap")
# product_name = " ".join([node.text() for node in product_name_nodes])
# print(product_name)
# link_node = parser.css_first('link[itemprop="image"]')

# # Извлекаем значение атрибута href
# image_url = link_node.attrs.get("href")
# print(image_url)
# product_info_nodes = parser.css("#product-info > li")

# # Извлекаем текст всех найденных li элементов
# product_info = [node.text(strip=True) for node in product_info_nodes]

# for info in product_info:
#     print(info)
# date_node = parser.css_first(
#     "table > tbody > tr:nth-child(2) > td:nth-child(2) > span > span:nth-child(1)"
# )
# price_node = parser.css_first(
#     "table > tbody > tr:nth-child(2) > td:nth-child(5) > span"
# )

# # Извлекаем текстовые значения
# date = date_node.text(strip=True)
# price = price_node.text(strip=True)
# print(date)
# print(price)


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


async def main(url):
    timeout_selector = 90000
    values = await read_csv_values()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=timeout_selector)
        # Проверка наличия элемента с селектором #headerSearchSmall
        for v in values[1:2]:
            sku = v[0].replace(" ", "")
            brand = v[1]
            if await page.query_selector("#headerSearchSmall"):
                # Ввод значения "OC47"
                await page.fill("#headerSearchSmall", sku)
                await page.press("#headerSearchSmall", "Enter")
                # Ожидание появления первого элемента с классом .search-results-row
                await page.wait_for_selector(
                    ".search-results-row", timeout=timeout_selector
                )
                # Поиск всех элементов с классом .search-results-row
                search_results = await page.query_selector_all(".search-results-row")

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
                        print(f"Найдено значение href: {parent_a_href}")
            else:
                print("Элемент не найден.")


if __name__ == "__main__":
    url = "https://auto1.by/"
    asyncio.run(main(url))
