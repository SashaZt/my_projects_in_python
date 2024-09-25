import csv
import glob
import os
import random
import time
import json
import sys
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from configuration.logger_setup import logger
from aiohttp import BasicAuth
from configuration.logger_setup import logger


# Получаем текущую директорию
current_directory = Path.cwd()
# Создайте полный путь к папке temp
temp_path = current_directory / "temp"
configuration_path = current_directory / "configuration"
list_path = temp_path / "list"
product_path = temp_path / "product"
img_path = temp_path / "img"
cookies_path = temp_path / "cookies"
# Установка директорий на основе конфигурационного файла
# Создание директорий, если их нет
temp_path.mkdir(parents=True, exist_ok=True)
list_path.mkdir(parents=True, exist_ok=True)
product_path.mkdir(parents=True, exist_ok=True)
img_path.mkdir(parents=True, exist_ok=True)
cookies_path.mkdir(parents=True, exist_ok=True)
configuration_path.mkdir(parents=True, exist_ok=True)


csv_file_categories = list_path / "categories.csv"
csv_file_data = list_path / "data.csv"
txt_file_proxies = configuration_path / "roman.txt"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    with open(txt_file_proxies, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        logger.error("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)
    headers = config["headers"]

    # Генерация строки кукисов из конфигурации
    if "cookies" in config:
        cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
        headers["Cookie"] = cookies_str
    return config


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path, img_path, cookies_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path, img_path]:
        files = glob.glob(os.path.join(folder, "*"))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


def get_categories_to_html_file():
    config = load_config()
    headers = config["headers"]
    url_all = []
    url = "http://www.wmmotor.pl/hurtownia/drzewo.php"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        src = response.text
        with open(csv_file_categories, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            soup = BeautifulSoup(src, "lxml")
            table_treee = soup.find("td", attrs={"class": "boxContentsMainNoBorder"})
            treelevel1 = table_treee.find_all("a", attrs={"class": "treelevel1"})
            for item in treelevel1:
                urls = "http://www.wmmotor.pl/hurtownia/" + item.get("href")
                url_all.append(urls)

            for url in url_all:
                writer.writerow([url])
    else:
        logger.error(response.status_code)


def get_urls_product():
    config = load_config()
    headers = config["headers"]
    proxies = load_proxies()
    with open(csv_file_categories, newline="", encoding="utf-8") as files:
        urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
        count = 0

        for url in urls:
            proxy = random.choice(proxies)  # Выбираем случайный прокси
            proxies_dict = {"http": proxy, "https": proxy}
            count += 1
            response = requests.get(url[0], headers=headers, proxies=proxies_dict)
            src = response.text
            soup = BeautifulSoup(src, "lxml")
            # group = (
            #     soup.find_all("a", attrs={"class": "nodecoration"})[1]
            #     .text.replace(" - ", "_")
            #     .replace(",", "")
            #     .replace(".", "")
            #     .replace("  ", " ")
            #     .replace(" ", "_")
            #     .replace("/", "_")
            # )
            table_pagin = int(
                soup.find("td", attrs={"class": "boxContentsMainNoBorder"})
                .find("td", attrs={"valign": "middle"})
                .text.replace("razem towarów: ", "")
            )
            amount_page = table_pagin // 50
            all_urls = []
            count = 0
            for i in range(1, amount_page + 2):
                proxy = random.choice(proxies)  # Выбираем случайный прокси
                proxies_dict = {"http": proxy, "https": proxy}
                count += 1
                logger.info(f"{count} из {amount_page + 2}")
                pause_time = random.randint(1, 5)
                if i == 1:
                    response = requests.get(
                        url[0],
                        headers=headers,
                        proxies=proxies_dict,
                    )

                    src = response.text
                    soup = BeautifulSoup(src, "lxml")
                    product_listing_even = soup.find(
                        "table", attrs={"class": "productListing"}
                    ).find_all("td", attrs={"class": "productListingEven"})
                    product_listing_odd = soup.find(
                        "table", attrs={"class": "productListing"}
                    ).find_all("td", attrs={"class": "productListingOdd"})
                    all_products = product_listing_even + product_listing_odd
                    for u in all_products:
                        url_ = u.find_all("a")
                        for a_tag in url_:
                            href = a_tag["href"]
                            if "towar.php" in href:
                                url_to_write = "http://www.wmmotor.pl/hurtownia/" + href
                                with open(csv_file_data, "a", newline="") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        [url_to_write]
                                    )  # добавление URL в csv
                logger.info(f"Пауза {pause_time}")
                time.sleep(pause_time)

                if i > 1:
                    proxy = random.choice(proxies)  # Выбираем случайный прокси
                    proxies_dict = {"http": proxy, "https": proxy}
                    response = requests.get(
                        f"{url[0]}&page={i}",
                        headers=headers,
                        proxies=proxies_dict,
                    )
                    src = response.text
                    soup = BeautifulSoup(src, "lxml")
                    product_listing_even = soup.find(
                        "table", attrs={"class": "productListing"}
                    ).find_all("td", attrs={"class": "productListingEven"})
                    product_listing_odd = soup.find(
                        "table", attrs={"class": "productListing"}
                    ).find_all("td", attrs={"class": "productListingOdd"})
                    all_products = product_listing_even + product_listing_odd
                    for u in all_products:
                        url__ = u.find_all("a")
                        for a_tag in url__:
                            href = a_tag["href"]
                            if "towar.php" in href:
                                url_to_write = "http://www.wmmotor.pl/hurtownia/" + href
                                # all_urls.append('http://www.wmmotor.pl/hurtownia/' + href)
                                with open(csv_file_data, "a", newline="") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        [url_to_write]
                                    )  # добавление URL в csv
                logger.info(f"Пауза {pause_time}")
                time.sleep(pause_time)


def get_asio():
    import aiohttp
    import asyncio
    import csv
    import os

    # Основная функция для загрузки данных

    async def fetch(session, url, coun, proxy, proxy_auth):
        config = load_config()
        headers = config["headers"]

        # Определение имени файла для сохранения
        filename = os.path.join(product_path, f"data_{coun}.html")

        # Проверка наличия файла, если его нет, делаем запрос
        if not os.path.exists(filename):
            async with session.get(
                url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
            ) as response:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(await response.text())

    # Асинхронная основная функция
    async def main():
        filename = os.path.join(list_path, "data.csv")
        coun = 0
        proxies = load_proxies()

        async with aiohttp.ClientSession() as session:
            with open(filename, newline="", encoding="utf-8") as files:
                urls = list(csv.reader(files, delimiter=" ", quotechar="|"))

                for i in range(0, len(urls), 100):
                    proxy = random.choice(proxies)  # Выбираем случайный прокси
                    proxy_url = proxy.split("@")[
                        -1
                    ]  # Получаем URL без авторизационной части (IP:port)
                    login, password = (
                        proxy.split("@")[0].replace("http://", "").split(":")
                    )  # Извлекаем логин и пароль
                    proxy_auth = BasicAuth(login, password)

                    tasks = []
                    for row in urls[i : i + 100]:
                        coun += 1
                        url = row[0]
                        filename_to_check = os.path.join(
                            product_path, f"data_{coun}.html"
                        )
                        if not os.path.exists(filename_to_check):
                            # Добавляем задание для выполнения запроса
                            tasks.append(
                                fetch(
                                    session,
                                    url,
                                    coun,
                                    f"http://{proxy_url}",
                                    proxy_auth,
                                )
                            )

                    if tasks:
                        await asyncio.gather(*tasks)
                        logger.info(f"Выполнено {coun} запросов")
                        await asyncio.sleep(5)

    asyncio.run(main())


def parsing_products():
    folder = os.path.join(product_path, "*.html")

    files_html = glob.glob(folder)
    heandler = [
        "nazva",
        "symbol",
        "price_netto",
        "price_brutto",
        "opis_tovaru",
        "in_stock",
        "category",
    ]
    with open("output.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            try:
                table_product = soup.find_all("td", attrs={"colspan": "2"})[0].find_all(
                    "td", attrs={"valign": "top"}
                )[0]
            except:
                continue
            tovar_in_magazine = table_product.find(
                "img", attrs={"title": "Towar dostępny w naszym magazynie"}
            )
            tovar_in_magazine_big_1 = table_product.find(
                "span", attrs={"title": "Towar dostępny w naszym magazynie"}
            )
            in_stock = ""
            if tovar_in_magazine or tovar_in_magazine_big_1:
                # product_yes = tovar_in_magazine.get('src')
                # if product_yes:
                in_stock = 9
                try:
                    product_name = table_product.find(
                        class_="productPageName"
                    ).get_text()
                except:
                    product_name = None

                try:
                    symbol = table_product.text.split("Symbol: ")[1].split("\n")[0]
                except:
                    symbol = None
                    logger.error(f"Нет symbol")

                try:
                    price_netto = (
                        table_product.find_all(class_="productPageName")[1]
                        .get_text()
                        .replace(",", ".")
                        .replace(" zł", "")
                    )
                except:
                    price_netto = None
                    logger.error(f"Нет price_netto")

                try:
                    price_brutto = (
                        table_product.find_all(class_="productPageName")[2]
                        .get_text()
                        .replace(",", ".")
                        .replace(" zł", "")
                    )
                except:
                    price_brutto = None
                    logger.error(f"Нет price_brutto")

                urls_photo = []
                photos = soup.find_all("a", attrs={"rel": "lightbox[galeria]"})
                for p in photos:
                    url_photo = p.get("href").replace("../", "http://www.wmmotor.pl/")
                    urls_photo.append(url_photo)
                '//span[@style="font-weight: bold; color: #CE0000;"]'
                try:
                    # Пытаемся найти элемент и извлечь его текст
                    category_text = soup.find(
                        "span", attrs={"style": "font-weight: bold; color: #CE0000;"}
                    ).get_text(strip=True)
                    # Применяем регулярные выражения для замены символов
                    category = (
                        re.sub(r"[ .,]", "_", category_text)
                        .replace("__", "_")
                        .replace(" - ", "_")
                    )
                except AttributeError:
                    # Если элемент не найден, soup.find() вернёт None, что приведёт к AttributeError при попытке вызвать .get_text()
                    category = None
                try:
                    opis_tovaru = table_product.find_all("td", attrs={"valign": "top"})[
                        1
                    ].get_text(strip=True)
                except:
                    opis_tovaru = None


                values = [
                    product_name,
                    symbol,
                    price_netto,
                    price_brutto,
                    opis_tovaru,
                    in_stock,
                    category,
                ]
                writer.writerow(values)  # Дописываем значения из values


def csv_to_excell():
    filename_to_csv_output = os.path.join(current_directory, "output.csv")
    filename_csv_to_xlsx = os.path.join(current_directory, "output.xlsx")
    data = pd.read_csv(filename_to_csv_output, encoding="utf-8", delimiter=";")

    # Сохранение данных в файл XLSX
    data.to_excel(filename_csv_to_xlsx, index=False, engine="openpyxl")


def get_cookies():
    import glob
    import asyncio
    import json
    import os
    import random
    import re
    from datetime import datetime
    from asyncio import sleep
    import aiofiles
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    async def save_cookies(page):
        cookies = await page.context.cookies()
        filename = os.path.join(cookies_path, "cookies.json")
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(cookies))
        return filename

    async def run(playwright):
        # current_directory = os.getcwd()  # Получаем текущий каталог
        # browsers_path = os.path.join(current_directory, "pw-browsers")
        # if os.path.exists(browsers_path):
        #     os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        # else:
        #     os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)  # Удаляем переменную, если она установлена
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        
        # browser = await playwright.chromium.launch(headless=False)
        # context = await browser.new_context()
        # page = await context.new_page()
        url = "http://www.wmmotor.pl/hurtownia/drzewo.php"

        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except TimeoutError:
            logger.error(f"Страница не загрузилась за 60 секунд.")
            return

        try:
            # Ввод логина и пароля
            logger.info("Вставьте логин, почту")
            fldEmail = "kupujwpl@gmail.com"
            logger.info("Вставьте пароль")
            fldPassword = "8T1cekQFO2"

            fldEmail_xpath = '//input[@name="fldEmail"]'
            fldPassword_xpath = '//input[@name="fldPassword"]'
            fldSaveEmail_xpath = '//input[@name="fldSaveEmail"]'

            await page.wait_for_selector(fldEmail_xpath, state="visible")
            await page.wait_for_selector(fldPassword_xpath, state="visible")
            await page.wait_for_selector(fldSaveEmail_xpath, state="visible")

            await page.click(fldSaveEmail_xpath)
            await page.fill(fldEmail_xpath, fldEmail)
            await page.fill(fldPassword_xpath, fldPassword)

            input_element = await page.query_selector('input[name="fldResult"]')

            """Решаем математическую задачу"""
            if input_element:
                text_content = await page.evaluate(
                    """(input) => {
                    const parentTd = input.closest('td');
                    return parentTd ? parentTd.textContent : '';
                }""",
                    input_element,
                )

                match_plus = re.search(
                    r"Podaj wynik działania: (\d+) \+ (\d+) =", text_content
                )
                match_minus = re.search(
                    r"Podaj wynik działania: (\d+) \- (\d+) =", text_content
                )

                if match_plus:
                    num1, num2 = map(int, match_plus.groups())
                    int_result = num1 + num2
                    logger.info(f"Результат: {int_result}")
                    await input_element.fill(str(int_result))
                elif match_minus:
                    num1, num2 = map(int, match_minus.groups())
                    int_result = num1 - num2
                    logger.info(f"Результат: {int_result}")
                    await input_element.fill(str(int_result))
            else:
                logger.error("Элемент не найден.")

            """Нажимаем кнопку ZALOGUJ"""
            flinkButton_xpath = '//a[@class="linkButton"]'
            flinkButton = await page.wait_for_selector(
                flinkButton_xpath, state="visible"
            )
            await flinkButton.click()

            await sleep(5)
        except TimeoutError:
            logger.error("Страница не загрузилась")

        filename = await save_cookies(page)
        await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())


def cookies_to_requests():
    # Пути к файлам
    filename_temp_cookies = os.path.join(cookies_path, "cookies.json")
    filename_config = os.path.join(current_directory, "config.json")

    # Чтение и обновление файла config.json
    with open(filename_config, "r", encoding="utf-8") as file:
        config_data = json.load(file)

    with open(filename_temp_cookies, "r", encoding="utf-8") as file:
        temp_cookies = json.load(file)

        # Преобразуем список cookies в словарь cookies
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in temp_cookies}

        # Обновляем только блок cookies
        config_data["cookies"] = cookies_dict

    # Запись обновленных данных обратно в файл
    with open(filename_config, "w", encoding="utf-8") as file:
        json.dump(config_data, file, ensure_ascii=False, indent=4)


while True:
    # Запрос ввода от пользователя
    print(
        "Введите 0 для получение куки"
        "\nВведите 1 для загрузки категорий"
        "\nВведите 2 для загрузки всех товаров"
        "\nВведите 3 после скачивания всех товаров, получаем отчет"
        "\nВведите 4 если у Вас есть файл с остатками, нужно удалить старые данные!!!!"
        "\nВведите 9 Закрытия программы"
    )
    try:
        user_input = input("Выберите действие: ")  # Сначала получаем ввод как строку
        user_input = int(user_input)  # Затем пытаемся преобразовать его в целое число
    except ValueError:  # Если введенные данные нельзя преобразовать в число
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
        continue  # Пропускаем оставшуюся часть цикла и начинаем с новой итерации

    if user_input == 1:
        print("Собираем категории товаров")
        get_categories_to_html_file()
        print("Скачиваем все ссылки")
        get_urls_product()
        print("Переходим к пункту 2")
    elif user_input == 2:
        get_asio()
        print("Переходим к пункту 3")
    elif user_input == 3:
        parsing_products()
        csv_to_excell()
        print("Переходим к пункту 0")
    elif user_input == 4:
        delete_old_data()
        print("Старые файлы удалены, переходим к пункту 1")
    elif user_input == 9:
        print("Программа завершена.")
        time.sleep(2)
        sys.exit(1)
    elif user_input == 0:
        get_cookies()
        cookies_to_requests()

    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
