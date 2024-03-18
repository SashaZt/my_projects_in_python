import asyncio
import aiofiles
import csv
import glob
from bs4 import BeautifulSoup

async def read_file(file_path):
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        return await f.read()

async def extract_data(file_path):
    src = await read_file(file_path)
    soup = BeautifulSoup(src, 'html.parser')
    try:
        name_product = soup.select_one('div.container-fluid h1').text.strip()
    except:
        name_product = ''
    try:
        categ_product = soup.select('div.bx-breadcrumb-item span')[-1].text.strip()
    except:
        categ_product = ''
    try:
        price_old = soup.select_one('div.product-item-detail-price-old').text.strip()
    except:
        price_old = ''
    try:
        price_new = soup.select_one('div.product-item-detail-price-current').text.strip()
    except:
        price_new = ''
    try:
        images = 'https://komfortmebli.com.ua' + soup.select_one('div.product-item-detail-slider-images-container div img')['src']
    except:
        images =''
    try:
        des = soup.select_one('div.product-item-detail-tab-content.active').text.strip().replace("\n", " ")
    except:
        des = ''

    values = []
    for i in range(1, 16):
        try:
            value = soup.select_one(
                f'div.col-xs-12 div.product-item-detail-tab-content dl dd:nth-of-type({i})').text.strip()
        except:
            value = ''
        values.append(value)

    return [name_product, categ_product, price_new, price_old, des, images] + values

async def main():
    target_pattern = r"data/*.html"
    files_html = glob.glob(target_pattern)

    with open("data.csv", mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(
            (
                'name_product', 'categ_product', 'price_new', 'price_old', 'Описание', 'images', 'Артикул', 'Висота', 'Ширина',
                'Глибина', 'Ціновий діапазон', 'Серія', 'Тип кухні', 'Можливість індивідуального замовлення', 'Гарантія',
                "Матеріал корпуса", 'Матеріал фасада', 'Упаковка', 'Наявність', 'Спосіб оплати'
            )
        )

    async with aiofiles.open("data.csv", mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        for file_path in files_html[:10]:
            data = await extract_data(file_path)
            await writer.writerow(data)

asyncio.run(main())