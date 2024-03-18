import zipfile
import pickle
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
from selenium.webdriver.common.keys import Keys
import csv
import time
import glob


def parsing_product():
    datas = []
    # targetPattern = r"E:\DATA_webstaurantstore\*.html"
    targetPattern = r"E:\DATA_webstaurantstore\*.html"
    files_html = glob.glob(targetPattern)
    datas = []
    count = 0

    for item in files_html:
        count += 1
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        try:
            script = soup.find_all('script', type="application/json")[1].text.strip()[4:-3]
        except:
            print(item)
            continue
        try:
            data_json = json.loads(script)
        except:
            continue
        try:
            if data_json['productTemplates']:
                availability = data_json['productTemplates'][0]['isInStock']
                if availability:
                    av = 1
                else:
                    av = 0
                try:
                    product_name = data_json['productTemplates'][0]['header']
                except:
                    product_name = ""
                try:
                    product_sky = data_json['productTemplates'][0]['upc']
                except:
                    product_sky = ""
                try:
                    product_url = data_json['layoutConfiguration']['openGraphMeta']['url']
                except:
                    product_url = ""
                try:
                    product_price = data_json['layoutConfiguration']['openGraphMeta']['productPrice']['amount']
                except:
                    product_price = ""
                try:
                    product_price_tapa = data_json['productTemplates'][0]['unitOfMeasure']
                except:
                    product_price_tapa = ""
                try:
                    price_adn_tara = f"{product_price}/{product_price_tapa}"
                except:
                    price_adn_tara = ""
                try:
                    product_price_min = data_json['productTemplates'][0]['price']['minimumAdvertisedPriceProperties'][
                        'price']
                    price_adn_tara_min = f"{product_price_min}/{product_price_tapa}"
                except:
                    product_price_min = 0
                    price_adn_tara_min = 0

                datas.append(
                    [product_url, product_name, product_sky, price_adn_tara, price_adn_tara_min, av]
                )
                print(count)
            else:
                continue
        except:
            continue

    with open(f"test.csv", "a", errors='ignore') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerows(
            datas
        )
    # write_csv(datas)


if __name__ == '__main__':
    parsing_product()
