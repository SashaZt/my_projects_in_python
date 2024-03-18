import aiohttp
import asyncio
import csv
import os

current_directory = os.getcwd()
temp_directory = 'temp'
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')

async def fetch(session, sku, filename, headers):
    params = {
        'action': 'catalog_price_view',
        'code': sku,
        'id_currency': '1',
        'cross_advance': ['0', '1'],
    }
    try:
        async with session.get('https://lal-auto.ru/', params=params, headers=headers) as response:
            src = await response.text()
            with open(filename, "w", encoding='utf-8') as file:
                file.write(src)
    except Exception as e:
        print(f"Error fetching SKU {sku}: {e}")
def extract_data_from_csv():
    csv_filename = 'data.csv'
    columns_to_extract = ['price', 'Numer katalogowy części', 'Producent części']

    data = []  # Создаем пустой список для хранения данных

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')  # Указываем разделитель точку с запятой

        for row in reader:
            item = {}  # Создаем пустой словарь для текущей строки
            for column in columns_to_extract:
                item[column] = row[column]  # Извлекаем значения только для указанных столбцов
            data.append(item)  # Добавляем словарь в список
    return data


async def main():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Cookie': 'PHPSESSID=erp05a6c0d8a9kvdres8ilh1p0',
        'DNT': '1',
        'Pragma': 'no-cache',
        # 'Referer': 'https://lal-auto.ru/?action=catalog_price_view&code=602+0008+00&id_currency=1&cross_advance=0&cross_advance=1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    data_csv = extract_data_from_csv()
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(data_csv), 1000):
            tasks = []
            for item in data_csv[i:i + 1000]:
                sku = item['Numer katalogowy części'].replace(" ", "").replace("/", "")
                filename = os.path.join(product_path, sku + '.html')
                if not os.path.exists(filename):
                    tasks.append(fetch(session, sku, filename, headers))
            if tasks:
                await asyncio.gather(*tasks)
                if i + 1000 < len(data_csv):
                    await asyncio.sleep(10)


asyncio.run(main())