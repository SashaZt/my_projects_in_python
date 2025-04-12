Исправление шаг за шагом
1. Удаление старого ключа и очистка кэша
Чтобы избежать конфликтов, удалим существующий ключ и очистим кэш apt:
bash

# Удаляем ключ
sudo rm /usr/share/keyrings/microsoft-prod.gpg

# Очищаем кэш apt
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

2. Повторное добавление ключа Microsoft
Попробуем заново добавить ключ, убедившись, что он скачивается и конвертируется в правильный формат:
bash

# Скачиваем ключ и конвертируем его в формат gpg
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

Пояснение:
gpg --dearmor преобразует ASCII-ключ в бинарный формат, который лучше распознаётся apt в современных версиях Ubuntu.

-o указывает, куда сохранить ключ.

Проверь, что ключ создан:
bash

ls /usr/share/keyrings/microsoft-prod.gpg

3. Обновление файла репозитория
Пересоздадим файл репозитория с правильной подписью:
bash

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/24.04/prod noble main" | sudo tee /etc/apt/sources.list.d/mssql-release.list

Проверь содержимое файла:
bash

cat /etc/apt/sources.list.d/mssql-release.list

Ожидаемый вывод:

deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/24.04/prod noble main

4. Обновление списка пакетов
Теперь обновим apt:
bash

sudo apt-get update

Если ошибка GPG (NO_PUBKEY EB3E94ADBE1229CF) всё ещё появляется, попробуем добавить ключ напрямую в apt:
bash

curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -

Примечание: Это устаревший метод, но иногда помогает как временное решение. Если сработает, продолжаем дальше, но лучше вернуться к использованию /usr/share/keyrings/ позже.
Снова выполни:
bash

sudo apt-get update

5. Установка msodbcsql17
Если apt-get update прошёл без ошибок GPG, установи драйвер:
bash

ACCEPT_EULA=Y sudo apt-get install -y msodbcsql17

Если хочешь новейшую версию:
bash

ACCEPT_EULA=Y sudo apt-get install -y msodbcsql18

6. Установка unixODBC
Убедись, что unixODBC установлен (нужен для pyodbc):
bash

sudo apt-get install -y unixodbc unixodbc-dev

7. Проверка драйвера
После установки проверь, зарегистрирован ли драйвер:
bash

odbcinst -q -d

Ожидаемый вывод:

[ODBC Driver 17 for SQL Server]

или

[ODBC Driver 18 for SQL Server]

8. Установка pyodbc
Убедись, что pyodbc установлен:
bash

pip3 install pyodbc

Если pip3 отсутствует:
bash

sudo apt-get install -y python3-pip

Проверь:
bash

pip3 show pyodbc

9. Тестирование подключения
Теперь протестируем подключение к базе данных Azure SQL. Используй имя драйвера из вывода odbcinst -q -d:
python

import pyodbc

# Проверяем доступные драйверы
print("Доступные драйверы ODBC:")
print(pyodbc.drivers())

# Строка подключения
connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"  # Замени на ODBC Driver 18, если установил msodbcsql18
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

Сохрани как connect.py и запусти:

