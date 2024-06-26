import glob
import pandas as pd
import asyncio
import aiofiles
from playwright.async_api import async_playwright
import os
from datetime import datetime
from selectolax.parser import HTMLParser
import re
import json
import requests

cookies = {
    "PHPSESSID": "037d6a52e601e895961d319452014b01",
    "_ms": "28ca1f18-a408-4eb1-bdd5-5edffce28982",
    "lang": "ua",
    "biatv-cookie": "{%22firstVisitAt%22:1719206878%2C%22visitsCount%22:3%2C%22currentVisitStartedAt%22:1719310027%2C%22currentVisitLandingPage%22:%22https://artmobile.com.ua/zapchastini-displeyi%22%2C%22currentVisitUpdatedAt%22:1719310030%2C%22currentVisitOpenPages%22:2%2C%22campaignTime%22:1719226494%2C%22campaignCount%22:2%2C%22utmDataCurrent%22:{%22utm_source%22:%22freelancehunt.com%22%2C%22utm_medium%22:%22referral%22%2C%22utm_campaign%22:%22(referral)%22%2C%22utm_content%22:%22/%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1719226494}%2C%22utmDataFirst%22:{%22utm_source%22:%22freelancehunt.com%22%2C%22utm_medium%22:%22referral%22%2C%22utm_campaign%22:%22(referral)%22%2C%22utm_content%22:%22/%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1719206878}}",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'PHPSESSID=037d6a52e601e895961d319452014b01; _ms=28ca1f18-a408-4eb1-bdd5-5edffce28982; lang=ua; biatv-cookie={%22firstVisitAt%22:1719206878%2C%22visitsCount%22:3%2C%22currentVisitStartedAt%22:1719310027%2C%22currentVisitLandingPage%22:%22https://artmobile.com.ua/zapchastini-displeyi%22%2C%22currentVisitUpdatedAt%22:1719310030%2C%22currentVisitOpenPages%22:2%2C%22campaignTime%22:1719226494%2C%22campaignCount%22:2%2C%22utmDataCurrent%22:{%22utm_source%22:%22freelancehunt.com%22%2C%22utm_medium%22:%22referral%22%2C%22utm_campaign%22:%22(referral)%22%2C%22utm_content%22:%22/%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1719226494}%2C%22utmDataFirst%22:{%22utm_source%22:%22freelancehunt.com%22%2C%22utm_medium%22:%22referral%22%2C%22utm_campaign%22:%22(referral)%22%2C%22utm_content%22:%22/%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1719206878}}',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")
img_path = os.path.join(temp_path, "img")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(all_hotels, exist_ok=True)
os.makedirs(hotel_path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)


# Сохранение html файлов
async def save_page_content_html(page, file_path):
    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
    print(file_path)
    await asyncio.sleep(1)


# Главная функция
async def main():
    # all_url = extract_urls_from_file()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        for pg in range(1, 176):
            url = "https://artmobile.com.ua/zapchastini-displeyi"
            # result_to_url = extract_code_and_id(url)
            save_path = os.path.join(all_hotels, f"0{pg}.html")
            if pg != 1:
                await page.goto(f"{url}?page={pg}")
            else:
                await page.goto(url)
            await save_page_content_html(page, save_path)
        await browser.close()


def parsing_htnl_url():
    folder = os.path.join(all_hotels, "*.html")

    files_html = glob.glob(folder)
    hrefs = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)
        # Находим все div с классом product-title
        product_divs = parser.css("div.product-title")

        # Извлекаем href из каждого элемента a внутри найденных div

        for div in product_divs:
            a_tag = div.css_first("a")
            if a_tag:
                href = a_tag.attributes.get("href")
                if href:
                    hrefs.append(href)
    # Сохранение извлеченных ссылок в текстовый файл
    with open("extracted_links.txt", "w", encoding="utf-8") as output_file:
        for href in hrefs:
            output_file.write(href + "\n")


# Извлекаем url из файла
def extract_urls_from_file():
    file_path = "extracted_links.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    urls = [line.strip() for line in lines if line.strip()]
    return urls


async def get_products():
    all_url = extract_urls_from_file()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        count = 0
        for url in all_url:
            save_path = os.path.join(hotel_path, f"0{count}.html")
            await page.goto(url)
            await save_page_content_html(page, save_path)
            count += 1


def parsing_product():
    folder = os.path.join(hotel_path, "*.html")

    files_html = glob.glob(folder)
    all_datas = []
    for item_html in files_html[:5]:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)

        # Извлекаем breadcrumb
        breadcrumb_ol = parser.css_first("ol.breadcrumb")
        breadcrumb = ""
        if breadcrumb_ol:
            breadcrumb_items = breadcrumb_ol.css("li.breadcrumb-item")
            breadcrumb_texts = []
            for item in breadcrumb_items:
                a_tag = item.css_first("a")
                if a_tag:
                    breadcrumb_texts.append(a_tag.text(strip=True))
                else:
                    breadcrumb_texts.append(item.text(strip=True))
            # breadcrumb = " / ".join(breadcrumb_texts[-2:-1])
            breadcrumb = "".join(breadcrumb_texts[-2:-1])

        # Извлекаем цену
        price_base = None
        pattern = re.compile(r"^product-card-\d+$")
        matching_elements = [
            node
            for node in parser.css("*")
            if "id" in node.attributes and pattern.match(node.attributes["id"])
        ]

        for element in matching_elements:
            price_base_raw = element.css_first(
                "div.product-page__right > div > div.card-buy-block.in-stock > div.block-section.block-price > div > div.price-base"
            )
            if price_base_raw:
                price_base = price_base_raw.text(strip=True)
                price_base = price_base.replace("$", "")
                break

        # Находим все элементы script с типом application/ld+json
        script_tags = parser.css('script[type="application/ld+json"]')
        json_data = None
        if len(script_tags) >= 2:
            json_content = script_tags[1].text(strip=True)
            try:
                json_data = json.loads(json_content)
            except json.JSONDecodeError:
                continue

        if json_data:
            description = json_data.get("description", "")
            sku = json_data.get("sku", "")

            # image = ", ".join(json_data.get("image", []))
            url = json_data.get("offers", {}).get("url", "")
            url = url.replace("https://artmobile.com.ua/", "")
            title_product = json_data.get("name", "")

            # Находим все элементы characteristics-item
            characteristics_items = parser.css("div.characteristics-item")

            # Извлекаем данные и формируем JSON объект
            characteristics = {}
            for item in characteristics_items:
                title = item.css_first("div.characteristics-title").text(strip=True)
                value_divs = item.css("div.characteristics-value div")
                values = [div.text(strip=True) for div in value_divs]
                characteristics[title] = ", ".join(values)
            # Находим все элементы a с классом product-gallery-item
            gallery_items = parser.css("a.product-gallery-item")

            # Извлекаем href из каждого найденного элемента
            hrefs = [
                item.attributes.get("href")
                for item in gallery_items
                if item.attributes.get("href")
            ]

            image_list = []
            # Скачиваем и сохраняем файлы
            for index, href in enumerate(hrefs):
                response = requests.get(href, cookies=cookies, headers=headers)
                file_name = f"{sku}_{index + 1}.jpg"
                image_list.append(file_name)

                file_path = os.path.join(img_path, file_name)
                if not os.path.exists(file_path):
                    if response.status_code == 200:
                        with open(file_path, "wb") as file:
                            file.write(response.content)
                        print(f"Файл сохранен: {file_path}")
                    else:
                        print(response.status_code)
                else:
                    print(f"Не удалось скачать файл: {href}")
            image_list = ", ".join(image_list)
            in_stock = 1
            data_product = {
                "Категория": breadcrumb,
                "Товар": title_product,
                "Цена": price_base,
                "Адрес": url,
                "Артикул": sku,
                "Видим": in_stock,
                "Заголовок страницы": title_product,
                "Описание страницы": title_product,
                "Описание": description,
                "Изображения": image_list,
                "Рекомендуемый": 0,
                "Бренд": "",
                "Вариант": "",
                "Старая цена": "",
                "Склад": "",
                "Аннотация": "",
                **characteristics,
            }
            all_datas.append(data_product)

    df = pd.DataFrame(all_datas)
    df.to_csv("parsing_products.csv", index=False, encoding="utf-8", sep=";")


if __name__ == "__main__":
    # asyncio.run(main())
    # parsing_htnl_url()
    # asyncio.run(get_products())
    parsing_product()
