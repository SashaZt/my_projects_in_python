"""Выгрузка данных в csv"""
import pandas as pd

# Создаем соединение с базой данных через SQLAlchemy
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine

password = urlquote('4tz_{4!r%x8~E@W')
engine = create_engine(f'mysql+mysqlconnector://python_mysql:{password}@185.65.245.79/kupypai_com')

# Выполняем запрос и загружаем результаты в DataFrame
df = pd.read_sql_query("SELECT * FROM ad", engine)

# Сохраняем DataFrame в файл CSV
df.to_csv('ad.csv', index=False)