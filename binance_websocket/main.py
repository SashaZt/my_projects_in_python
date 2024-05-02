import websockets
import asyncio
import json
from datetime import datetime, timezone, timedelta
import aiofiles
import csv
import math
import os
import pandas as pd



async def main_trade():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(uri) as websocket:
        print("Соединение установлено.")
        async with aiofiles.open('trades.json', 'a', encoding='utf-8') as file:
            while True:
                response = await websocket.recv()
                trade_data = json.loads(response)
                formatted_data = format_trade_data(trade_data)
                await file.write(json.dumps(formatted_data, ensure_ascii=False) + '\n')

def format_trade_data(trade_data):
    # Конвертируем время события из UNIX в UTC+3
    trade_time = datetime.fromtimestamp(trade_data["T"] / 1000, tz=timezone.utc) + timedelta(hours=3)
    formatted_time = trade_time.strftime('%Y-%m-%d %H:%M:%S')
    # price = float(trade_data["p"])
    # rounded_price = math.ceil(price / 100.0) * 100  # Определение переменной rounded_price
    if trade_data["m"] is True:
        buying_or_selling = "Покупка"
    else:    
        buying_or_selling = "Продажа"

    # Форматируем данные для записи
    formatted_data = {
        "Сделка": trade_data["t"],
         "Цена": trade_data["p"],
        "Количество": trade_data["q"],
        # "ID ордера покупателя": trade_data["b"],
        # "ID ордера продавца": trade_data["a"],
        "Время сделки": formatted_time,
        "Покупка или продажа:": buying_or_selling
    }
    return formatted_data


def process_files(json_file, csv_file, xlsx_file):
    try:
        # Читаем JSON и записываем в CSV
        with open(json_file, 'r', encoding='utf-8') as file:
            data = [json.loads(line) for line in file]

        headers = data[0].keys() if data else []
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"Данные из {json_file} успешно записаны в {csv_file}")

        # Загружаем данные из CSV в DataFrame
        data_df = pd.read_csv(csv_file, encoding="utf-8")

        # Сохраняем данные из DataFrame в Excel
        data_df.to_excel(xlsx_file, index=False, engine="openpyxl")
        print(f"Данные из {csv_file} успешно записаны в {xlsx_file}")

    except Exception as e:
        print(f"Произошла ошибка при обработке файлов: {e}")

def json_to_csv():
    current_directory = os.getcwd()
    json_trades, csv_trades, xlsx_trades = 'trades.json', 'trades.csv', 'trades.xlsx'
    json_asks, csv_asks, xlsx_asks = 'asks.json', 'asks.csv', 'asks.xlsx'
    json_bids, csv_bids, xlsx_bids = 'bids.json', 'bids.csv', 'bids.xlsx'
    
    # Обработка файлов для трейдов, аскс и бидс
    process_files(json_trades, csv_trades, xlsx_trades)
    process_files(json_asks, csv_asks, xlsx_asks)
    process_files(json_bids, csv_bids, xlsx_bids)
    print(f"успешно добавлен файл {csv_trades}")
    # Открыть после тестов
    excel_file_path = os.path.join(current_directory, xlsx_trades)


async def main_order_book():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    # uri = "wss://stream.binance.com:9443/ws/btcusdt@depth50@100ms"
    async with websockets.connect(uri) as websocket:
        print("Соединение установлено.")
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print("Получены данные стакана ордеров:")
            print(data)
            process_order_book(data)


async def process_order_book(data):
    bids = data["bids"]  # Список заявок на покупку
    asks = data["asks"]  # Список заявок на продажу
    # Получаем текущее время в UTC
    current_utc_time = datetime.utcnow()

    # Добавляем 3 часа к текущему времени
    moscow_time = current_utc_time + timedelta(hours=3)

    # Преобразуем время в строку в нужном формате
    formatted_time = moscow_time.strftime('%Y-%m-%d %H:%M:%S')

    # Сохраняем лучшие заявки на покупку
    async with aiofiles.open('bids.json', 'a', encoding='utf-8') as file:
        for bid in bids:
            price, quantity = bid
            formatted_data_bids = {
                "Цена": price,
                "Количество": quantity,
                "Время события": formatted_time,
            }
            await file.write(json.dumps(formatted_data_bids,ensure_ascii=False) + '\n')
    
    # Сохраняем лучшие заявки на продажу
    async with aiofiles.open('asks.json', 'a', encoding='utf-8') as file:
        for ask in asks:
            price, quantity = ask
            formatted_data_asks = {
                "Цена": price,
                "Количество": quantity,
                "Время события": formatted_time,
            }
            await file.write(json.dumps(formatted_data_asks,ensure_ascii=False) + '\n') 
        
async def receive_data(websocket, label):
    while True:
        response = await websocket.recv()
        if label == "Depth":
            
            data = json.loads(response)
            await process_order_book(data)  # Использование await для асинхронной функции
        elif label == "Trade":
            trade_data = json.loads(response)
            formatted_data = format_trade_data(trade_data)
            async with aiofiles.open('trades.json', 'a', encoding='utf-8') as file:
                await file.write(json.dumps(formatted_data, ensure_ascii=False) + '\n')


async def main_order_book_and_trade():
    uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    # uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth100@100ms"
    uri_trade = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    async with websockets.connect(uri_depth) as websocket_depth, websockets.connect(uri_trade) as websocket_trade:
        print("Соединение установлено.")
        # Создаём асинхронные задачи для каждого потока данных
        task_depth = asyncio.create_task(receive_data(websocket_depth, "Depth"))
        task_trade = asyncio.create_task(receive_data(websocket_trade, "Trade"))
        
        # Ожидаем завершения обеих задач (это произойдёт, если WebSocket соединение будет закрыто)
        await asyncio.gather(task_depth, task_trade)
def print_unix_timestamp():
    # Получаем текущее время в UTC
    current_time_utc = datetime.now(timezone.utc)
    # Преобразуем время в UNIX timestamp
    unix_timestamp = int(current_time_utc.timestamp())
    print("Текущее время в UNIX timestamp:", unix_timestamp)

async def run_for_a_while():
    try:
        # Запускаем main_trade на 10 минут (600 секунд)
        await asyncio.wait_for(main_order_book_and_trade(), 20)
    except asyncio.TimeoutError:
        print("Время работы программы истекло")

if __name__ == "__main__":
    # asyncio.run(main_order_book_and_trade())
    
    # asyncio.run(run_for_a_while())
    # json_to_csv()
    
    
    asyncio.run(main_order_book())
