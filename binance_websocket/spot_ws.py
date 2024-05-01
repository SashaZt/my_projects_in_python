# import websocket
# import threading
#
# class SocketConn:
#     def __init__(self, url):
#         self.ws = websocket.WebSocketApp(url,
#                                          on_open=self.on_open,
#                                          on_message=self.on_message,
#                                          on_error=self.on_error,
#                                          on_close=self.on_close)
#
#     def on_open(self, ws):
#         print("Websocket was opened")
#
#     def on_message(self, ws, msg):
#         print(msg)
#
#     def on_error(self, ws, e):
#         print("Error", e)
#
#     def on_close(self, ws):
#         print('Closing')
#
#     def run_forever(self):
#         self.ws.run_forever()
#
#
# def start_socket(url):
#     sc = SocketConn(url)
#     sc.run_forever()
#
#
# threading.Thread(target=start_socket, args=('wss://stream.binance.com:9443/ws/bnbusdt@trade',)).start()
#


#
# import websocket
# import json
#
# try:
#     ws = websocket.create_connection("wss://stream.binance.com:9443/ws/bnbusdt@trade")
#     result = ws.recv()
#     result = json.loads(result)
#     print(result)
#     ws.close()
# except Exception as e:
#     print(f"Произошла ошибка при соединении: {e}")

import websockets
import asyncio
import json

async def main():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@depth20@1000ms"
    async with websockets.connect(uri) as websocket:
        print("Соединение установлено.")
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print("Получены данные стакана ордеров:")
            print(data)
            process_order_book(data)

def process_order_book(data):
    last_update_id = data['lastUpdateId']  # ID последнего обновления стакана
    bids = data['bids']  # Список заявок на покупку
    asks = data['asks']  # Список заявок на продажу

    print(f"Последнее обновление ID: {last_update_id}")
    print("Лучшие заявки на покупку:")
    for bid in bids:
        price, quantity = bid
        print(f"Цена: {price}, Количество: {quantity}")

    print("Лучшие заявки на продажу:")
    for ask in asks:
        price, quantity = ask
        print(f"Цена: {price}, Количество: {quantity}")

if __name__ == '__main__':
    asyncio.run(main())