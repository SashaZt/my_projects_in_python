import asyncio
from math import e
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
import string
import csv

import os
import glob
from asyncio import sleep


async def download_file(session, url, cookies_dict, filename_pdf):
    headers = {
        "authority": "www.assessedvalues2.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'ASP.NET_SessionId=w1lubbprygi3wq5hdfiwa0tl; CookieTest=Testme; sucuri_cloudproxy_uuid_0766875d6=399c6876557455524af4b491910baaac; SearchList2=; SearchList3=; SearchList=000101',
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://www.assessedvalues2.com/SearchPage.aspx?jurcode=112",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    async with session.get(url, headers=headers, cookies=cookies_dict) as response:
        if response.status == 200:
            async with aiofiles.open(filename_pdf, "wb") as out_file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await out_file.write(chunk)
        else:
            print(f"Ошибка при загрузке файла: {response.status}")
async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)

async def run():
    # Создайте полный путь к папке temp
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    csv_path = os.path.join(temp_path, "csv")
    html_path = os.path.join(temp_path, "html")
    # Убедитесь, что папки существуют или создайте их
    await create_directories_async(
        [
            temp_path,
            csv_path,
            html_path,
        ]
    )
    url_start = 'https://mapublicaccess.tylerhost.net/search/CommonSearch.aspx?mode=ADDRESS'
    print("Введите начальную букву улицы")
    inpStreet = str(input())
    inpStreet = 'A'
    print("Введите юрисдикцию, MA199 - как пример")
    inpCity = str(input())
    inpCity = 'MA199'
    
    # print("Введите диапозон поиска по кодам, до")
    # range_b = int(input())
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    pdf_path = os.path.join(temp_path, "pdf")
    # Убедитесь, что папки существуют или создайте их
    for folder in [
        temp_path,
        pdf_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    timeout = 3000
    current_directory = os.getcwd()
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    async with async_playwright() as playwright, aiohttp.ClientSession() as session:
        browser = await playwright.chromium.launch(
            headless=False
        )  # Для отладки можно использовать headless=False
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(url_start)
        await sleep(1)
        parcel_set = set()
        for num in range(10):
            xpath_inpNumber = '//input[@id="inpNumber"]'
            await page.wait_for_selector(f"xpath={xpath_inpNumber}", timeout=timeout)
            await page.fill(xpath_inpNumber, str(num))

            xpath_inpStreet = '//input[@id="inpStreet"]'
            await page.wait_for_selector(f"xpath={xpath_inpStreet}", timeout=timeout)
            await page.fill(xpath_inpStreet, str(inpStreet))

            
            xpath_inpCity = '//select[@id="inpCity"]'
            await page.wait_for_selector(f"xpath={xpath_inpCity}", timeout=timeout)
            await page.select_option(f"xpath={xpath_inpCity}", 'MA199')
            # await sleep(5)
            
            """Нажимаем кнопку поиска"""
            xpath_btSearch = '//button[@id="btSearch"]'
            await page.wait_for_selector(f"xpath={xpath_btSearch}", timeout=timeout)
            await page.click(xpath_btSearch)
            # await sleep(5)
        
            """ПринтВерсия"""
            xpath_printSearch = '//a[@onclick="printSearch()"]'
            await asyncio.sleep(1)  # Используйте asyncio.sleep в асинхронном контексте
            await page.wait_for_selector(f"xpath={xpath_printSearch}", timeout=timeout)

            # Используем async with для асинхронного ожидания попапа
            async with page.expect_popup() as popup_info:
                await page.click(f"xpath={xpath_printSearch}")
            new_page = await popup_info.value

            # Даем новой странице немного времени, чтобы загрузиться
            await new_page.wait_for_load_state('networkidle')

            # Получаем содержимое новой страницы
            page_content = await new_page.content()
            td_elements = await new_page.query_selector_all('td.NewLink')

            # Инициализируем пустой список для хранения извлеченных текстовых значений
            td_texts = []

            # Проходим по каждому найденному элементу
            for td_element in td_elements:
                # Получаем текстовое содержимое элемента и добавляем его в список
                text = await td_element.text_content()
                parcel_set.add(text.strip())  # Используем .add() для добавления элемента в набор

            # По завершении работы с новой страницей не забудьте ее закрыть
            await new_page.close()
        # Определение имени файла
        filename_csv = os.path.join(csv_path, f"{inpCity}_{inpStreet}.csv")

        # Открытие файла для записи
        with open(filename_csv, mode='w', newline='', encoding='utf-8') as file:
            # Создание объекта writer для записи в csv
            writer = csv.writer(file)
            
            # Запись каждого уникального текстового значения из set в новую строку файла
            for parcel_number in parcel_set:
                writer.writerow([parcel_number])
        exit()

        match = re.search(r"jurcode=(\d+)", url_start)

        jurcode = match.group(1)
        # Ждем появление кнопки поиска и нажимаем на нее
        xpath_begin_search = '//input[@id="ctl00_MainContent_BtnSearch"]'
        # Дожидаемся появления кнопки с заданным текстом и кликаем по ней
        await page.wait_for_selector(f"xpath={xpath_begin_search}", timeout=timeout)
        await page.click(xpath_begin_search)
        await asyncio.sleep(1)
        # Ждем появление поля ввода, вводим значение из переменной current и нажимаем Enter
        xpath_keyno = '//input[@id="ctl00_MainContent_TxtKey"]'
        await page.wait_for_selector(f"xpath={xpath_keyno}", timeout=timeout)
        folder_pdf = os.path.join(pdf_path, "*.pdf")
        files_pdf = glob.glob(folder_pdf)
        found_parts = []

        # Обход всех файлов и сбор номеров в заданном диапазоне
        for item in files_pdf:
            filename = os.path.basename(item)
            parts = filename.split("_")
            if len(parts) >= 2:
                try:
                    part_number = int(parts[1])  # Извлекаем номер
                    if range_a <= part_number <= range_b:
                        found_parts.append(part_number)
                except ValueError:
                    # Если part2 не является числом, пропускаем этот файл
                    continue

        # Определяем отсутствующие номера в диапазоне
        missing_parts = [n for n in range(range_a, range_b + 1) if n not in found_parts]

        # Определяем номер, с которого начать обработку
        # Если в missing_parts есть элементы, берем первый как начальный номер для обработки
        current = missing_parts[0] if missing_parts else range_b + 1

        while current <= range_b:
            if current in found_parts:
                current += 1
                continue

            await page.fill(xpath_keyno, str(current))
            await page.press(xpath_keyno, "Enter")
            # Получаем куки из контекста браузера
            cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
            # Ждем появление ссылки и получаем с нее href
            try:
                xpath_href = '//a[@target="_blank"]'
                await page.wait_for_selector(f"xpath={xpath_href}", timeout=timeout)
                url_href = await page.get_attribute(xpath_href, "href")

                pattern = r"pdf=([^&]+)"
                match = re.search(pattern, url_href)

                if match:
                    extracted_part = match.group(1)
                    keyno_match = re.search(r'K(\d+)N', extracted_part)
                    keyno = keyno_match.group(1) if keyno_match else None
                else:
                    print("Совпадение не найдено.")
                url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
                filename_pdf = os.path.join(
                    pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
                )
                await download_file(session, url, cookies_dict, filename_pdf)
                current += 1
            except:
                current += 1
                continue
                
        print("Все скачано")
        await sleep(5)
        await browser.close()
    # elif collection_method == 1:
    #     lowercase_letters_list = list(string.ascii_lowercase)
    #     for letter_streed in lowercase_letters_list:
    #         print(f'Поиск по букве {letter_streed}')
    #         current_directory = os.getcwd()
    #         # Создайте полный путь к папке temp
    #         temp_path = os.path.join(current_directory, "temp")
    #         pdf_path = os.path.join(temp_path, "pdf")
    #         # Убедитесь, что папки существуют или создайте их
    #         for folder in [
    #             temp_path,
    #             pdf_path,
    #         ]:
    #             if not os.path.exists(folder):
    #                 os.makedirs(folder)

    #         timeout = 5000
    #         current_directory = os.getcwd()
    #         browsers_path = os.path.join(current_directory, "pw-browsers")
    #         os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    #         async with async_playwright() as playwright, aiohttp.ClientSession() as session:
    #             browser = await playwright.chromium.launch(
    #                 headless=False
    #             )  # Для отладки можно использовать headless=False
    #             context = await browser.new_context(accept_downloads=True)
    #             page = await context.new_page()

    #             await page.goto(url_start)
    #             match = re.search(r"jurcode=(\d+)", url_start)

    #             jurcode = match.group(1)
    #             # Ждем появление кнопки поиска и нажимаем на нее
    #             xpath_begin_search = '//input[@id="ctl00_MainContent_BtnSearch"]'
    #             # Дожидаемся появления кнопки с заданным текстом и кликаем по ней
    #             await page.wait_for_selector(f"xpath={xpath_begin_search}", timeout=timeout)
    #             await page.click(xpath_begin_search)
    #             await asyncio.sleep(1)
    #             # Получаем куки из контекста браузера
    #             cookies = await context.cookies()
    #             cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                
                


                
    #             # Ждем появление поля ввода, вводим значение из переменной current и нажимаем Enter
    #             xpath_txtstreet = '//input[@id="ctl00_MainContent_TxtStreet"]'
    #             await page.wait_for_selector(f"xpath={xpath_txtstreet}", timeout=timeout)
    #             await page.fill(xpath_txtstreet, str(letter_streed))
    #             await page.press(xpath_txtstreet, "Enter")
                
                
                
    #             xpath_error_message = '//span[@id="ctl00_MainContent_lblMaxRec"]'
    #             xpath_href = '//a[@target="_blank"]'

    #             # Пытаемся найти элемент с сообщением об ошибке
    #             error_message_element = await page.query_selector(xpath_error_message)
                
    #             if error_message_element:
    #                 error_message_text = await error_message_element.text_content()
    #                 if error_message_text == 'No records found using chosen criteria!':
    #                     print("Нет записей, соответствующих критериям.")
    #                 elif error_message_text == 'Search results are limited to the first 300 records!':

    #                     lowercase_letters_list = list(string.ascii_lowercase)
    #                     for letter in lowercase_letters_list:
    #                         find_letter = f"{letter_streed}{letter}"
    #                         await asyncio.sleep(1)
    #                         await page.fill(xpath_txtstreet, find_letter)
    #                         await page.press(xpath_txtstreet, "Enter")
    #                         await asyncio.sleep(1)
    #                         # Обновляем состояние элемента с сообщением об ошибке
    #                         error_message_element = await page.query_selector(xpath_error_message)
    #                         if error_message_element:
    #                             error_message_text = await error_message_element.text_content()
    #                             if error_message_text == 'No records found using chosen criteria!':
    #                                 print(f"Нет записей, пропускаем {find_letter}")
    #                                 continue  # Пропускаем текущую итерацию и переходим к следующей букве
    #                             elif error_message_text == 'Search results are limited to the first 300 records!':
    #                                 print(f'Ручная проверка запроса\n {find_letter}!!!!!!!!!!!!!!!!!!')
    #                         else:
    #                             print(f"качаем {find_letter}")

    #                         xpath_href = '//a[@target="_blank"]'
    #                         links_elements = await page.query_selector_all(f"xpath={xpath_href}")
    #                         urls = [await link_element.get_attribute('href') for link_element in links_elements]
    #                         # Создаем список словарей, где каждый словарь содержит jurcode, extracted_part и keyno для каждого URL
    #                         jurcode_extracted_list = []
    #                         pattern = re.compile(r'jurcode=(\d+)&pdf=([^&]+)')

    #                         for url in urls:
    #                             match = pattern.search(url)
    #                             if match:
    #                                 jurcode, extracted_part = match.groups()
    #                                 keyno_match = re.search(r'K(\d+)N', extracted_part)
    #                                 keyno = keyno_match.group(1) if keyno_match else None

    #                                 # Создаем словарь для каждого найденного совпадения и добавляем его в список
    #                                 jurcode_extracted_dict = {
    #                                     "jurcode": jurcode,
    #                                     "extracted_part": extracted_part,
    #                                     "keyno": keyno
    #                                 }
    #                                 jurcode_extracted_list.append(jurcode_extracted_dict)

    #                         # Выводим полученный список словарей
    #                         for item in jurcode_extracted_list:
    #                             jurcode = item['jurcode']
    #                             extracted_part = item['extracted_part']
    #                             keyno = item['keyno']
    #                             url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
    #                             filename_pdf = os.path.join(
    #                                 pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
    #                             )
    #                             if not os.path.exists(filename_pdf):
    #                                 await download_file(session, url, cookies_dict, filename_pdf)
    #             else:
    #                 print(f"качаем {letter_streed}")
    #                 # Если элемент с сообщением об ошибке не найден, собираем все ссылки
    #                 links_elements = await page.query_selector_all(xpath_href)
    #                 pattern = re.compile(r'jurcode=(\d+)&pdf=([^&]+)')

    #                 urls = [await link_element.get_attribute('href') for link_element in links_elements]
    #                 # Создаем список словарей, где каждый словарь содержит jurcode, extracted_part и keyno для каждого URL
    #                 jurcode_extracted_list = []

    #                 for url in urls:
    #                     match = pattern.search(url)
    #                     if match:
    #                         jurcode, extracted_part = match.groups()
    #                         keyno_match = re.search(r'K(\d+)N', extracted_part)
    #                         keyno = keyno_match.group(1) if keyno_match else None

    #                         # Создаем словарь для каждого найденного совпадения и добавляем его в список
    #                         jurcode_extracted_dict = {
    #                             "jurcode": jurcode,
    #                             "extracted_part": extracted_part,
    #                             "keyno": keyno
    #                         }
    #                         jurcode_extracted_list.append(jurcode_extracted_dict)

    #                 # Выводим полученный список словарей
    #                 for item in jurcode_extracted_list:
    #                     jurcode = item['jurcode']
    #                     extracted_part = item['extracted_part']
    #                     keyno = item['keyno']
    #                     url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
    #                     filename_pdf = os.path.join(
    #                         pdf_path, f"{jurcode}_{keyno}_{extracted_part}.pdf"
    #                     )
    #                     if not os.path.exists(filename_pdf):
    #                         await download_file(session, url, cookies_dict, filename_pdf)


    #             print("Все скачано")
    #             await sleep(5)
    #             await browser.close()



asyncio.run(run())
