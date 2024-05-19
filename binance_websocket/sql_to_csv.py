import pandas as pd
import asyncio
from databases import Database

# Замените эти значения на соответствующие параметры вашей базы данных
db_type = "mysql"
username = "python_mysql"
password = "python_mysql"
host = "164.92.240.39"
port = "3306"
db_name = "btc"

# Создание строки подключения
database_url = f"{db_type}+aiomysql://{username}:{password}@{host}:{port}/{db_name}"

# Создание подключения к базе данных
database = Database(database_url)


async def fetch_data_and_save_to_csv():
    # Подключение к базе данных
    await database.connect()

    # Запрос на извлечение данных
    query = "SELECT * FROM asks;"

    # Выполнение запроса и чтение данных
    rows = await database.fetch_all(query=query)

    # Преобразование данных в DataFrame
    df = pd.DataFrame([dict(row) for row in rows])

    # Сохранение данных в CSV
    df.to_csv("asks.csv", index=False, sep=";")

    # Отключение от базы данных
    await database.disconnect()


# Запуск асинхронной функции
if __name__ == "__main__":
    asyncio.run(fetch_data_and_save_to_csv())
