import schedule
import time
from datetime import datetime

from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse, parse_qs
import glob
import re
from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import requests
import json
import cloudscraper
import random
import os
import time
import undetected_chromedriver as webdriver
from config import bot_token, chat_id
import csv


async def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text
    }
    async with aiohttp.ClientSession() as session:
        await session.post(url, data=data)

def get_cookies_sf():
    url_pl = 'https://www.vaurioajoneuvo.fi'
    # res = requests.get(url_pl)
    # if '<title>Just a moment...</title>' in res.text:
    #     print("cf challenge fail")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        sync_stealth(page, pure=True)
        page.goto(url_pl)
        res = sync_cf_retry(page)
        if res:
            cookies = page.context.cookies()
            for cookie in cookies:
                if cookie.get('name') == 'cf_clearance':
                    cf_clearance_value = cookie.get('value')
                    # print(cf_clearance_value)
            ua = page.evaluate('() => {return navigator.userAgent}')
            # print(ua)
            # get_cloudscraper(ua, cf_clearance_value)

        else:
            print("cf challenge fail")

        browser.close()
        # print(url)
    headers = {"user-agent": ua}
    cookies = {"cf_clearance": cf_clearance_value}
    return headers, cookies


def process_urls_and_send_messages(bot_token, chat_id):
    headers, cookies = get_cookies_sf()
    while True:
        url = 'https://www.vaurioajoneuvo.fi/api/1.0.0/products/'
        try:
            response = requests.get(url, cookies=cookies, headers=headers)
        except:
            continue
        if response.status_code != 200:
            now = datetime.now()
            formatted_now = now.strftime("%H:%M_%d.%m.%Y")
            # print(formatted_now)
            headers, cookies = get_cookies_sf()
            response = requests.get(url, cookies=cookies, headers=headers)
        json_data = response.json()
        first_ad = json_data['items'][0]
        ad_pid = first_ad['pid']
        file_name = 'id_ad.csv'
        try:
            with open(file_name, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                id_list = [int(row[0]) for row in reader]
        except:
            with open(file_name, 'a', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
        try:
            ad_model = first_ad['model']
        except:
            ad_model = None
        if ad_pid in id_list:
            # print(f"{ad_pid}")
            # time.sleep(5)
            continue
        else:
            now = datetime.now()
            formatted_now = now.strftime("%H:%M_%d.%m.%Y")
            print(f"Новый id {ad_pid}__________________{formatted_now}____________________")
            # print(url)
            with open(file_name, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([ad_pid])
            try:
                ad_price = first_ad['price']
            except:
                ad_price = None
            ad_url = f"https://www.vaurioajoneuvo.fi{first_ad['url']}"
            try:
                ad_model_year = first_ad['model_year']
            except:
                ad_model_year = None
            try:
                ad_kilometrage = first_ad['kilometrage']
            except:
                ad_kilometrage = None

            message = f"\nAPI\nTitle: {ad_model}\nLink: {ad_url}\nPrice: {ad_price}\nmodel year: {ad_model_year}\nkilometrage: {ad_kilometrage}"
            # print(message)  # print to console

            # send the same message to telegram
            asyncio.run(send_message(bot_token, chat_id, message))
        # time.sleep(5)
        # print('Паузка 5сек')


process_urls_and_send_messages(bot_token, chat_id)
