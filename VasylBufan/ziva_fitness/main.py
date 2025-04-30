import asyncio
import hashlib
import json
import re
from pathlib import Path

import gspread
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
config_directory = current_directory / "config"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]
login_url = config["site"]["login_url"]
username = config["site"]["username"]
password = config["site"]["password"]
BASE_URL = config["site"]["base_url"]


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


# Получение листа Google Sheets
sheet = get_google_sheet()


async def authorization():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Переходим на страницу логина
        await page.goto(login_url)

        # Заполняем поле логина
        await page.fill('//input[@name="login"]', username)

        # Заполняем поле пароля
        await page.fill('//input[@name="password"]', password)

        # Ставим галочку на чекбоксе
        await page.check('//input[@class="permanentLogin"]')

        # Нажимаем на кнопку отправки формы
        await page.click('//a[@class="button login xta_doLogin"]')
        await page.wait_for_load_state("networkidle")
        await category(page)
        await browser.close()


async def category(page):
    # Ждем появления элемента с XPath
    await page.wait_for_selector('xpath=//dc-con[@class="popup"]')

    # Находим все теги <a> внутри popup с XPath
    links = await page.query_selector_all('xpath=//dc-con[@class="popup"]//a')

    # Собираем href в список
    hrefs = []
    for link in links:
        href = await link.get_attribute("href")
        if href:  # Проверяем, что href не None
            hrefs.append(f'{BASE_URL}{href.lstrip("/")}')

    # Преобразуем в множество для уникальности
    hrefs = set(hrefs)

    logger.info(len(hrefs))
    await pagination(hrefs, page)


async def pagination(urls, page):
    hrefs_product = set()
    for url in urls:
        logger.info(url)
        # Переходим на страницу
        await page.goto(url)
        count_products = await page.query_selector(
            'xpath=//span[@class="totalItems"]//span'
        )
        if count_products:
            text_raw = await count_products.inner_text()  # Получаем текст элемента
            text = int(text_raw)
            if text == 0:
                logger.info(f"Страница {url} пуста")
                continue
        # Ждем появления элемента productHolder
        await page.wait_for_selector("div.productHolder")

        while True:
            items = await page.query_selector('xpath=//div[@class="items"]')
            # Прокручиваем страницу до самого низа
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Даем время для подгрузки контента (если требуется)
            await page.wait_for_timeout(
                1000
            )  # Можно настроить или заменить на wait_for_selector

            # Находим все теги <a> внутри popup с XPath
            links_product = await items.query_selector_all(
                'xpath=//div[@data-name="ProductCustom1"]//h2//a'
            )
            logger.info(len(links_product))
            # Собираем href
            for link in links_product:
                href_product = await link.get_attribute("href")
                if href_product:  # Проверяем, что href не None
                    hrefs_product.add(f'{BASE_URL}{href_product.lstrip("/")}')

            # Проверяем наличие кнопки "Следующая страница"
            next_button = await page.query_selector(
                'xpath=//div[@id="CompoundPagingBottom"]//a[@class="gotoNext"]'
            )
            if not next_button:
                break  # Если кнопки нет, выходим из цикла

            # Кликаем по кнопке "Следующая"
            await next_button.click()
            # Ждем загрузки новой страницы или контента
            await page.wait_for_timeout(2000)

    logger.info(f"Найдено {len(hrefs_product)} продуктовых ссылок")
    await product(hrefs_product, page)
    return hrefs_product


async def product(urls, page):

    for url in urls:
        logger.info(url)
        await page.goto(url)

        # Находим все скрипты с type='text/javascript'
        scripts = await page.query_selector_all('script[type="text/javascript"]')
        variants_ids = []

        # Проверяем каждый скрипт на наличие //<![CDATA[ и variants_ids
        for script in scripts:
            script_content = await script.inner_html()
            if "//<![CDATA[" in script_content:
                # Ищем variants_ids с помощью регулярного выражения
                match = re.search(r'"variants_ids":\[(.*?)\]', script_content)
                if match:
                    # Извлекаем массив variants_ids и преобразуем в список
                    variants_ids_str = match.group(1)
                    variants_ids = json.loads(f"[{variants_ids_str}]")
                    logger.info(f"Найдены variants_ids: {variants_ids}")

        # Если variants_ids найдены, переходим по URL с &vid=
        if variants_ids:
            for vid in variants_ids:
                # Формируем новый URL с &vid=
                new_url = (
                    f"{url}&vid={vid}"
                    if "&vid=" not in url
                    else re.sub(r"&vid=\d+", f"&vid={vid}", url)
                )
                logger.info(f"Переход по URL: {new_url}")
                await page.goto(new_url)

                # Сохраняем HTML для нового URL
                output_html_file = (
                    html_directory / f"{hashlib.md5(new_url.encode()).hexdigest()}.html"
                )
                html_content = await page.content()
                with open(output_html_file, "w", encoding="utf-8") as file:
                    file.write(html_content)

        # Сохраняем HTML для исходной страницы
        output_html_file = (
            html_directory / f"{hashlib.md5(url.encode()).hexdigest()}.html"
        )
        html_content = await page.content()
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(html_content)


def parse_html_to_json():
    """
    Парсит HTML-файлы из html_directory, извлекает данные и сохраняет их в JSON.

    Args:
        html_directory (Path): Директория с HTML-файлами.
        output_json (str): Путь к выходному JSON-файлу.
    """
    products = []

    # Проходим по всем HTML-файлам в директории
    for html_file in html_directory.glob("*.html"):
        try:
            with open(html_file, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, "html.parser")
                # Инициализируем словарь для данных продукта
                product_data = {}

                # Извлекаем название продукта
                h1 = soup.find("h1", class_="HeadingView")
                product_data["Name"] = h1.get_text(strip=True) if h1 else None
                pd_table = soup.find("div", id="PDTable")

                # Извлекаем цену с НДС
                price_with_vat = pd_table.find(
                    "span",
                    attrs={
                        "class": "price bs-priceLayout notranslate vat primary user"
                    },
                )
                product_data["Price Brutto"] = None
                if price_with_vat:
                    price_value = price_with_vat.find("span", attrs={"class": "value"})
                    product_data["Price Brutto"] = (
                        price_value.get_text(strip=True).replace(" EUR", "")
                        if price_value
                        else None
                    )

                # Извлекаем цену без НДС
                price_without_vat = pd_table.find(
                    "span",
                    attrs={
                        "class": "price bs-priceLayout notranslate novat secondary user"
                    },
                )
                product_data["Price Netto"] = None
                if price_without_vat:
                    price_value = price_without_vat.find("span", class_="value")
                    product_data["Price Netto"] = (
                        price_value.get_text(strip=True).replace(" EUR", "")
                        if price_value
                        else None
                    )

                # Извлекаем данные о наличии как отдельные поля
                availability_div = None
                if pd_table:
                    availability_div = pd_table.find(
                        "div", class_="fitnessproAvailability"
                    )
                if not availability_div:
                    availability_div = soup.find("div", class_="fitnessproAvailability")

                product_data["In-stock"] = None
                product_data["In 30 days"] = None
                product_data["In 60 days"] = None

                if availability_div:
                    for span_class, key in [
                        ("inStock", "In-stock"),
                        ("avail30", "In 30 days"),
                        ("avail60", "In 60 days"),
                    ]:
                        span = availability_div.find("span", class_=span_class)
                        if span:
                            caption = span.find_previous("span", class_="caption")
                            caption_text = (
                                caption.get_text(strip=True) if caption else ""
                            )
                            product_data[key] = span.get_text(strip=True)
                else:
                    logger.warning(f"fitnessproAvailability не найден в {html_file}")

                # Извлекаем код продукта
                code_item = soup.find("bs-grid-item", attrs={"class": "code value"})
                product_data["code"] = None
                if code_item:
                    code_span = code_item.find("span")
                    product_data["code"] = (
                        code_span.get_text(strip=True) if code_span else None
                    )
                # Добавляем данные в список, если есть хоть одно поле
                if any(product_data.values()):
                    products.append(product_data)

        except Exception as e:
            logger.error(f"Ошибка парсинга {html_file}: {e}")
            continue
    output_json = "products.json"
    # Сохраняем результат в JSON
    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(products, json_file, ensure_ascii=False, indent=4)
    update_sheet_with_data(sheet, products)


def update_sheet_with_data(sheet, data, total_rows=8000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Добавление пустых строк до общего количества total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A2:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")
    logger.info(f"Обновлено {len(data)} строк в Google Sheets")


async def main():
    await authorization()


if __name__ == "__main__":
    asyncio.run(main())
    parse_html_to_json()
