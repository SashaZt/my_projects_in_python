# -*- mode: python ; coding: utf-8 -*-
import random
import csv
import os
import sys
import asyncio
import time
import glob
import json
import html
import re
import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
category_path = os.path.join(temp_path, "category")


"""
Универсальная загрузка proxy
"""


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
    filename_csv_to_xlsx = os.path.join(current_directory, "output.xlsx")
    if os.path.exists(filename_csv_to_xlsx):
        # Удалите файлы из папок list и product
        for folder in [temp_path, html_path, category_path]:
            files = glob.glob(os.path.join(folder, "*"))
            for f in files:
                if os.path.isfile(f):
                    os.remove(f)


def create_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, html_path, category_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def parsing_url_category_in_html():
    config = load_config()
    headers = config["headers"]
    """Универсальное использование прокси-серверов"""
    proxies_requests, proxy_aiohttp = load_proxy()

    filename_to_csv = os.path.join(category_path, "category_product.csv")
    url = "https://shop.olekmotocykle.com/"
    try:
        response = requests.get(url, headers=headers, proxies=proxies_requests)
    except RequestException:
        print(f"Проблема с прокси {proxies_requests}. Пропускаем.")
        return None  # или возвращайте какое-либо значение по умолчанию
    category_product = []
    if response.content:
        soup = BeautifulSoup(response.content, "lxml")

        for link in soup.select(".category-links-ui a"):
            href = link.get("href")
            if "produkty/" in href:
                category_product.append(url + href)
        filename_to_csv = os.path.join(category_path, "category_product.csv")
        with open(filename_to_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\r")
            for item in category_product:
                writer.writerow([item])
    else:
        print("No content received")


# def parsing_product():
#     targetPattern = f"c:\\Data_olekmotocykle\\*.html"
#     files_html = glob.glob(targetPattern)
#     data = []
#     with open("output.csv", "w", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file)
#         writer.writerow(
#             ["id_product", "name", "brandName", "gtin", "brutto_price", "netto_price"]
#         )
#         for item in files_html:
#             print(item)
#             with open(item, encoding="utf-8") as file:
#                 src = file.read()
#             soup = BeautifulSoup(src, "html.parser")
#             script_tag = soup.find("script", {"id": "datablock1"})
#             json_content = script_tag.contents[0].strip().replace("},\n}\n}", "}\n}\n}")
#             try:
#                 data = json.loads(json_content)
#                 id_product = soup.find(
#                     "div", {"class": "product-code-ui product-code-lq"}
#                 ).text
#                 name = data["itemOffered"]["productName"][0]["@value"]
#                 brandName = data["itemOffered"]["brand"]["brandName"][0]["@value"]
#                 gtin = data["itemOffered"]["gtin"]
#                 brutto_price = (
#                     soup.find("div", {"class": "brutto-price-ui"})
#                     .text.strip()
#                     .replace(" PLN", "")
#                     .replace("\nbrutto", "")
#                 )
#                 netto_price = (
#                     soup.find("div", {"class": "netto-price-ui"})
#                     .text.strip()
#                     .replace(" PLN", "")
#                     .replace("\nnetto", "")
#                 )
#                 writer.writerow(
#                     [id_product, name, brandName, gtin, brutto_price, netto_price]
#                 )
#             except:
#                 continue
#             div = soup.find_all("div", {"class": "lazyslider-container-lq"})[0]
#             imgs = div.find_all("img", {"class": "open-gallery-lq"})

#             urls_photo = []
#             for img in imgs:
#                 urls_photo.append("https://" + img["data-src"].replace("//", ""))

#             coun = 0
#             file_path_1 = (
#                 f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}.jpg'
#             )
#             file_path_2 = f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}_{coun}.jpg'
#             for u in urls_photo:
#                 proxies = proxy_random()
#                 coun += 1
#                 if len(urls_photo) == 1:
#                     if not os.path.exists(file_path_1):
#                         try:
#                             img_data = requests.get(u, headers=header, proxies=proxies)
#                             with open(file_path_1, "wb") as file_img:
#                                 file_img.write(img_data.content)
#                         except:
#                             print(f"Ошибка при выполнении запроса для URL: {u}")
#                             continue
#                 elif len(urls_photo) > 1:
#                     if not os.path.exists(file_path_2):
#                         img_data = requests.get(u, headers=header, proxies=proxies)
#                         with open(file_path_2, "wb") as file_img:
#                             file_img.write(img_data.content)


# def urls_photo():
#     targetPattern = f"c:\\Data_olekmotocykle\\*.html"
#     files_html = glob.glob(targetPattern)

#     result_dict = {}
#     for item in files_html:
#         with open(item, encoding="utf-8") as file:
#             src = file.read()
#         soup = BeautifulSoup(src, "html.parser")
#         div = soup.find_all("div", {"class": "lazyslider-container-lq"})[0]
#         id_product = soup.find(
#             "div", {"class": "product-code-ui product-code-lq"}
#         ).text.strip()
#         imgs = div.find_all("img", {"class": "open-gallery-lq"})

#         item_dict = {}
#         for i, img in enumerate(imgs):
#             url_photo = "https://" + img["data-src"].replace("//", "")
#             item_dict[f"url_{i + 1}"] = url_photo
#             item_dict[f"id_{i + 1}"] = id_product

#         result_dict[item.replace("c:\\Data_olekmotocykle\\", "")] = item_dict

#     # записываем результат в файл JSON
#     with open("result.json", "w") as json_file:
#         json.dump(result_dict, json_file)


def main_download_url():
    import random
    import requests
    from bs4 import BeautifulSoup
    import asyncio
    import csv
    import re
    import os
    from requests.exceptions import RequestException

    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    category_path = os.path.join(temp_path, "category")

    def get_with_proxies(url, headers):
        try:
            proxies_requests, proxy_aiohttp = load_proxy()
            response = requests.get(url, headers=headers, proxies=proxies_requests)
            return response
        except RequestException:
            print(f"Проблема с прокси {proxies_requests}. Пропускаем.")
            return None  # или возвращайте какое-либо значение по умолчанию

    async def fetch_url(url, headers):
        response = await asyncio.get_event_loop().run_in_executor(
            None, get_with_proxies, url, headers
        )
        url_home = "https://shop.olekmotocykle.com/"
        if response is not None:
            soup = BeautifulSoup(response.text, "lxml")
            # Создаём пустой список для сохранения ссылок
            img_links = []

            regex_cart = re.compile("product-item.*")

            product_blocks = soup.find_all("div", class_=regex_cart)
            for block in product_blocks:
                # Ищем все изображения в блоке
                a = block.find("a", class_="product-link-ui")
                if a and a.has_attr("href"):
                    img_links.append(f"{url_home}" + a["href"])
            # # for img in soup.find_all('img', alt=lambda x: x and '9' in x):

            #     # Для каждого найденного тега <img> ищем ближайший предшествующий тег <a>.
            #     # Метод find_previous('a') возвращает ближайший выше по коду тег <a>.
            #     a = img.find_previous('a')

            #     # Проверяем, что тег <a> найден (a не является None) и у него есть атрибут 'href'.
            #     if a and 'href' in a.attrs:
            #         # Добавляем в список img_links полную ссылку, состоящую из какой-то базовой части 'url'
            #         # (предполагается, что это какой-то базовый URL, к которому нужно добавить относительную ссылку из 'href'),
            #         # и сами значения 'href' из тега <a>.
            #         img_links.append(f'{url_home}' + a['href'])

            # Возвращаем список ссылок
            return img_links
        else:
            return []

    async def process_category(url, headers, writer, unique_links):
        response = await asyncio.get_event_loop().run_in_executor(
            None, get_with_proxies, url, headers
        )
        soup = BeautifulSoup(response.text, "lxml")
        # Получаем пагинацию
        span_tag = soup.find("span", {"class": "page-amount-ui"})
        data_max_int = int(span_tag.text.split()[1]) if span_tag is not None else 1
        group = url.split("produkty/")[1].split(",")[0]
        tasks = []
        for i in range(1, data_max_int + 1):
            if i == 1:
                img_links = await fetch_url(url, headers)
                for img_link in img_links:
                    if img_link not in unique_links:
                        writer.writerow([img_link])
                        unique_links.add(img_link)
            else:
                tasks.append(fetch_url(f"{url}?pageId={i}", headers))
        if tasks:
            img_links_list = await asyncio.gather(*tasks)
            for img_links in img_links_list:
                for img_link in img_links:
                    if img_link not in unique_links:
                        writer.writerow([img_link])
                        unique_links.add(img_link)

    async def main():
        config = load_config()
        headers = config["headers"]
        filename_category = os.path.join(category_path, "category_product.csv")
        filename_url = os.path.join(category_path, "url.csv")
        with open(filename_category, newline="", encoding="utf-8") as files, open(
            filename_url, "a", newline="", encoding="utf-8"
        ) as f:
            urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
            writer = csv.writer(f)
            tasks = []
            unique_links = set()
            for row in urls:

                url = row[0]
                tasks.append(process_category(url, headers, writer, unique_links))

            await asyncio.gather(*tasks)

    if __name__ == "__main__":
        asyncio.run(main())


coun = 0


def download_html_files():
    import aiohttp
    import asyncio
    import os

    async def fetch(session, url, coun):

        config = load_config()
        headers = config["headers"]
        filename = os.path.join(html_path, f"data_{coun}.html")
        if not os.path.exists(filename):
            proxies_requests, proxy_aiohttp = load_proxy()
            try:
                async with session.get(
                    url, headers=headers, proxy=proxy_aiohttp
                ) as response:
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(await response.text())
            except Exception as e:
                print(f"Ошибка при загрузке {url}: {e}")

    async def main():
        filename = os.path.join(category_path, "url.csv")
        coun = 0
        async with aiohttp.ClientSession() as session:
            with open(filename, newline="", encoding="utf-8") as files:
                urls = list(csv.reader(files, delimiter=" ", quotechar="|"))
                for i in range(0, len(urls), 20):
                    tasks = []
                    for row in urls[i : i + 20]:
                        coun += 1
                        url = row[0]
                        filename_to_check = os.path.join(html_path, f"data_{coun}.html")
                        if not os.path.exists(
                            filename_to_check
                        ):  # Проверка на существование файла
                            tasks.append(fetch(session, url, coun))
                    if tasks:
                        await asyncio.gather(*tasks)
                        print(f"Completed {coun} requests")
                        await asyncio.sleep(1)

    # import aiohttp
    # import asyncio
    # from pathlib import Path
    # import csv
    # import os
    # import random

    # config = load_config()
    # headers = config["headers"]
    # current_directory = os.getcwd()
    # # Создайте полный путь к папке temp
    # temp_path = os.path.join(current_directory, "temp")
    # html_path = os.path.join(temp_path, "html")
    # category_path = os.path.join(temp_path, "category")

    # def get_next_file_number(html_path):
    #     # Получаем список всех файлов в формате 'data_{номер}.html'
    #     files = glob.glob(f"{html_path}/data_*.html")
    #     max_num = 0
    #     for file in files:
    #         # Ищем номер в имени каждого файла
    #         match = re.search(r"data_(\d+).html", file)
    #         if match:
    #             num = int(match.group(1))
    #             if num > max_num:
    #                 max_num = num
    #     return max_num + 1  # Возвращаем следующий номер

    # async def fetch(session, url, coun, max_count, html_path):
    #     if coun >= max_count:
    #         print("Достигнуто максимальное количество файлов.")
    #         return  # Прекратить выполнение, если достигли лимита

    #     filename_html = os.path.join(html_path, f"data_{coun}.html")
    #     if not os.path.exists(filename_html):
    #         try:
    #             proxies_requests, proxy_aiohttp = load_proxy()
    #             async with session.get(url, headers=headers, proxy=proxy_aiohttp) as response:
    #                 content = await response.text()
    #                 with open(filename_html, "w", encoding="utf-8") as file:
    #                     file.write(content)
    #         except Exception as e:
    #             print(f"Ошибка при загрузке {url}: {e}")

    # async def main():
    #     filename_url = os.path.join(category_path, "url.csv")
    #     global coun
    #     coun = get_next_file_number(html_path)

    #     async with aiohttp.ClientSession() as session:
    #         with open(filename_url, 'r', encoding='utf-8') as file:
    #             url_count = sum(1 for row in csv.reader(file))

    #         coun = get_next_file_number(html_path)
    #         max_count = coun + url_count  # Максимальное количество файлов равно текущему количеству файлов плюс количество URL

    #         async with aiohttp.ClientSession() as session:
    #             with open(filename_url, 'r', newline='', encoding='utf-8') as file:
    #                 urls = list(csv.reader(file))
    #                 for i in range(0, len(urls), 5):  # Обрабатываем URL по 5 штук
    #                     tasks = []
    #                     for row in urls[i:i + 5]:
    #                         url = row[0]
    #                         if coun >= max_count:
    #                             break  # Прекратить создание новых задач, если достигнут лимит
    #                         tasks.append(fetch(session, url, coun, max_count, html_path))
    #                         coun += 1

    #                     if tasks:
    #                         await asyncio.gather(*tasks)
    #                         print(f"Completed {coun} requests")
    #                     await asyncio.sleep(5)  # Пауза после каждого пакета из 5 URL

    #                     if coun >= max_count:
    #                         break  # Выход из цикла, если обработаны все URL или достигнут лимит

    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())


def delete_dublicate():
    # Загрузка данных из CSV файла
    filename_url = os.path.join(category_path, "url.csv")
    filename_url_new = os.path.join(category_path, "url_new.csv")
    # Загрузка и удаление дубликатов
    df = pd.read_csv(filename_url, header=None, delimiter=",", dtype=str)
    df.drop_duplicates(inplace=True)

    # Преобразование DataFrame в строку без кавычек и запись в файл
    df.to_csv(
        filename_url, index=False, header=False, quoting=csv.QUOTE_NONE, escapechar="\\"
    )
    # Открытие файла для записи
    with open(filename_url, "w", newline="", encoding="utf-8") as file:
        for url in df[0]:
            file.write(url + "\n")

    # with open("url.csv", "w", newline='', encoding='utf-8') as file:
    #     writer = csv.writer(file, quoting=csv.QUOTE_NONE, escapechar='\\')
    #     for row in df.itertuples(index=False, name=None):
    #         writer.writerow(row)


def parsing_product():
    folder = os.path.join(html_path, "*.html")

    files_html = glob.glob(folder)

    data = []
    filename_to_csv_output = os.path.join(current_directory, "output.csv")
    with open(filename_to_csv_output, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file, delimiter=";")
        writer.writerow(
            [
                "id_product",
                "name",
                "brandName",
                "gtin",
                "brutto_price",
                "netto_price",
                "magazyn_główny",
            ]
        )
        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            script_tag = soup.find("script", {"id": "datablock1"})
            try:
                json_content = (
                    script_tag.contents[0].strip().replace("},\n}\n}", "}\n}\n}")
                )
            except Exception as e:
                print(f"Ошибка при обработке содержимого тега script: {item}")

            try:
                # Экранирование всех недопустимых последовательностей обратного слэша.
                json_content = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", json_content)
                data = json.loads(json_content)
            except json.JSONDecodeError as e:
                print(f"Ошибка {item} обработке JSON: {e}")

            id_product_element = soup.find(
                "div", {"class": "product-code-ui product-code-lq"}
            )
            if id_product_element is not None:
                id_product = id_product_element.get_text()
            else:
                id_product = None
            name = data["itemOffered"]["productName"][0]["@value"]
            brandName = data["itemOffered"]["brand"]["brandName"][0]["@value"]
            gtin = data["itemOffered"]["gtin"]
            brutto_price_element = soup.find("div", {"class": "brutto-price-ui"})
            if brutto_price_element is not None:
                brutto_price = (
                    brutto_price_element.get_text()
                    .strip()
                    .replace(" PLN", "")
                    .replace("\nbrutto", "")
                )
            else:
                brutto_price = None

            netto_price_element = soup.find("div", {"class": "netto-price-ui"})
            if netto_price_element is not None:
                netto_price = (
                    netto_price_element.get_text()
                    .strip()
                    .replace(" PLN", "")
                    .replace("\nnetto", "")
                )
            else:
                netto_price = None
            try:
                product_blocks = soup.find(
                    "div", class_=re.compile("stock-ui no-on-mobile.*")
                )
                in_stock = product_blocks.find("img").get("alt")
                if in_stock != "niedostępny":
                    main_storehouse = 9
                else:
                    main_storehouse = 0
            except:
                main_storehouse = None

            writer.writerow(
                [
                    id_product,
                    name,
                    brandName,
                    gtin,
                    brutto_price,
                    netto_price,
                    main_storehouse,
                ]
            )
            # div = soup.find_all("div", {"class": "lazyslider-container-lq"})[0]
            # imgs = div.find_all("img", {"class": "open-gallery-lq"})
            #
            # urls_photo = []
            # for img in imgs:
            #     urls_photo.append('https://' + img["data-src"].replace("//", ""))
            #
            # coun = 0
            # file_path_1 = f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}.jpg'
            # file_path_2 = f'c:\\Data_olekmotocykle\\img\\{id_product.replace("/", "_")}_{coun}.jpg'
            # for u in urls_photo:
            #     """Настройка прокси серверов случайных"""
            #     proxy = random.choice(proxies)
            #     proxy_host = proxy[0]
            #     proxy_port = proxy[1]
            #     proxy_user = proxy[2]
            #     proxy_pass = proxy[3]
            #
            #     proxi = {
            #         'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
            #         'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            #     }
            #     coun += 1
            #     if len(urls_photo) == 1:
            #         if not os.path.exists(file_path_1):
            #             try:
            #                 img_data = requests.get(u, headers=header, proxies=proxi)
            #                 with open(file_path_1, 'wb') as file_img:
            #                     file_img.write(img_data.content)
            #             except:
            #                 print(f"Ошибка при выполнении запроса для URL: {u}")
            #                 continue
            #     elif len(urls_photo) > 1:
            #         if not os.path.exists(file_path_2):
            #             img_data = requests.get(u, headers=header, proxies=proxi)
            #             with open(file_path_2, 'wb') as file_img:
            #                 file_img.write(img_data.content)


def csv_to_excell():
    filename_to_csv_output = os.path.join(current_directory, "output.csv")
    filename_csv_to_xlsx = os.path.join(current_directory, "output.xlsx")
    data = pd.read_csv(filename_to_csv_output, encoding="utf-8", delimiter=";")

    # Сохранение данных в файл XLSX
    data.to_excel(filename_csv_to_xlsx, index=False, engine="openpyxl")


# if __name__ == "__main__":
# load_proxy()
# create_folders()
# print("Собираем категории товаров")
# parsing_url_category_in_html()
# print("Скачиваем все ссылки")
# main_download_url()
# delete_dublicate()
# download_html_files()
# parsing_product()
# csv_to_excell()
# delete_old_data()


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
        print("Собираем категории товаров")
        parsing_url_category_in_html()
        print("Скачиваем все ссылки")
        main_download_url()
        delete_dublicate()
        print("Переходим к пункту 2")
    elif user_input == 2:
        download_html_files()
        print("Переходим к пункту 3")
    elif user_input == 3:
        parsing_product()
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
