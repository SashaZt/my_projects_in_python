import mysql.connector

conn = mysql.connector.connect(
    host="88.99.217.197",  # Адрес хоста базы данных
    user="aiorg_ai",  # Имя пользователя базы данных
    password="y;*?[86fqWmZ",  # Пароль пользователя базы данных
    database="aiorg_ai"  # Имя базы данных
)

"""Создание структуры БД ql"""
cursor = conn.cursor()

select_query = "SELECT * FROM aiorg_ai.dle_post;"
cursor.execute(select_query)

result = cursor.fetchall()

for row in result:
    print(row)