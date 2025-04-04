import json
import sqlite3
import sys
import traceback
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
            "data_transaction": data_transaction,
            "income_account_title": income_account_title,
            "outcome_account_title": outcome_account_title,
            "comment": comment,
            "income": income,
            "outcome": outcome,
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

        # Создаем таблицу с уникальным полем id_transaction и новым полем update_google_sheets
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_transaction TEXT UNIQUE NOT NULL,
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
        id_transaction = data["id_transaction"]
        data_transaction = data["data_transaction"]
        income_account_title = data["income_account_title"]
        outcome_account_title = data["outcome_account_title"]
        comment = data["comment"]
        income = data["income"]
        outcome = data["outcome"]

        # Формируем словарь с русскими ключами, добавляем update_google_sheets
        all_data_transaction = {
            "id_transaction": id_transaction,
            "data_transaction": data_transaction,
            "income_account_title": income_account_title,
            "outcome_account_title": outcome_account_title,
            "comment": comment,
            "income": income,
            "outcome": outcome,
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
                (id_transaction, data_transaction, income_account_title, outcome_account_title, 
                comment, income, outcome, update_google_sheets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    trans["id_transaction"],
                    trans["data_transaction"],
                    trans["income_account_title"],
                    trans["outcome_account_title"],
                    trans["comment"],
                    trans["income"],
                    trans["outcome"],
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
    id_transaction, status, db_name="zenmoney_transactions.db"
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
            WHERE id_transaction = ?
        """,
            (1 if status else 0, id_transaction),
        )

        conn.commit()
        if cursor.rowcount > 0:
            print(
                f"Статус update_google_sheets для транзакции {id_transaction} обновлен на {status}"
            )
        else:
            print(f"Транзакция с ID {id_transaction} не найдена")

    except sqlite3.Error as e:
        print(f"Ошибка при обновлении статуса: {e}")
    finally:
        conn.close()


# def get_transactions_by_date(data_transaction, db_name="zenmoney_transactions.db"):
#     """Возвращает все транзакции за указанную дату из SQLite базы данных"""
#     try:
#         conn = sqlite3.connect(db_name)
#         cursor = conn.cursor()

#         # Выполняем запрос с фильтром по data_transaction
#         cursor.execute(
#             """
#             SELECT id_transaction, data_transaction, income_account_title,
#             outcome_account_title, comment, income, outcome, update_google_sheets
#             FROM transactions
#             WHERE data_transaction = ?
#         """,
#             (data_transaction,),
#         )

#         # Получаем все строки
#         rows = cursor.fetchall()

#         if not rows:
#             print(f"Транзакции за дату {data_transaction} не найдены")
#             return []

#         # Формируем список словарей с русскими ключами
#         transactions = []
#         for row in rows:
#             trans_dict = {
#                 "id_transaction": row[0],
#                 "Дата": row[1],
#                 "Получатель": row[2],
#                 "Плательщик": row[3],
#                 "Коментарий": row[4],
#                 "Поступления": row[5],
#                 "Выплаты": row[6],
#                 "update_google_sheets": bool(row[7]),  # Преобразуем 0/1 в True/False
#             }
#             transactions.append(trans_dict)

#         # Выводим результат для проверки
#         print(f"\nНайдено {len(transactions)} транзакций за дату {data_transaction}:")
#         for i, trans in enumerate(transactions, 1):
#             print(f"\nТранзакция {i}:")
#             for key, value in trans.items():
#                 print(f"{key}: {value}")

#         return transactions

#     except sqlite3.Error as e:
#         print(f"Ошибка при запросе к базе данных: {e}")
#         return []
#     finally:
#         conn.close()


def get_transactions_by_date(
    data_transaction,
    income_account_title=None,
    outcome_account_title=None,
    db_name="zenmoney_transactions.db",
):
    """Возвращает все транзакции за указанную дату и, опционально, по получателю из SQLite базы данных"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Базовый запрос
        query = """
            SELECT id_transaction, data_transaction, income_account_title,
                   outcome_account_title, comment, income, outcome, update_google_sheets 
            FROM transactions 
            WHERE data_transaction = ?
        """
        params = [data_transaction]

        # Добавляем фильтр по income_account_title, если он указан
        if income_account_title is not None:
            query += " AND income_account_title = ?"
            params.append(income_account_title)
        # Добавляем фильтр по income_account_title, если он указан
        if outcome_account_title is not None:
            query += " AND outcome_account_title = ?"
            params.append(outcome_account_title)

        # Выполняем запрос
        cursor.execute(query, tuple(params))

        # Получаем все строки
        rows = cursor.fetchall()

        if not rows:
            print(
                f"Транзакции за дату {data_transaction} с получателем {income_account_title or outcome_account_title or'любым'} не найдены"
            )
            return []

        # Формируем список словарей с русскими ключами
        transactions = []
        for row in rows:
            trans_dict = {
                "id_transaction": row[0],
                "data_transaction": row[1],
                "income_account_title": row[2],
                "outcome_account_title": row[3],
                "comment": row[4],
                "income": row[5],
                "outcome": row[6],
                "update_google_sheets": bool(row[7]),  # Преобразуем 0/1 в True/False
            }
            transactions.append(trans_dict)

        # Выводим результат для проверки
        print(
            f"\nНайдено {len(transactions)} транзакций за дату {data_transaction} с получателем {income_account_title or outcome_account_title or 'любым'}:"
        )
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


def load_product_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def find_next_empty_row(sheet):
    """
    Находит следующую пустую строку в таблице по колонке A.

    Args:
        sheet: Объект листа Google Sheets

    Returns:
        int: Номер следующей пустой строки
    """
    try:
        # Получаем все значения в колонке A
        column_a = sheet.col_values(1)  # 1 = колонка A

        if not column_a:
            # Если колонка пуста, начинаем с первой строки
            return 1

        # Находим количество непустых ячеек и добавляем 1
        next_row = len(column_a) + 1
        logger.info(f"Найдена следующая пустая строка: {next_row}")
        return next_row

    except Exception as e:
        logger.error(f"Ошибка при поиске пустой строки: {e}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        # В случае ошибки возвращаем большое значение (например, 10000)
        # чтобы не перезаписать важные данные
        return 10000


def update_transaction_db_status(
    transaction_id, status=True, db_name="zenmoney_transactions.db"
):
    """
    Обновляет статус транзакции в базе данных SQLite.

    Args:
        transaction_id (str): ID транзакции для обновления
        status (bool): Новый статус (True = обновлено, False = не обновлено)
        db_name (str): Имя файла базы данных

    Returns:
        bool: True если обновление успешно, False в противном случае
    """
    try:
        logger.info(f"Обновление статуса транзакции {transaction_id} в БД на {status}")
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Обновляем статус транзакции
        cursor.execute(
            """
            UPDATE transactions 
            SET update_google_sheets = ? 
            WHERE id_transaction = ?
            """,
            (int(status), transaction_id),
        )

        # Проверяем, была ли обновлена запись
        if cursor.rowcount > 0:
            logger.info(f"Статус транзакции {transaction_id} успешно обновлен в БД")
            conn.commit()
            return True
        else:
            logger.warning(f"Транзакция {transaction_id} не найдена в БД")
            conn.rollback()
            return False

    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении статуса транзакции в БД: {e}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        return False

    finally:
        conn.close()


def update_google_sheet_with_transaction(transaction, sheet_raw):
    """
    Обновляет Google таблицу данными из транзакции, автоматически находя свободную строку.

    Args:
        transaction (dict): Словарь с данными транзакции
        sheet_raw (list): Данные о структуре таблицы
    """
    try:
        logger.info(
            f"Начало обновления для транзакции ID: {transaction.get('id_transaction')}"
        )

        # Получаем лист Google таблицы
        sheet = get_google_sheet()
        logger.info("Успешно получен лист Google таблицы")

        # Находим следующую пустую строку
        line_table = find_next_empty_row(sheet)
        logger.info(f"Будет использована строка {line_table} для новой записи")

        # sheet_raw - это список словарей, объединим их в один для облегчения поиска
        combined_sheet_raw = {}
        for item in sheet_raw:
            if isinstance(item, dict):
                combined_sheet_raw.update(item)

        logger.info(f"Обработанная структура sheet_raw: {combined_sheet_raw}")

        # Обновляем ячейки по одной
        try:
            # Добавляем дату в колонку A
            if "data_transaction" in transaction and transaction["data_transaction"]:
                # Преобразуем строку в объект datetime
                data_transaction = transaction["data_transaction"]
                logger.info(f"Исходная дата транзакции: {data_transaction}")

                try:
                    date_obj = datetime.strptime(data_transaction, "%Y-%m-%d")
                    formatted_date = f"{date_obj.month}/{date_obj.day}/{date_obj.year}"
                    logger.info(f"Отформатированная дата: {formatted_date}")

                    # Обновляем ячейку с датой
                    sheet.update_cell(line_table, 1, formatted_date)  # 1 = колонка A
                    logger.info(
                        f"Дата {formatted_date} добавлена в ячейку A{line_table}"
                    )
                except ValueError as date_error:
                    logger.error(f"Ошибка при форматировании даты: {date_error}")

            # Добавляем комментарий в колонку B
            if "comment" in transaction and transaction["comment"]:
                comment = transaction["comment"]
                sheet.update_cell(line_table, 2, comment)  # 2 = колонка B
                logger.info(f"Комментарий '{comment}' добавлен в ячейку B{line_table}")

            # Добавляем доход в соответствующую колонку
            income_account = transaction.get("income_account_title")
            if income_account and "income" in transaction:
                if income_account in combined_sheet_raw:
                    income_column_letter = combined_sheet_raw[income_account]["income"]
                    # Преобразуем буквенный столбец в числовой индекс
                    income_column_index = column_letter_to_index(income_column_letter)
                    income_value = transaction["income"]
                    sheet.update_cell(line_table, income_column_index, income_value)
                    logger.info(
                        f"Доход {income_value} добавлен в ячейку {income_column_letter}{line_table}"
                    )
                else:
                    logger.warning(
                        f"Не найдена колонка для счета дохода: {income_account}"
                    )

            # Добавляем расход в соответствующую колонку
            outcome_account = transaction.get("outcome_account_title")
            if outcome_account and "outcome" in transaction:
                if outcome_account in combined_sheet_raw:
                    outcome_column_letter = combined_sheet_raw[outcome_account][
                        "outcome"
                    ]
                    # Преобразуем буквенный столбец в числовой индекс
                    outcome_column_index = column_letter_to_index(outcome_column_letter)
                    outcome_value = transaction["outcome"]
                    sheet.update_cell(line_table, outcome_column_index, outcome_value)
                    logger.info(
                        f"Расход {outcome_value} добавлен в ячейку {outcome_column_letter}{line_table}"
                    )
                else:
                    logger.warning(
                        f"Не найдена колонка для счета расхода: {outcome_account}"
                    )

            logger.info(
                f"Таблица успешно обновлена для транзакции {transaction['id_transaction']}"
            )
            return True

        except Exception as update_error:
            logger.error(f"Ошибка при обновлении ячейки: {update_error}")
            logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
            return False

    except Exception as e:
        logger.error(f"Ошибка при обновлении таблицы: {e}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        return False


def column_letter_to_index(col_str):
    """
    Преобразует буквенное обозначение колонки в числовой индекс, начиная с 1.
    Например, A -> 1, B -> 2, Z -> 26, AA -> 27, ...

    Args:
        col_str (str): Буквенное обозначение колонки (например, 'A', 'BC')

    Returns:
        int: Числовой индекс колонки
    """
    index = 0
    for c in col_str:
        index = index * 26 + (ord(c.upper()) - ord("A") + 1)
    return index


def process_transaction_to_sheet(transaction, sheet_raw):
    """
    Обрабатывает транзакцию и записывает ее в Google таблицу.
    После успешной записи обновляет статус в БД.

    Args:
        transaction (dict): Данные транзакции
        sheet_raw (list): Информация о структуре таблицы
    """
    try:
        logger.info(f"Начало обработки транзакции: {transaction.get('id_transaction')}")

        # Значение False означает, что данные еще не обновлены и их нужно загрузить
        if transaction.get("update_google_sheets") is False:
            logger.info(
                f"Транзакция {transaction.get('id_transaction')} требует обновления в таблице"
            )
        else:
            logger.info(
                f"Статус update_google_sheets: {transaction.get('update_google_sheets')}"
            )
            logger.info(
                f"Транзакция {transaction.get('id_transaction')} уже была обновлена"
            )
            return True  # Пропускаем обновление, если уже обработано

        # Обновляем Google таблицу
        result = update_google_sheet_with_transaction(transaction, sheet_raw)

        if result:
            logger.info(
                f"Транзакция {transaction.get('id_transaction')} успешно записана в таблицу"
            )

            # Обновляем статус в базе данных
            db_update_result = update_transaction_db_status(
                transaction["id_transaction"], True
            )
            if db_update_result:
                logger.info(
                    f"Статус транзакции {transaction.get('id_transaction')} обновлен в БД"
                )
            else:
                logger.warning(
                    f"Не удалось обновить статус транзакции {transaction.get('id_transaction')} в БД"
                )

            return True
        else:
            logger.error(
                f"Не удалось записать транзакцию {transaction.get('id_transaction')} в таблицу"
            )
            return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке транзакции: {e}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        return False


# Пример использования
def process_transactions(
    target_date=None, account=None, db_name="zenmoney_transactions.db"
):
    """
    Получает транзакции из БД и обрабатывает их для обновления Google таблицы.

    Args:
        target_date (str, optional): Дата для фильтрации транзакций (формат YYYY-MM-DD)
        account (str, optional): Название счета для фильтрации транзакций
        db_name (str): Имя файла базы данных

    Returns:
        int: Количество успешно обработанных транзакций
    """
    try:
        # Получаем транзакции из БД
        transactions = get_transactions_by_date(target_date, None, account)

        # Загружаем конфигурацию структуры таблицы
        sheet_raw = load_product_data("sheet_raw.json")

        logger.info(f"Получено {len(transactions)} транзакций для обработки")
        logger.info(f"Структура таблицы: {sheet_raw}")

        success_count = 0
        for transaction in transactions:
            if process_transaction_to_sheet(transaction, sheet_raw):
                success_count += 1

        logger.info(
            f"Успешно обработано {success_count} из {len(transactions)} транзакций"
        )
        return success_count

    except Exception as e:
        logger.error(f"Ошибка при обработке транзакций: {e}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        return 0


if __name__ == "__main__":
    # sheet = get_google_sheet()
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

    target_date = "2025-03-29"
    transactions = get_transactions_by_date(target_date, None, "Amehan MONO WHITE")[:1]
    sheet_raw = load_product_data("sheet_raw.json")
    logger.info(transactions)
    logger.info(sheet_raw)
    for transaction in transactions:
        process_transaction_to_sheet(transaction, sheet_raw)
