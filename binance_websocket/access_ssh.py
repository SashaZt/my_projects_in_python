import pandas as pd
import paramiko
import os
import asyncio
import time
from dotenv import load_dotenv
from databases import Database
from datetime import datetime, timedelta


def execute_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        return stdout.read().decode()
    else:
        error_msg = stderr.read().decode()
        raise Exception(f"Error executing command '{command}': {error_msg}")


def count_files_in_directory(ssh, directory):
    # Команда для получения списка файлов
    command = f"ls -l {directory} | grep '^-' | wc -l"
    output = execute_ssh_command(ssh, command)
    return int(output.strip())


def get_service_status(output):
    if "active (running)" in output:
        return "running"
    elif "inactive (dead)" in output or "inactive (stopped)" in output:
        return "stopped"
    else:
        return "unknown"


def ssh_connect():
    # Загрузка переменных окружения из .env файла
    load_dotenv()

    # Получение текущей директории
    current_directory = os.getcwd()

    # Получение имени файла ключа из переменной окружения
    key_filename = os.getenv("PRIVATE_KEY_FILENAME")
    if not key_filename:
        raise Exception("PRIVATE_KEY_FILENAME not found in environment variables")

    # Составление полного пути к файлу ключа
    key_path = os.path.join(current_directory, key_filename)
    if not os.path.exists(key_path):
        raise Exception(f"Key file not found at {key_path}")

    # Настройки подключения
    hostname = os.getenv("HOSTNAME_SERVER")
    if not hostname:
        raise Exception("HOSTNAME_SERVER not found in environment variables")

    port = os.getenv("PORT_SSH")
    if not port:
        raise Exception("PORT_SSH not found in environment variables")
    port = int(port)  # Ensure port is an integer

    username = "root"
    # username = os.getenv("USERNAME")
    if not username:
        raise Exception("USERNAME not found in environment variables")

    # Создание SSH клиента и подключение
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Загрузка приватного ключа RSA
    private_key = paramiko.RSAKey.from_private_key_file(key_path)

    ssh.connect(hostname, port=port, username=username, pkey=private_key)
    return ssh


def mysql_connect():
    load_dotenv()
    db_type = os.getenv("DB_TYPE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    # Проверка, что все переменные окружения установлены
    if not all([db_type, username, password, host, port, db_name]):
        raise ValueError("One or more environment variables are not set")

    # Создание строки подключения
    database_url = f"{db_type}+aiomysql://{username}:{password}@{host}:{port}/{db_name}"

    # Создание подключения к базе данных
    database = Database(database_url)
    return database


async def get_unique_dates(database):
    query = """
    SELECT DISTINCT DATE(Event_time) as date
    FROM asks
    WHERE DATE(Event_time) < CURDATE()
    """
    rows = await database.fetch_all(query=query)
    return [row["date"] for row in rows]


async def work_with_mysql(database):

    await database.connect()
    print("Получаем даты в БД")
    dates = await get_unique_dates(database)
    formatted_dates = [date.strftime("%Y-%m-%d") for date in dates]
    print("Даты в БД:", formatted_dates)


def stop_service():
    ssh = ssh_connect()

    try:
        directory_path = "/home/binance/temp/asks/"
        file_count = count_files_in_directory(ssh, directory_path)
        if file_count == 1:
            service_status_command = "sudo systemctl status write_bd.service"
            output = execute_ssh_command(ssh, service_status_command)
            # Получение статуса службы
            service_status = get_service_status(output)
            print(f"Служба 'write_bd.service' is {service_status}")
            if service_status == "running":
                stop_service_command = "sudo systemctl stop write_bd.service"
                execute_ssh_command(ssh, stop_service_command)
                print("Служба остановлена")
                return True
        else:
            return False

    finally:
        # Отключение от SSH
        ssh.close()
        print("Отключение от SSH")


def start_service():
    ssh = ssh_connect()
    stop_service_command = "sudo systemctl start write_bd.service"
    execute_ssh_command(ssh, stop_service_command)
    print("Служба запущена, пишем данные в БД")
    ssh.close()
    print("Отключение от SSH")


# Функция сохранения данных в csv
async def save_to_csv(database, target_date, table):
    now = datetime.now()
    time_now = now.strftime("%H:%M:%S")
    print(time_now)
    query = f"""
    SELECT * FROM {table}
    WHERE DATE(Event_time) = :target_date
    """
    rows = await database.fetch_all(query=query, values={"target_date": target_date})

    if rows:
        # Преобразуем каждую строку в словарь
        data = [dict(row) for row in rows]

        # Преобразуем в DataFrame
        df = pd.DataFrame(data)
        if not df.empty:
            file_name = f"{target_date}_{table}.csv"
            df.to_csv(file_name, index=False)
            print(f"Сохранил {file_name}")
            now = datetime.now()
            time_now = now.strftime("%H:%M:%S")
            print(time_now)
        else:
            print("Данные отсутствуют для заданной даты.")
    else:
        print("Запрос не вернул никаких данных.")


# Удаление данных из БД
async def delete_data_sql(database, target_date, table):
    start_date = target_date
    end_date = start_date + timedelta(days=1)
    # Подтверждение удаления данных
    # confirm = input(f"Удалить данные из базы {table} за {start_date}? Y/N: ")
    # if confirm.lower() == "y":
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
    # else:
    #     print("Удаление данных отменено.")


# Получение таблиц в БД
async def get_all_tables(database):
    query = "SHOW TABLES"
    rows = await database.fetch_all(query=query)
    return [row[0] for row in rows]  # MySQL возвращает имена таблиц как кортежи


# Анализ и оптимизация БД
async def optimize_and_analyze_db(database):
    tables = await get_all_tables(database)
    for table in tables:
        optimize_query = f"OPTIMIZE TABLE {table};"
        analyze_query = f"ANALYZE TABLE {table};"
        await database.execute(optimize_query)
        print(f"Оптимизация таблицы {table}.")
        await database.execute(analyze_query)
        print(f"Анализ таблицы {table}.")


async def main_async():
    database = mysql_connect()
    await database.connect()

    try:
        dates = await get_unique_dates(database)
        formatted_dates = [date.strftime("%Y-%m-%d") for date in dates]
        print("Даты в БД:", formatted_dates)

        while True:
            print(
                "Введите 1 для выгрузки данных в csv "
                "\nВведите 2 для удаления данных из БД"
                "\nВведите 3 для оптимизации БД"
                "\nВведите 4 для загрузки данных в БД"
                "\nВведите 0 для закрытия программы"
            )
            user_input = int(input("Выберите действие: "))
            if user_input == 0:
                print("Программа завершена.")
                break  # Выход из цикла, завершение программы

            tables = ["asks", "bids", "trades"]
            if user_input == 1:
                for target_date in dates:
                    for table in tables:
                        await save_to_csv(database, target_date, table)
            elif user_input == 2:
                for target_date in dates:
                    for table in tables:
                        await delete_data_sql(database, target_date, table)
            elif user_input == 3:
                await optimize_and_analyze_db(database)
            elif user_input == 4:
                start_service()
            else:
                print("Неверный ввод, пожалуйста, введите корректный номер действия.")
    finally:
        await database.disconnect()


if __name__ == "__main__":
    if stop_service():
        print("Получаем даты которые есть в БД")
        asyncio.run(main_async())
    else:
        print("Запусти позже")
        time.sleep(10)
