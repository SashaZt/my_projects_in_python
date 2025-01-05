# -*- coding: utf-8 -*-
"""Создание БД"""
import sqlite3
import os

"""Добавление в таблицу колонки"""
def crative_sql_bd():
    current_directory = os.getcwd()
    filename_db = os.path.join(current_directory, 'prozorro.db')
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()

    # Создание таблицы tender
    c.execute(
        """CREATE TABLE IF NOT EXISTS tender (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Автоинкрементный ID
            tender_id TEXT UNIQUE,                 -- Уникальный ID тендера
            url_tender TEXT,                       -- Ссылка на тендер
            customer TEXT,                         -- Заказчик
            status_tender TEXT,                    -- Статус тендера
            complaint TEXT,                        -- Жалобы
            budget TEXT,                           -- Бюджет тендера
            date_auction TEXT,                     -- Дата аукциона
            time_auction TEXT,                     -- Время аукциона
            bids_amount TEXT,                      -- Остаточна пропозиція
            date_enquiryPeriod TEXT,               -- Звернення за роз’ясненнями дата
            time_enquiryPeriod TEXT,               -- Звернення за роз’ясненнями время
            date_auctionPeriod_auctionPeriod TEXT, -- Кінцевий строк подання тендерних пропозицій дата
            time_auctionPeriod_auctionPeriod TEXT, -- Кінцевий строк подання тендерних пропозицій время
            award_name_customer TEXT,              -- Победитель
            award_value_customer TEXT,             -- Ставка которая победила
            date_pending TEXT,                     -- Дата победившей ставки
            time_pending TEXT,                     -- Время победившей ставки
            award_status TEXT,                     -- Статус переможця
            guarantee_amount TEXT,                 -- Розмір надання забезпечення пропозицій учасників
            bank_garantiy TEXT,                    -- забезпечення виконання договору
            tender_verification TEXT               -- Наличие статуса завершен
            )"""
    )

    # Сохранение (коммит) изменений
    conn.commit()

    # Закрытие соединения
    conn.close()
    # import sqlite3
    #
    # # Подключение к базе данных
    # conn = sqlite3.connect('prozorro.db')
    # c = conn.cursor()
    #
    # # Добавление столбца guarantee_amount, если он отсутствует
    # try:
    #     c.execute("ALTER TABLE tender ADD COLUMN guarantee_amount TEXT")
    #     conn.commit()
    #     print("Столбец 'guarantee_amount' успешно добавлен в таблицу 'tender'.")
    # except sqlite3.OperationalError as e:
    #     print("Ошибка при добавлении столбца 'guarantee_amount':", e)
    #
    # # Закрытие соединения
    # conn.close()

if __name__ == '__main__':
    crative_sql_bd()
