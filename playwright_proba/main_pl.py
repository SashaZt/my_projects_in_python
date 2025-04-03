# import asyncio
# import json
# import aiofiles
# from playwright.async_api import async_playwright
# import time
# import glob
# import os
# from datetime import datetime
# from selectolax.parser import HTMLParser

# import re

# current_directory = os.getcwd()
# temp_path = os.path.join(current_directory, "temp")
# all_hotels = os.path.join(temp_path, "all_hotels")
# hotel_path = os.path.join(temp_path, "hotel")

# # Создание директории, если она не существует
# os.makedirs(temp_path, exist_ok=True)
# os.makedirs(all_hotels, exist_ok=True)
# os.makedirs(hotel_path, exist_ok=True)


# async def save_response_json(json_response, url_name):
#     """Асинхронно сохраняет JSON-данные в файл."""
#     filename = os.path.join(hotel_path, f"{url_name}.json")
#     async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
#         await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


# # async def save_page_content_html(page, file_path):

# #     content = await page.content()
# #     async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
# #         await f.write(content)


# # async def main():
# #     now = datetime.now()
# #     time_start = now.strftime("%H:%M:%S")
# #     timeout_selector = 60000

# #     async with async_playwright() as playwright:
# #         browser = await playwright.chromium.launch(headless=False)
# #         context = await browser.new_context()
# #         page = await context.new_page()

# #         # Читаем данные из JSON файла
# #         output_path = os.path.join(current_directory, "all_href.json")
# #         with open(output_path, "r", encoding="utf-8") as json_file:
# #             all_href = json.load(json_file)

# #         all_data = []

# #         # Функция для извлечения текста по селектору
# #         def get_text(element):
# #             return (
# #                 element.text().replace(" \n", "").replace("\n", "").strip()
# #                 if element is not None
# #                 else None
# #             )

# #         # Функция для добавления значений в словарь
# #         def add_to_dict(d, key, value):
# #             if key in d:
# #                 d[key] += f"; {value}"
# #             else:
# #                 d[key] = value

# #         for href in all_href:
# #             await page.goto(href, wait_until="load", timeout=60000)
# #             await asyncio.sleep(1)
# #             content = await page.content()

# #             parser = HTMLParser(content)

# #             # Извлечение всех p-тегов, находящихся в нужных div-блоках
# #             paragraphs = parser.css("div > div > div > div > p")

# #             data = [get_text(p) for p in paragraphs]

# #             # Создание словаря из данных
# #             data_dict = {}
# #             name_company_element = parser.css_first("div.page-header.clearfix > h1")
# #             name_company = get_text(name_company_element)

# #             if name_company:
# #                 data_dict["Company Name"] = name_company

# #             for entry in data:
# #                 if ":" in entry:
# #                     key, value = entry.split(":", 1)
# #                     key = key.strip()
# #                     value = value.strip()
# #                 elif entry.lower().startswith("ph") or entry.lower().startswith(
# #                     "phone"
# #                 ):
# #                     key = "Phone"
# #                     value = entry.split(" ", 1)[1].strip()
# #                 else:
# #                     continue

# #                 add_to_dict(data_dict, key, value)

# #             all_data.append(data_dict)

# #         # Запись всех данных в JSON файл
# #         output_path = os.path.join(current_directory, "all_data.json")
# #         with open(output_path, "w", encoding="utf-8") as json_file:
# #             json.dump(all_data, json_file, ensure_ascii=False, indent=4)

# #         # url_row = href.split("/")[-1]
# #         # url_name = url_row.replace("-", "_")
# #         # if len(url_name) > max_length:
# #         #     url_name = url_name[:max_length]
# #         # filename = f"{url_name}.html"
# #         # file_path = os.path.join(hotel_path, filename)
# #         # if not os.path.exists(file_path):

# #         #     await asyncio.sleep(1)
# #         #     await save_page_content_html(page, file_path)
# #         # else:
# #         #     filename = f"{url_name}_.html"
# #         #     file_path = os.path.join(hotel_path, filename)
# #         #     await page.goto(href, wait_until="load", timeout=60000)

# #         #     await save_page_content_html(page, file_path)

# #         # try:
# #         #     await page.wait_for_selector(
# #         #         "button#onetrust-accept-btn-handler", timeout=10000
# #         #     )
# #         #     accept_button = await page.query_selector(
# #         #         "button#onetrust-accept-btn-handler"
# #         #     )

# #         #     if accept_button:
# #         #         await accept_button.click()
# #         #         await asyncio.sleep(1)
# #         #         await save_page_content_html(page, file_path)
# #         #     else:
# #         #         print("Accept button not found")
# #         # except Exception as e:
# #         #     print(f"An error occurred: {e}")

# #         # Для сохранения json файла
# #         # handler = create_log_response_with_counter(url_name)
# #         # page.on("response", handler)
# #         # await asyncio.sleep(1)
# #         # await browser.close()
# #         # now = datetime.now()
# #         # time_now = now.strftime("%H:%M:%S")
# #         now = datetime.now()
# #         time_stop = now.strftime("%H:%M:%S")
# #         print(time_stop)
# #     # # Здесь нажимаем кнопку cookies
# #     # button_cookies = '//button[@class="r-button r-button--accent r-button--hover r-button--contained r-button--only-text r-button--svg-margin-left r-consent-buttons__button cmpboxbtnyes"]'
# #     # await page.wait_for_selector(button_cookies, timeout=timeout_selector)
# #     # cookies_button = await page.query_selector(button_cookies)
# #     # if cookies_button:
# #     #     # Кликаем по кнопке "Следующая", если она найдена
# #     #     await cookies_button.click()

# #     # # Дождитесь загрузки страницы и элементов
# #     # await page.wait_for_selector(
# #     #     '//button[@class="r-select-button r-select-button-termin"]',
# #     #     timeout=timeout_selector,
# #     # )
# #     # termin_element = '//button[@class="r-select-button r-select-button-termin"]'
# #     # # Найдите все элементы по селектору
# #     # await page.wait_for_selector(termin_element, timeout=timeout_selector)
# #     # element_termin = await page.query_selector(termin_element)
# #     # # Проверка наличия элементов перед извлечением текста
# #     # # await asyncio.sleep(5)
# #     # if element_termin:
# #     #     await element_termin.click()
# #     # else:
# #     #     print("Элементы не найдены")
# #     # list_element = '//button[@class="r-tab"]'
# #     # # Найдите все элементы по селектору
# #     # await page.wait_for_selector(list_element, timeout=timeout_selector)
# #     # element_list = await page.query_selector(list_element)
# #     # # Проверка наличия элементов перед извлечением текста
# #     # # await asyncio.sleep(5)
# #     # if element_list:
# #     #     await element_list.click()
# #     # else:
# #     #     print("Элементы не найдены")
# #     # try:
# #     #     list_item = '//div[@class="kh-terminy-list__item"]'
# #     # except:
# #     #     list_item = (
# #     #         '//div[@class="kh-terminy-list__item kh-terminy-list__item--active"]'
# #     #     )
# #     # await page.wait_for_selector(list_item, timeout=timeout_selector)
# #     # item_list = await page.query_selector_all(list_item)
# #     # # Проверка наличия элементов перед извлечением текста
# #     # # await asyncio.sleep(5)
# #     # if item_list:
# #     #     await item_list[0].click()
# #     # else:
# #     #     print("Элементы не найдены")

# #     # # Итерация по страницам


# def parsing_num():
#     # Указываем путь к папке с файлами
#     folder = os.path.join(hotel_path, "*.html")
#     files_html = glob.glob(folder)

#     # Функция для извлечения текста по селектору
#     def get_text(element):
#         return (
#             element.text().replace(" \n", "").replace("\n", "").strip()
#             if element is not None
#             else None
#         )

#     # Функция для добавления значений в словарь
#     def add_to_dict(d, key, value):
#         if key in d:
#             d[key] += f"; {value}"
#         else:
#             d[key] = value

#     all_data = []
#     # Проходим по всем HTML файлам в папке
#     for item in files_html:
#         with open(item, encoding="utf-8") as file:
#             src = file.read()

#         parser = HTMLParser(src)

#         # Извлечение всех p-тегов, находящихся в нужных div-блоках
#         paragraphs = parser.css("div > div > div > div > p")

#         data = [get_text(p) for p in paragraphs]

#         # Создание словаря из данных
#         data_dict = {}
#         for entry in data:
#             if ":" in entry:
#                 key, value = entry.split(":", 1)
#                 key = key.strip()
#                 value = value.strip()
#             elif entry.lower().startswith("ph") or entry.lower().startswith("phone"):
#                 key = "Phone"
#                 value = entry.split(" ", 1)[1].strip()
#             else:
#                 continue

#             add_to_dict(data_dict, key, value)

#         all_data.append(data_dict)

#     # Запись всех данных в JSON файл
#     output_path = os.path.join(current_directory, "all_data.json")
#     with open(output_path, "w", encoding="utf-8") as json_file:
#         json.dump(all_data, json_file, ensure_ascii=False, indent=4)

#         # Печать словаря данных
#         # # Извлекаем данные
#         # data = {
#         #     "name_company": name_company,
#         #     "LEI code": extract_text_by_strong(info_company_node, "LEI code"),
#         #     "Registration code": extract_text_by_strong(
#         #         info_company_node, "Registration code"
#         #     ),
#         #     "Category": (
#         #         info_company_node.css_first(
#         #             'p:has(strong:contains("Category")) a'
#         #         ).text()
#         #         if info_company_node.css_first('p:has(strong:contains("Category")) a')
#         #         else None
#         #     ),
#         #     "Country": extract_text_by_strong(info_company_node, "Country"),
#         #     "Address": extract_text_by_strong(info_company_node, "Address"),
#         #     "Correspondence address": extract_text_by_strong(
#         #         info_company_node, "Correspondence address"
#         #     ),
#         #     "Email address": (
#         #         info_company_node.css_first(
#         #             'p:has(strong:contains("Email address")) a'
#         #         ).text()
#         #         if info_company_node.css_first(
#         #             'p:has(strong:contains("Email address")) a'
#         #         )
#         #         else None
#         #     ),
#         #     "Phone": (
#         #         info_company_node.css_first('p:contains("Ph.")')
#         #         .text()
#         #         .replace("Ph.", "")
#         #         .strip()
#         #         if info_company_node.css_first('p:contains("Ph.")')
#         #         else None
#         #     ),
#         # }

#         # print(data)

#         # # Ищем ссылки в первых 100 строках таблицы
#         # for i in range(1, 101):
#         #     selector = f"div.table-responsive > table > tbody > tr:nth-child({i}) > td:nth-child(1) a"
#         #     for node in parser.css(selector):
#         #         href = node.attributes.get("href").replace("//www", "www")
#         #         if href:
#         #             all_href.append(href)

#     # # Записываем найденные ссылки в JSON файл


# # Функция для извлечения текста по тегу <strong>
# def extract_text_by_label(node, label):
#     element = node.css_first(f'p:has(strong:contains("{label}"))')
#     if element:
#         text = element.text().replace(f"{label}:", "").strip()
#         # Проверка на наличие вложенного тега <a>
#         link = element.css_first("a")
#         if link:
#             text = link.text().strip()
#         return text
#     return None


# def remove_duplicates():
#     current_directory = os.path.dirname(os.path.abspath(__file__))
#     input_path = os.path.join(current_directory, "all_data.json")

#     # Загрузка данных из JSON файла
#     with open(input_path, "r", encoding="utf-8") as json_file:
#         all_data = json.load(json_file)

#     unique_data = {}

#     # Функция для создания уникального ключа
#     def create_unique_key(entry):
#         if "Registration code" in entry:
#             return entry["Registration code"]
#         elif "LEI code" in entry:
#             return entry["LEI code"]
#         return None

#     # Проход по всем элементам и удаление дубликатов
#     for entry in all_data:
#         unique_key = create_unique_key(entry)
#         if unique_key:
#             unique_data[unique_key] = entry

#     # Получение списка уникальных записей
#     unique_data_list = list(unique_data.values())

#     # Запись уникальных данных обратно в JSON файл
#     with open(input_path, "w", encoding="utf-8") as json_file:
#         json.dump(unique_data_list, json_file, ensure_ascii=False, indent=4)


# async def save_page_content_html(page, file_path):
#     content = await page.content()
#     async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
#         await f.write(content)


# def extract_product_ids(file_path):
#     product_ids = []
#     with open(file_path, "r") as file:
#         for line in file:
#             url = line.strip()
#             match = re.search(r"ObjectID=(\d+)", url)
#             if match:
#                 product_ids.append(match.group(1))
#     return product_ids


# async def main():
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=False)
#         context = await browser.new_context()
#         page = await context.new_page()
#         file_path = "url_product.txt"
#         product_ids = extract_product_ids(file_path)

#         for product_id in product_ids:
#             url = f"https://catalog.weidmueller.com/catalog/Start.do?localeId=ru&ObjectID={product_id}"
#             await page.goto(url)
#             save_path = os.path.join(all_hotels, f"{product_id}.html")
#             await asyncio.sleep(1)
#             await save_page_content_html(page, save_path)

#         await browser.close()


# def parsing_content():
#     file_path = os.path.join(hotel_path, "html.html")
#     with open(file_path, encoding="utf-8") as file:
#         src = file.read()

#         parser = HTMLParser(src)

#         # Извлечение всех p-тегов, находящихся в нужных div-блоках
#         name_extension = parser.css_first(
#             "#yDmH0d > c-wiz:nth-child(29) > div > div > main > div > section.VWBXhd > section > div.dSsD7e > a > h1"
#         )
#         print(name_extension)

# import asyncio
# from playwright.async_api import async_playwright

# async def run(playwright):
#     # Указываем настройки прокси
#     proxy = {
#         "server": "http://proxy-server.scraperapi.com:8001",
#         "username": "scraperapi",
#         "password": "5edddbdddb89aed6e9d529c4ff127e8f"
#     }

#     # Запускаем браузер с использованием прокси
#     browser = await playwright.chromium.launch(headless=False, proxy=proxy)
#     context = await browser.new_context()
#     page = await context.new_page()

#     # Переходим на URL
#     url = "https://example.com"  # Замените на нужный вам URL
#     await page.goto(url)

#     # Ожидаем 5 секунд
#     await asyncio.sleep(5)

#     # Сохраняем содержимое страницы в HTML-файл
#     html_content = await page.content()
#     with open("page_content.html", "w", encoding="utf-8") as file:
#         file.write(html_content)

#     # Закрываем браузер
#     await browser.close()

# async def main():
#     async with async_playwright() as playwright:
#         await run(playwright)

# # Запуск основной функции
# asyncio.run(main())


# if __name__ == "__main__":
#     # parsing_num()
#     # remove_duplicates()
#     # url = "https://catalog.weidmueller.com/catalog/Start.do?localeId=ru&ObjectID=1021000000"
#     # asyncio.run(main())
#     # parsing_content()


import asyncio
import csv
import re
from pathlib import Path

from playwright.async_api import async_playwright

current_directory = Path.cwd()
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def get_urls_from_csv(file_path):
    """
    Читает CSV файл и возвращает список URL.

    Args:
        file_path (str): Путь к файлу CSV.

    Returns:
        list: Список URL из CSV файла.
    """
    urls = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if "url" in row:  # Убедимся, что есть столбец 'url'
                    urls.append(row["url"])
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

    return urls


def format_url(url):
    """
    Преобразует URL в формат: 'migueldefelipedelacuerda_4401',
    удаляя специальные символы и заменяя их на подчеркивания.

    Args:
        url (str): URL в виде строки.

    Returns:
        str: Преобразованный формат строки.
    """
    # Извлекаем последний сегмент пути из URL
    last_segment = url.rstrip("/").split("/")[-1]

    # Удаляем расширения файлов (если есть)
    last_segment = re.sub(r"\.[a-zA-Z0-9]+$", "", last_segment)

    # Заменяем все небуквенно-цифровые символы на подчеркивания
    formatted = re.sub(r"[^a-zA-Z0-9]", "_", last_segment)

    # Убираем лишние подряд идущие подчеркивания
    formatted = re.sub(r"_+", "_", formatted)

    # Удаляем подчеркивания в начале и конце строки
    formatted = formatted.strip("_")

    return formatted


# async def run(playwright):
#     # Указываем настройки прокси одной строкой
#     # proxy_url = "http://scraperapi:5edddbdddb89aed6e9d529c4ff127e8f@proxy-server.scraperapi.com:8001"
#     # proxy = {"server": proxy_url}

#     # Запускаем браузер
#     browser = await playwright.chromium.launch(headless=False)
#     context = await browser.new_context(
#         bypass_csp=True,
#         java_script_enabled=True,
#         permissions=["geolocation"],
#         device_scale_factor=1.0,
#         has_touch=True,
#         ignore_https_errors=True,
#     )
#     page = await context.new_page()
#     urls = get_urls_from_csv("extracted_urls.csv")

#     # # Отключаем загрузку изображений, шрифтов и других медиафайлов
#     # await context.route(
#     #     "**/*",
#     #     lambda route, request: (
#     #         route.abort()
#     #         if request.resource_type in ["image", "media", "font", "stylesheet"]
#     #         else route.continue_()
#     #     ),
#     # )

#     # Переходим на URL
#     url = "https://feepyf.com/entrenadores/barcelona/all"
#     await page.goto(url)
#     # for i in range(1, 22):
#     #     url = f"https://feepyf.com/entrenadores/barcelona/all/pagina{i}"
#     #     await page.goto(url)
#     #     # Ждем завершения всех сетевых запросов
#     #     await page.wait_for_load_state("networkidle")
#     #     output_file = current_directory / f"Page_0{i}.html"
#     #     html_content = await page.content()
#     #     with open(output_file, "w", encoding="utf-8") as file:
#     #         file.write(html_content)

#     # Ходим по ссылкам
#     for url in urls:
#         output_file = html_directory / f"{format_url(url)}.html"

#         if output_file.exists():
#             continue
#         await page.goto(url)
#         # Ждем завершения всех сетевых запросов
#         await page.wait_for_load_state("networkidle")

#         # Ожидаем начальную загрузку
#         # await asyncio.sleep(30)
#         html_content = await page.content()
#         with open(output_file, "w", encoding="utf-8") as file:
#             file.write(html_content)
#     # Клик по whatsapp_cont

#     # while True:
#     #     # Находим текущую страницу
#     #     current_page_element = await page.locator(
#     #         '//li[@aria-current="page"]'
#     #     ).element_handle()
#     #     if not current_page_element:
#     #         print("Не удалось найти текущую страницу.")
#     #         break
#     #     # Извлекаем номер текущей страницы
#     #     aria_label = await current_page_element.get_attribute("aria-label")
#     #     number_page = int(aria_label.split()[-1].strip())
#     # html_content = await page.content()
#     # with open(f"page_content{number_page}.html", "w", encoding="utf-8") as file:
#     #     file.write(html_content)
#     #     print(f"Текущая страница: {number_page}")
#     #     # Находим кнопку "Next page"
#     #     next_button = await page.locator(
#     #         '//button[@aria-label="Next page"]'
#     #     ).element_handle()
#     #     if not next_button:
#     #         print("Кнопка 'Next page' не найдена. Конец.")
#     #         break

#     #     # Кликаем по кнопке "Next page" и ждем загрузки
#     #     await next_button.click()
#     #     await asyncio.sleep(1)  # Пауза для загрузки страницы

#     # # Нажимаем на кнопку "Next" и ждем загрузки
#     # for i in range(1, 11):
#     #     # Сохраняем содержимое страницы в HTML-файл
#     #     html_content = await page.content()
#     #     with open(f"page_content{i}.html", "w", encoding="utf-8") as file:
#     #         file.write(html_content)

#     #     # Проверяем наличие кнопки "Next"
#     #     next_button = page.locator("//span[@class='sr-only' and text()='Next']")
#     #     if await next_button.is_visible():
#     #         # Нажимаем на родительский элемент кнопки "Next"
#     #         await next_button.locator("..").click()

#     #         # Ждем завершения загрузки страницы
#     #         await page.wait_for_load_state("networkidle")
#     #     else:
#     #         print("Next button not found.")
#     #         break

#     # Закрываем браузер
#     await browser.close()


async def run(playwright):
    # Указываем настройки прокси одной строкой
    # proxy_url = "http://scraperapi:5edddbdddb89aed6e9d529c4ff127e8f@proxy-server.scraperapi.com:8001"
    # proxy = {"server": proxy_url}

    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()
    urls = get_urls_from_csv("extracted_urls.csv")

    # # Отключаем загрузку изображений, шрифтов и других медиафайлов
    # await context.route(
    #     "**/*",
    #     lambda route, request: (
    #         route.abort()
    #         if request.resource_type in ["image", "media", "font", "stylesheet"]
    #         else route.continue_()
    #     ),
    # )

    # Переходим на URL
    url = "https://zenmoney.app/share/account/h5Hml5SciJzYErESWYsAzXkRHwsF6j/"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(30)  # Пауза
    output_file = current_directory / "Page_01.html"
    html_content = await page.content()
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(html_content)
    # count = 1
    # while True:
    #     try:
    #         # Ждём появления элемента с таймаутом (например, 5 секунд)
    #         await page.wait_for_selector(
    #             "#ContentPlaceHolder1_imgNextPage", timeout=5000
    #         )
    #         await page.wait_for_load_state("networkidle")

    #         # Если элемент найден, кликаем
    #         await page.click("#ContentPlaceHolder1_imgNextPage")
    #         count += 1
    #         output_file = current_directory / f"Page_0{count}.html"
    #         html_content = await page.content()
    #         with open(output_file, "w", encoding="utf-8") as file:
    #             file.write(html_content)

    #         print("Clicked on #ContentPlaceHolder1_imgNextPage")
    #     except:
    #         # Если элемент не найден, выходим из цикла
    #         print(
    #             "Element #ContentPlaceHolder1_imgNextPage no longer present. Stopping."
    #         )
    #         break
    await browser.close()

    # for i in range(1, 22):
    #     await page.goto(url)
    #     # Ждем завершения всех сетевых запросов
    #     await page.wait_for_load_state("networkidle")
    #     output_file = current_directory / f"Page_0{i}.html"
    #     html_content = await page.content()
    #     with open(output_file, "w", encoding="utf-8") as file:
    #         file.write(html_content)

    # # Ждем завершения всех сетевых запросов
    # # await page.wait_for_load_state("networkidle")
    # await asyncio.sleep(5)  # Пауза для загрузки страницы
    # print("Страница загружена")

    # # Ищем и нажимаем элемент с текстом "Sign In Midasbuy Account"
    # sign_in_button = page.locator(
    #     "div.Button_icon_text__C-ysi:has-text('Sign In Midasbuy Account')"
    # )
    # if await sign_in_button.is_visible():
    #     print("Кнопка 'Sign In Midasbuy Account' найдена, нажимаем")
    #     await sign_in_button.click()
    # else:
    #     print("Ошибка: Кнопка 'Sign In Midasbuy Account' не найдена")
    #     return
    # await asyncio.sleep(5)  # Пауза
    # # Переходим к iframe
    # iframe = page.frame(name="iframe-window")
    # if not iframe:
    #     print("Ошибка: iframe не найден")
    #     return
    # await asyncio.sleep(5)  # Пауза
    # # Ждем появления поля для ввода email
    # email_input = iframe.locator(
    #     "input[placeholder='Enter email to sign in or sign up'][type='email'][autocomplete='username']"
    # )
    # await email_input.wait_for()

    # # Вводим email
    # await email_input.fill("testmidass@gmail.com")  # Замените на ваш email
    # print("Email введен")
    # await asyncio.sleep(5)  # Пауза

    # # Нажимаем кнопку "Continue"
    # continue_button = page.locator(".btn.comfirm-btn:has-text('Continue')")
    # if await continue_button.is_visible():
    #     print("Кнопка 'Continue' найдена, нажимаем")
    #     await continue_button.click()
    # else:
    #     print("Ошибка: Кнопка 'Continue' не найдена")
    #     return
    # await asyncio.sleep(5)  # Пауза

    # # Ждем появления поля для ввода пароля
    # password_input = page.locator("input[type='password']")
    # await password_input.wait_for()
    # await asyncio.sleep(5)  # Пауза
    # print("Поле для ввода пароля найдено")

    # # Вводим пароль
    # await password_input.fill("xebgyd-cabnag-xoXba6")  # Замените на ваш пароль
    # print("Пароль введен")

    # # Устанавливаем чекбокс
    # checkbox = page.locator("svg[viewBox='0 0 16 16']")
    # if await checkbox.is_visible():
    #     print("Чекбокс найден, устанавливаем")
    #     await checkbox.click()
    # else:
    #     print("Ошибка: Чекбокс не найден")
    #     return
    # await asyncio.sleep(5)  # Пауза

    # # Нажимаем кнопку "SIGN IN"
    # sign_in_button = page.locator(".btn.comfirm-btn:has-text('SIGN IN')")
    # if await sign_in_button.is_visible():
    #     print("Кнопка 'SIGN IN' найдена, нажимаем")
    #     await sign_in_button.click()
    # else:
    #     print("Ошибка: Кнопка 'SIGN IN' не найдена")
    #     return

    # # Пауза на 30 секунд
    # await asyncio.sleep(30)
    # print("Авторизация завершена, закрываем браузер")

    # # Закрываем браузер
    # await browser.close()

    # # Ожидhtml_content)
    # Клик по whatsapp_cont

    # while True:
    #     # Находим текущую страницу
    #     current_page_element = await page.locator(
    #         '//li[@aria-current="page"]'
    #     ).element_handle()
    #     if not current_page_element:
    #         print("Не удалось найти текущую страницу.")
    #         break
    #     # Извлекаем номер текущей страницы
    #     aria_label = await current_page_element.get_attribute("aria-label")
    #     number_page = int(aria_label.split()[-1].strip())
    # html_content = await page.content()
    # with open(f"page_content{number_page}.html", "w", encoding="utf-8") as file:
    #     file.write(html_content)
    #     print(f"Текущая страница: {number_page}")
    #     # Находим кнопку "Next page"
    #     next_button = await page.locator(
    #         '//button[@aria-label="Next page"]'
    #     ).element_handle()
    #     if not next_button:
    #         print("Кнопка 'Next page' не найдена. Конец.")
    #         break

    #     # Кликаем по кнопке "Next page" и ждем загрузки
    #     await next_button.click()
    #     await asyncio.sleep(1)  # Пауза для загрузки страницы

    # # Нажимаем на кнопку "Next" и ждем загрузки
    # for i in range(1, 11):
    #     # Сохраняем содержимое страницы в HTML-файл
    #     html_content = await page.content()
    #     with open(f"page_content{i}.html", "w", encoding="utf-8") as file:
    #         file.write(html_content)

    #     # Проверяем наличие кнопки "Next"
    #     next_button = page.locator("//span[@class='sr-only' and text()='Next']")
    #     if await next_button.is_visible():
    #         # Нажимаем на родительский элемент кнопки "Next"
    #         await next_button.locator("..").click()

    #         # Ждем завершения загрузки страницы
    #         await page.wait_for_load_state("networkidle")
    #     else:
    #         print("Next button not found.")
    #         break


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


# Запуск основной функции
asyncio.run(main())
