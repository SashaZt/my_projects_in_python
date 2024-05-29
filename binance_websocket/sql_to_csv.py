import pandas as pd
import asyncio
from databases import Database
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение значений переменных из окружения
db_type = os.getenv("DB_TYPE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

# Создание строки подключения
database_url = f"{db_type}+aiomysql://{username}:{password}@{host}:{port}/{db_name}"

# Создание подключения к базе данных
database = Database(database_url)


# Функция сохранения данных в csv
async def save_to_csv(target_date, table):

    query = f"""
    SELECT * FROM {table}
    WHERE DATE(Event_time) = :target_date
    """
    rows = await database.fetch_all(query=query, values={"target_date": target_date})
    df = pd.DataFrame(rows)
    if not df.empty:
        file_name = f"{target_date}_{table}.csv"
        df.to_csv(file_name, index=False)
        print(f"Сохранил {file_name}")


# Удаление данных из БД
async def delete_data_sql(target_date, table):
    start_date = target_date
    end_date = start_date + timedelta(days=1)
    # Подтверждение удаления данных
    confirm = input(f"Удалить данные из базы {table} за {start_date}? Y/N: ")
    if confirm.lower() == "y":
        delete_query = f"""
        DELETE FROM {table}
        WHERE Event_time >= :start_date AND Event_time < :end_date
        """
        await database.execute(
            delete_query,
            values={
                "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        print(f"Данные удалены успешно {start_date} in table {table}.")
    else:
        print("Удаление данных отменено.")


# Получение даты по таблицам
async def get_unique_dates():
    query = """
    SELECT DISTINCT DATE(Event_time) as date
    FROM asks
    WHERE DATE(Event_time) < CURDATE()
    """
    rows = await database.fetch_all(query=query)
    return [row["date"] for row in rows]


# Получение таблиц в БД
async def get_all_tables():
    query = "SHOW TABLES"
    rows = await database.fetch_all(query=query)
    return [row[0] for row in rows]  # MySQL возвращает имена таблиц как кортежи


# Анализ и оптимизация БД
async def optimize_and_analyze_db():
    tables = await get_all_tables()
    for table in tables:
        optimize_query = f"OPTIMIZE TABLE {table};"
        analyze_query = f"ANALYZE TABLE {table};"
        await database.execute(optimize_query)
        await database.execute(analyze_query)
        print(f"Optimized and analyzed table {table}.")


# Главная функция запуска
async def main():
    await database.connect()
    print("Получаем даты в БД")
    dates = await get_unique_dates()
    formatted_dates = [date.strftime("%Y-%m-%d") for date in dates]
    print("Даты в БД:", formatted_dates)
    while True:
        print(
            "Введите 1 для выгрузки данных в csv "
            "\nВведите 2 для удаления данных из БД"
            "\nВведите 3 для оптимизации БД"
            "\nВведите 0 для закрытия программы"
        )
        user_input = int(input("Выберите действие: "))
        tables = ["asks", "bids", "trades"]
        if user_input == 0:
            print("Программа завершена.")
            break  # Выход из цикла, завершение программы
        for target_date in dates:
            for table in tables:
                if user_input == 1:
                    await save_to_csv(target_date, table)
                elif user_input == 2:
                    await delete_data_sql(target_date, table)
                elif user_input == 3:
                    await optimize_and_analyze_db()
                else:
                    print(
                        "Неверный ввод, пожалуйста, введите корректный номер действия."
                    )
    await database.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Программа прервана пользователем")
