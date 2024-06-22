import glob
import pandas as pd
import asyncio
import aiofiles
from playwright.async_api import async_playwright
import os
from datetime import datetime
from selectolax.parser import HTMLParser
import re

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(all_hotels, exist_ok=True)
os.makedirs(hotel_path, exist_ok=True)


# Сохранение html файлов
async def save_page_content_html(page, file_path):
    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
    print(file_path)


# Главная функция
async def main():
    all_url = extract_urls_from_file()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        for url in all_url[2575:]:
            result_to_url = extract_code_and_id(url)
            save_path = os.path.join(all_hotels, f"{result_to_url}.html")
            if not os.path.exists(save_path):
                await page.goto(url)

                # Дождитесь загрузки страницы
                # await asyncio.sleep(1)
                # Дождитесь появления элемента
                feature_choices = None
                try:
                    await page.wait_for_selector(
                        "#config-data-sheet-container > div:nth-child(5) > div.config.feature-choices",
                        timeout=2000,
                    )
                    # После обновления страницы заново ищем элементы
                    feature_choices = await page.query_selector(
                        "#config-data-sheet-container > div:nth-child(5) > div.config.feature-choices"
                    )
                except:
                    await save_page_content_html(page, save_path)
                if feature_choices:
                    # Извлеките цвета и нажмите на каждый элемент, начиная со второго
                    num_features = len(
                        await feature_choices.query_selector_all("div.feature")
                    )
                    for index in range(1, num_features + 1):
                        feature_selector = f"#config-data-sheet-container > div:nth-child(5) > div.config.feature-choices > div:nth-child({index})"
                        feature = await page.query_selector(feature_selector)
                        color = await feature.inner_text()
                        color_clean = color.strip().replace(" ", "_")

                        if index == 1:
                            # Для первого элемента просто получаем цвет и сохраняем без клика
                            color_save_path = os.path.join(
                                all_hotels, f"{result_to_url}_{color_clean}.html"
                            )
                            await save_page_content_html(page, color_save_path)
                        else:
                            # Ожидание навигации после клика для остальных элементов
                            # async with page.expect_navigation():
                            await feature.click()
                            await asyncio.sleep(1)

                            # После обновления страницы заново ищем элементы
                            await page.wait_for_selector(
                                "#config-data-sheet-container > div:nth-child(5) > div.config.feature-choices"
                            )

                            # Получаем текущий элемент
                            feature = await page.query_selector(feature_selector)
                            color = await feature.inner_text()
                            color_clean = color.strip().replace(" ", "_")

                            color_save_path = os.path.join(
                                all_hotels, f"{result_to_url}_{color_clean}.html"
                            )
                            await save_page_content_html(page, color_save_path)
                else:
                    await save_page_content_html(page, save_path)

            else:
                print(f"файл {save_path}")
        await browser.close()


# def extract_product_ids(file_path):
#     product_ids = []
#     with open(file_path, "r") as file:
#         for line in file:
#             url = line.strip()
#             match = re.search(r"ObjectID=(\d+)", url)
#             if match:
#                 product_ids.append(match.group(1))
#     return product_ids


# Извлекаем url из файла
def extract_urls_from_file():
    file_path = "url_product.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    urls = [line.strip() for line in lines if line.strip()]
    return urls


# Регулярное выражение для извлечения кода и ID из URL
def extract_code_and_id(url):

    pattern = r"cod=([\w.-]+)&idmenu=(\d+)"
    match = re.search(pattern, url)

    if match:
        code = match.group(1).replace(".", "_").replace("-", "_")
        idmenu = match.group(2)
        result = f"{code}_{idmenu}"
        return result
    else:
        return None


def find_html_file(folder, result_to_url):
    search_pattern = os.path.join(folder, f"{result_to_url}.html")
    files = glob.glob(search_pattern)
    return files[0] if files else None


# def parsing_products():
#     all_urls = extract_urls_from_file()
#     # Обрабатывать каждый URL
#     all_datas = []
#     for url in all_urls:
#         result_to_url = extract_code_and_id(url)
#         if result_to_url:
#             html_file_path = find_html_file(all_hotels, result_to_url)
#             if html_file_path:
#                 with open(html_file_path, encoding="utf-8") as file:
#                     src = file.read()
#                 parser = HTMLParser(src)
#                 links = parser.css("a.brd")
#                 texts = [link.text() for link in links]
#                 bread_text = " > ".join(texts)
#                 img = parser.css_first("img.img-fluid.image-primary")
#                 if img:
#                     img_src = img.attributes.get("src")
#                 code_product_raw = parser.css_first(
#                     "#product-info-container > div:nth-child(2) > div:nth-child(2)"
#                 )
#                 code_product = code_product_raw.text(strip=True)
#                 description_product_raw = parser.css_first(
#                     "#product-info-container > div:nth-child(3) > div:nth-child(2)"
#                 )
#                 description_product = description_product_raw.text(strip=True)
#                 gtin_product_raw = parser.css_first(
#                     "#product-info-container > div:nth-child(10) > div:nth-child(2)"
#                 )
#                 gtin_product = gtin_product_raw.text(strip=True)
#                 datas = {
#                     "1 - URL": url,
#                     "2 - вхождение группы": bread_text,
#                     "3- Ссылка на ОСНОВНОЕ изображение": img_src,
#                     "4- Код продукта": code_product,
#                     "5- Описание продукта": description_product,
#                     "5- GTIN продукта": gtin_product,
#                 }
#                 all_datas.append(datas)
#     df = pd.DataFrame(all_datas)
#     df.to_csv("parsing_products.csv", index=False, encoding="utf-8", sep=";")

#     # all_url = extract_urls_from_file()
#     # for url in all_url:
#     #     result_to_url = extract_code_and_id(url)
#     #     # Указываем путь к папке с файлами
#     #     folder = os.path.join(all_hotels, "*.html")
#     #     files_html = glob.glob(folder)
#     # all_datas = []
#     # for item in files_html:
#     #     match = re.search(r"(\d+)\.html$", item)
#     #     if match:
#     #         number = match.group(1)
#     #         url = f"https://catalog.weidmueller.com/catalog/Start.do?localeId=ru&ObjectID={number}"
#     # with open(item, encoding="utf-8") as file:
#     #     src = file.read()
#     # parser = HTMLParser(src)
#     #     # Extract all the text from the element
#     #     breadcrumb_div = parser.css(".newBreadcrumb")
#     #     texts = [node.text(strip=True) for node in breadcrumb_div]
#     #     # Find the div element with the specified class
#     #     div_element = parser.css_first("div.zoomWrapper")

#     #     # Extract the 'data-zoom-image' attribute from the img tag inside this div element
#     #     img_src = None
#     #     if div_element:
#     #         img_tag = div_element.css_first("img")
#     #         if img_tag:
#     #             data_zoom_image = img_tag.attributes.get("data-zoom-image")
#     #             img_src = f"https://catalog.weidmueller.com{data_zoom_image}"
#     #         else:
#     #             img_src = "No img"
#     #     else:
#     #         img_src = "No img"
#     #         print("No div element with the specified class found.")
#     #     # Join the texts with commas
#     #     result = ", ".join(texts)
#     #     # Find the table rows
#     #     rows = parser.css("table.products.tabview.noTopMargin tr")

#     #     data_dict = {}
#     #     count = 0

#     #     # Iterate through each row and extract key-value pairs
#     #     for row in rows:
#     #         if count >= 5:
#     #             break
#     #         key_td = row.css_first("td.myListLable")
#     #         value_td = row.css_first("td.myListValue")

#     #         if key_td and value_td:
#     #             key = key_td.text(strip=True)
#     #             value = value_td.text(strip=True).replace(
#     #                 "\u00a0", " "
#     #             )  # Replace non-breaking spaces with regular spaces
#     #             data_dict[key] = value
#     #             count += 1

#     # datas = {
#     #     "1 - URL": url,
#     #     "2 - вхождение группы": result,
#     #     "3- Ссылка на ОСНОВНОЕ изображение": img_src,
#     # }
#     #     # Add the data_dict to datas
#     #     datas.update(data_dict)

#     #     all_datas.append(datas)

#     # # Optionally, save all_datas to a CSV file
#     # df = pd.DataFrame(all_datas)
#     # df.to_csv("parsing_products.csv", index=False, encoding="utf-8", sep=";")


def parsing_products():
    # Указываем путь к папке с файлами
    folder = os.path.join(all_hotels, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)
        links = parser.css("a.brd")
        texts = [link.text() for link in links]
        bread_text = " > ".join(texts)
        img = parser.css_first("img.img-fluid.image-primary")
        if img:
            img_src = img.attributes.get("src")
        code_product_raw = parser.css_first(
            "#product-info-container > div:nth-child(2) > div:nth-child(2)"
        )
        code_product = code_product_raw.text(strip=True)
        url = f"https://newelfin.com/en/product/?cod={code_product}"
        description_product_raw = parser.css_first(
            "#product-info-container > div:nth-child(3) > div:nth-child(2)"
        )
        description_product = description_product_raw.text(strip=True)
        gtin_product_raw = parser.css_first(
            "#product-info-container > div:nth-child(10) > div:nth-child(2)"
        )
        gtin_product = gtin_product_raw.text(strip=True)
        datas = {
            "1 - URL": url,
            "2 - вхождение группы": bread_text,
            "3- Ссылка на ОСНОВНОЕ изображение": img_src,
            "4- Код продукта": code_product,
            "5- Описание продукта": description_product,
            "5- GTIN продукта": gtin_product,
        }
        all_datas.append(datas)
    df = pd.DataFrame(all_datas)
    df.to_csv("parsing_products.csv", index=False, encoding="utf-8", sep=";")


if __name__ == "__main__":
    # asyncio.run(main())
    parsing_products()
