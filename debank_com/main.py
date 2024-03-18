import csv
import glob
import json
import os
import sys
import time

import requests


def get_wallet():
    name_files = 'wallet.csv'
    with open(name_files, newline='', encoding='utf-8') as files:
        reader = csv.reader(files, delimiter=',', quotechar='|')
        for w in reader:
            if len(w) == 2:  # Убедимся, что в строке два элемента
                yield w[0], w[1]  # Используем yield для генерации кошелька и даты


def get_token():
    with open('token.txt', 'r') as file:
        first_value = file.readline().strip()
        return first_value


def get_api():
    # Определите текущую директорию, где находится скрипт
    current_directory = os.getcwd()

    # Задайте имя папки data_json
    data_json_directory = 'data_json'

    # Создайте полный путь к папке data_json
    data_json_path = os.path.join(current_directory, data_json_directory)

    # Проверьте, существует ли папка data_json, и если нет, создайте ее
    if not os.path.exists(data_json_path):
        os.makedirs(data_json_path)
    for wallet, date in get_wallet():  # Итерируемся по всем кошелькам и датам
        date = int(date)
        token = get_token()
        headers = {
            'accept': 'application/json',
            'AccessKey': token,
        }

        start_time = 0
        count = 0
        print(f'Сохраняю файлы по кошельку {wallet}')
        while True:
            filename = f'{wallet}_{start_time}.json'

            if os.path.exists(filename):  # Проверка на существование файла
                print(f"File {filename} already exists. Skipping.")
                continue
            params = {
                'chain': '',
                'start_time': start_time,
                'page_count': '20',
                'id': wallet,
            }
            response = requests.get('https://pro-openapi.debank.com/v1/user/all_history_list', params=params,
                                    headers=headers)
            try:
                json_data = response.json()
            except:
                continue
            try:
                first_operation = int(json_data['history_list'][:1][0]['time_at'])
            except (IndexError, KeyError, TypeError):
                try:
                    first_operation = int(json_data['history_list'][1:2][0]['time_at'])
                except (IndexError, KeyError, TypeError):
                    first_operation = None  # или какое-либо другое значение по умолчанию

            if first_operation is not None and first_operation == date:
                break
            file_path = os.path.join(data_json_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

            if len(json_data['history_list']) == 0:
                break  # выход из цикла, если history_list пуст

            # Обновляем start_time на значение time_at последнего элемента
            for j in json_data['history_list'][-1:]:
                time_at = int(j['time_at'])

            if time_at == date:
                break  # выход из цикла, если time_at равен date

            start_time = time_at  # обновляем start_time для следующего запроса
            count += 1
            print(f'Сохранил файл {count}')

    print(f'Данные кошельков сохранены')
    time.sleep(5)


def par_json():
    # Определите текущую директорию, где находится скрипт
    current_directory = os.getcwd()

    # Задайте имя папки data_json
    data_json_directory = 'data_json'

    # Создайте полный путь к папке data_json
    data_json_path = os.path.join(current_directory, data_json_directory)

    folder = fr'{data_json_path}\*.json'
    files_html = glob.glob(folder)
    if not files_html:
        print("Новых данных нету")
        time.sleep(10)  # Подождать 10 секунд
        sys.exit()

    with open("wallet.csv", "w", errors='ignore', newline='', encoding="utf-8") as wallet_csv:
        wallet_writer = csv.writer(wallet_csv, delimiter=",")
        # wallet_writer.writerow(['first_operation', 'wallet'])  # Заголовок

        with open("wallet_transactions.csv", "a", errors='ignore', newline='', encoding="utf-8") as result_csv:
            result_writer = csv.writer(result_csv, delimiter=",")
            result_writer.writerow(
                (
                    'wallet', 'cate_id', 'cex_id', 'chain', 'id', 'is_scam', 'other_addr', 'project_id', 'cate_id',
                    'receives_amount', 'receives_from_addr', 'receives_token_id', 'sends_amount', 'sends_to_addr',
                    'sends_token_id', 'time_at', 'token_approve_spender', 'token_approve_token_id',
                    'token_approve_value', 'tx_from_eth_gas_fee', 'tx_from_addr', 'tx_message',
                    'tx_name', 'tx_selector', 'tx_status', 'tx_to_addr', 'tx_usd_gas_fee', 'tx_value', 'price_r',
                    'symbol_r', 'price_s', 'symbol_s', 'sends_amount_2', 'sends_to_addr_2', 'sends_token_id_2', 'price_s_2', 'symbol_s_2'
                ))

            for item in files_html:
                # print(item)
                file_name = os.path.splitext(os.path.basename(item))[0]
                parts = file_name.split('_')
                wallet = parts[0]

                with open(item, 'r', encoding="utf-8") as f:
                    data_json = json.load(f)
                    if '_0' in file_name:
                        try:
                            first_operation = int(data_json['history_list'][:1][0]['time_at'])
                            # Записать данные в wallet.csv
                            wallet_writer.writerow([wallet, first_operation])
                        except:
                            continue
                    token_dict = data_json['token_dict']
                    for j in data_json['history_list']:
                        cate_id = j['cate_id']
                        cex_id = j['cex_id']
                        chain = j['chain']
                        j_id = j['id']
                        is_scam = j['is_scam']
                        other_addr = j['other_addr']
                        project_id = j['project_id']

                        receives_data = j.get("receives", [])
                        receives_amount = receives_data[0].get('amount') if receives_data and 'amount' in receives_data[
                            0] else None
                        receives_from_addr = receives_data[0].get('from_addr') if receives_data and 'from_addr' in \
                                                                                  receives_data[0] else None
                        receives_token_id = receives_data[0].get('token_id') if receives_data and 'token_id' in \
                                                                                receives_data[0] else None
                        sends_token_id = None
                        sends_amount = None
                        sends_to_addr = None
                        sends_token_id_2 = None
                        sends_amount_2 = None
                        sends_to_addr_2 = None

                        sends_data = j.get("sends", [])
                        if len(sends_data) == 1:
                            sends_amount = sends_data[0].get('amount') if sends_data and 'amount' in sends_data[
                                0] else None
                            sends_price = sends_data[0].get('price') if sends_data and 'price' in sends_data[
                                0] else None
                            sends_to_addr = sends_data[0].get('to_addr') if sends_data and 'to_addr' in sends_data[
                                0] else None
                            sends_token_id = sends_data[0].get('token_id') if sends_data and 'token_id' in sends_data[
                                0] else None
                        if len(sends_data) == 2:
                            sends_amount = sends_data[0].get('amount') if sends_data and 'amount' in sends_data[
                                0] else None
                            sends_price = sends_data[0].get('price') if sends_data and 'price' in sends_data[
                                0] else None
                            sends_to_addr = sends_data[0].get('to_addr') if sends_data and 'to_addr' in sends_data[
                                0] else None
                            sends_token_id = sends_data[0].get('token_id') if sends_data and 'token_id' in sends_data[
                                0] else None
                            sends_amount_2 = sends_data[1].get('amount') if sends_data and 'amount' in sends_data[
                                1] else None
                            sends_price = sends_data[1].get('price') if sends_data and 'price' in sends_data[
                                1] else None
                            sends_to_addr_2 = sends_data[1].get('to_addr') if sends_data and 'to_addr' in sends_data[
                                1] else None
                            sends_token_id_2 = sends_data[1].get('token_id') if sends_data and 'token_id' in sends_data[
                                1] else None

                        time_at = int(j['time_at'])
                        token_approve_data = j.get("token_approve", [])
                        token_approve_spender = token_approve_data.get(
                            'spender') if token_approve_data and 'spender' in token_approve_data else None
                        token_approve_token_id = token_approve_data.get(
                            'token_id') if token_approve_data and 'token_id' in token_approve_data else None
                        token_approve_value = token_approve_data.get(
                            'value') if token_approve_data and 'value' in token_approve_data else None

                        tx_data = j.get("tx", [])
                        tx_from_eth_gas_fee = tx_data.get(
                            'eth_gas_fee') if tx_data and 'eth_gas_fee' in tx_data else None
                        tx_from_addr = tx_data.get('from_addr') if tx_data and 'from_addr' in tx_data else None
                        tx_message = tx_data.get('message') if tx_data and 'message' in tx_data else None
                        tx_name = tx_data.get('name') if tx_data and 'name' in tx_data else None
                        tx_selector = tx_data.get('selector') if tx_data and 'selector' in tx_data else None
                        tx_status = tx_data.get('status') if tx_data and 'status' in tx_data else None
                        tx_to_addr = tx_data.get('to_addr') if tx_data and 'to_addr' in tx_data else None
                        tx_usd_gas_fee = tx_data.get('usd_gas_fee') if tx_data and 'usd_gas_fee' in tx_data else None
                        tx_value = tx_data.get('value') if tx_data and 'value' in tx_data else None

                        token_id_to_lookup = receives_token_id or sends_token_id  # Предпочитайте receives_token_id перед sends_token_id
                        price_r = None
                        symbol_r = None
                        price_s = None
                        symbol_s = None
                        price_s_2 = None
                        symbol_s_2 = None
                        if receives_token_id in token_dict:

                            token_info = token_dict[receives_token_id]
                            price_r = token_info.get('price')
                            symbol_r = token_info.get('symbol')

                        if sends_token_id in token_dict:
                            token_info = token_dict[sends_token_id]
                            price_s = token_info.get('price')
                            symbol_s = token_info.get('symbol')

                        if sends_token_id_2 in token_dict:
                            token_info = token_dict[sends_token_id_2]
                            price_s_2 = token_info.get('price')
                            symbol_s_2 = token_info.get('symbol')

                        # Записать данные в result.csv
                        datas = [wallet, cate_id, cex_id, chain, j_id, is_scam, other_addr, project_id, cate_id,
                                 receives_amount, receives_from_addr, receives_token_id, sends_amount, sends_to_addr,
                                 sends_token_id, time_at, token_approve_spender, token_approve_token_id,
                                 token_approve_value, tx_from_eth_gas_fee, tx_from_addr, tx_message, tx_name,
                                 tx_selector, tx_status, tx_to_addr, tx_usd_gas_fee, tx_value, price_r, symbol_r,
                                 price_s, symbol_s, sends_amount_2, sends_to_addr_2, sends_token_id_2, price_s_2, symbol_s_2]
                        result_writer.writerow(datas)

    # Получаем список всех файлов в папке
    files = glob.glob(os.path.join(data_json_path, '*'))

    # Удаляем каждый файл
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
            print(f'Удаляю {f}')

    print("Все удачно выполнено")
    time.sleep(5)


if __name__ == '__main__':
    get_api()
    par_json()
