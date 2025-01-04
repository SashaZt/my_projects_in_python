# Рабочий код по загрузке данных из Binance в json
import pandas as pd
import asyncio
import websockets
import json
from datetime import datetime, timezone, timedelta
import aiofiles
import os

# Глобальные переменные для имен файлов
current_trade_file = None
current_bids_file = None
current_asks_file = None
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
trades_path = os.path.join(temp_path, "trades")
bids_path = os.path.join(temp_path, "bids")
asks_path = os.path.join(temp_path, "asks")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(trades_path, exist_ok=True)
os.makedirs(bids_path, exist_ok=True)
os.makedirs(asks_path, exist_ok=True)

# Списки для накопления данных
trade_data_list = []
bids_data_list = []
asks_data_list = []


def format_order_data(price, quantity, event_time):
    return {
        "Цена": price,
        "Количество": quantity,
        "Время события": event_time,
    }


# Формируем данные для записи об ордерах
def format_trade_data(trade_data):
    trade_time = datetime.fromtimestamp(
        trade_data["T"] / 1000, tz=timezone.utc
    ) + timedelta(hours=3)
    formatted_time = trade_time.strftime("%Y-%m-%d %H:%M:%S")
    buying_or_selling = "Покупка" if trade_data["m"] else "Продажа"

    formatted_data = {
        "Сделка": trade_data["t"],
        "Цена": trade_data["p"],
        "Количество": trade_data["q"],
        "Время сделки": formatted_time,
        "Покупка или продажа": buying_or_selling,
    }
    return formatted_data


# Сохраняем лучшие заявки на покупку и продажу
async def process_order_book(data):
    global bids_data_list, asks_data_list
    bids = data["bids"]
    asks = data["asks"]
    current_utc_time = datetime.now(timezone.utc)
    moscow_time = current_utc_time + timedelta(hours=3)
    formatted_time = moscow_time.strftime("%Y-%m-%d %H:%M:%S")

    for bid in bids:
        price, quantity = bid
        bids_data_list.append(format_order_data(price, quantity, formatted_time))

    for ask in asks:
        price, quantity = ask
        asks_data_list.append(format_order_data(price, quantity, formatted_time))


async def receive_data(websocket, label, filename_event):
    await filename_event.wait()
    while True:
        response = await websocket.recv()
        if label == "Depth":
            data = json.loads(response)
            await process_order_book(data)
        elif label == "Trade":
            trade_data = json.loads(response)
            trade_data_list.append(format_trade_data(trade_data))


async def update_filenames(filename_event):
    global current_trade_file, current_bids_file, current_asks_file
    while True:
        now = datetime.now(timezone.utc) + timedelta(hours=3)
        timestamp = now.strftime("%H_%M_%d_%m_%Y")
        current_trade_file = os.path.join(trades_path, f"{timestamp}_trades.json")
        current_bids_file = os.path.join(bids_path, f"{timestamp}_bids.json")
        current_asks_file = os.path.join(asks_path, f"{timestamp}_asks.json")
        filename_event.set()
        # print(
        #     f"Updated filenames: {current_trade_file}, {current_bids_file}, {current_asks_file}"
        # )
        await asyncio.sleep(60)
        filename_event.clear()


async def initialize_filenames(filename_event):
    global current_trade_file, current_bids_file, current_asks_file
    now = datetime.now(timezone.utc) + timedelta(hours=3)
    timestamp = now.strftime("%H_%M_%d_%m_%Y")
    current_trade_file = os.path.join(trades_path, f"{timestamp}_trades.json")
    current_bids_file = os.path.join(bids_path, f"{timestamp}_bids.json")
    current_asks_file = os.path.join(asks_path, f"{timestamp}_asks.json")
    filename_event.set()
    # print(
    #     f"Initialized filenames: {current_trade_file}, {current_bids_file}, {current_asks_file}"
    # )


async def save_data_to_file(file_name, data_list):
    async with aiofiles.open(file_name, "a", encoding="utf-8") as file:
        await file.write(json.dumps(data_list, ensure_ascii=False) + "\n")
    # print(f"Data saved to file: {file_name}")


async def periodic_save():
    global trade_data_list, bids_data_list, asks_data_list
    while True:
        await asyncio.sleep(60)  # Сохраняем данные каждую минуту
        await save_data_to_file(current_trade_file, trade_data_list)
        await save_data_to_file(current_bids_file, bids_data_list)
        await save_data_to_file(current_asks_file, asks_data_list)
        trade_data_list = []
        bids_data_list = []
        asks_data_list = []


async def main_order_book_and_trade():
    uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    uri_trade = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    filename_event = asyncio.Event()

    # Инициализация имен файлов до начала получения данных
    await initialize_filenames(filename_event)

    async with websockets.connect(uri_depth) as websocket_depth, websockets.connect(
        uri_trade
    ) as websocket_trade:
        print("Соединение установлено.")
        task_depth = asyncio.create_task(
            receive_data(websocket_depth, "Depth", filename_event)
        )
        task_trade = asyncio.create_task(
            receive_data(websocket_trade, "Trade", filename_event)
        )
        task_update_files = asyncio.create_task(update_filenames(filename_event))
        task_periodic_save = asyncio.create_task(periodic_save())

        await asyncio.gather(
            task_depth, task_trade, task_update_files, task_periodic_save
        )


if __name__ == "__main__":
    asyncio.run(main_order_book_and_trade())
