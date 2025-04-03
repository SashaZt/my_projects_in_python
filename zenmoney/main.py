import json
from datetime import datetime

import requests

# Ваш токен
TOKEN = "wNiaTY9fihwOyTXqR159rPk2yL2xFP"

# Базовый URL API
BASE_URL = "https://api.zenmoney.ru/v8/"


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


def get_account_by_id(token, account_id):
    """Получает полную информацию по конкретному счету по его ID и сохраняет в JSON"""
    accounts, _ = get_accounts_data(token)

    if accounts is None:
        return None

    for account in accounts:
        if account["id"] == account_id:
            print(f"\nПолная информация по счету с ID: {account_id}")
            print("--------------------------------")
            for key, value in account.items():
                print(f"{key}: {value}")

            filename = f"{account_id}.json"
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(account, json_file, ensure_ascii=False, indent=4)
            print(f"\nДанные счета сохранены в файл: {filename}")
            return account

    print(f"Счет с ID {account_id} не найден")
    return None


def get_transactions_by_account(token, account_id):
    """Получает транзакции по конкретному счету и сохраняет их в JSON"""
    _, transactions = get_accounts_data(token)

    if transactions is None:
        return None

    # Фильтруем транзакции по счету (incomeAccount или outcomeAccount)
    account_transactions = [
        t
        for t in transactions
        if t.get("incomeAccount") == account_id or t.get("outcomeAccount") == account_id
    ]

    if account_transactions:
        print(
            f"\nНайдено {len(account_transactions)} транзакций для счета {account_id}:"
        )
        for i, trans in enumerate(account_transactions, 1):
            print(f"\nТранзакция {i}:")
            for key, value in trans.items():
                print(f"{key}: {value}")

        # Сохраняем транзакции в JSON-файл с именем account_id_transactions.json
        filename = f"{account_id}_transactions.json"
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(account_transactions, json_file, ensure_ascii=False, indent=4)
        print(f"\nТранзакции сохранены в файл: {filename}")
        return account_transactions
    else:
        print(f"Транзакции для счета {account_id} не найдены")
        return []


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
            "data_transaction": data_transaction,
            "Поступления": income_account_title,  # Название вместо ID
            "Выплаты": outcome_account_title,  # Название вместо ID
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
    parsing_transaction()
