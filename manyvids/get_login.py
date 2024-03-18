import csv
import os
import mysql.connector

from config import db_config, use_table_login_pass
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
login_pass_path = os.path.join(temp_path, 'login_pass')

def get_login_pass_to_sql():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Очистка таблицы перед вставкой новых данных
    truncate_query = f"TRUNCATE TABLE {use_table_login_pass}"
    cursor.execute(truncate_query)
    cnx.commit()  # Подтверждение изменений

    csv_file_path = os.path.join(login_pass_path, 'login_pass.csv')
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for c in csv_reader:
            identifier = f'{c[0]}'
            login = c[1]
            password = c[2]
            values = [identifier, login, password]

            # SQL-запрос для вставки данных
            insert_query = f"""
            INSERT INTO {use_table_login_pass} (identifier, login,pass)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, values)
            cnx.commit()  # Подтверждение изменений
    # Закрытие соединения с базой данных
    cursor.close()
    cnx.close()
if __name__ == '__main__':
    get_login_pass_to_sql()