import glob
import requests
import pandas as pd
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selectolax.parser import HTMLParser
import asyncio
import aiofiles
from playwright.async_api import async_playwright
from databases import Database
from aiomysql import IntegrityError
import random
import time
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),  # Запись в файл
    ],
)


# Настройки базы данных
db_type = "mysql"
username = "python_mysql"
password = "python_mysql"
host = "localhost"  # или "164.92.240.39"
port = "3306"
db_name = "corn"
# db_name = "crypto"
database_url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"
database = Database(database_url)


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
page_path = os.path.join(temp_path, "page")
html_path = os.path.join(temp_path, "html")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(page_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)


def get_random_pause(time_pause):
    return random.uniform(time_pause, time_pause * 2)


# Пример асинхронной функции для сохранения содержимого страницы
async def save_page_content_html(page, file_path):
    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
    logging.info(f"Сохранено содержимое страницы в файл: {file_path}")


# Функция получения всех страниц
async def main():
    # Открываем соединение с базой данных
    await database.connect()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )
        for url in range(41, 221):
            all_datas = []
            url_start = f"https://agro-ukraine.com/ru/trade/r-5/p-{url}/"
            await page.goto(url_start, wait_until="load", timeout=60000)
            content = await page.content()
            parser = HTMLParser(content)
            # Находим элемент с id="items_list"
            items_list = parser.css_first("#items_list")
            if items_list:
                # Находим все div, у которых класс содержит i_l_i_c_mode3
                divs = items_list.css("div")
                for div in divs:
                    if "i_l_i_c_mode3" in div.attributes.get("class", ""):
                        div_id = div.attributes.get("id", "")
                        # Находим div с классом i_title внутри текущего div
                        title_div = div.css_first("div.i_title")
                        if title_div:
                            # Находим тег a внутри div с классом i_title
                            a_tag = title_div.css_first("a")
                            if a_tag:
                                href = a_tag.attributes.get("href", "")
                                data = {"id": div_id, "href": href}
                                all_datas.append(data)
                                # print(data)  # Для проверки, выводим полученные данные

                                # Вставляем данные в таблицу agro_ukraine_com_url
                                query = """
                                INSERT INTO agro_ukraine_com_url (url_id, url) VALUES (:url_id, :url)
                                """
                                # for data in all_datas:
            # Вставляем данные в таблицу agro_ukraine_com_url
            query = """
            INSERT INTO agro_ukraine_com_url (url_id, url) VALUES (:url_id, :url)
            """
            for data in all_datas:
                try:
                    await database.execute(
                        query, values={"url_id": data["id"], "url": data["href"]}
                    )
                except IntegrityError as e:
                    print(f"Duplicate entry for url_id {data['id']}: {e}")

            logging.info(f"Страница {url}")
            await asyncio.sleep(10)

    # Закрываем соединение с базой данных
    await database.disconnect()

    # save_path = os.path.join(page_path, f"{url_name}.html")
    # await asyncio.sleep(1)
    # await save_page_content_html(page, save_path)
    # await browser.close()


async def fetch_data():
    query = "SELECT url_id AS id, url AS href FROM agro_ukraine_com_url"
    await database.connect()
    rows = await database.fetch_all(query)
    await database.disconnect()

    data_list = []
    for row in rows:
        data = {"id": row["id"], "href": row["href"]}
        data_list.append(data)

    return data_list


# Функция получения всех страниц
async def get_html():
    # Открываем соединение с базой данных
    await database.connect()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )
        data = await fetch_data()
        for item in data:
            url = item["href"]
            name_file = f"{item['id']}.html"
            save_path = os.path.join(html_path, name_file)
            if not os.path.exists(save_path):

                await page.goto(url, wait_until="load", timeout=60000)
                # Ожидание появления элемента #ad_phone_view
                await page.wait_for_selector("#ad_phone_view")

                # Клик по элементу #ad_phone_view
                try:
                    await page.click("#ad_phone_view")
                except Exception as e:
                    logging.error(
                        f"Ошибка при клике по элементу для id {item['id']}: {e}"
                    )
                await asyncio.sleep(2)
                await save_page_content_html(page, save_path)
                random_pause = get_random_pause(5)
                time.sleep(random_pause)


async def parsing_page():

    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)
        title = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div.h1_desktop_c > div:nth-child(2) > span"
        ).text(strip=True)
        # Находим элемент div:nth-child(8) внутри div.i3_grid_main_c
        grid_main_c = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c"
        )
        div_8 = grid_main_c.css_first("div:nth-child(8)") if grid_main_c else None

        purpose_of_grain = None
        quantity = None

        if div_8:
            # Проверяем и извлекаем Назначение зерна
            div_1 = div_8.css_first("div:nth-child(1) > span.descr")
            if div_1 and "Назначение зерна:" in div_1.text():
                purpose_of_grain_text = div_1.next.text(strip=True).replace("\xa0", " ")
                purpose_of_grain = (
                    purpose_of_grain_text if purpose_of_grain_text else None
                )

            # Проверяем и извлекаем Количество
            div_2 = div_8.css_first("div:nth-child(2) > span.descr")
            if div_2 and "Количество:" in div_2.text():
                quantity_text = (
                    div_2.next.text(strip=True)
                    .replace("\xa0", " ")
                    .replace("тонн", " ")
                    .strip()
                )
                quantity = quantity_text if quantity_text else None
        price = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div:nth-child(3) > div > span.sprite_7_1.value > span > span:nth-child(1)"
        ).text(strip=True)
        # Находим элемент с регионом
        region_div = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div:nth-child(4)"
        )

        region = None
        city = None
        if region_div:
            # Извлекаем весь текст из region_div в одну строку
            region_text = region_div.text(separator=" ").strip()
            # Ищем в тексте значение региона
            if "Регион:" in region_text:
                region_start = region_text.index("Регион:") + len("Регион:")
                region_end = region_text.index("(", region_start)
                region = region_text[region_start:region_end].strip()
            # Ищем в тексте значение города
            if "(" in region_text and ")" in region_text:
                city_start = region_text.index("(") + 1
                city_end = region_text.index(")", city_start)
                city = region_text[city_start:city_end].strip()
        region = f"{region}, {city}"
        region = " ".join(region.replace("\n", " ").split()).strip()
        # Находим элемент с обновлением
        # Находим элементы с обновлением
        updated_div = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div:nth-child(5)"
        )

        formatted_date = None
        if updated_div:
            time_tag = updated_div.css_first("time")
            if time_tag:
                datetime_attr = time_tag.attributes.get("datetime")
                date, time = datetime_attr.split("T")

                # Преобразуем дату в формат dd.mm.yyyy
                formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime(
                    "%d.%m.%Y"
                )
        # Находим элемент с нужным классом
        description_div = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div.i_text.bw"
        )
        description_text = None
        if description_div:
            # Извлекаем весь текст и заменяем переносы строк пробелами
            description_text = (
                description_div.text(separator=" ")
                .strip()
                .replace("\n", " ")
                .replace("\r", " ")
            )
            # Удаляем множественные пробелы
            description_text = " ".join(description_text.split())
        # Извлекаем имя
        user_name_div = parser.css_first("div.sprite_box_7_1.ct_user_box_7_1")
        user_name = None
        if user_name_div:
            user_name = user_name_div.text(separator=" ").split("/")[0].strip()

        # Извлекаем номер телефона
        phone_div = parser.css_first("div.sprite_box_7_1.ct_phone_box_7_1")
        phone_numbers = []
        if phone_div:
            phone_links = phone_div.css("a[href^='tel:']")
            for phone_link in phone_links:
                phone_number = phone_link.attributes.get("href").replace("tel:", "")
                phone_numbers.append(phone_number)
        phone_numbers = "; ".join(phone_numbers)
        # Извлекаем ссылки Telegram, Viber, WhatsApp и сайт компании
        telegram_link = None
        telegram_td = parser.css_first("td > a[href^='https://t.me/']")
        if telegram_td:
            telegram_link = telegram_td.attributes.get("href")

        viber_link = None
        viber_td = parser.css_first("td > a[href^='https://viber.click/']")
        if viber_td:
            viber_link = viber_td.attributes.get("href")

        whatsapp_link = None
        whatsapp_td = parser.css_first("td > a[href^='https://wa.me/']")
        if whatsapp_td:
            whatsapp_link = whatsapp_td.attributes.get("href")

        company_link = None
        company_td = parser.css_first(
            "td > a[href^='https://agro-ukraine.com/ru/goto-url/']"
        )
        if company_td:
            company_link = company_td.text(strip=True)
        data = {
            "title": title,
            "purpose_of_grain": purpose_of_grain,
            "quantity": quantity,
            "price": price,
            "region": region,
            "updated_data": formatted_date,
            "updated_time": time,
            "description_text": description_text,
            "user_name": user_name,
            "phone_number": phone_numbers,
            "telegram": telegram_link,
            "viber": viber_link,
            "whatsapp": whatsapp_link,
            "company_link": company_link,
        }
        print(data)


#     # Находим элемент с id="items_list"
#     items_list = parser.css_first("#items_list")
#     if items_list:
#         # Находим все div, у которых класс содержит i_l_i_c_mode3
#         divs = items_list.css("div")
#         for div in divs:
#             if "i_l_i_c_mode3" in div.attributes.get("class", ""):
#                 div_id = div.attributes.get("id", "")
#                 # Находим div с классом i_title внутри текущего div
#                 title_div = div.css_first("div.i_title")
#                 if title_div:
#                     # Находим тег a внутри div с классом i_title
#                     a_tag = title_div.css_first("a")
#                     if a_tag:
#                         href = a_tag.attributes.get("href", "")
#                         data = {"id": div_id, "href": href}
#                         all_datas.append(data)
#                         print(data)  # Для проверки, выводим полученные данные

# # Открываем соединение с базой данных
# await database.connect()

# # Вставляем данные в таблицу agro_ukraine_com_url
# query = """
# INSERT INTO agro_ukraine_com_url (url_id, url) VALUES (:url_id, :url)
# """
# for data in all_datas:
#     await database.execute(
#         query, values={"url_id": data["id"], "url": data["href"]}
#     )

# # Закрываем соединение с базой данных
# await database.disconnect()


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(get_html())
    # asyncio.run(parsing_page())

    # category_group = str(input("Введите категорию:  "))
    # get_sell_min_price_path(category_group)
    # parsing_products_sell_min_price_path()
# asyncio.run(get_cookies())
# asyncio.run(get_sell_min_price_path())
#
# asyncio.run(get_price())


# #     parsing_products_price()
# while True:
#     print(
#         "Введите 1 для получения куки"
#         "\nВведите 2 для запуска первого скрипта"
#         "\nВведите 3 для запуска второго скрипта"
#         "\nВведите 0 для закрытия программы"
#     )
#     user_input = int(input("Выберите действие: "))
#     if user_input == 1:
#         asyncio.run(get_cookies())
#     elif user_input == 2:
#         # url = str((input("Вставьте ссылку на срипт 1: ")))
#         # asyncio.run(get_sell_min_price_path(url))
#         slices = 1
#         parsing_products_sell_min_price_path()
#     elif user_input == 3:
#         asyncio.run(get_price())
#         parsing_products_price()
