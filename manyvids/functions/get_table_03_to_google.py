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


def get_table_03_to_google():
    """
    Функция для отправки данных об истории в Google sheets
    """
    filename = "payout_history.csv"
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                    SELECT model_id,  payment_date, paid FROM {database}.payout_history
                    ORDER BY model_id, payment_date;
                    """
    )

    # Получение результатов в DataFrame

    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    df = df.drop_duplicates(subset=["model_id", "payment_date"], keep="first")

    pivot_df = df.pivot(index="model_id", columns="payment_date", values="paid")

    for column in pivot_df.columns:
        pivot_df[column] = pd.to_numeric(pivot_df[column], errors="coerce").fillna(0)

    total_row = pivot_df.sum().rename("Итого").to_frame().T
    pivot_df_with_total = pd.concat([pivot_df, total_row], axis=0)
    pivot_df_with_total = pivot_df_with_total.round(2)
    # pivot_df.to_csv('payout_history.csv')

    pivot_df_with_total.to_csv(filename)

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    """Запись в Google Таблицу"""

    client, spreadsheet_id = get_google()
    sheet_payout_history = client.open_by_key(spreadsheet_id).worksheet(
        "payout_history"
    )

    # Читаем CSV файл
    df = pd.read_csv(filename)
    df.fillna(0, inplace=True)

    # Поскольку мы уже округлили числа до сохранения в CSV,
    # заменяем точку на запятую уже после чтения из файла, если это необходимо
    df = df.astype(str).applymap(lambda x: x.replace(".", ","))

    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())

    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        try:
            # Попытка обновить данные
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
