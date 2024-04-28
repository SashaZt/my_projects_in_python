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
    try:
        # Устанавливаем соединение с сервером
        async with websockets.connect('wss://stream.binance.com:9443/ws/btcusdt@trade') as ws:
            print("Соединение установлено.")
            while True:
                try:
                    # Получаем данные
                    data = await ws.recv()
                    print("Получены данные:")
                    print(data)  # Вывод всех данных

                    # Парсим JSON
                    trade_data = json.loads(data)

                    # Извлекаем и выводим информацию о сделке
                    event_type = trade_data['e']  # Тип события
                    event_time = trade_data['E']  # Время события
                    symbol = trade_data['s']  # Символ торговой пары
                    trade_id = trade_data['t']  # ID сделки
                    price = float(trade_data['p'])  # Цена сделки
                    quantity = float(trade_data['q'])  # Объем сделки
                    buyer_order_id = trade_data['b']  # ID ордера покупателя
                    seller_order_id = trade_data['a']  # ID ордера продавца
                    trade_time = trade_data['T']  # Время сделки
                    is_buyer_maker = trade_data['m']  # Покупатель является маркет-мейкером?

                    # Выводим подробную информацию о сделке
                    print(f"Сделка на {symbol}:")
                    print(f"ID сделки: {trade_id}")
                    print(f"Цена: {price}")
                    print(f"Объем: {quantity}")
                    print(f"ID ордера покупателя: {buyer_order_id}")
                    print(f"ID ордера продавца: {seller_order_id}")
                    print(f"Время сделки (мс с эпохи Unix): {trade_time}")
                    print(f"Покупатель - маркет-мейкер: {'да' if is_buyer_maker else 'нет'}")
                    print()
                except json.JSONDecodeError:
                    print("Ошибка декодирования JSON.")
                except KeyError as e:
                    print(f"Ключ не найден в данных: {e}")
    except Exception as e:
        print(f"Ошибка соединения: {e}")

if __name__ == '__main__':
    asyncio.run(main())