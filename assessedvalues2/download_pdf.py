import asyncio
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
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


async def run():
    print("Вставьте ссылку ссылку на город")
    url_start = str(input())
    print("Введите диапозон поиска по кодам, от")
    range_a = int(input())
    print("Введите диапозон поиска по кодам, до")
    range_b = int(input())
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

    timeout = 60000
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
            xpath_href = '//a[@target="_blank"]'
            await page.wait_for_selector(f"xpath={xpath_href}", timeout=timeout)
            url_href = await page.get_attribute(xpath_href, "href")

            pattern = r"pdf=([^&]+)"
            match = re.search(pattern, url_href)

            if match:
                extracted_part = match.group(1)
            else:
                print("Совпадение не найдено.")
            url = f"https://www.assessedvalues2.com/pdfs/{jurcode}/{extracted_part}.pdf"
            filename_pdf = os.path.join(
                pdf_path, f"{jurcode}_{current}_{extracted_part}.pdf"
            )
            await download_file(session, url, cookies_dict, filename_pdf)
            current += 1
        print("Все скачано")
        await sleep(5)
        await browser.close()


asyncio.run(run())
