import glob
import asyncio
import json
import os
import random
from datetime import datetime

import aiofiles
import aiohttp
import aiomysql
from aiohttp import BasicAuth
import os
import csv
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
img_dir = os.path.join(temp_path, "img_dir")


async def download_image(session, img_url, file_path):
    async with session.get(img_url) as response:
        img_data = await response.read()
        async with aiofiles.open(file_path, "wb") as file_img:
            await file_img.write(img_data)
        await asyncio.sleep(5)


async def read_csv_as_list_of_dicts(filename):
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as file:
        # Чтение содержимого файла
        content = await file.read()

    # Явное указание заголовков столбцов
    reader = csv.DictReader(
        content.splitlines(), delimiter=";", fieldnames=["SKU", "URL"]
    )
    result = [row for row in reader]
    return result


def create_filename(sku, idx):
    if idx == 0:
        return f"{sku}.jpg"
    else:
        return f"{sku}({idx}).jpg"


def unique_filenames(img_dir):
    # Регулярное выражение для поиска (1), (2), ... в имени файла
    regex = re.compile(r"\(\d+\)$")

    # Получаем список файлов в директории
    filenames = os.listdir(img_dir)

    # Удаляем расширения и части с (1), (2), ...
    cleaned_names = set()
    for filename in filenames:
        # Удаление расширения файла
        name_without_extension = os.path.splitext(filename)[0]
        # Удаление (1), (2), ...
        cleaned_name = regex.sub("", name_without_extension)
        cleaned_names.add(cleaned_name)

    return list(cleaned_names)


async def run(playwright):
    current_directory = os.getcwd()
    current_datetime = datetime.now().strftime("%H_%M_%d_%m_%Y")
    # Создаем путь к новой папке с текущей датой и временем
    print("Введите имя папки, куда будут сохранятся фото")
    name_folder = str(input())
    print("Введите количество сек")
    time_b = int(input())
    img_dir = os.path.join(current_directory, "img_dir", name_folder)
    list_files = unique_filenames(img_dir)
    # Проверяем, существует ли папка. Если нет, создаем ее.
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    filename = "intercars.csv"
    csv_data = await read_csv_as_list_of_dicts(filename)
    # Устанавливаем путь к браузерам Playwright
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    for c in csv_data:
        sku_product = c["SKU"]
        url_product = c["URL"]
        if not sku_product in  list_files:
            try:
                await page.goto(
                    url_product,
                    wait_until="networkidle",
                    timeout=60000,
                )
            except TimeoutError:
                print(f"{sku_product} не открылась страница")
                continue
            src = await page.content()
            soup = BeautifulSoup(src, "lxml")
            # Предположим, что `src` содержит исходный HTML

            # selectors_img = [
            # ('a', {"data-gc-onclick": "dyn-gallery"}),
            # ('img', {"id": "article-image-thumb"}),
            # ('a', {"id": "btn_gallery_30"}),]

            # Поиск элемента по заданному селектору
            element = soup.find("img", class_="hidden fullcard-galery fc-desc-image-big")

            # Проверка, найден ли элемент и есть ли у него нужный атрибут
            if element and "data-dyngalposstring" in element.attrs:
                script_div_img = element["data-dyngalposstring"]
            pattern = re.compile(r"'src': '(.+?)',")
            if script_div_img is not None:
                result = pattern.findall(str(script_div_img))
            else:
                result = []
            max_images = len(result)
            filenames = []
            async with aiohttp.ClientSession() as session:
                tasks = []
                for idx, img in enumerate(result[:max_images]):
                    # Использование новой функции для формирования имени файла
                    filename = create_filename(sku_product, idx)
                    file_path = os.path.join(img_dir, filename)
                    filenames.append(filename)

                    # Проверка на существование файла пропущена для упрощения
                    # Если файл существует, можно пропустить загрузку или обработать по-другому

                    tasks.append(download_image(session, img, file_path))

                if tasks:
                    await asyncio.gather(*tasks)
            pause_time = random.randint(10, time_b)
            await asyncio.sleep(pause_time)

    """
    Закрываем
    """
    await browser.close()


async def main():

    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
