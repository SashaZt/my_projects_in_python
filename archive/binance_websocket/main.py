import websockets
import asyncio
import json
from datetime import datetime, timezone, timedelta
import csv
import math
import aiomysql
import os
from collections import defaultdict
import aiofiles
import pandas as pd


# Формируем данные для записи об ордерах
def format_trade_data(trade_data):
    # Конвертируем время события из UNIX в UTC+3
    trade_time = datetime.fromtimestamp(
        trade_data["T"] / 1000, tz=timezone.utc
    ) + timedelta(hours=3)
    formatted_time = trade_time.strftime("%Y-%m-%d %H:%M:%S")
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
        "Покупка или продажа:": buying_or_selling,
    }
    return formatted_data


# Сохраняем лучшие заявки на покупку и продажу
async def process_order_book(data):
    bids = data["bids"]  # Список заявок на покупку
    asks = data["asks"]  # Список заявок на продажу
    # Получаем текущее время в UTC
    current_utc_time = datetime.utcnow()

    # Добавляем 3 часа к текущему времени
    moscow_time = current_utc_time + timedelta(hours=3)

    # Преобразуем время в строку в нужном формате
    formatted_time = moscow_time.strftime("%Y-%m-%d %H:%M:%S")
    # покупка
    async with aiofiles.open("bids.json", "a", encoding="utf-8") as file:
        for bid in bids:
            price, quantity = bid
            formatted_data_bids = {
                "Цена": price,
                "Количество": quantity,
                "Время события": formatted_time,
            }
            await file.write(json.dumps(formatted_data_bids, ensure_ascii=False) + "\n")

    # продажа
    async with aiofiles.open("asks.json", "a", encoding="utf-8") as file:
        for ask in asks:
            price, quantity = ask
            formatted_data_asks = {
                "Цена": price,
                "Количество": quantity,
                "Время события": formatted_time,
            }
            await file.write(json.dumps(formatted_data_asks, ensure_ascii=False) + "\n")


# Распределяем по потокам Depth и Trade
async def receive_data(websocket, label):
    while True:
        response = await websocket.recv()
        if label == "Depth":
            data = json.loads(response)
            await process_order_book(data)
        elif label == "Trade":
            trade_data = json.loads(response)
            formatted_data = format_trade_data(trade_data)
            async with aiofiles.open("trades.json", "a", encoding="utf-8") as file:
                await file.write(json.dumps(formatted_data, ensure_ascii=False) + "\n")


# Указывае ссылки uri_depth и uri_trade
async def main_order_book_and_trade():
    uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    # uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth100@100ms"
    uri_trade = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    async with websockets.connect(uri_depth) as websocket_depth, websockets.connect(
        uri_trade
    ) as websocket_trade:
        print("Соединение установлено.")
        # Создаём асинхронные задачи для каждого потока данных
        task_depth = asyncio.create_task(receive_data(websocket_depth, "Depth"))
        task_trade = asyncio.create_task(receive_data(websocket_trade, "Trade"))

        # Ожидаем завершения обеих задач (это произойдёт, если WebSocket соединение будет закрыто)
        await asyncio.gather(task_depth, task_trade)


# Основная функция запуска программы
# async def run_for_a_while(number_of_seconds):

#     try:
#         # Запускаем main_trade на 10 минут (600 секунд)
#         await asyncio.wait_for(main_order_book_and_trade(), number_of_seconds)
#     except asyncio.TimeoutError:
#         print("Время работы программы истекло")


async def run_forever():
    # database = await get_database_connection()
    await main_order_book_and_trade()


# # Формирование отчета
# def report():
#     def process_file(
#         file_name, time_key, quantity_key, filter_key=None, filter_value=None
#     ):
#         """Обрабатывает файл для подсчета количества данных по минутам."""
#         quantity_per_minute = defaultdict(float)
#         with open(file_name, "r", encoding="utf-8") as file:
#             for line in file:
#                 data = json.loads(line)
#                 if (
#                     filter_key is None
#                     or data.get(filter_key, "").strip() == filter_value
#                 ):
#                     event_time = datetime.strptime(data[time_key], "%Y-%m-%d %H:%M:%S")
#                     minute_key = event_time.replace(second=0, microsecond=0)
#                     quantity_per_minute[minute_key] += float(data[quantity_key])
#         return quantity_per_minute

#     def write_results(results, label, file_path):
#         """Записывает результаты подсчета по минутам в файл."""
#         with open(file_path, "a", encoding="utf-8") as file:
#             file.write(f"{label}\n")
#             for minute, total_quantity in sorted(results.items()):
#                 file.write(
#                     f"Время: {minute}, Суммарное количество: {total_quantity:.8f}\n"
#                 )

#     output_file = "report_results.txt"
#     # Удаляем файл, если он уже существует
#     if os.path.exists(output_file):
#         os.remove(output_file)

#     # Подсчет данных для различных файлов и условий
#     quantity_per_minute_asks = process_file("asks.json", "Время события", "Количество")
#     write_results(quantity_per_minute_asks, "Ордера на продажу:", output_file)

#     quantity_per_minute_bids = process_file("bids.json", "Время события", "Количество")
#     write_results(quantity_per_minute_bids, "Ордера на покупку:", output_file)

#     sales_per_minute = process_file(
#         "trades.json", "Время сделки", "Количество", "Покупка или продажа:", "Продажа"
#     )
#     write_results(sales_per_minute, "Совершенная сделка на продажу:", output_file)

#     purchases_per_minute = process_file(
#         "trades.json", "Время сделки", "Количество", "Покупка или продажа:", "Покупка"
#     )
#     write_results(purchases_per_minute, "Совершенная сделка на покупку:", output_file)


# # Удаляем старые файлы
# def remove_if_exists():
#     files_to_check = ["trades.json", "bids.json", "asks.json"]
#     current_directory = os.getcwd()
#     for file_name in files_to_check:
#         file_path = os.path.join(current_directory, file_name)
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             print(f"Файл {file_path} удален.")


if __name__ == "__main__":
    # remove_if_exists()
    print("Сколько времени нужно что бы скрипт работал? Введите в секунах")
    number_of_seconds = int(input())
    asyncio.run(run_for_a_while(number_of_seconds))
    # report()
