# from binance.client import Client
# import config
# import pandas as pd
# import time
#
# client = Client(config.api_key, config.api_secret)
#
# def top_coin():
#     all_tickers = pd.DataFrame(client.get_ticker())
#     usdt = all_tickers[all_tickers.symbol.str.contains('USDT')]
#     work = usdt[~((usdt.symbol.str.contains('UP'))| ((usdt.symbol.str.contains('DOWN'))))]
#     top_coin = work[work.priceChangePercent == work.priceChangePercent.max()]
#     top_coin = top_coin.symbol.values[0]
#     return top_coin
#
# def last_data(symbol, interval, lookback):
#     frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'min ago UTC'))
#     frame = frame.iloc[:,:6]
#     frame.columns = ['Time', 'Open', 'Higt', 'Low', 'Close', 'Valime']
#     frame = frame.set_index('Time')
#     frame.index = pd.to_datetime(frame.index, unit='ms')
#     frame = frame.astype(float)
#     return frame
# def strategy(buy_amt, SL=0.985, Target=1.02, open_position=False):
#     try:
#         # asset = top_coin()
#         asset = 'ETHUSDT'
#         df = last_data(asset, '1m', '120')
#     except:
#         time.sleep(61)
#         # asset = top_coin()
#         asset = 'ETHUSDT'
#         df = last_data(asset, '1m', '120')
#     #Обьем монет которые мы купиЫ
#     qty = round(buy_amt/df.Close.iloc[-1], 1)
#     print(qty)
#     print(asset)
#     # if ((df.Close.pct_change() + 1).cumprod()).iloc[-1] > 1:
#     #     print(asset)
#     #     print(df.Close.iloc[-1])
#     #     print(qty)
#     #     order = client.cancel_order(symbol=asset, side='BUY', type='MARKET', quantity=qty)
#     #     print(order)
#     #     buyprice = float(order['fills'][0]['price'])
#     #     open_position = True
#     #     while open_position:
#     #         try:
#     #             df = last_data(asset, '1m', '2')
#     #         except:
#     #             print('Restart 1min')
#     #             time.sleep(61)
#     #             df = last_data(asset, '1m', '2')
#     #         print(f'Price ' + str(df.Close[-1]))
#     #         print(f'Target ' + str(buyprice * Target))
#     #         print(f'STOP ' + str(buyprice * SL))
#     #         if df.Close[-1] <= buyprice * SL or df.Close[-1] >= buyprice * Target:
#     #             order = client.cancel_order(symbol=asset, side='SELL', type='MARKET', quantity = qty)
#     #             print(order)
#     #             break
#     # else:
#     #     print('No find')
#     #     time.sleep(20)
# while True:
#     strategy(10)


#
# from binance.client import Client
# from binance.websockets import BinanceSocketManager
# from binance.enums import *
# from talib.abstract import *
# import pandas as pd
# import numpy as np
#
# api_key = "YOUR_API_KEY"
# api_secret = "YOUR_API_SECRET"
#
# client = Client(api_key, api_secret)
#
# balance = 1000.0  # Ваш начальный баланс
# buy_price = None  # Цена покупки
# buy_qty = None  # Количество купленных монет
#
# def process_message(msg):
#     global balance, buy_price, buy_qty
#     # Получаем цену в реальном времени
#     price = float(msg['c'])
#     symbol = msg['s']
#
#     # Получаем исторические данные
#     candles = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE)
#
#     # Преобразуем данные в DataFrame
#     df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
#     df['close'] = df['close'].astype(float)
#
#     # Вычисляем MACD
#     macd, signal, hist = MACD(df['close'])
#
#     # Если MACD > signal и цена повышается, оформляем лимитный ордер на покупку
#     if macd.iloc[-1] > signal.iloc[-1] and price > df['close'].iloc[-1] and balance > 0:
#         buy_qty = balance / price
#         balance = 0
#         buy_price = price
#         # Закомментировал реальную торговлю для безопасности
#         # order = client.order_limit_buy(symbol=symbol, quantity=buy_qty, price=str(price))
#         print(f"Bought {buy_qty} of {symbol} at {price}")
#
#     # Если цена упала на 10% или более с момента последней покупки, оформляем ещё один лимитный ордер на покупку
#     if buy_price is not None and price <= buy_price * 0.9 and balance > 0:
#         buy_qty = balance / price
#         balance = 0
#         buy_price = price
#         # Закомментировал реальную торговлю для безопасности
#         # order = client.order_limit_buy(symbol=symbol, quantity=buy_qty, price=str(price))
#         print(f"Bought {buy_qty} of {symbol} at {price}")
#
# bsm = BinanceSocketManager(client)
# # Измените 'BTCUSDT' на нужную вам валютную пару
# conn_key = bsm.start_symbol_ticker_socket('BTCUSDT', process_message)
# bsm.start()


import nest_asyncio
import numpy as np
import pandas as pd
import asyncio
from binance.client import Client
from binance import BinanceSocketManager
from config import PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS,api_key, api_secret
# proxy = random.choice(proxies)
# proxy_host = proxy[0]
# proxy_port = proxy[1]
# proxy_user = proxy[2]
# proxy_pass = proxy[3]
#
# proxi = {
#     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{proxy_host}:{proxy_port}',
#     'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
# }


client = Client(api_key, api_secret)
ST = 7
LT = 25

def get_history(symbol, LT):
    df = pd.DataFrame(client.get_historical_klines(symbol, '1d', str(LT) + 'days ago UTC', '1 day ago UTC'))
    closes = pd.DataFrame(df[4])
    closes.columns = ['Close']
    closes['ST'] = closes.Close.rolling(ST-1).sum()
    closes['LT'] = closes.Close.rolling(LT-1).sum()
    closes.dropna(inplace=True)
    return  closes

def live_SMA(hist, live):
    live_ST = (hist['ST'].values + live.Price.values) / ST
    live_LT = (hist['LT'].values + live.Price.values) / LT
    return  live_LT, live_ST
def create_frame(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df

async def main(coin, qty, SL_limit, ope_position = False, buyprice = 0):
    bm = BinanceSocketManager(client)
    ts = bm.trade_socket(coin)
    hist = get_history(coin, LT)
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res:
                live = float(res['p'])
                frame = create_frame(res)
                live_ST, live_LT = live_SMA(hist, frame)
                print(live_ST , live_LT)
                if live_ST > live_LT and not ope_position:
                    order = client.create_order(symbol=coin, side= 'BUY', type='MARKET', quantity=qty)
                    print(order)
                    buyprice = float(order['fills'][0]['price'])
                    ope_position = True
                if ope_position:
                    if frame.Price[0] < buyprice * SL_limit or frame.Price[0] > 1.02 * buyprice:
                        order = client.create_order(symbol=coin, side = 'SELL', type='MARKET', quantity=qty)
                        print(order)
                        ope_position = False
                        loop.stop()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main('ETHUSDT', 10, 0.999))
    loop.close()

# def gethistoricals (symbol, LT):
#   df = pd.DataFrame(client.get_historical_klines(symbol, '1d',
#                                                  str(LT) + 'days ago UTC',
#                                                  '1 day ago UTC'))
#   closes = pd.DataFrame(df[4])
#   closes.columns = ['Close']
#   closes['ST'] = closes.Close.rolling(ST-1).sum()
#   closes['LT'] = closes.Close.rolling(LT-1).sum()
#   closes.dropna(inplace=True)
#   return closes
#
# historicals = gethistoricals('BTCUSDT', LT)
#
# def liveSMA(hist, live):
#   liveST = (hist['ST'].values + live.Price.values) / ST
#   liveLT = (hist['LT'].values + live.Price.values) / LT
#   return liveST, liveLT
#
# def createframe(msg):
#   df = pd.DataFrame([msg])
#   df = df.loc[:,['s', 'E', 'p']]
#   df.columns = ['symbol', 'Time', 'Price']
#   df.Price = df.Price.astype(float)
#   df.Time = pd.to_datetime(df.Time, unit='ms')
#   return df
#
# async def main(coin, qty, SL_limit, open_position = False):
#   bm = BinanceSocketManager(client)
#   ts = bm.trade_socket(coin)
#   async with ts as tscm:
#     while True:
#       res = await tscm.recv()
#       if res:
#         frame = createframe(res)
#         print(frame)
#         livest, livelt = liveSMA(historicals, frame)
#         if livest > livelt and not open_position:
#           print('Open Order')
#           open_position = True
#         if open_position:
#           if frame.Price[0] < buyprice * SL_limit or frame.Price[0] > 1.02 * buyprice:
#             print('Close Order')
#             loop.stop()
#
# if __name__ == "__main__":
#   loop = asyncio.get_event_loop()
#   loop.run_until_complete(main('LINKUSDT', 10, 0.999))

