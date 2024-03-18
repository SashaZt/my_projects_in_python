import cloudscraper
import cloudscraper.exceptions
import random
import csv
import os
import re
import time
from typing import List, Dict
import requests


bad_url = []

wait_time = random.uniform(5, 10)
def get_page(url, category):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    """Get page by url"""
    try:
        scraper_get = scraper.get(url).content
        return scraper_get
    except requests.exceptions.RequestException as e:
        print(e)
        return None


def save_html(html, counter, category):
    """Save the html page with the given counter and category"""
    try:
        filename = f"c:\\salomon_pl\\html_product\\{category}\\0_{counter}.html"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(html.decode('utf-8')) #Основная настройка при сохранении html файлов html.decode('utf-8')
    except cloudscraper.exceptions.CloudflareChallengeError:
        print("Ошибка Cloudflare Challenge. Пропуск URL.")


def process_url(url, counter, category):
    """Process url to get page and save as html"""
    if re.match(r'^https?://', url):
        try:
            html = get_page(url, category)  # передаем аргумент category в get_page()
            if html is not None:
                save_html(html, counter, category)
        except cloudscraper.exceptions.CloudflareChallengeError:
            print("Ошибка Cloudflare Challenge. Пропуск URL.")
            return

def main_asio():
    categories = ['kids', 'men', 'women']
    for category in categories:
        time.sleep(2)
        counter = 0
        with open(f'c:\\salomon_pl\\csv_url\\{category}\\url.csv', newline='', encoding='utf-8') as files:
            urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            if os.path.isfile(f'c:\\salomon_pl\\csv_url\\{category}\\url.csv'):
                with open(f'c:\\salomon_pl\\csv_url\\{category}\\url.csv', newline='', encoding='utf-8') as files:
                    urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
            for url in urls:
                counter += 1
                filename = f"c:\\salomon_pl\\html_product\\{category}\\0_{counter}.html"
                if os.path.isfile(filename):
                    continue
                process_url(url[0], counter, category)
                print(f"{category} | ссылка {counter} из {len(urls)}")
                time.sleep(wait_time)


if __name__ == '__main__':
    main_asio()
