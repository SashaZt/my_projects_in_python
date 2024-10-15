import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import random
import csv
import xml.etree.ElementTree as ET
import re
import threading
import sys
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import shutil
import traceback
import sqlite3


class DynamicSQLite:
    def __init__(self, db_name):
        # Инициализировать соединение с базой данных SQLite
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_or_update_table(self, table_name, data):
        # Предполагается, что data - это список словарей
        for row in data:
            # Создать строку с определениями столбцов на основе ключей словаря
            columns = ", ".join([f'"{key}" TEXT' for key in row.keys()])
            # SQL-запрос для создания таблицы, если она не существует, включая автоинкрементируемый первичный ключ
            create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns});'
            self.cursor.execute(create_table_query)
            self.conn.commit()

            # Добавить новые столбцы, если их нет в текущей таблице
            existing_columns = [
                info[1]
                for info in self.cursor.execute(f'PRAGMA table_info("{table_name}");')
            ]
            for key in row.keys():
                if key not in existing_columns:
                    # SQL-запрос для добавления нового столбца, если он не существует
                    alter_table_query = (
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{key}" TEXT;'
                    )
                    self.cursor.execute(alter_table_query)
                    self.conn.commit()

    def insert_data(self, table_name, data):
        # Вставить каждый словарь из списка data в таблицу
        for row in tqdm(data, desc="Processing data"):
            # Проверить, существует ли запись с тем же значением "Код ЄДРПОУ"
            check_query = f'SELECT id FROM "{table_name}" WHERE "Код ЄДРПОУ" = ?;'
            self.cursor.execute(check_query, (row["Код ЄДРПОУ"],))
            existing_record = self.cursor.fetchone()

            if existing_record:
                # Если запись существует, обновить её
                update_columns = ", ".join([f'"{key}" = ?' for key in row.keys()])
                update_values = tuple(row.values()) + (existing_record[0],)
                update_query = (
                    f'UPDATE "{table_name}" SET {update_columns} WHERE id = ?;'
                )
                self.cursor.execute(update_query, update_values)
            else:
                # Если запись не существует, вставить новую
                columns = ", ".join([f'"{key}"' for key in row.keys()])
                placeholders = ", ".join(["?" for _ in row.keys()])
                values = tuple(row.values())
                insert_query = (
                    f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders});'
                )
                self.cursor.execute(insert_query, values)
            self.conn.commit()

    def close(self):
        # Закрыть соединение с базой данных SQLite
        self.conn.close()
