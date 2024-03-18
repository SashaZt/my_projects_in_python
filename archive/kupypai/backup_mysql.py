# import subprocess

#
# def dump_database(username, password, database_name, output_file):
#     dump_cmd = f"mysqldump -u {username} -p{password} {database_name} > {output_file}"
#     process = subprocess.Popen(dump_cmd, shell=True)
#     output, error = process.communicate()
#
# # Используйте параметры из mysql.connector для mysqldump
# username = 'python_mysql'
# password = 'python_mysql'
# database_name = 'kupypai_com'
# output_file = 'dump.sql'
#
# dump_database(username, password, database_name, output_file)




# import mysql.connector
#
# # Создание соединения
# cnx = mysql.connector.connect(
#     host="185.65.245.79",  # ваш хост, например "localhost"
#     user="python_mysql",  # ваше имя пользователя
#     password="4tz_{4!r%x8~E@W",  # ваш пароль
#     database="kupypai_com"  # имя вашей базы данных
# )
#
# # Создание объекта курсора
# cursor = cnx.cursor()
#
# # Подготовка запроса SQL
# query = "DELETE FROM ad WHERE id = %s"
#
# # Запрос на удаление
# cursor.execute(query, (851,))
#
# # Подтверждение изменений
# cnx.commit()
#
# # Закрытие соединения
# cnx.close()

#
# """"Добавить колонку"""
# # 1. Подключаемся к серверу MySQL
# # cnx = mysql.connector.connect(user='python_mysql', password='python_mysql', host='localhost', database='kupypai_com') #
# cnx = mysql.connector.connect(user='python_mysql', password='4tz_{4!r%x8~E@W', host='185.65.245.79', database='kupypai_com')
#
# # Создаем объект курсора, чтобы выполнять SQL-запросы
# cursor = cnx.cursor()
#
# # Указываем, что будем использовать эту базу данных
# cursor.execute("USE kupypai_com")
#
# # Добавляем новую колонку delta_time в таблицу my_table
# cursor.execute("ALTER TABLE ad ADD title_holding TEXT")
#
# cnx.commit()  # сохраняем изменения
# cnx.close()  # закрываем соединение


# """Модификация колонки"""
# cnx = mysql.connector.connect(user='python_mysql', password='python_mysql', host='localhost', database='kupypai_com')
# cnx = mysql.connector.connect(user='python_mysql', password='4tz_{4!r%x8~E@W', host='185.65.245.79', database='kupypai_com')
#
# # Создаем объект курсора, чтобы выполнять SQL-запросы
# cursor = cnx.cursor()
#
# # Указываем, что будем использовать эту базу данных
# cursor.execute("USE kupypai_com")
#
# # Изменяем тип колонки delta_time на INT
# cursor.execute("ALTER TABLE ad MODIFY delta_time INT")
#
# # Обновляем значение status_ad для записи с id = 830
# cursor.execute("UPDATE ad SET status_ad = 'В процесі укладання угоди купівлі-продажу' WHERE id = 258")
#
# # Делаем commit для сохранения изменений
# cnx.commit()


# cnx = mysql.connector.connect(user='python_mysql', password='4tz_{4!r%x8~E@W', host='185.65.245.79', database='kupypai_com')
#
#
# # Создаем объект курсора, чтобы выполнять SQL-запросы
# cursor = cnx.cursor()
#
# # Очищаем колонку delta_time, устанавливая все значения в NULL
# cursor.execute("UPDATE ad SET delta_time = NULL")
# cnx.commit()
"""Выгрузка данных в csv"""
import pandas as pd
import mysql.connector

# Создаем соединение с базой данных через SQLAlchemy
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine

password = urlquote('4tz_{4!r%x8~E@W')
engine = create_engine(f'mysql+mysqlconnector://python_mysql:{password}@185.65.245.79/kupypai_com')

# Выполняем запрос и загружаем результаты в DataFrame
df = pd.read_sql_query("SELECT * FROM ad", engine)

# Сохраняем DataFrame в файл CSV
df.to_csv('ad.csv', index=False)


# """Бекап и очистка БД"""
# import subprocess
# import os
#
# username = "python_mysql"
# password = "python_mysql"
# database_name = "kupypai_com"
#
# dumpcmd = '"c:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysqldump" -u' + username + ' -p' + password + ' ' + database_name + ' > ' + os.getcwd() + "\\dump.sql"
# subprocess.call(dumpcmd, shell=True)
# import subprocess
# from mysql.connector import connect, Error
#
# # Создаем бэкап базы данных
# subprocess.run(f'mysqldump -u python_mysql -p python_mysql kupypai_com > backup.sql', shell=True)
#
# # Подключаемся к базе данных
# with connect(
#     host="localhost",
#     user="python_mysql",
#     password="python_mysql",
#     database="kupypai_com",
# ) as connection:
#     # Создаем курсор
#     with connection.cursor() as cursor:
#         # Удаляем все данные из таблицы ad
#         cursor.execute("DELETE FROM ad")
#
# # Закрываем подключение
# connection.close()

#
# """Удаление дублей"""
# cnx = mysql.connector.connect(user='python_mysql', password='4tz_{4!r%x8~E@W', host='185.65.245.79', database='kupypai_com')
# cursor = cnx.cursor()
# #
# # # Указываем, что будем использовать эту базу данных
# cursor.execute("USE kupypai_com")
# cursor.execute("""
#     DELETE a1 FROM ad a1
#     JOIN (
#         SELECT id_ad, MAX(id) AS max_id
#         FROM ad
#         GROUP BY id_ad
#         HAVING COUNT(*) > 1
#     ) a2 ON a1.id_ad = a2.id_ad AND a1.id != a2.max_id
# """)
#
# cnx.commit()
# cnx.close()