import os
import glob
import urllib3.exceptions
import re
import json
import traceback
from random import randint
import time
import psutil
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки
from selenium.webdriver.support.wait import WebDriverWait

import csv
header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}

def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--proxy-server=37.233.3.100:9999')
    chrome_options.add_argument('--disable-gpu')
    s = Service(
        executable_path="C:\\scrap_tutorial-master\\chromedriver.exe"
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver
def main():
    url = 'https://www.booking.com/hotel/es/the-river-hostel.ru.html?aid=356980&checkin=2023-05-23&checkout=2023-05-24&dest_id=-406131&dest_type=city&group_adults=1&group_children=0&label=Share-h3aBao%401682674837&no_rooms=1&req_adults=1&req_children=0'

    driver = get_chromedriver()
    driver.get(url=url)
    driver.maximize_window()
    time.sleep(10)
    with open(f"data.html", "w", encoding='utf-8') as file:
        file.write(driver.page_source)

def parsing_html():
    with open('data.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # инициализировать объект BeautifulSoup и найти тег <script>
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', string=lambda text: text and 'b_rooms_available_and_soldout:' in text)
    json_string = script_tag.string.split('b_rooms_available_and_soldout: ')[1].split(',\n')[0]
    json_data = json.loads(json_string)
    print(json_data[0]['b_name'])
    print(json_data[0]['b_blocks'][0]['b_raw_price'])
    print(json_data[0]['b_blocks'][1]['b_raw_price'])
    print(json_data[1]['b_name'])
    print(json_data[1]['b_blocks'][0]['b_raw_price'])
    print(json_data[1]['b_blocks'][1]['b_raw_price'])


if __name__ == '__main__':
    # main()
    parsing_html()
