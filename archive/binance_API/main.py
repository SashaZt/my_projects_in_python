import datetime
import asyncio
import aiohttp
from aiohttp import ClientProxyConnectionError
import json
import csv
import time
from config import  PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, api_key, api_secret



async def fetch_data():
    async def read_csv():
        with open(f'id.csv', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=' ', quotechar='|')
            urls = list(reader)
        return urls

    urls = await read_csv()

    async with aiohttp.ClientSession(
            connector=aiohttp.connector.TCPConnector(ssl=False, limit=None, force_close=True)) as session:
        for url in urls[39:40]:
            futures = url[0]
            url_24 = f'https://www.binance.com/fapi/v1/ticker/24hr?symbol={futures}'
            url_trade = f'https://www.binance.com/api/v1/aggTrades?limit=80&symbol={futures}'

            # try:
            #     async with session.get(url_24,
            #                            proxy=f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}') as response:
            #         data = await response.json()
            #     symbol_24 = data['symbol']
            #     high_price_24 = float(data['highPrice'])
            #     low_price_24 = float(data['lowPrice'])
            #     quote_volume_24 = float(data['quoteVolume'])
            #     print(symbol_24, high_price_24, low_price_24, quote_volume_24)
            # except ClientProxyConnectionError as e:
            #     print(f'Failed to connect to the proxy: {PROXY_HOST}:{PROXY_PORT}')

            try:
                async with session.get(url_trade,
                                       proxy=f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}') as response:
                    data_trade = await response.json()
                for trade in data_trade:
                    pr_trade = trade['p']
                    q_trade = trade['q']
                    time_trade = trade['T']
                    timestamp = time_trade / 1000.0  # Преобразуем миллисекунды в секунды
                    dt_object = datetime.datetime.fromtimestamp(timestamp)
                    formatted_time = dt_object.strftime('%H:%M:%S')  # форматируем время в формат HH:MM:SS
                    print(pr_trade, q_trade, formatted_time)
            except ClientProxyConnectionError as e:
                print(f'Failed to connect to the proxy: {PROXY_HOST}:{PROXY_PORT}')

            await asyncio.sleep(1)

async def main():
    while True:
        await fetch_data()

if __name__ == '__main__':
    asyncio.run(main())
