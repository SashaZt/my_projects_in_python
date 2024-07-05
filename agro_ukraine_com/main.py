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
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
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


# Функция для подключения к Google Sheets
def get_google():
    current_directory = os.getcwd()
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_file = os.path.join(
        current_directory, "calm-analog-428315-h9-7e51eabd0ab7.json"
    )
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)
    return client


# Колонки таблицы
column_names = [
    "title",
    "purpose_of_grain",
    "quantity",
    "price",
    "region_text",
    "updated_date",
    "updated_time",
    "description_text",
    "user_name",
    "phone_numbers",
    "telegram_link",
    "viber_link",
    "whatsapp_link",
    "company_link",
]


# Функция для выборки данных из базы данных
async def fetch_data_from_db():
    query = "SELECT * FROM agro_ukraine_com_ua_ads"
    await database.connect()
    rows = await database.fetch_all(query)
    await database.disconnect()

    data_list = []
    for row in rows:
        data = {
            "Название": row["title"],
            "Товар": row["purpose_of_grain"],
            "Количество": row["quantity"],
            "Прайс": row["price"],
            "Регион": row["region_text"],
            "Дата резмещения": (
                row["updated_date"].strftime("%Y-%m-%d")
                if row["updated_date"]
                else None
            ),
            "Время размещения": str(row["updated_time"]),
            "Текст": row["description_text"],
            "Контактная особа": row["user_name"],
            "Номер телефона": row["phone_numbers"],
            "Telegram": row["telegram_link"],
            "Viber": row["viber_link"],
            "Whatsapp": row["whatsapp_link"],
            "Company_link": row["company_link"],
        }
        data_list.append(data)

    # Преобразование данных в DataFrame
    df = pd.DataFrame(data_list)

    return df


# Функция для загрузки данных в Google Sheets
async def upload_data_to_google_sheets():
    df = await fetch_data_from_db()
    client = get_google()
    spreadsheet_id = "1FP344GQ9q4w3zprtyXDHCsTBbzDVkUaOt5a0IJ5fFHU"
    sheet_name = "agro_ukraine"

    # Открытие Google Sheet
    sheet = client.open_by_key(spreadsheet_id)

    # Получение листа
    try:
        worksheet = sheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Если лист не найден, создаем новый
        worksheet = sheet.add_worksheet(title=sheet_name, rows="1000", cols="20")

    # Очистка существующих данных
    worksheet.clear()

    # Подготовка данных для загрузки
    data = [df.columns.values.tolist()] + df.values.tolist()

    # Загрузка данных в Google Sheet
    worksheet.update(data)


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

                                # # Вставляем данные в таблицу agro_ukraine_com_url
                                # query = """
                                # INSERT INTO agro_ukraine_com_url (url_id, url) VALUES (:url_id, :url)
                                # """
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
async def update_ads():
    data_bd = await fetch_data()
    proxies = load_proxies()
    proxy_gen = proxy_generator(proxies)
    # Открываем соединение с базой данных
    await database.connect()

    async with async_playwright() as playwright:
        proxy = next(proxy_gen)
        proxy_server = {
            "server": f"http://{proxy[0]}:{proxy[1]}",
            "username": proxy[2],
            "password": proxy[3],
        }
        browser = await playwright.chromium.launch(headless=False, proxy=proxy_server)
        context = await browser.new_context()
        page = await context.new_page()
        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )

        all_datas = []
        has_new_data = True
        # Максимальное количество страниц для проверки
        max_pages_to_check = 10

        try:
            for page_number in range(1, max_pages_to_check + 1):
                url_start = f"https://agro-ukraine.com/ru/trade/r-5/p-{page_number}/"
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

            # Проверка на совпадения с данными из базы данных
            if any(data in data_bd for data in all_datas):
                has_new_data = False

        finally:
            # Закрываем контекст и браузер
            try:
                await context.close()
            except Exception as e:
                print(f"Error closing context: {e}")

            try:
                await browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")

    # Сохранение новых данных если присутсвуют в файл new_url.json
    if has_new_data:
        with open("new_url.json", "w", encoding="utf-8") as f:
            json.dump(all_datas, f, ensure_ascii=False, indent=4)
        print(f"Файл сохранил new_url.json")

    # Закрываем соединение с базой данных
    await database.disconnect()


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Функция получения всех страниц
async def get_html():
    # Открываем соединение с базой данных
    # await database.connect()
    data = await fetch_data()
    # with open("proxi.json", "r") as f:
    #     proxies = json.load(f)
    proxies = load_proxies()
    proxy_gen = proxy_generator(proxies)
    count = 0
    async with async_playwright() as playwright:
        proxy = next(proxy_gen)
        proxy_server = {
            "server": f"http://{proxy[0]}:{proxy[1]}",
            "username": proxy[2],
            "password": proxy[3],
        }
        browser = await playwright.chromium.launch(headless=False, proxy=proxy_server)
        context = await browser.new_context()
        page = await context.new_page()
        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )

        for item in data:
            url = item["href"]
            name_file = f"{item['id']}.html"
            save_path = os.path.join(html_path, name_file)
            if not os.path.exists(save_path):
                try:
                    await page.goto(url, wait_until="load", timeout=60000)
                    # Ожидание появления элемента #ad_phone_view
                    try:
                        await page.wait_for_selector("#ad_phone_view", timeout=1000)
                    except:
                        await save_page_content_html(page, save_path)
                        continue
                    # Клик по элементу #ad_phone_view
                    try:
                        await page.click("#ad_phone_view")
                    except Exception as e:
                        logging.error(
                            f"Ошибка при клике по элементу для id {item['id']}: {e}"
                        )
                    await asyncio.sleep(1)
                    await save_page_content_html(page, save_path)
                except Exception as e:
                    logging.error(f"Ошибка при обработке URL {url}: {e}")

                count += 1
                if count == 50:
                    await context.close()
                    await browser.close()
                    proxy = next(proxy_gen)
                    proxy_server = {
                        "server": f"http://{proxy[0]}:{proxy[1]}",
                        "username": proxy[2],
                        "password": proxy[3],
                    }
                    browser = await playwright.chromium.launch(
                        headless=False, proxy=proxy_server
                    )
                    context = await browser.new_context()
                    page = await context.new_page()
                    # Отключение загрузки изображений
                    await context.route(
                        "**/*",
                        lambda route, request: (
                            route.continue_()
                            if request.resource_type != "image"
                            else route.abort()
                        ),
                    )
                    count = 0  # Сброс счетчика после смены прокси

        await context.close()
        await browser.close()

    return None


# Функция для извлечения данных по ключевым словам


async def parsing_page():
    await database.connect()
    folder = os.path.join(html_path, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item_html in files_html:
        with open(item_html, encoding="utf-8") as file:
            src = file.read()
        id_add = item_html.split("\\")[-1].replace(".html", "")
        parser = HTMLParser(src)
        # Пытаемся найти элемент по первому пути
        title_element = parser.css_first(
            "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div.h1_desktop_c > div:nth-child(2) > span"
        )

        # Если элемент не найден, пробуем второй путь
        if title_element:
            title = title_element.text(strip=True)
        else:
            h1_element = parser.css_first(
                "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div.h1_desktop_c > div:nth-child(2) > h1"
            )
            if h1_element:
                title = h1_element.text(strip=True)
            else:
                title = None
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

        try:
            price_row = parser.css_first(
                "body > div.container > div.item_container > div.i3_grid_c > div.i3_grid_main_c > div:nth-child(3) > div > span.sprite_7_1.value > span > span:nth-child(1)"
            )
            price = price_row.text(strip=True)
        except:
            price = None

        # # Извлекаем дату и время обновления
        # updated_date, updated_time = None, None
        # try:
        #     result = extract_info_by_keyword("Обновлено:")
        #     if result:
        #         updated_date, updated_time = result
        # except Exception as e:
        #     print(item_html)
        #     break
        def extract_info_by_keyword(keyword):
            elements = parser.css("span.descr")
            for element in elements:
                if keyword in element.text():
                    parent_div = element.parent
                    if keyword == "Обновлено:":
                        time_tag = parent_div.css_first("time")
                        if time_tag:
                            datetime_attr = time_tag.attributes.get("datetime")
                            if datetime_attr:
                                return datetime_attr
                    else:
                        return (
                            parent_div.text(strip=True)
                            .replace("\n", " ")
                            .replace("\r", " ")
                            .replace("\xa0", " ")
                        )

        # Извлекаем данные по ключевым словам
        region_text = extract_info_by_keyword("Регион:")
        if region_text is not None:
            region_text = region_text.replace("Регион:", "").strip()
        updated_datetime = extract_info_by_keyword("Обновлено:")
        try:
            date, updated_time = updated_datetime.split("T")
            updated_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except:
            updated_date = None
            updated_time = None

        purpose_of_grain = extract_info_by_keyword("Назначение зерна:")
        if purpose_of_grain is not None:
            purpose_of_grain = purpose_of_grain.replace("Назначение зерна:", "").strip()
        quantity = extract_info_by_keyword("Количество:")
        if quantity is not None:
            quantity = quantity.replace("Количество:", "").strip()

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
            "id_add": id_add,
            "title": title,
            "purpose_of_grain": purpose_of_grain,
            "quantity": quantity,
            "price": price,
            "region": region_text,
            "updated_date": convert_date_format(updated_date),
            "updated_time": updated_time,
            "description_text": description_text,
            "user_name": user_name,
            "phone_numbers": phone_numbers,
            "telegram_link": telegram_link,
            "viber_link": viber_link,
            "whatsapp_link": whatsapp_link,
            "company_link": company_link,
        }
        all_datas.append(data)
    # await load_data_to_db(database, all_datas)
    await database.disconnect()
    print(len(all_datas))
    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Запись DataFrame в Excel
    output_file = "output_sell_min_price.xlsx"
    df.to_excel(output_file, index=False)


async def load_data_to_db(database, data):
    query = """
INSERT INTO agro_ukraine_com_ua_ads (
    id_add, title, purpose_of_grain, quantity, price,
    region_text, updated_date, updated_time, description_text,
    user_name, phone_numbers, telegram_link, viber_link,
    whatsapp_link, company_link
) VALUES (
    :id_add, :title, :purpose_of_grain, :quantity, :price,
    :region, :updated_date, :updated_time, :description_text,
    :user_name, :phone_numbers, :telegram_link, :viber_link,
    :whatsapp_link, :company_link
)
"""
    await database.execute_many(query, data)


# Преобразование формата даты
def convert_date_format(date_str):
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        # Обработка неправильного формата даты
        print(f"Incorrect date format: {date_str}")
        return None


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(update_ads())
    # asyncio.run(get_html())
    # asyncio.run(parsing_page())
    # asyncio.run(upload_data_to_google_sheets())

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
