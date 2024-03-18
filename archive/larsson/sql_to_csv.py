import threading
import mysql.connector
import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor
from proxi import proxies
import concurrent.futures
from config import db_config, use_bd, use_table
import pandas as pd
from sqlalchemy import create_engine
# Замените эти значения на соответствующие параметры вашей базы данных
db_type = 'mysql'  # Пример: 'mysql', 'postgresql', 'sqlite'
username = 'python_mysql'
password = 'python_mysql'
host = 'localhost'
port = '3306'
db_name = 'larsson'

# Создание строки подключения
connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"

# Подключение к базе данных
engine = create_engine(connection_string)

# Запрос на извлечение данных
query = "SELECT * FROM larsson"

# Чтение данных в DataFrame и сохранение в CSV
df = pd.read_sql(query, engine)
df.to_csv('larsson_data.csv', index=False, sep=';')
