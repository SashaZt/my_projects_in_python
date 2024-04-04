# -*- mode: python ; coding: utf-8 -*-
# Получаем json в папку list

import asyncio
from time import sleep
from playwright.async_api import async_playwright
import aiohttp
import aiofiles
import re
import string
import csv
import json
import os
import glob
from asyncio import sleep


async def create_directories_async(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.makedirs(folder)


async def save_response_json(json_response, url_name):
    current_directory = os.getcwd()
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, "temp")
    list_path = os.path.join(temp_path, "list")
    """Асинхронно сохраняет JSON-данные в файл."""
    filename = os.path.join(list_path, f"{url_name}.json")
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))



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

    async with async_playwright() as playwright, aiohttp.ClientSession() as session:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(url_start)
        await sleep(5)
        parcel_set = set()
        xpath_Username = '//input[@id="Username"]'
        await page.wait_for_selector(f"xpath={xpath_Username}", timeout=timeout)
        await page.fill(xpath_Username, str(ligin_username))

        xpath_password = '//input[@id="password"]'
        await page.wait_for_selector(f"xpath={xpath_password}", timeout=timeout)
        await page.fill(xpath_password, str(password_username))

        # Нажимаем Enter после ввода пароля
        await page.press(xpath_password, "Enter")
        # Устанавливаем обработчик для сбора и сохранения данных ответов
        def create_log_response_with_counter(url_name):
            async def log_response(response):
                api_url = "https://prod-csa-bff.awsmanlog13.manheim.com/api/customers-search"
                request = response.request
                if (
                    request.method == "POST" and api_url in request.url
                ):  # Подставьте актуальное условие URL
                    try:
                        json_response = await response.json()
                        await save_response_json(json_response, url_name)

                    except Exception as e:
                        print(
                            f"Ошибка при получении JSON из ответа {response.url}: {e}"
                        )

            return log_response
        
        await sleep(5)
        
        lowercase_letters_list = list(string.ascii_lowercase)
        previous_handler = None  # Для хранения предыдущего обработчика

        for letter in lowercase_letters_list:
            url_next = f"https://app.centraldispatch.com/company-search?s={letter}&page=1&size=100&sort=relevance&desc=true"
            # Если уже существует обработчик, отписываемся от него
            if previous_handler:
                page.remove_listener("response", previous_handler)

            # Подписываемся на новый обработчик ДО перехода на страницу
            url_name = f"initial_180000{letter}"
            handler = create_log_response_with_counter(url_name)
            page.on("response", handler)
            previous_handler = handler  # Сохраняем текущий обработчик как предыдущий

            # Выполняем переход
            await page.goto(url_next)
            await sleep(5)
            """Нажимаем кнопку next page"""
            xpath_next_page = '//button[@title="Go to next page"]'
            await page.wait_for_selector(f"xpath={xpath_next_page}", timeout=timeout)
            # await page.click(xpath_next_page)
           
            counter = 1

            while True:
                # Проверяем, активна ли кнопка "следующая страница"
                is_disabled = await page.is_disabled(xpath_next_page)
                
                if is_disabled:
                    print(f"Button is disabled for letter {letter}, stopping.")
                    break
                
                # Если кнопка активна, готовимся перехватить ответы сервера
                url_name = f"page_180000{counter}_{letter}"
                handler = create_log_response_with_counter(url_name)
                
                # Отписываемся от предыдущего обработчика, если он есть
                if previous_handler:
                    page.remove_listener("response", previous_handler)
                
                # Подписываемся на новый обработчик
                page.on("response", handler)
                previous_handler = handler  # Обновляем предыдущий обработчик
                
                # Нажимаем на кнопку "следующая страница" и ожидаем загрузку
                await page.click(xpath_next_page)
                await sleep(5)
                await page.wait_for_load_state('networkidle')

                counter += 1
        # После выхода из всех циклов, отписываемся от последнего обработчика
        if previous_handler:
            page.remove_listener("response", previous_handler)
        await browser.close()
   


asyncio.run(run())
