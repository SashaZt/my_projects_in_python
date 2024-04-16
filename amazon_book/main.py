# -*- mode: python ; coding: utf-8 -*-
# Скачивание PDF файлов

import aiofiles
import asyncio
import sys
from time import sleep
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
import re

import json
import time
import glob
import asyncio
import string
import shutil
import random
import os
import glob
from asyncio import sleep

import json


async def run():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    log_path = os.path.join(temp_path, "log")

    # Удаление папки log_path вместе со всем содержимым
    shutil.rmtree(log_path, ignore_errors=True)

    url_start = f"https://www.amazon.com/dp/B084ZH43LV/"
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    html_path = os.path.join(temp_path, "html")
    search_results_path = os.path.join(temp_path, "search_results")
    # Убедитесь, что папки существуют или создайте их
    for folder in [
        temp_path,
        html_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    current_directory = os.getcwd()
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(url_start)
        await asyncio.sleep(10)
        keywords = ""
        # Путь к файлу, в который будет сохранено содержимое
        page_content = await page.content()
        filename = "saved_page.html"
        filename_to_check = os.path.join(html_path, f"data_.html")
        # Асинхронная запись содержимого в файл
        async with aiofiles.open(filename_to_check, "w", encoding="utf-8") as file:
            await file.write(page_content)

        print("Все скачано")
        await sleep(5)
        await browser.close()
def parsin_html():
    current_directory = os.getcwd()
    temp_path = os.path.join(current_directory, "temp")
    html_path = os.path.join(temp_path, "html")
    folder_html = os.path.join(html_path, "*.html")

    files_html = glob.glob(folder_html)
    for item in files_html:
        with open(item, encoding="utf-8") as file:
            src = file.read()
        # Создаем парсер для прочитанного HTML
        parser = HTMLParser(src)

        product_title = parser.css_first('span#productTitle').text()
        
        a_autoid_0_announce = parser.css_first('a#a-autoid-0-announce').text().split()
        a_autoid_0_announce_string = ' '.join(a_autoid_0_announce)
        a_autoid_1_announce = parser.css_first('a#a-autoid-1-announce').text().split()
        a_autoid_1_announce_string = ' '.join(a_autoid_1_announce)
        bylineInfo = parser.css_first('div#bylineInfo').text().split()
        bylineInfo_string = ' '.join(bylineInfo)
        acrPopover = parser.css_first('span#acrPopover span.a-declarative > a > i.a-icon.a-icon-star.a-star-4.cm-cr-review-stars-spacing-big > span').text().split()
        averageCustomerReviews_string = ' '.join(acrPopover)

        
        
        print(averageCustomerReviews_string)

        

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

    return config



if __name__ == "__main__":
    # asyncio.run(run())
    parsin_html()
# while True:
#     print(
#         "Введите 1 для запуска парсинга\nВведите 3 для загрузки данных в БД \nВведите 0 для закрытия программы"
#     )
#     user_input = int(input("Выберите действие: "))

#     if user_input == 1:
#         asyncio.run(run())
#     elif user_input == 0:
#         print("Программа завершена.")
#         sys.exit(1)
#     elif user_input == 3:
#         asyncio.run(insert_data_into_table())

#     else:
#         print("Неверный ввод, пожалуйста, введите корректный номер действия.")
