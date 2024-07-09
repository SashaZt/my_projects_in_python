import time
import mysql.connector
import csv
import os
from mysql.connector import Error

from config import db_config, use_table_login_pass

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
login_pass_path = os.path.join(temp_path, "login_pass")


def get_login_pass_to_sql():
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        truncate_query = f"TRUNCATE TABLE `{use_table_login_pass}`"
        cursor.execute(truncate_query)
        cnx.commit()

        csv_file_path = os.path.join(
            current_directory, "temp", "login_pass", "login_pass.csv"
        )
        with open(csv_file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            next(csv_reader)  # Пропускаем заголовок, если он есть
            for c in csv_reader:
                values = (c[0], c[1], c[2], c[3])
                insert_query = f"INSERT INTO `{use_table_login_pass}` (model_id, identifier, login, `pass`) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, values)
            cnx.commit()
    except Error as err:
        print(f"Ошибка при работе с MySQL: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
        print("Данные обновлены в БД")
        time.sleep(1)


if __name__ == "__main__":
    get_login_pass_to_sql()
