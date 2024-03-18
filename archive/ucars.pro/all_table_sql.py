import mysql.connector

# Подключение к базе данных
conn = mysql.connector.connect(
    host="162.55.63.6",  # Адрес хоста базы данных
    user="car_db_user_001",  # Имя пользователя базы данных
    password="wE8wH9jA3jfC5hK6hY6j",  # Пароль пользователя базы данных
    database="lot_database"  # Имя базы данных
)


# Создание курсора
cursor = conn.cursor()

# Запрос на извлечение всех таблиц в базе данных
query = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'lot_database'
"""

# Выполнение запроса
cursor.execute(query)

# Извлечение результатов запроса
tables = cursor.fetchall()

# Вывод списка таблиц
for table in tables:
    print(table[0])

# Закрытие соединения
cursor.close()
conn.close()