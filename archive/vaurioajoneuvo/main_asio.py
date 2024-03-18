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
from config import bot_token, chat_id, proxies, list_urls, cookies, headers
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


def process_urls_and_send_messages(bot_token, chat_id, list_urls):
    headers, cookies = get_cookies_sf()
    while True:
        for url in list_urls:
            scraper = cloudscraper.create_scraper(browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
                'mobile': False})
            # response = scraper.get(url, cookies=cookies, headers=headers)  # , proxies=proxies
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
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            table_row = soup.find('div', attrs={'class': 'cars-list'})
            regex_containr = re.compile('.*(?=item-lift-container)')
            try:
                item_lift_container = table_row.find_all('div', attrs={'class': 'col-12 col-lg-3 item-lift-container'})
            except:
                continue
            if item_lift_container:  # Проверка, что список не пуст
                file_name = 'id_ad.csv'
                try:
                    with open(file_name, 'r', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        id_list = [row[0] for row in reader]
                except:
                    with open(file_name, 'a', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                i = item_lift_container[0]
                id_avto = i.find('div', {'class': 'item-lift'}).get('data-auction-id')
                # print(id_avto, url)
                if id_avto in id_list:
                    continue
                else:
                    now = datetime.now()
                    formatted_now = now.strftime("%H:%M_%d.%m.%Y")
                    print(f"Новый id {id_avto}_____________{formatted_now}_____________________________")
                    # print(url)
                    with open(file_name, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([id_avto])
                    link = 'https://www.vaurioajoneuvo.fi' + i.find('a').get('href')
                    # Извлечь текст из блока с названием
                    title = i.find('strong').text
                    # Извлечь текст из блока с информацией о цене
                    regex_price = re.compile('item-lift-price-now auction-price-now.*')
                    try:
                        price = i.find('strong', {'class': regex_price}).text
                    except:
                        price = None
                    details_all = [span.text for span in i.find_all('span')]
                    details = f"{details_all[0]} {details_all[1]} {details_all[2]}"
                    message = f"Title: {title}\nLink: {link}\nPrice: {price}\nDetails: {details}"
                    # print(message)  # print to console

                    # send the same message to telegram
                    asyncio.run(send_message(bot_token, chat_id, message))
            time.sleep(5)
            # print('Паузка 5сек')


process_urls_and_send_messages(bot_token, chat_id, list_urls)
