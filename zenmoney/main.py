import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import gspread
import requests
from google.oauth2.service_account import Credentials
from loguru import logger

# Ваш токен
# TOKEN =

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
log_directory = current_directory / "log"

# Создание директорий, если они не существуют
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

# Файлы
output_xml_file = data_directory / "output.xml"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"

# Настройка логгера
logger.remove()
# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]
BASE_URL = config["google"]["sheet"]
# Базовый URL API


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


def get_accounts_data(token):
    """Получает все счета"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    current_timestamp = 0

    payload = {
        "currentClientTimestamp": int(datetime.now().timestamp()),
        "serverTimestamp": current_timestamp,
    }

    try:
        response = requests.post(
            f"{BASE_URL}diff/", headers=headers, data=json.dumps(payload), timeout=30
        )
        response.raise_for_status()
        data = response.json()
        with open("accounts.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        return data.get("account", []), data.get("transaction", [])

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None, None


# def get_account_by_id(token, account_id):
#     """Получает полную информацию по конкретному счету по его ID и сохраняет в JSON"""
#     accounts, _ = get_accounts_data(token)

#     if accounts is None:
#         return None

#     for account in accounts:
#         if account["id"] == account_id:
#             print(f"\nПолная информация по счету с ID: {account_id}")
#             print("--------------------------------")
#             for key, value in account.items():
#                 print(f"{key}: {value}")

#             filename = f"{account_id}.json"
#             with open(filename, "w", encoding="utf-8") as json_file:
#                 json.dump(account, json_file, ensure_ascii=False, indent=4)
#             print(f"\nДанные счета сохранены в файл: {filename}")
#             return account

#     print(f"Счет с ID {account_id} не найден")
#     return None


# def get_transactions_by_account(token, account_id):
#     """Получает транзакции по конкретному счету и сохраняет их в JSON"""
#     _, transactions = get_accounts_data(token)

#     if transactions is None:
#         return None

#     # Фильтруем транзакции по счету (incomeAccount или outcomeAccount)
#     account_transactions = [
#         t
#         for t in transactions
#         if t.get("incomeAccount") == account_id or t.get("outcomeAccount") == account_id
#     ]

#     if account_transactions:
#         print(
#             f"\nНайдено {len(account_transactions)} транзакций для счета {account_id}:"
#         )
#         for i, trans in enumerate(account_transactions, 1):
#             print(f"\nТранзакция {i}:")
#             for key, value in trans.items():
#                 print(f"{key}: {value}")

#         # Сохраняем транзакции в JSON-файл с именем account_id_transactions.json
#         filename = f"{account_id}_transactions.json"
#         with open(filename, "w", encoding="utf-8") as json_file:
#             json.dump(account_transactions, json_file, ensure_ascii=False, indent=4)
#         print(f"\nТранзакции сохранены в файл: {filename}")
#         return account_transactions
#     else:
#         print(f"Транзакции для счета {account_id} не найдены")
#         return []


def parsing_transaction():
    # Читаем данные из файла accounts.json
    with open("accounts.json", "r", encoding="utf-8") as json_file:
        datas = json.load(json_file)

    transactions = datas["transaction"]
    accounts = datas["account"]

    all_accounts = []
    all_transactions = []

    # Создаем список счетов с ID и названиями
    for account in accounts:
        account_id = account["id"]
        account_title = account["title"]
        all_data_account = {
            "account_id": account_id,
            "account_title": account_title,
        }
        all_accounts.append(all_data_account)

    # Обрабатываем транзакции
    for data in transactions:
        id_transaction = data["id"]
        data_transaction = data["date"]
        income_account_id = data["incomeAccount"]
        outcome_account_id = data["outcomeAccount"]
        comment = data["comment"]
        income = data["income"]
        outcome = data["outcome"]

        # Ищем названия счетов по их ID
        income_account_title = None
        outcome_account_title = None

        for account in all_accounts:
            if account["account_id"] == income_account_id:
                income_account_title = account["account_title"]
            if account["account_id"] == outcome_account_id:
                outcome_account_title = account["account_title"]

        # Формируем данные транзакции с названиями счетов вместо ID
        all_data_transaction = {
            "id_transaction": id_transaction,
            "Дата": data_transaction,
            "Получатель": income_account_title,
            "Плательщик": outcome_account_title,
            "Коментарий": comment,
            "Поступления": income,
            "Выплаты": outcome,
        }
        all_transactions.append(all_data_transaction)

    # Выводим результат для проверки (опционально)
    for i, trans in enumerate(all_transactions, 1):
        print(f"\nТранзакция {i}:")
        for key, value in trans.items():
            print(f"{key}: {value}")

    # Сохраняем результат в файл (опционально)
    with open("parsed_transactions.json", "w", encoding="utf-8") as json_file:
        json.dump(all_transactions, json_file, ensure_ascii=False, indent=4)

    return all_transactions


def create_sqlite_db(db_name="zenmoney_transactions.db"):
    """Создает SQLite базу данных с таблицей транзакций"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Создаем таблицу с уникальным полем transaction_id и новым полем update_google_sheets
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                data_transaction TEXT NOT NULL,
                income_account_title TEXT,
                outcome_account_title TEXT,
                comment TEXT,
                income REAL NOT NULL,
                outcome REAL NOT NULL,
                update_google_sheets BOOLEAN NOT NULL DEFAULT 0
            )
        """
        )

        conn.commit()
        print(f"База данных {db_name} и таблица transactions успешно созданы")

    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        conn.close()


def prepare_transactions_for_db(transactions):
    """Подготавливает список словарей для записи в SQLite"""
    prepared_transactions = []

    for data in transactions:
        transaction_id = data["id_transaction"]
        data_transaction = data["Дата"]
        income_account_title = data["Получатель"]
        outcome_account_title = data["Плательщик"]
        comment = data["Коментарий"]
        income = data["Поступления"]
        outcome = data["Выплаты"]

        # Формируем словарь с русскими ключами, добавляем update_google_sheets
        all_data_transaction = {
            "id_transaction": transaction_id,
            "Дата": data_transaction,
            "Получатель": income_account_title,
            "Плательщик": outcome_account_title,
            "Коментарий": comment,
            "Поступления": income,
            "Выплаты": outcome,
            "update_google_sheets": False,  # Значение по умолчанию
        }
        prepared_transactions.append(all_data_transaction)

    return prepared_transactions


def save_transactions_to_db(transactions, db_name="zenmoney_transactions.db"):
    """Сохраняет транзакции в SQLite базу данных"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Подготовка данных для вставки
        for trans in transactions:
            cursor.execute(
                """
                INSERT OR IGNORE INTO transactions 
                (transaction_id, data_transaction, income_account_title, outcome_account_title, 
                comment, income, outcome, update_google_sheets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    trans["id_transaction"],
                    trans["Дата"],
                    trans["Получатель"],
                    trans["Плательщик"],
                    trans["Коментарий"],
                    trans["Поступления"],
                    trans["Выплаты"],
                    trans["update_google_sheets"],
                ),
            )

        conn.commit()
        print(f"Успешно сохранено {len(transactions)} транзакций в базу данных")

    except sqlite3.Error as e:
        print(f"Ошибка при сохранении в базу данных: {e}")
    finally:
        conn.close()


def update_google_sheets_status(
    transaction_id, status, db_name="zenmoney_transactions.db"
):
    """Обновляет поле update_google_sheets для указанной транзакции"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Обновляем статус
        cursor.execute(
            """
            UPDATE transactions 
            SET update_google_sheets = ?
            WHERE transaction_id = ?
        """,
            (1 if status else 0, transaction_id),
        )

        conn.commit()
        if cursor.rowcount > 0:
            print(
                f"Статус update_google_sheets для транзакции {transaction_id} обновлен на {status}"
            )
        else:
            print(f"Транзакция с ID {transaction_id} не найдена")

    except sqlite3.Error as e:
        print(f"Ошибка при обновлении статуса: {e}")
    finally:
        conn.close()


def get_transactions_by_date(data_transaction, db_name="zenmoney_transactions.db"):
    """Возвращает все транзакции за указанную дату из SQLite базы данных"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Выполняем запрос с фильтром по data_transaction
        cursor.execute(
            """
            SELECT transaction_id, data_transaction, income_account_title,
            outcome_account_title, comment, income, outcome, update_google_sheets 
            FROM transactions 
            WHERE data_transaction = ?
        """,
            (data_transaction,),
        )

        # Получаем все строки
        rows = cursor.fetchall()

        if not rows:
            print(f"Транзакции за дату {data_transaction} не найдены")
            return []

        # Формируем список словарей с русскими ключами
        transactions = []
        for row in rows:
            trans_dict = {
                "id_transaction": row[0],
                "Дата": row[1],
                "Получатель": row[2],
                "Плательщик": row[3],
                "Коментарий": row[4],
                "Поступления": row[5],
                "Выплаты": row[6],
                "update_google_sheets": bool(row[7]),  # Преобразуем 0/1 в True/False
            }
            transactions.append(trans_dict)

        # Выводим результат для проверки
        print(f"\nНайдено {len(transactions)} транзакций за дату {data_transaction}:")
        for i, trans in enumerate(transactions, 1):
            print(f"\nТранзакция {i}:")
            for key, value in trans.items():
                print(f"{key}: {value}")

        return transactions

    except sqlite3.Error as e:
        print(f"Ошибка при запросе к базе данных: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    # Пример вызова для всех счетов
    # accounts, _ = get_accounts_data(TOKEN)
    # if accounts:
    #     print("Найденные счета:")
    #     for account in accounts:
    #         print(f"ID: {account['id']}")
    #         print(f"Название: {account['title']}")
    #         print(f"Валюта: {account['instrument']}")
    #         print(f"Баланс: {account['balance']}")
    #         print(f"Тип: {account['type']}")
    #         print(f"Включен в баланс: {account['inBalance']}")
    #         print("---")

    # # Пример вызова для конкретного счета
    # target_account_id = "7337d4ec-16e8-4663-887b-551daf077e59"
    # detailed_account = get_account_by_id(TOKEN, target_account_id)

    # Получение и сохранение транзакций
    # transactions = get_transactions_by_account(TOKEN, target_account_id)

    # sample = parsing_transaction()
    # # Создаем базу данных
    # create_sqlite_db()

    # # Подготавливаем транзакции
    # prepared_data = prepare_transactions_for_db(sample)
    # save_transactions_to_db(prepared_data)

    target_date = "2025-04-02"
    transactions = get_transactions_by_date(target_date)
    sheet = get_google_sheet()
