import os
import json
import asyncio
import time
import aiofiles
import pandas as pd
from databases import Database

# Настройки базы данных
db_type = "mysql"
username = "python_mysql"
password = "python_mysql"
host = "localhost"  # или "164.92.240.39"
port = "3306"
# db_name = "btc"
db_name = "crypto"
database_url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"
database = Database(database_url)

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
trades_path = os.path.join(temp_path, "trades")
bids_path = os.path.join(temp_path, "bids")
asks_path = os.path.join(temp_path, "asks")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(trades_path, exist_ok=True)
os.makedirs(bids_path, exist_ok=True)
os.makedirs(asks_path, exist_ok=True)


async def process_file(file_path, columns, table_name, query):
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        data = json.loads(await file.read())
        if data:
            df = pd.DataFrame(data)
            df.columns = columns
            await database.execute_many(query, df.to_dict(orient="records"))
    os.remove(file_path)


async def load_files_to_db(path, file_suffix, columns, table_name):
    file_names = [
        file_name for file_name in os.listdir(path) if file_name.endswith(file_suffix)
    ]
    file_names.sort()
    tasks = []

    if len(file_names) > 1:
        files_to_process = file_names[:-1][:10]
        for file_name in files_to_process:
            file_path = os.path.join(path, file_name)
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join([f':{col}' for col in columns])})"
            tasks.append(process_file(file_path, columns, table_name, query))

    await asyncio.gather(*tasks)


async def load_trades_to_db():
    await load_files_to_db(
        trades_path,
        "_trades.json",
        ["id_deal", "Price", "Quantity", "Event_time", "Transaction_type"],
        "trades",
    )


async def load_bids_to_db():
    await load_files_to_db(
        bids_path, "_bids.json", ["Price", "Quantity", "Event_time"], "bids"
    )


async def load_asks_to_db():
    await load_files_to_db(
        asks_path, "_asks.json", ["Price", "Quantity", "Event_time"], "asks"
    )


# async def load_all_data_to_db():
#     await database.connect()
#     await asyncio.gather(load_trades_to_db(), load_bids_to_db(), load_asks_to_db())
#     await database.disconnect()


async def load_all_data_to_db():
    await database.connect()
    await load_trades_to_db()
    await load_bids_to_db()
    await load_asks_to_db()
    await database.disconnect()


if __name__ == "__main__":
    while True:
        asyncio.run(load_all_data_to_db())
        time.sleep(60)  # Спать 1 минуту (60 секунд)
