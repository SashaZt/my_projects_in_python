import openpyxl

import csv
import datetime
from pathlib import Path
import pandas as pd
import mysql.connector
import os


def create_sql():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(user='python_mysql', password='python_mysql', host='localhost')

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE weather")

    # Указываем, что будем использовать эту базу данных
    cursor.execute("USE weather")

    # 3. В базе данных создаем таблицу Zhytomyr
    # 4. Создаем необходимые колонки
    cursor.execute("""
    CREATE TABLE lutsk (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,
        time TIME,
        temp FLOAT
    )
    """)

    # Закрываем соединение
    cnx.close()


def updates_data():
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="weather"  # имя вашей базы данных
    )
    cursor = cnx.cursor()

    name_files = Path(f'/home/alex/PycharmProjects/scrap_tutorial-master/Погода/') / 'archive.csv'
    with open(name_files, newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=',', quotechar='|'))
        for row in urls:
            deta = row[0]
            formatted_datetime = datetime.datetime.strptime(deta, "%Y-%m-%dT%H:%M")
            formatted_date = formatted_datetime.date()
            formatted_time = formatted_datetime.time()
            temper = row[1]
            data = [formatted_date, formatted_time, temper]
            insert_query = """
                INSERT INTO zhytomyr (
                    date, time, temp
                ) VALUES (
                    %s, %s, %s
                )
            """

            cursor.execute(insert_query, data)
    cnx.commit()
    cnx.close()


def check_data_sql():
    cnx = mysql.connector.connect(
        host="localhost",  # ваш хост, например "localhost"
        user="python_mysql",  # ваше имя пользователя
        password="python_mysql",  # ваш пароль
        database="weather"  # имя вашей базы данных
    )
    cursor = cnx.cursor()

    # Пример запроса на выборку данных
    select_query = "SELECT * FROM zhytomyr"
    cursor.execute(select_query)

    # Получение результатов
    results = cursor.fetchall()

    # Вывод результатов
    for row in results:
        print(row)

    # Закрытие cursor и соединения
    cnx.commit()
    cnx.close()

def result():
    cnx = mysql.connector.connect(
        host="192.168.1.208",
        user="python_mysql",
        password="python_mysql",
        database="weather"
    )
    cursor = cnx.cursor()

    # Запрос
    query = "SELECT * FROM zhytomyr"
    cursor.execute(query)

    # Получение данных
    data = cursor.fetchall()
    cnx.commit()
    cnx.close()

    # Создание DataFrame
    columns = [column[0] for column in cursor.description]
    df = pd.DataFrame(data, columns=columns)

    # Проверка, что колонка 'date' существует в DataFrame
    if 'date' not in df.columns:
        raise ValueError("The column 'date' does not exist in the DataFrame.")

    # Преобразование колонки 'date' в datetime
    df['date'] = pd.to_datetime(df['date'])

    # Группировка данных по месяцу и году и вычисление средней температуры
    avg_temp = df.groupby(df['date'].dt.to_period("M")).mean()
    avg_temp = avg_temp.rename_axis('month_year').reset_index()

    # Отформатирование результатов
    avg_temp['formatted_date'] = avg_temp['month_year'].dt.strftime('%m.%Y')
    avg_temp['result'] = avg_temp.apply(lambda row: f"{row['formatted_date']}, {row['temp']:.1f}", axis=1)

    # print(avg_temp['result'])  # вывод всех результатов
    avg_temp['year'] = avg_temp['month_year'].dt.year
    avg_temp['month'] = avg_temp['month_year'].dt.strftime('%m')


    # Преобразование данных с помощью pivot
    pivot_table = avg_temp.pivot(index='month', columns='year', values='temp')
    avg_yearly = pivot_table.mean()

    pivot_table.loc['Среднее за год'] = avg_yearly
    pivot_table = pivot_table.round(2)
    pivot_table.to_excel("output.xlsx", engine='openpyxl')
    # print(pivot_table)


if __name__ == '__main__':
    # updates_data()
    # check_data_sql()
    result()
