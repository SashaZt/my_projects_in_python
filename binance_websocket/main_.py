import asyncio
import json
from datetime import datetime, timedelta, timezone
from databases import Database
import websockets


# Асинхронное подключение к базе данных
async def get_database_connection():
    db_url = "mysql+aiomysql://python_mysql:python_mysql@127.0.0.1/crypto"
    database = Database(db_url)
    await database.connect()
    return database


async def save_to_database(database, table, data, event_time):
    query = f"""
        INSERT INTO {table} (price, quantity, event_time)
        VALUES (:price, :quantity, :event_time)
    """
    for item in data:
        await database.execute(
            query=query,
            values={"price": item[0], "quantity": item[1], "event_time": event_time},
        )


async def save_trade_data(database, trade_data):
    query = """
    INSERT INTO trades (id_deal, Price, Quantity, Event_time, Transaction_type)
    VALUES (:id_deal, :Price, :Quantity, :Event_time, :Transaction_type)
    """
    values = {
        "id_deal": trade_data["Сделка"],
        "Price": trade_data["Цена"],
        "Quantity": trade_data["Количество"],
        "Event_time": trade_data["Время сделки"],
        "Transaction_type": trade_data["Покупка или продажа:"],
    }
    await database.execute(query=query, values=values)


# Форматирование данных о сделках
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
        "Покупка или продажа:": buying_or_selling,
    }
    return formatted_data


# Обработка данных ордербука
async def process_order_book(database, data):
    bids = data.get("bids", [])
    asks = data.get("asks", [])
    current_utc_time = datetime.utcnow()
    moscow_time = current_utc_time + timedelta(hours=3)
    formatted_time = moscow_time.strftime("%Y-%m-%d %H:%M:%S")
    if bids:
        await save_to_database(database, "bids", bids, formatted_time)
    if asks:
        await save_to_database(database, "asks", asks, formatted_time)


# Обработка потока данных
async def receive_data(database, websocket, label):
    try:
        while True:
            response = await websocket.recv()
            if label == "Depth":
                data = json.loads(response)
                await process_order_book(database, data)
            elif label == "Trade":
                trade_data = json.loads(response)
                formatted_data = format_trade_data(trade_data)
                await save_trade_data(database, formatted_data)
    except websockets.ConnectionClosedError as e:
        print(f"Соединение WebSocket {label} было закрыто с ошибкой: {e}")
    except Exception as e:
        print(f"Произошла ошибка при получении данных {label}: {e}")


# Основная функция управления ордербуком и торгами
async def main_order_book_and_trade(database, number_of_seconds):
    uri_depth = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    uri_trade = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    try:
        async with websockets.connect(
            uri_depth, ping_interval=10
        ) as websocket_depth, websockets.connect(
            uri_trade, ping_interval=10
        ) as websocket_trade:
            print("Соединение установлено.")
            task_depth = asyncio.create_task(
                receive_data(database, websocket_depth, "Depth")
            )
            task_trade = asyncio.create_task(
                receive_data(database, websocket_trade, "Trade")
            )
            await asyncio.gather(task_depth, task_trade)
    except websockets.ConnectionClosedError as e:
        print(f"Соединение было закрыто с ошибкой: {e}")


# Основная функция запуска программы
async def run_for_a_while(number_of_seconds):
    database = await get_database_connection()
    try:
        await asyncio.wait_for(
            main_order_book_and_trade(database, number_of_seconds), number_of_seconds
        )
    except asyncio.TimeoutError:
        print("Время работы программы истекло")
    finally:
        await database.disconnect()
        print("Соединение с базой данных закрыто.")


if __name__ == "__main__":
    print("Сколько времени нужно чтобы скрипт работал? Введите в секундах")
    number_of_seconds = int(input())
    asyncio.run(run_for_a_while(number_of_seconds))
