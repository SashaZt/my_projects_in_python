from curl_cffi.requests import AsyncSession
import glob
import pandas as pd
import json
import os
import re
from datetime import datetime, timedelta
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


# Функция для выборки данных из базы данных
async def fetch_data_from_db():
    query = "SELECT * FROM agrotender_com_ua_ads"
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
            # "Время размещения": str(row["updated_time"]),
            "Текст": row["description_text"],
            "Контактная особа": row["user_name"],
            "Номер телефона": row["phone_numbers"],
            # "Telegram": row["telegram_link"],
            # "Viber": row["viber_link"],
            # "Whatsapp": row["whatsapp_link"],
            # "Company_link": row["company_link"],
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
    # указываем имя листа
    sheet_name = "agrotender"

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


# Пример асинхронной функции для сохранения содержимого страницы
async def save_page_content_html(page, file_path):
    content = await page.content()
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
    logging.info(f"Сохранено содержимое страницы в файл: {file_path}")


# Функция получения всех страниц с категорий all_category
async def get_category():
    # Открываем соединение с базой данных
    await database.connect()
    all_category = [
        "https://agrotender.com.ua/board/all_t150",
        "https://agrotender.com.ua/board/all_t16",
        "https://agrotender.com.ua/board/all_t2",
        "https://agrotender.com.ua/board/all_t175",
        "https://agrotender.com.ua/board/all_t161",
        "https://agrotender.com.ua/board/all_t188",
        "https://agrotender.com.ua/board/all_t249",
        "https://agrotender.com.ua/board/all_t282",
        "https://agrotender.com.ua/board/all_t250",
    ]

    async with async_playwright() as playwright:
        proxies = load_proxies()
        proxy_gen = proxy_generator(proxies)
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

        for category in all_category:
            await page.goto(category, wait_until="networkidle", timeout=60000)
            content = await page.content()
            parser = HTMLParser(content)
            # Извлекаем все элементы <a> внутри <h3> с указанным классом

            all_page_element = parser.css_first(
                "body > main > div.container.mb-5 > div > div > a:nth-child(4)"
            )
            all_page = 1
            if all_page_element:
                all_page = int(all_page_element.text(strip=True))

            for pg in range(1, all_page + 1):
                all_datas = []
                await page.goto(f"{category}_p{pg}", wait_until="load", timeout=60000)

                # Обновляем контент и парсер для каждой страницы
                content = await page.content()
                parser = HTMLParser(content)

                links = parser.css("h3.title.ml-0.d-none.d-sm-block a")
                for link in links:
                    url = f'https://agrotender.com.ua{link.attributes.get("href")}'
                    id_url = url.split("/")[-1].replace("post-", "")
                    data = {"id": id_url, "href": url}
                    all_datas.append(data)

                await asyncio.sleep(1)

                # Вставляем данные в таблицу agrotender_com_ua_url
                query = """
                INSERT INTO agrotender_com_ua_url (url_id, url) VALUES (:url_id, :url)
                """
                for data in all_datas:
                    try:
                        await database.execute(
                            query, values={"url_id": data["id"], "url": data["href"]}
                        )
                    except IntegrityError as e:
                        logging.warning(f"Duplicate entry for url_id {data['id']}: {e}")

                logging.info(f"Обработана страница {pg} категории {category}")

    # Закрываем соединение с базой данных
    await database.disconnect()


def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Загрузить прокси-серверы из файла
def load_proxies_curl_cffi():
    filename = "proxi.json"
    with open(filename, "r") as f:
        raw_proxies = json.load(f)

    formatted_proxies = []
    for proxy in raw_proxies:
        ip, port, username, password = proxy
        formatted_proxies.append(f"http://{username}:{password}@{ip}:{port}")

    return formatted_proxies


def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


# Функция для выполнения запроса
async def fetch_url(url, proxy, headers, sem):
    from asyncio import WindowsSelectorEventLoopPolicy

    # Установим политику цикла событий для Windows
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    async with sem:
        async with AsyncSession() as session:
            post = url.split("/")[-1].replace("post-", "")
            filename_html = os.path.join(html_path, f"{post}.html")
            if not os.path.exists(filename_html):
                response = await session.get(
                    url, proxy=proxy, headers=headers, ssl_version="TLSv1_2"
                )  # , ssl_version="TLSv1_2"тестовая настройка
                src = response.text
                with open(filename_html, "w", encoding="utf-8") as f:
                    f.write(src)
                await asyncio.sleep(1)


# Основная функция для распределения URL по прокси и запуска задач
async def get_html():
    urls = await fetch_data_url()

    tasks = []
    proxies = load_proxies_curl_cffi()
    proxy_count = len(proxies)
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    # Устанавливаем ограничение на количество одновременно выполняемых задач
    sem = asyncio.Semaphore(10)  # Ограничение на 10 одновременно выполняемых задач
    for i, url in enumerate(urls):
        proxy = proxies[i % proxy_count]
        tasks.append(fetch_url(url, proxy, headers, sem))
    await asyncio.gather(*tasks)


# Получаем с БД все url
async def fetch_data_url():
    query = "SELECT url FROM agrotender_com_ua_url"
    await database.connect()
    rows = await database.fetch_all(query)
    await database.disconnect()

    data_list = []
    for row in rows:
        data = row["url"]
        data_list.append(data)

    return data_list


async def fetch_data():
    query = "SELECT url_id AS id, url AS href FROM agrotender_com_ua_url"
    await database.connect()
    rows = await database.fetch_all(query)
    await database.disconnect()

    data_list = []
    for row in rows:
        data = {"id": row["id"], "href": row["href"]}
        data_list.append(data)

    return data_list


# Функция для обновлении всех категорий
async def update_ads():
    data_bd = await fetch_data_url()
    proxies = load_proxies()
    proxy_gen = proxy_generator(proxies)
    # Открываем соединение с базой данных
    # await database.connect()

    all_category = [
        "https://agrotender.com.ua/board/all_t150",
        "https://agrotender.com.ua/board/all_t16",
        "https://agrotender.com.ua/board/all_t2",
        "https://agrotender.com.ua/board/all_t175",
        "https://agrotender.com.ua/board/all_t161",
        "https://agrotender.com.ua/board/all_t188",
        "https://agrotender.com.ua/board/all_t249",
        "https://agrotender.com.ua/board/all_t282",
        "https://agrotender.com.ua/board/all_t250",
    ]

    async with async_playwright() as playwright:
        proxies = load_proxies()
        proxy_gen = proxy_generator(proxies)
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
        for category in all_category:
            try:
                await page.goto(category, wait_until="load", timeout=60000)
            except:
                print(proxy_server)
                break
            content = await page.content()
            parser = HTMLParser(content)
            # Извлекаем все элементы <a> внутри <h3> с указанным классом

            has_new_data = True
            # Максимальное количество страниц для проверки
            max_pages_to_check = 2

            for pg in range(1, max_pages_to_check + 1):

                await page.goto(f"{category}_p{pg}", wait_until="load", timeout=60000)

                # Обновляем контент и парсер для каждой страницы
                content = await page.content()
                parser = HTMLParser(content)

                links = parser.css("h3.title.ml-0.d-none.d-sm-block a")
                for link in links:
                    url = f'https://agrotender.com.ua{link.attributes.get("href")}'
                    all_datas.append(url)
        # Проверка на совпадения с данными из базы данных
        if any(data in data_bd for data in all_datas):
            has_new_data = False

    # Сохранение новых данных если присутсвуют в файл new_url.json
    if has_new_data:
        with open("new_url.json", "w", encoding="utf-8") as f:
            json.dump(all_datas, f, ensure_ascii=False, indent=4)
        print(f"Файл сохранил new_url.json")

    print(
        f"Проверили наличие новых объявлений \n  {datetime.now().strftime('%H:%M %d-%m-%Y')}"
    )


# Функция парсинга данных из html
async def parsing_page():
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
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-9 > h1"
        )

        # Если элемент не найден, пробуем второй путь
        if title_element:
            title = title_element.text(strip=True)
        else:
            print("Нету title_element")
            print(item_html)

        purpose_of_grain = None
        quantity = None

        purpose_of_grain_element = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-9 > div.row.mt-1 > div.col"
        )
        if purpose_of_grain_element:
            purpose_of_grain = purpose_of_grain_element.text(strip=True).replace(
                "Рубрика:", ""
            )
        quantity_element = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-3.pr-0.pl-4 > span.count.d-block"
        )
        if quantity_element:
            quantity = quantity_element.text(strip=True)
            match = re.search(r"\d+", quantity)
            if match:
                quantity = match.group()

        price_element = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-3.pr-0.pl-4 > span.price.d-block.text-uppercase"
        )
        if price_element:
            price = price_element.text(strip=True)
            # match = re.search(r"\d+", quantity)
            # quantity = match.group()

        region_text_elem = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-9 > div.row.mt-3 > div.col > span"
        )
        if region_text_elem:
            region_text = region_text_elem.text(strip=True)
        # Словарь для перевода русских названий месяцев в номера месяцев
        months = {
            "Января": "01",
            "Февраля": "02",
            "Марта": "03",
            "Апреля": "04",
            "Мая": "05",
            "Июня": "06",
            "Июля": "07",
            "Августа": "08",
            "Сентября": "09",
            "Октября": "10",
            "Ноября": "11",
            "Декабря": "12",
        }

        def convert_date_to_mysql_format(date_str):
            # Разбиваем строку на части
            parts = date_str.split()
            if len(parts) == 3:
                day = parts[0]
                month = months.get(parts[1])
                year = parts[2]
                if month:
                    # Формируем дату в формате YYYY-MM-DD
                    mysql_date = f"{year}-{month}-{int(day):02d}"
                    return mysql_date
            return None

        updated_date_elem = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-9 > div.row.mt-3 > div.col-auto > span"
        )
        if updated_date_elem:
            updated_date = updated_date_elem.text(strip=True)
            updated_date = updated_date.replace("Оновлено: ", "")
            updated_date = convert_date_to_mysql_format(updated_date)

        description_text_elem = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-9 > div.mt-3.desc > p"
        )
        if description_text_elem:
            description_text = description_text_elem.text(strip=True)
        user_name_elem = parser.css_first(
            "body > main > div.container.px-0.px-sm-3.mt-0.mt-sm-4 > div > div.col-3.pr-0.pl-4 > a > span.postCompanyTitle"
        )
        if user_name_elem:
            user_name = user_name_elem.text(strip=True)

        def split_and_format(text):
            # Определяем регулярное выражение для поиска номеров телефонов и имен
            pattern = re.compile(r"(\+?\d{5,12})([А-Яа-яA-Za-z\s]+)")

            # Находим все совпадения в тексте
            matches = pattern.findall(text)

            # Формируем отформатированную строку
            formatted_parts = [f"{match[0]} {match[1].strip()}" for match in matches]

            # Объединяем части с разделителем ;
            formatted_text = "; ".join(formatted_parts)

            return formatted_text

        phone_numbers_elem = parser.css("div.col.pl-2 a.phone")
        if phone_numbers_elem:
            formatted_parts = []

            for elem in phone_numbers_elem:
                phone_href = elem.attributes.get("href", "")
                phone_number = phone_href.replace("tel:", "").strip()
                formatted_parts.append(phone_number)
            phone_numbers = "; ".join(formatted_parts)
        data = {
            "id_add": id_add,
            "title": title,
            "purpose_of_grain": purpose_of_grain,
            "quantity": quantity,
            "price": price,
            "region_text": region_text,
            "updated_date": updated_date,
            "description_text": description_text,
            "user_name": user_name,
            "phone_numbers": phone_numbers,
        }
        all_datas.append(data)
    await database.connect()
    try:
        await load_data_to_db(database, all_datas)
    finally:
        await database.disconnect()

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Запись DataFrame в Excel
    output_file = "output.xlsx"
    df.to_excel(output_file, index=False)


# загрузка  в БД всех объевлений
async def load_data_to_db(database, data):
    query = """
    INSERT INTO agrotender_com_ua_ads (
        id_add, title, purpose_of_grain, quantity, price,
        region_text, updated_date, description_text,
        user_name, phone_numbers
    ) VALUES (
        :id_add, :title, :purpose_of_grain, :quantity, :price,
        :region_text, :updated_date, :description_text,
        :user_name, :phone_numbers
    )
    """
    await database.execute_many(query, data)


# Функция для паузы
async def main_sleep():
    while True:
        await update_ads()
        next_run_time = datetime.now() + timedelta(hours=3)
        print(f"Следующий запуск в {next_run_time.strftime('%H:%M %d-%m-%Y')}")
        await asyncio.sleep(3 * 60 * 60)  # Задержка на 3 часа


if __name__ == "__main__":
    asyncio.run(main_sleep())
    # asyncio.run(get_category())
    # asyncio.run(get_html())
    # asyncio.run(update_ads())
    # asyncio.run(parsing_page())
    # asyncio.run(upload_data_to_google_sheets())
