import asyncio
import aiogram
from aiogram.utils.exceptions import RetryAfter
import aiohttp
from aiohttp import ClientProxyConnectionError
from bs4 import BeautifulSoup
import json
import csv
import time
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import bot_token, chat_id, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, filter_quoteVolume, time_restart, value_track_type, check_time, inclusion_quote_volume_filter

bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

previous_low_prices = {}
previous_high_prices = {}
previous_quote_volume = {}

async def fetch_data():
    async def read_csv():
        with open(f'id.csv', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=' ', quotechar='|')
            urls = list(reader)
        return urls

    urls = await read_csv()

    async with aiohttp.ClientSession(
            connector=aiohttp.connector.TCPConnector(ssl=False, limit=None, force_close=True)) as session:
        for url in urls:
            futures = url[0]
            url = f'https://www.binance.com/fapi/v1/ticker/24hr?symbol={futures}'
            try:
                async with session.get(url,
                                       proxy=f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}') as response:
                    src = await response.text()
            except ClientProxyConnectionError as e:
                print(f'Failed to connect to the proxy: {PROXY_HOST}:{PROXY_PORT}')
                return

            soup = BeautifulSoup(src, 'html.parser')
            json_data = soup.string
            data = json.loads(json_data)
            symbol = data['symbol']
            high_price = float(data['highPrice'])
            low_price = float(data['lowPrice'])
            quote_volume = float(data['quoteVolume'])
            # Проверка quote_volume
            if inclusion_quote_volume_filter:
                if quote_volume > filter_quoteVolume:
                    if track_type == "max" or track_type == "both":
                        if futures in previous_high_prices and high_price > previous_high_prices[futures]:
                            message_high_price = f'{symbol} ++++: {high_price}'
                            await send_message_to_group(message_high_price)
                            print(message_high_price)
                        previous_high_prices[futures] = high_price

                    if track_type == "min" or track_type == "both":
                        if futures in previous_low_prices and low_price < previous_low_prices[futures]:
                            message_low_price = f'{symbol} ----: {low_price}'
                            await send_message_to_group(message_low_price)
                            print(message_low_price)
                        previous_low_prices[futures] = low_price
            else:
                if track_type == "max" or track_type == "both":
                    if futures in previous_high_prices and high_price > previous_high_prices[futures]:
                        message_high_price = f'{symbol} ++++: {high_price}'
                        await send_message_to_group(message_high_price)
                        print(message_high_price)
                    previous_high_prices[futures] = high_price

                if track_type == "min" or track_type == "both":
                    if futures in previous_low_prices and low_price < previous_low_prices[futures]:
                        message_low_price = f'{symbol} ----: {low_price}'
                        await send_message_to_group(message_low_price)
                        print(message_low_price)
                    previous_low_prices[futures] = low_price
    # Закрытие сессии и коннектора
    await session.close()


async def send_message_to_group(message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except aiogram.utils.exceptions.RetryAfter as e:
        delay = e.timeout
        print(f"Flood control exceeded. Retry in {delay} seconds.")
        await asyncio.sleep(delay)
        await send_message_to_group(message)


async def main():
    while True:
        await fetch_data()
        await asyncio.sleep(check_time)


async def schedule_script():
    loop = asyncio.get_event_loop()
    loop.create_task(main())

    while True:
        await asyncio.sleep(60 * time_restart)  # Подождать 60 минут
        loop.create_task(main())  # Запустить скрипт заново


if __name__ == '__main__':
    track_type = value_track_type  # Установите "max", "min" или "both" в зависимости от ваших требований
    asyncio.run(schedule_script())
