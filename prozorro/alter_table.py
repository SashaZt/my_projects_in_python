# -*- coding: utf-8 -*-
"""Добавление в таблицу колонки"""
import sqlite3
import os

def crative_sql_bd():
    current_directory = os.getcwd()
    filename_db = os.path.join(current_directory, 'prozorro.db')
    # Подключение к базе данных (файлу). Если файла нет, он будет создан.
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()

    # Добавление новой колонки tender_verification в таблицу tender
    c.execute("ALTER TABLE tender ADD COLUMN tender_verification TEXT")

    # Сохранение изменений
    conn.commit()

    # Закрытие соединения
    conn.close()

if __name__ == '__main__':
    crative_sql_bd()
