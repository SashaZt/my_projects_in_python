import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from config import db_config
import os


# Данные для подключения к базе данных
def sql_to_csv():
    # Создаем строку подключения для SQLAlchemy
    database_uri = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

    # Подключаемся к базе данных с использованием SQLAlchemy для упрощения работы с Pandas
    engine = create_engine(database_uri)

    # Подключаемся к базе данных с использованием mysql.connector для получения списка таблиц
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Получаем список всех таблиц в базе данных
    cursor.execute("SHOW TABLES;")
    tables = [table[0] for table in cursor.fetchall()]

    # Перебираем каждую таблицу и сохраняем ее содержимое в CSV-файл
    for table_name in tables:
        # Используем Pandas для чтения данных из таблицы
        df = pd.read_sql_table(table_name, con=engine)

        # Сохраняем DataFrame в CSV-файл, имя файла соответствует имени таблицы
        csv_file_name = f"{table_name}.csv"
        df.to_csv(csv_file_name, index=False)
        print(f"Данные таблицы {table_name} сохранены в {csv_file_name}")

    # Закрываем соединение
    cursor.close()
    cnx.close()
def csv_to_sql():
    database_uri = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

    # Подключаемся к базе данных с использованием SQLAlchemy для упрощения работы с Pandas
    engine = create_engine(database_uri)

    # Путь к директории с CSV-файлами
    csv_dir_path = "path/to/your/csv_files"

    # Получаем список всех CSV-файлов в директории
    csv_files = [f for f in os.listdir(csv_dir_path) if f.endswith('.csv')]

    # Перебираем каждый CSV-файл для загрузки данных
    for csv_file in csv_files:
        file_path = os.path.join(csv_dir_path, csv_file)
        # Читаем CSV-файл в DataFrame
        df = pd.read_csv(file_path)

        # Определяем имя таблицы на основе имени файла (без расширения)
        table_name = csv_file[:-4]  # Удалить расширение ".csv"

        # Загружаем данные из DataFrame в таблицу в базе данных
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        print(f"Данные из файла {csv_file} загружены в таблицу {table_name}")

    print("Все данные успешно загружены.")

if __name__ == '__main__':
    # sql_to_csv()
    csv_to_sql()
