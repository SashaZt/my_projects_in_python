import mysql.connector
from config import (
    db_config,
    database,
)
import pandas as pd
import logging
from datetime import datetime
from functions.get_google import get_google
import gspread
import time
import os

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)


def get_table_04_to_google():
    """
    Функция для отправки данных об клиентах в Google sheets
    """
    filename = "withdrawals.csv"
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                   SELECT 
            buyer_stage_name,
            buyer_user_id,
            ROUND(SUM(seller_commission_price), 2) AS total_commission,
            COUNT(*) AS total_count,
            ROUND(AVG(seller_commission_price), 2) AS average_commission,
            GROUP_CONCAT(DISTINCT model_fm
                SEPARATOR ', ') AS all_buyer_usernames
        FROM
            {database}.daily_sales
        GROUP BY buyer_stage_name , buyer_user_id
        ORDER BY total_commission DESC;
        """
    )

    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv(filename, index=False)
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet("clients")

    # Читаем CSV файл
    df = pd.read_csv(filename)
    df.fillna(0, inplace=True)
    df = df.astype(str)
    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        try:
            # Очистка всего листа
            sheet_payout_history.clear()
            # Обновляем данные в Google Sheets
            sheet_payout_history.update(values, "A1")

            # Форматирование текущей даты и времени
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Обновление ячейки A1 с текущей датой и временем
            sheet_payout_history.update([[current_datetime]], "A1")
            break  # Если успешно, выходим из цикла
        except gspread.exceptions.APIError as e:
            logging.info(f"Произошла ошибка: {e}")
            attempts += 1
            time.sleep(5)  # Ожидание перед следующей попыткой
            if attempts == max_attempts:
                logging.info("Не удалось обновить данные после нескольких попыток.")
    if os.path.exists(filename):
        os.remove(filename)
