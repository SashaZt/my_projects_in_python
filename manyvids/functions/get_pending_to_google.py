import mysql.connector
from config import (
    db_config,
    host,
    user,
    password,
    database,
    use_table_monthly_sales,
)
import pandas as pd
import logging
from datetime import datetime
from functions.get_google import get_google
from functions.get_id_models_from_sql import get_id_models_from_sql
import gspread
import time
import os
from bs4 import BeautifulSoup
import numpy as np
from sqlalchemy import create_engine
import glob

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
pending_custom_path = os.path.join(temp_path, "pending_custom")

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)


def get_pending_to_google():
    """
    Функция для отправки данных об pending в Google sheets
    """
    # scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
    #          'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    # creds_file = os.path.join(current_directory, 'access.json')
    # creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    # client = gspread.authorize(creds)
    client, spreadsheet_id = get_google()
    filename_monthly_sales = "monthly_sales.csv"
    spreadsheet = client.open_by_key(spreadsheet_id)
    database_uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"

    # Создание движка SQLAlchemy
    engine = create_engine(database_uri)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(
        f"""
                  SELECT
                        model_fm,
                        EXTRACT(YEAR FROM sales_date) AS year,
                        EXTRACT(MONTH FROM sales_date) AS month,
                        ROUND(SUM(seller_commission_price), 2) AS total_seller_commission
                        FROM {database}.daily_sales 
                        GROUP BY model_fm , year , month
                        ORDER BY model_fm ASC , year ASC , month ASC;
                """
    )
    # Получение результатов в DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[x[0] for x in cursor.description])
    # Запись DataFrame в CSV файл
    df.to_csv(filename_monthly_sales, index=False)

    # Чтение CSV файла
    df = pd.read_csv(filename_monthly_sales)

    # Переименование столбцов в DataFrame для соответствия таблице в БД
    df.rename(
        columns={
            "model_fm": "model_id",
            "year": "sales_year",
            "month": "sales_month",  # Убедитесь, что названия столбцов соответствуют вашему CSV файлу
            "total_seller_commission": "total_sum",
        },
        inplace=True,
    )

    # # Создание строки подключения
    # connection_string = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}'

    # Создание движка SQLAlchemy

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_monthly_sales}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений
    cursor.close()
    cnx.close()

    # Запись DataFrame в таблицу MySQL
    df.to_sql(name="monthly_sales", con=engine, if_exists="append", index=False)
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    """Загрузка в месячную таблицу уникальных клиентов"""

    clear_pending_query = f"""
            UPDATE {database}.monthly_sales
            SET pending_custom = NULL
            WHERE sales_month != %s;
        """
    cursor.execute(clear_pending_query, (month,))
    cnx.commit()

    cnx.commit()
    update_query = f"""
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)

    folder = os.path.join(pending_custom_path, "*.html")
    files_html = glob.glob(folder)
    id_models = get_id_models_from_sql()
    for item in files_html:

        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        custom_vids_body = soup.find_all("div", id="customVidsBody")
        try:
            mvtoken = soup.find("a", id="hiddenPremiumTrigger").get("data-model-id")
        except:
            continue
        # Ищем, какому ключу соответствует mvtoken
        models_id = [key for key, value in id_models.items() if value == mvtoken]
        try:
            model_id = models_id[0]
        except:
            model_id = None
        total_pending_custom = 0
        for c in custom_vids_body:
            rows = c.find_all("tr")
            for row in rows:
                if len(row.find_all("td")) >= 6:
                    strong_tag = row.find_all("td")[5].find("strong")
                    if strong_tag:
                        pending = strong_tag.get_text(strip=True).replace("$", "")
                        try:
                            pending_value = float(pending)
                            total_pending_custom += pending_value
                        except ValueError:
                            # Обрабатываем случай, когда pending не может быть преобразовано в число
                            continue

        # После накопления суммы выполняем обновление базы данных одной строкой
        update_query = f"""
                        UPDATE {database}.monthly_sales
                        SET pending_custom = %s
                        WHERE model_id = %s AND sales_month = %s;
                        """
        cursor.execute(update_query, (total_pending_custom, model_id, month))
        cnx.commit()
    if os.path.exists(filename_monthly_sales):
        os.remove(filename_monthly_sales)
    cursor.close()
    cnx.close()

    """
    Запись в Google Таблицу
    """

    query = f"""
        SELECT model_id,  sales_month, total_sum, pending_custom, chat_user 
        FROM {database}.monthly_sales
        WHERE sales_year = YEAR(CURDATE());

    """
    df = pd.read_sql_query(query, engine)
    filename_pending_custom = "pending_custom.csv"
    # Преобразование DataFrame
    # Предполагается, что df уже загружен и содержит необходимые данные.
    # Создаем pivot_table.
    df_pivot = df.pivot_table(
        index="model_id",
        columns="sales_month",
        values=["total_sum", "pending_custom", "chat_user"],
        aggfunc="first",
    ).reset_index()

    # Обновляем названия столбцов, чтобы они были более читаемыми.
    df_pivot.columns = [
        "_".join(str(i) for i in col).strip() for col in df_pivot.columns.values
    ]

    # Заменяем NaN на 0.
    df_pivot.fillna(0, inplace=True)

    # Убедимся, что столбцы, содержащие числовые значения, имеют числовой тип данных.
    for col in df_pivot.columns:
        if "total_sum" in col or "chat_user" in col or "pending_custom" in col:
            df_pivot[col] = pd.to_numeric(df_pivot[col], errors="coerce")

    # Сохраняем результат в CSV. Индекс не сохраняем, если он не несет важной информации.
    df_pivot.to_csv(filename_pending_custom, index=False)
    #
    df = pd.read_csv(filename_pending_custom)
    months = range(1, 13)  # От 1 до 12

    for month in months:
        sheet_name = f"{month:02}_monthly_sales"

        # Подготовка данных для записи
        columns = ["model_id_"]  # Основной столбец
        data_columns = []  # Столбцы данных для текущего месяца

        # Добавляем колонки в список, если они существуют в DataFrame
        pending_custom_col = f"pending_custom_{month}"
        total_sum_col = f"total_sum_{month}"
        chat_user_col = f"chat_user_{month}"  # Предполагаем, что столбец chat_user существует для каждого месяца

        if total_sum_col in df.columns:
            columns.append(total_sum_col)
            data_columns.append(total_sum_col)
        # Проверяем наличие столбцов в DataFrame
        if pending_custom_col in df.columns:
            columns.append(pending_custom_col)
            data_columns.append(pending_custom_col)
        if chat_user_col in df.columns:
            columns.append(
                chat_user_col
            )  # Добавляем chat_user в список столбцов для выборки
        else:
            # Если столбец chat_user отсутствует, предполагаем, что это ошибка в данных или логике
            # log_message(f"Warning: Column {chat_user_col} not found in DataFrame. Adding it with default value 0.")
            df[chat_user_col] = (
                0  # Добавляем столбец с 0, чтобы сохранить структуру данных
            )
            columns.append(chat_user_col)

        # Если нет ни одной из специфичных колонок для месяца, кроме chat_user, пропускаем итерацию
        if not data_columns and chat_user_col not in df.columns:
            continue

        # Создаем подмножество DataFrame с нужными столбцами и заменяем плохие значения
        df_subset = df[columns].copy()
        df_subset.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

        # Проверяем, есть ли данные для total_sum_col и только тогда работаем с листом
        if total_sum_col in data_columns and df[total_sum_col].any():
            # Пытаемся получить лист, если он существует, иначе создаем новый
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, rows="100", cols="20"
                )

            # Добавляем строку "Итого" с подсчетом сумм по колонкам
            totals = (
                df_subset.select_dtypes(include=["number"]).sum().tolist()
            )  # Считаем суммы только для числовых колонок
            # Создаем итоговую строку
            totals_row = ["Итого"] + totals

            # Убедимся, что итоговая строка правильно выровнена с заголовками
            # Отнимаем 1, так как 'Итого' уже добавлено в totals_row
            non_numeric_columns_count = len(df_subset.columns) - len(totals) - 1
            totals_row = [""] * non_numeric_columns_count + totals_row

            # Формируем данные для обновления листа, добавляя totals_row
            values = (
                [df_subset.columns.tolist()] + df_subset.values.tolist() + [totals_row]
            )

            # Очистка и обновление листа
            max_attempts = 5
            attempts = 0
            while attempts < max_attempts:
                try:
                    worksheet.clear()
                    worksheet.update(values, "A1")

                    # Форматирование текущей даты и времени
                    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Обновление ячейки A1 с текущей датой и временем
                    worksheet.update([[current_datetime]], "A1")
                    break  # Если успешно, выходим из цикла
                except gspread.exceptions.APIError as e:
                    print(f"Произошла ошибка: {e}")
                    attempts += 1
                    time.sleep(5)  # Ожидание перед следующей попыткой
                    if attempts == max_attempts:
                        print("Не удалось обновить данные после нескольких попыток.")
        else:
            # Если нет данных для total_sum_col, лист не создается и пропускаем обновление
            logging.info(
                f"Skipping sheet creation and update for {sheet_name} due to no data in {total_sum_col}."
            )

    engine.dispose()
    if os.path.exists(filename_pending_custom):
        os.remove(filename_pending_custom)
