import websockets
import asyncio
import json


async def main_trade():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(uri) as websocket:
        print("Соединение установлено.")
        while True:
            response = await websocket.recv()
            trade_data = json.loads(response)
            print_trade_data(trade_data)


def print_trade_data(trade_data):
    # Извлекаем и выводим детали каждой сделки
    event_time = trade_data["E"]  # Время события
    trade_id = trade_data["t"]  # ID сделки
    price = trade_data["p"]  # Цена сделки
    quantity = trade_data["q"]  # Количество
    buyer_order_id = trade_data["b"]  # ID ордера покупателя
    seller_order_id = trade_data["a"]  # ID ордера продавца
    trade_time = trade_data["T"]  # Время сделки
    is_buyer_maker = trade_data["m"]  # Покупатель является маркет-мейкером?

    print(f"Сделка #{trade_id} на {trade_time}:")
    print(f"Цена: {price}")
    print(f"Количество: {quantity}")
    print(f"ID ордера покупателя: {buyer_order_id}")
    print(f"ID ордера продавца: {seller_order_id}")
    print(f"Покупатель является маркет-мейкером: {'да' if is_buyer_maker else 'нет'}")
    print()


async def main_order_book():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"
    async with websockets.connect(uri) as websocket:
        print("Соединение установлено.")
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print("Получены данные стакана ордеров:")
            print(data)
            process_order_book(data)


def process_order_book(data):
    last_update_id = data["lastUpdateId"]  # ID последнего обновления стакана
    bids = data["bids"]  # Список заявок на покупку
    asks = data["asks"]  # Список заявок на продажу

    print(f"Последнее обновление ID: {last_update_id}")
    print("Лучшие заявки на покупку:")
    for bid in bids:
        price, quantity = bid
        print(f"Цена: {price}, Количество: {quantity}")

    print("Лучшие заявки на продажу:")
    for ask in asks:
        price, quantity = ask
        print(f"Цена: {price}, Количество: {quantity}")


if __name__ == "__main__":
    asyncio.run(main_trade())
    asyncio.run(main_order_book())
