from bs4 import BeautifulSoup
import shutil
import csv
import glob
import re
import requests
import json
import cloudscraper
import os
import time
import undetected_chromedriver as webdriver
from selenium.common.exceptions import TimeoutException
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv
def parsing():
    files = [f"C:\\ChatExport_2023-06-12\\messages.html",
             f"C:\\ChatExport_2023-06-12\\messages2.html"]
    with open(f"data.csv", "w",
              errors='ignore', encoding="utf-8") as file_csv:
        writer = csv.writer(file_csv, delimiter=",", lineterminator="\r")
        writer.writerow(
            (
                'Handle', 'Title', 'Body(HTML)', 'Vendor', 'Type', 'Tags', 'Published', 'Option1'
                                                                                        'Name', 'Option1' 'Value',
                'Option2 Name', 'Option2 Value', 'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams',
                'Variant Inventory Tracker', 'Variant Inventory Qty', 'Variant Inventory Policy',
                'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping',
                'Variant Taxable', 'Variant Barcode', 'Image Src', 'Image Alt Text', 'Gift Card', 'Google Shopping/MPN',
                'Google Shopping/Age Group', 'Google Shopping/Gender', 'Google Shopping/Google Product Category',
                'SEO Title, SEO Description', 'Google Shopping/AdWords Grouping', 'Google Shopping/AdWords Labels',
                'Google Shopping/Condition', 'Google Shopping/Custom Product', 'Google Shopping/Custom Label 0',
                'Google Shopping/Custom Label 1', 'Google Shopping/Custom Label 2', 'Google Shopping/Custom Label 3',
                'Google Shopping/Custom Label 4', 'Variant Image', 'Variant Weight Unit'
            ))
    for i in files:
        with open(i, encoding="utf-8") as file:
             src = file.read()
        # print(i)
        soup = BeautifulSoup(src, 'lxml')
        regex = re.compile('^message default clearfix.*')
        messages = soup.find_all('div', class_=regex)

        for message in messages:
            message.id = message.get('id')
            current_photo = message.find_next('a', class_='photo_wrap clearfix pull_left')
            try:
                photo_href = current_photo.get('href')
                source_photo_path = photo_href.replace("photos/", 'C:\\ChatExport_2023-06-12\\photos\\')
            except:
                print(f'Ошибка {message.id}')

            # Извлечение текста из div с классом "text"
            text_div = message.find('div', class_='text')
            if text_div:
                text = text_div.get_text(separator='\n', strip=True)
                text_lines = text.split('\n')
                if len(text_lines) >= 8 and re.match(r'^МРРЦ*', text_lines[-1]):  # Проверяем, что последняя строка начинается с "МРРЦ:"
                    name_photo = text_lines[0].replace('Арт ', 'art')
                    Title = text_lines[1]
                    Body_HTML = ', '.join(
                        text_lines[2:-1])  # Объединяем все строки, кроме первой, второй и последней, с помощью запятой
                    Variant_SKU = text_lines[0]
                    price = text_lines[-1]
                    Variant_Price = re.findall(r'\d+', price)[0]

                    filename = f"photo/{message.id}_{name_photo}.jpg"
                    shutil.copy(source_photo_path, filename)
                    data = [message.id, Title, Body_HTML, 'Greenzda', 'Clothing', '', '', '', '', '', '', '', '', Variant_SKU,
                            '',
                            '', '100', 'deny', 'manual', Variant_Price, '', '', '', '',
                            f'https://cdn.shopify.com/s/files/1/0699/5620/6899/files/{message.id}_{name_photo}.jpg', '', '', '',
                            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
                    with open(f"data.csv", "a",
                              errors='ignore', encoding="utf-8") as file:
                        writer = csv.writer(file, delimiter=",", lineterminator="\r")
                        writer.writerow((data))

                #
                # print(f"ID: {message.id}")
                # print(f"Text: {text}")
                # print(f"Photos: {photo_href}")



if __name__ == '__main__':
    # get_requests()
    # get_cloudscraper()
    # get_selenium()
    parsing()
