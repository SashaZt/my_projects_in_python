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
temp_path = os.path.join(current_directory, "temp")


def get_cookies():

    async def update_session_cookies(session, cookies):
        for cookie in cookies:
            session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async def save_cookies(page):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(current_directory, "raw_cookies.json")
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
        url = "https://app1.shippingeasy.com/inventory/products"
        """Вход на страницу с логин и пароль"""
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)  # 60 секунд
        except TimeoutError:
            print(f"Страница не загрузилась 60 секунд.")
        await asyncio.sleep(50)

        filename = await save_cookies(page)

        """Закрываем"""
        await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())


if __name__ == "__main__":
    get_cookies()
