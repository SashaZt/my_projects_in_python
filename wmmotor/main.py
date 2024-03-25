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

from headers_cookies import cookies, headers
from proxi import proxies

current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
list_path = os.path.join(temp_path, "list")
product_path = os.path.join(temp_path, "product")
img_path = os.path.join(temp_path, "img")
cookies_path = os.path.join(temp_path, "cookies")


def load_proxy():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_proxy = os.path.join(application_path, "proxi.json")
    if not os.path.exists(filename_proxy):
        print("Нету файла с прокси-серверами!!!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)  # Завершаем выполнение скрипта с кодом ошибки 1
    else:
        with open(filename_proxy, "r") as file:
            proxies = json.load(file)
        proxy = random.choice(proxies)
        proxy_host, proxy_port, proxy_user, proxy_pass = proxy
        formatted_proxy_http = (
            f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        )
        formatted_proxy_https = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"  # Измените, если https требует другой прокси

        # Для requests
        proxies_dict = {"http": formatted_proxy_http, "https": formatted_proxy_https}

        # Для aiohttp (если вам нужен только один прокси, верните formatted_proxy_http или formatted_proxy_https)
        # Возвращаем оба формата для удобства
        return proxies_dict, formatted_proxy_http


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
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
        filename_config = os.path.join(list_path, "categories.csv")
        with open(filename_config, "w", newline="") as csvfile:
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
        print(response.status_code)


def get_urls_product():
    config = load_config()
    headers = config["headers"]
    filename_config = os.path.join(list_path, "categories.csv")

    with open(filename_config, newline="", encoding="utf-8") as files:
        urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
        count = 0
        for url in urls:
            """Универсальное использование прокси-серверов"""
            proxies_requests, proxy_aiohttp = load_proxy()
            count += 1
            response = requests.get(url[0], headers=headers, proxies=proxies_requests)
            src = response.text
            soup = BeautifulSoup(src, "lxml")
            group = (
                soup.find_all("a", attrs={"class": "nodecoration"})[1]
                .text.replace(" - ", "_")
                .replace(",", "")
                .replace(".", "")
                .replace("  ", " ")
                .replace(" ", "_")
                .replace("/", "_")
            )
            table_pagin = int(
                soup.find("td", attrs={"class": "boxContentsMainNoBorder"})
                .find("td", attrs={"valign": "middle"})
                .text.replace("razem towarów: ", "")
            )
            amount_page = table_pagin // 50
            all_urls = []
            count = 0
            for i in range(1, amount_page + 2):
                """Универсальное использование прокси-серверов"""
                proxies_requests, proxy_aiohttp = load_proxy()
                count += 1
                print(f"{count} из {amount_page + 2}")
                pause_time = random.randint(1, 10)
                filename = os.path.join(list_path, "data.csv")
                if i == 1:
                    response = requests.get(
                        url[0],
                        headers=headers,
                        proxies=proxies_requests,
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
                                with open(filename, "a", newline="") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        [url_to_write]
                                    )  # добавление URL в csv
                print(f"Пауза {pause_time}")
                time.sleep(pause_time)

                if i > 1:
                    """Универсальное использование прокси-серверов"""
                    proxies_requests, proxy_aiohttp = load_proxy()
                    response = requests.get(
                        f"{url[0]}&page={i}",
                        headers=headers,
                        proxies=proxies_requests,
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
                                with open(filename, "a", newline="") as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        [url_to_write]
                                    )  # добавление URL в csv
                print(f"Пауза {pause_time}")
                time.sleep(pause_time)


def get_asio():
    import aiohttp
    import asyncio
    import csv
    import os

    async def fetch(session, url, coun):
        config = load_config()
        headers = config["headers"]
        """Универсальное использование прокси-серверов"""
        proxies_requests, proxy_aiohttp = load_proxy()

        filename = os.path.join(product_path, f"data_{coun}.html")
        if not os.path.exists(filename):
            async with session.get(
                url, headers=headers, proxy=proxy_aiohttp
            ) as response:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(await response.text())

    async def main():
        filename = os.path.join(list_path, "data.csv")
        coun = 0
        async with aiohttp.ClientSession() as session:
            with open(filename, newline="", encoding="utf-8") as files:
                urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
                for i in range(0, len(urls), 100):
                    tasks = []
                    for row in urls[i : i + 100]:
                        coun += 1
                        url = row[0]
                        filename_to_check = os.path.join(
                            product_path, f"data_{coun}.html"
                        )
                        if not os.path.exists(filename_to_check):
                            tasks.append(fetch(session, url, coun))
                    if tasks:
                        await asyncio.gather(*tasks)
                        print(f"Completed {coun} requests")
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
                    print(f"Нет symbol")

                try:
                    price_netto = (
                        table_product.find_all(class_="productPageName")[1]
                        .get_text()
                        .replace(",", ".")
                        .replace(" zł", "")
                    )
                except:
                    price_netto = None
                    print(f"Нет price_netto")

                try:
                    price_brutto = (
                        table_product.find_all(class_="productPageName")[2]
                        .get_text()
                        .replace(",", ".")
                        .replace(" zł", "")
                    )
                except:
                    price_brutto = None
                    print(f"Нет price_brutto")

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
                # print(category)
                try:
                    opis_tovaru = table_product.find_all("td", attrs={"valign": "top"})[
                        1
                    ].get_text(strip=True)
                except:
                    opis_tovaru = None

                # coun = 0
                # for u in urls_photo:
                #     pause_time = random.randint(1, 2)
                #     """Настройка прокси серверов случайных"""
                #     proxy = random.choice(proxies)
                #     proxy_host = proxy[0]
                #     proxy_port = proxy[1]
                #     proxy_user = proxy[2]
                #     proxy_pass = proxy[3]

                #     proxi = {
                #         "http": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}",
                #         "https": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}",
                #     }

                # if len(urls_photo) > 1 and coun > 0:
                #     file_path = f'c:\\data_wmmotor\\img\\{symbol}_{coun}.jpg'
                # else:
                #     file_path = f'c:\\data_wmmotor\\img\\{symbol}.jpg'

                # if len(urls_photo) > 1 and coun > 0:
                #     file_name = f'{symbol}_{coun}.jpg'
                # else:
                #     file_name = f'{symbol}.jpg'
                #
                # file_path = os.path.join(img_path, file_name)
                # if not os.path.exists(file_path):
                #     try:
                #         img_data = requests.get(u, headers=headers, cookies=cookies, proxies=proxi)
                #         with open(file_path, 'wb') as file_img:
                #             file_img.write(img_data.content)
                #     except:
                #         print(f"Ошибка при выполнении запроса для URL: {u}")
                # coun += 1

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
    from datetime import datetime
    from asyncio import sleep
    import aiofiles
    import aiohttp
    from aiohttp import BasicAuth
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    current_directory = os.getcwd()
    temp_directory = "temp"
    # Создайте полный путь к папке temp

    daily_sales_path = os.path.join(temp_path, "daily_sales")
    payout_history_path = os.path.join(temp_path, "payout_history")
    pending_custom_path = os.path.join(temp_path, "pending_custom")
    chat_path = os.path.join(temp_path, "chat")

    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def save_cookies(page):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(cookies_path, "cookies.json")
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def run(playwright):
        # async with aiohttp.ClientSession() as session:
        browsers_path = os.path.join(current_directory, "pw-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        url = "http://www.wmmotor.pl/hurtownia/drzewo.php"
        """Вход на страницу с логин и пароль"""
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)  # 60 секунд
        except TimeoutError:
            print(f"Страница не загрузилась 60 секунд.")
        try:
            # Ожидаем появления элемента h1 с текстом "Login to ManyVids"
            print("Вставьте логин, почту")
            fldEmail = "kupujwpl@gmail.com"
            # fldEmail = str(input())
            print("Вставьте пароль")
            fldPassword = "8T1cekQFO2"
            # fldPassword = str(input())
            fldEmail_xpath = '//input[@name="fldEmail"]'
            fldPassword_xpath = '//input[@name="fldPassword"]'
            fldSaveEmail_xpath = '//input[@name="fldSaveEmail"]'
            # Ожидаем появления элементов формы на странице
            await page.wait_for_selector(fldEmail_xpath, state="visible")
            await page.wait_for_selector(fldPassword_xpath, state="visible")
            await page.wait_for_selector(fldSaveEmail_xpath, state="visible")
            # Кликаем по чекбоксу, чтобы изменить его состояние
            await page.click(fldSaveEmail_xpath)
            # Вводим логин и пароль
            await page.fill(fldEmail_xpath, fldEmail)
            await page.fill(fldPassword_xpath, fldPassword)
            # Находим input элемент по имени
            input_element = await page.query_selector('input[name="fldResult"]')

            """Решаем математическую задачу"""
            
            if input_element:
                # Для получения родительского элемента используем XPath и функцию evaluate
                text_content = await page.evaluate('''(input) => {
                    const parentTd = input.closest('td'); // Находим ближайший родительский элемент td
                    return parentTd ? parentTd.textContent : ''; // Возвращаем текстовое содержимое элемента td или пустую строку
                }''', input_element)

                # Применяем регулярное выражение к текстовому содержимому
                match = re.search(r"Podaj wynik działania: (\d+) \+ (\d+) =", text_content)

                if match:
                    # Извлекаем числа из найденного совпадения
                    num1, num2 = map(int, match.groups())
                    
                    # Вычисляем результат
                    int_result = num1 + num2
                    
                    # Выводим и/или вводим результат обратно в форму
                    print(f"Результат: {int_result}")
                    await input_element.fill(str(int_result))  # Заполняем поле результатом
                    

            else:
                print("Элемент не найден.")

            """Нажимаем кнопку ZALOGUJ"""
            flinkButton_xpath = '//a[@class="linkButton"]'
            flinkButton = await page.wait_for_selector(flinkButton_xpath, state="visible")
            await flinkButton.click()


            await sleep(5)
        except TimeoutError:
            print("Страница не загрузилась")

        filename = await save_cookies(page)

        """Закрываем"""
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
        "Введите 1 для загрузки категорий"
        "\nВведите 2 для загрузки всех товаров"
        "\nВведите 3 после скачивания всех товаров, получаем отчет"
        "\nВведите 4 если у Вас есть файл с остатками, нужно удалить старые данные!!!!"
        "\nВведите 0 Закрытия программы"
    )
    try:
        user_input = input("Выберите действие: ")  # Сначала получаем ввод как строку
        user_input = int(user_input)  # Затем пытаемся преобразовать его в целое число
    except ValueError:  # Если введенные данные нельзя преобразовать в число
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
        continue  # Пропускаем оставшуюся часть цикла и начинаем с новой итерации

    if user_input == 1:
        get_cookies()
        cookies_to_requests()
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
    elif user_input == 0:
        print("Программа завершена.")
        time.sleep(2)
        sys.exit(1)

    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
