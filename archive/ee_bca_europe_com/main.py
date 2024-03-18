# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import glob
import json
import os
import random
import time
from collections import defaultdict
from datetime import datetime, timedelta

import gspread
import mysql.connector
import numpy as np
import pandas as pd
import requests
import schedule
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine

headers = {
    'authority': 'ee.bca-europe.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    # 'content-length': '0',
    # 'cookie': '_cf_7b=1862468106.47873.0000; OptanonAlertBoxClosed=2023-11-15T06:20:14.692Z; X-CSRF-TOKEN-COOKIE=CfDJ8CFSqQ64OTdKvgetmHK3MvTeARjDI1LpFo6WRZzLJw3D780yH6oX1Pt_EVHJShH32KAIt4Rd2fNdBGIajX96FDDUTj4tO1f8ZqbEmdQJv-RUjnwaLmYCap_QvhBHmMiyEh6BT35BwgpxC6_FTpAlHKg; RecentSearches=; AMCVS_E5F2C8A15481C0E20A4C98BC%40AdobeOrg=1; Basket=; .ASPXANONYMOUS=2ZKss1DosAL7kRA9g6tcT8iWmzSe46ouOOjkhZA2t6SSzQke8LpiTUmm3MdWvM36GDk_BOx0NlpScc9mafrJwdIvhj_Bgt6tkR_FeQkr-aqCsWa1vGdR__tYSPPOHlIaF2x6lQ2; __cf_bm=OCtACF7XxY9PO99vIfPyhkKfs9_RIFnmNtWGowR3T0A-1709672420-1.0.1.1-WodJnRzYc6a4Rh2gGIHKrsI5XqYr_po01J9z1fWXMnca450h5cp2JrF4.xFqWGp3nWE8ktWVFmXaA.ZD_Cjp8bKUKGX26b6BKS.Uk1vgzF0; AMCV_E5F2C8A15481C0E20A4C98BC%40AdobeOrg=179643557%7CMCIDTS%7C19788%7CMCMID%7C87554041928093596420804521706073250235%7CMCOPTOUT-1709680233s%7CNONE%7CvVersion%7C5.5.0; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Mar+05+2024+23%3A10%3A33+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.30.0&isIABGlobal=false&hosts=&consentId=345b7345-9d1a-4ca7-929e-198e46cbd241&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
    'dnt': '1',
    'origin': 'https://ee.bca-europe.com',
    'referer': 'https://ee.bca-europe.com/buyer/facetedSearch/saleCalendar?page=2',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, 'cookies')
login_pass_path = os.path.join(temp_path, 'login_pass')
daily_sales_path = os.path.join(temp_path, 'daily_sales')
monthly_sales_path = os.path.join(temp_path, 'monthly_sales')
payout_history_path = os.path.join(temp_path, 'payout_history')
pending_custom_path = os.path.join(temp_path, 'pending_custom')
chat_path = os.path.join(temp_path, 'chat')
max_attempts = 3
attempts = 0
def creative_temp_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

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
    from urllib.parse import urlparse, parse_qs

    from playwright.async_api import TimeoutError
    from playwright.async_api import async_playwright

    current_directory = os.getcwd()
    temp_directory = 'temp'
    # Создайте полный путь к папке temp
    temp_path = os.path.join(current_directory, temp_directory)


    async def save_cookies(page, identifier):
        cookies = await page.context.cookies()
        # Убедитесь, что mvtoken корректен и не является объектом корутины
        filename = os.path.join(temp_path, f"{identifier}.json")
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(cookies))
        # print(f"Сохранены куки для {identifier}")
        return filename

    async def load_cookies_and_update_session(session, filename):
        async with aiofiles.open(filename, 'r') as f:
            cookies_list = json.loads(await f.read())
        for cookie in cookies_list:
            session.cookie_jar.update_cookies({cookie['name']: cookie['value']})

    async def get_requests_day(session, filename):
        await load_cookies_and_update_session(session, filename)
        params = {
            'page': '1',
        }
        async with session.post('https://ee.bca-europe.com/buyer/facetedSearch/GetSaleCalendarViewModel',
                                headers=headers,
                                params=params) as response:
            # data_json = await response.text()
            # return data_json
            if response.headers.get('Content-Type') == 'application/json':
                data_json = await response.json()
                return data_json
            else:
                content = await response.text()
                print(f'Unexpected response: {content}')
                return None
    async def save_day_json(data_json, p):
        filename = os.path.join(temp_path, f'0_{p}.json')
        async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data_json, ensure_ascii=False, indent=4))

    async def run(playwright):
        async with aiohttp.ClientSession() as session:

            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            url = 'https://ee.bca-europe.com/buyer/facetedSearch/saleCalendar?page=1'
            """Вход на страницу с логин и пароль"""
            try:
                await page.goto(url, wait_until='networkidle',
                                timeout=60000)  # 60 секунд
                # await page.goto('https://www.manyvids.com/Login/', wait_until='load', timeout=60000) нужно тестировать
            except TimeoutError:
                print(f"Страница не загрузилась для ")
            if await page.is_visible('//button[@id="onetrust-accept-btn-handler"]'):
                print("Кнопка согласия на cookies найдена. Кликаем по ней.")
                await page.click('//button[@id="onetrust-accept-btn-handler"]')
            else:
                print("Кнопка согласия на cookies не найдена.")
            # Разбор URL для получения его компонентов
            parsed_url = urlparse(url)

            # Извлекаем параметры запроса
            query_params = parse_qs(parsed_url.query)

            # Получаем значение параметра 'page', предполагая, что оно есть и является списком
            page_number = query_params.get('page', [None])[0]  # Берём первое значение, если 'page' есть

            # Формируем строку в нужном формате
            p = f"page_{page_number}" if page_number else "page_not_found"
            await asyncio.sleep(2)

            filename = await save_cookies(page, p)

            await load_cookies_and_update_session(session, filename)  # Загружаем куки в session

            """Дневные продажи"""
            data_json_day = await get_requests_day(session, filename)
            await save_day_json(data_json_day, p)

            # latest_date = await check_chat()

            """Закрываем"""
            await browser.close()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())



if __name__ == '__main__':
    creative_temp_folders()
    get_asio()
