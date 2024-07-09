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
from loguru import logger

# Настройка базовой конфигурации логирования
logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",  # Формат сообщения
    level="DEBUG",  # Уровень логирования
    encoding="utf-8",  # Кодировка
    mode="w",  # Перезапись файла при каждом запуске
)


def get_table_01_to_google():
    """
    Функция для отправки данных об дневных в Google sheets
    """
    filename = "daily_sales.csv"
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(
            f"""
            SELECT model_fm, sales_date, 
            ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
            FROM {database}.daily_sales 
            WHERE YEAR(sales_date) = YEAR(CURDATE()) AND MONTH(sales_date) = MONTH(CURDATE())
            GROUP BY model_fm, sales_date
            ORDER BY model_fm ASC, sales_date ASC;
        """
        )
        results = cursor.fetchall()
        
        # Обработка результатов запроса здесь
        # Например, вывод результатов:
        # for row in results:
        #     print(row)
    except mysql.connector.Error as e:
        logger.error(f"Произошла ошибка при выполнении запроса к базе данных: {e}")
    finally:
        if "cnx" in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

    # Получение результатов в DataFrame
    df = pd.DataFrame(results, columns=[x[0] for x in cursor.description])

    # Преобразование DataFrame в сводную таблицу
    pivot_df = df.pivot_table(
        index="model_fm",
        columns="sales_date",
        values="total_seller_commission",
        fill_value=0,
    )

    # Добавляем строку 'Итого' в конец сводной таблицы
    total_row = pivot_df.sum().rename("Итого").to_frame().T
    # Обратите внимание: мы преобразуем Series total_row в DataFrame и используем .T для транспонирования

    # Используем pd.concat для добавления итоговой строки к pivot_df
    pivot_df_with_total = pd.concat([pivot_df, total_row], axis=0)

    # Сохранение в CSV
    pivot_df_with_total.to_csv(filename, index=True)

    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()

    """Запись в Google Таблицу"""
    client, spreadsheet_id = get_google()
    sheet_daily_sales = client.open_by_key(spreadsheet_id).worksheet("daily_sales")
    # Читаем CSV файл
    df = pd.read_csv(filename)

    # Конвертируем DataFrame в список списков
    values = df.values.tolist()

    # Добавляем заголовки столбцов в начало списка
    values.insert(0, df.columns.tolist())
    # Очистка и обновление листа
    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        try:
            sheet_daily_sales.clear()
            sheet_daily_sales.update(values, "A1")
            current_datetime_get_table_01 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Обновляем ячейку A1 с текущей датой и временем
            sheet_daily_sales.update(
                [[current_datetime_get_table_01]],
                "A1",
                value_input_option="USER_ENTERED",
            )
            break  # Если успешно, выходим из цикла
        except gspread.exceptions.APIError as e:
            logger.error(f"Произошла ошибка: {e}")
            attempts += 1
            time.sleep(5)  # Ожидание перед следующей попыткой
            if attempts == max_attempts:
                logger.error("Не удалось обновить данные после нескольких попыток.")
    if os.path.exists(filename):
        os.remove(filename)
