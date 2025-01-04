import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from matplotlib.dates import MinuteLocator, DateFormatter

# Шаг 1: Загрузить данные из файла trades.json
with open('trades.json', 'r', encoding="utf-8") as file:
    trades = [json.loads(line) for line in file]

# Шаг 2: Преобразовать время и округлить до ближайшей минуты
for trade in trades:
    trade['Время сделки'] = datetime.strptime(trade['Время сделки'], "%Y-%m-%d %H:%M:%S").replace(second=0)

# Преобразовать в DataFrame
df = pd.DataFrame(trades)

# Шаг 3: Суммировать количество сделок по минутам для покупок и продаж
df['Количество'] = df['Количество'].astype(float)
df['Покупка или продажа'] = df['Покупка или продажа:'].str.strip()

# Группировать по покупке и продаже
df_pokupka = df[df['Покупка или продажа'] == 'Покупка'].groupby('Время сделки')['Количество'].sum().reset_index()
df_prodazha = df[df['Покупка или продажа'] == 'Продажа'].groupby('Время сделки')['Количество'].sum().reset_index()

# Определить полный диапазон времени для обоих графиков
all_times = pd.date_range(min(df['Время сделки']), max(df['Время сделки']), freq='min')

# Объединить с полным временным диапазоном, заполнив отсутствующие значения нулями
df_pokupka = pd.merge(pd.DataFrame({'Время сделки': all_times}), df_pokupka, on='Время сделки', how='left').fillna(0)
df_prodazha = pd.merge(pd.DataFrame({'Время сделки': all_times}), df_prodazha, on='Время сделки', how='left').fillna(0)

# Увеличиваем размер графика
plt.figure(figsize=(40, 20))

# График для покупок
plt.subplot(1, 2, 1)
plt.plot(df_pokupka['Время сделки'], df_pokupka['Количество'])
plt.xlabel('Время сделки')
plt.ylabel('Общее количество')
plt.title('Суммарное количество покупок по времени')
plt.xticks(rotation=45)
plt.gca().xaxis.set_major_locator(MinuteLocator(interval=10))  # Разделение по 10 минут
plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))
plt.gca().tick_params(axis='x', labelsize=10)

# График для продаж
plt.subplot(1, 2, 2)
plt.plot(df_prodazha['Время сделки'], df_prodazha['Количество'])
plt.xlabel('Время сделки')
plt.ylabel('Общее количество')
plt.title('Суммарное количество продаж по времени')
plt.xticks(rotation=45)
plt.gca().xaxis.set_major_locator(MinuteLocator(interval=10))  # Разделение по 10 минут
plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))
plt.gca().tick_params(axis='x', labelsize=10)

plt.tight_layout()
plt.show()
