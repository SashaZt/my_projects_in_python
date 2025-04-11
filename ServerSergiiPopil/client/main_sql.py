import pyodbc

# Проверяем доступные драйверы
print("Доступные драйверы ODBC:")
print(pyodbc.drivers())

# Попробуем использовать драйвер 17, но можно заменить на 18 или другой
connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
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
    
    # Тестовый запрос для проверки
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"Версия SQL Server: {row[0]}")
    
except pyodbc.Error as e:
    print(f"Ошибка подключения: {e}")
    
finally:
    try:
        cursor.close()
        conn.close()
    except:
        pass