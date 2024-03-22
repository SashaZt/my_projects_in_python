from asyncio import sleep
from re import S


def get_asio():
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
    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    from config import db_config_asio, headers, use_bd
    from proxi import proxies

    current_directory = os.getcwd()
    temp_directory = 'temp'
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, temp_directory)
    cookies_path = os.path.join(temp_path, 'cookies')
    daily_sales_path = os.path.join(temp_path, 'daily_sales')
    payout_history_path = os.path.join(temp_path, 'payout_history')
    pending_custom_path = os.path.join(temp_path, 'pending_custom')
    chat_path = os.path.join(temp_path, 'chat')


    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie['name']: cookie['value']})

    async def save_cookies(page):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(cookies_path, "cookies.json")
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def load_cookies_and_update_session(session, filename):
        async with aiofiles.open(filename, 'r') as f:
            cookies_list = json.loads(await f.read())
        for cookie in cookies_list:
            session.cookie_jar.update_cookies({cookie['name']: cookie['value']})

    

    async def run(playwright):
        async with aiohttp.ClientSession() as session:

            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            url = 'http://www.wmmotor.pl/hurtownia/drzewo.php'
            """Вход на страницу с логин и пароль"""
            try:
                await page.goto(url, wait_until='networkidle',
                                timeout=60000)  # 60 секунд
            except TimeoutError:
                print(f"Страница не загрузилась 60 секунд.")
            try:
                # Ожидаем появления элемента h1 с текстом "Login to ManyVids"
                print("Вставьте логин, почту")
                fldEmail = str(input())
                print("Вставьте пароль")
                fldPassword = str(input())
                await page.fill('input#fldEmail', fldEmail)
                await page.fill('input#fldPassword', fldPassword)
                print("Введите значение в Podaj wynik działania\nнажмите Ентер, у Вас 20сек")
                await sleep(20)
            except TimeoutError:
                print("Страница не загрузилась")

            filename = await save_cookies(page)

            # await load_cookies_and_update_session(session, filename)  # Загружаем куки в session
            # """Дневные продажи"""
            # data_json_day = await get_requests_day(session, proxy, headers, mvtoken, month, filterYear, filename)
            # await save_day_json(data_json_day, mvtoken, month, filterYear)
            # """История"""
            # data_json_history = await get_requests_history(session, proxy, headers, mvtoken, filterYear, filename)
            # await save_history_json(data_json_history, mvtoken, filterYear)
            # """Pending"""
            # await save_page_content(page, mvtoken, filterYear)
            # #
            # """Загрузка чатов"""
            # data_json_first_chat = await get_requests_chat(session, proxy, headers, mvtoken, filename)
            # #
            # await save_chat_json(data_json_first_chat, mvtoken)

            # total_msg = await get_total_msg()
            # # data_json_all_chat, i = await get_requests_all_chat(session, proxy, headers, mvtoken, filename, total_msg)

            # results = await get_requests_all_chat(session, proxy, headers, mvtoken, filename, total_msg)
            # for data_json, i in results:cd
            #     await save_all_chat_json(data_json, mvtoken, i)

            # latest_date = await check_chat()

            """Закрываем"""
            await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())