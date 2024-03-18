import glob
import re
import csv
import asyncio
import aiofiles
from bs4 import BeautifulSoup


async def scrape_data(file_path):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        src = await f.read()

    soup = BeautifulSoup(src, 'lxml')
    script = soup.find('script', string=re.compile(r'window\.dataLayer\.push\({.*}\);', re.DOTALL))

    data = script.text
    item = re.search(
        r"ecommerce: {[^}]*?item_name: '([^']*)',[^}]*?item_id: '([^']*)',[^}]*?price: '([^']*)',[^}]*?item_brand: '([^']*)',[^}]*?item_category: '([^']*)'",
        data, re.DOTALL)
    item_name = item.group(1)
    item_id = item.group(2)
    price = item.group(3)
    item_brand = item.group(4)
    item_category = item.group(5)
    description = soup.find('div', attrs={
        'class': 'p-3 product-info-collapse-body-inner product-info-content font-14 nc-text'}).text.strip().replace("\n", "")

    values = [prop.text.strip() for prop in soup.find_all('div', class_='property-value')]
    return [item_name, item_id, price, item_brand, item_category, description, *values]


async def write_to_csv(filename, rows):
    async with aiofiles.open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            await writer.writerow(row)


async def process_files():
    lang = ['ua', 'ru']
    for i in lang:
        target_pattern = f"C:\\scrap_tutorial-master\\grandinstrument\\data_{i}\\*.html"
        files_html = glob.glob(target_pattern)
        data = []

        rows = []
        for file_path in files_html[:21]:
            scraped_data = await scrape_data(file_path)
            item_category_ua, item_category_ru = '', ''
            description_ua, description_ru = '', ''
            if i == 'ua':
                item_category_ua = scraped_data[4]
                description_ua = scraped_data[5]
            elif i == 'ru':
                item_category_ru = scraped_data[4]
                description_ru = scraped_data[5]

            rows.append([scraped_data[0], scraped_data[1], scraped_data[2], scraped_data[3], item_category_ua, item_category_ru, description_ua, description_ru])

        await write_to_csv('data.csv', rows)


async def main():
    await process_files()


if __name__ == '__main__':
    asyncio.run(main())
