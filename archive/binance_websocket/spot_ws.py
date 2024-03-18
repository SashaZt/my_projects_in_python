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


