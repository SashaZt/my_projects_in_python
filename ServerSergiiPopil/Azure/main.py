import pyodbc

# Проверяем доступные драйверы
print("Доступные драйверы ODBC:")
print(pyodbc.drivers())

# Строка подключения
connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"  # Замени на ODBC Driver 18, если установил msodbcsql18
    "Server=allegrosearchservice.database.windows.net,1433;"
    "Database=AlegroSearchService;"
    "UID=Igor;"
    "PWD=ZGIA_01078445iv;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

try:
    # Устанавливаем соединение
    conn = pyodbc.connect(connection_string)
    print("Успешно подключились к базе данных!")

    # Создаём курсор для выполнения запросов
    cursor = conn.cursor()

    # Тестовый запрос
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"Версия SQL Server: {row[0]}")

except pyodbc.Error as e:
    print(f"Ошибка подключения: {e}")

finally:
    try:
        cursor.close()
        conn.close()
        print("Соединение закрыто.")
    except:
        pass
