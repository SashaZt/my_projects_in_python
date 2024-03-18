import datetime
import asyncio
import aiomysql
from database import connect_to_database

# async def connect_to_database():
#     conn = await aiomysql.connect(
#         host="162.55.63.6",
#         user="car_db_user_001",
#         password="wE8wH9jA3jfC5hK6hY6j",
#         db="lot_database"
#     )
#     return conn

# Function to get a list of all tables in the database
async def get_all_tables():
    conn = await connect_to_database()

    async with conn.cursor() as cursor:
        show_tables_query = "SHOW TABLES"
        await cursor.execute(show_tables_query)
        tables = [table[0] for table in await cursor.fetchall()]

    conn.close()

    return tables

# Function to count the number of records in a table
async def count_records(table):
    conn = await connect_to_database()

    async with conn.cursor() as cursor:
        count_query = f"SELECT COUNT(*) AS total_count FROM {table}"
        await cursor.execute(count_query)
        result = await cursor.fetchone()
        count = result[0]

    conn.close()

    return count

# Function to wait for one hour
async def wait_one_hour():
    await asyncio.sleep(10)

# Function to print the difference in record count
def print_record_difference(table, initial_count, final_count):
    difference = final_count - initial_count
    if difference != 0:
        print(f"Таблица: {table}, Новых записей: {difference}")

async def main():
    while True:
        conn = await connect_to_database()

        async with conn.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = [table[0] for table in await cursor.fetchall()]

        conn.close()

        report_start_time = datetime.datetime.now()

        for table in tables:
            initial_count = await count_records(table)
            await wait_one_hour()
            final_count = await count_records(table)
            print_record_difference(table, initial_count, final_count)

        report_end_time = datetime.datetime.now()
        report_hour_minute = report_end_time.strftime("%H:%M")
        print(f"Отчет сгенерирован в {report_hour_minute}")

        await asyncio.sleep(10)

asyncio.run(main())
