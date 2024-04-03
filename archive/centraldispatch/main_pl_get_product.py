import asyncio
from math import e
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
import string
import csv
import re
import os
import glob
from asyncio import sleep



async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)

async def read_csv_values():
    current_directory = os.getcwd()
    filename_csv = os.path.join(current_directory, "unique_company_ids.csv")
    values = []
    async with aiofiles.open(filename_csv, mode='r', encoding='utf-8') as file:
        async for line in file:
            # Удалите символы переноса строки и добавьте значения в список
            values.append(line.strip())
    return values


async def run():
    timeout = 20000
    ligin_username = "ospro1"
    password_username = "LggtTLQC123!"
    # Создайте полный путь к папке temp
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    list_path = os.path.join(temp_path, "list")
    products_path = os.path.join(temp_path, "products")
    browsers_path = os.path.join(current_directory, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    # Убедитесь, что папки существуют или создайте их
    await create_directories_async(
        [
            temp_path,
            list_path,
            products_path,
        ]
    )
    url_start = (
        "https://id.centraldispatch.com/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3Dcentraldispatch_authentication%26scope%3Dlisting_service%2520offline_access%2520openid%26response_type%3Dcode%26redirect_uri%3Dhttps%253A%252F%252Fwww.centraldispatch.com%252Fprotected"
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(url_start)
        await sleep(5)
        xpath_Username = '//input[@id="Username"]'
        await page.wait_for_selector(f"xpath={xpath_Username}", timeout=timeout)
        await page.fill(xpath_Username, str(ligin_username))

        xpath_password = '//input[@id="password"]'
        await page.wait_for_selector(f"xpath={xpath_password}", timeout=timeout)
        await page.fill(xpath_password, str(password_username))

        # Нажимаем Enter после ввода пароля
        await page.press(xpath_password, "Enter")
        values = await read_csv_values()
        await sleep(5)
        for v in values:
            url_name = v.split("=")[-1]
            filename_html = os.path.join(products_path, f"{url_name}.html")
            if not os.path.isfile(filename_html):
                await page.goto(v)
                
                xpath_page_header = '//div[@class="page-header"]'
                await page.wait_for_selector(f"xpath={xpath_page_header}", timeout=timeout)
                page_content = await page.content()
                with open(filename_html, "w", encoding="utf-8") as f:
                    f.write(page_content)
                await sleep(1)
        
        
        await browser.close()





asyncio.run(run())
