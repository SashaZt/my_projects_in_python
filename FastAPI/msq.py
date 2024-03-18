from config import db_config, use_bd, use_table
import mysql.connector

def create_sql():

    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE ugr")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 3. В базе данных создаем таблицу ad
    # 4. Создаем необходимые колонки
    cursor.execute(f"""
        CREATE TABLE {use_table} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date_of_creation DATE,
            nomer VARCHAR(10),
            status VARCHAR(1000),
            date_of_status_change DATE
        )
    """)

    # Закрываем соединение
    cnx.close()
if __name__ == '__main__':
    # """Создание таблицы"""
    create_sql()