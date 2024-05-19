import requests
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import time
import glob

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
json_path = os.path.join(temp_path, "json")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)


# Функция для получение данных с API
def get_json_data():

    # url = f"https://betatransfer.io/excel/cascades/{id_accounts}/accounts"
    first_url = "https://betatransfer.io/excel/cascades"
    token = "pLaZ2zGFtbKt8UOdw6EAfpIBWwbsGETd"
    headers = {"Authorization": f"Basic {token}"}
    response = requests.get(first_url, headers=headers)

    if response.status_code == 200:
        datas = response.json()
        tables = []
        first_currency = None  # Переменная для хранения первой валюты
        for data in datas:

            id_cascada = data["id"]

            name_cascada = data["name"]

            second_url = f"https://betatransfer.io/excel/cascades/{id_cascada}/accounts"

            response = requests.get(second_url, headers=headers)
            if response.status_code == 200:
                datas = response.json()
                for data in datas:
                    id_account = data["id"]
                    name_account = data["name"]
                    periods = data["periods"]
                    currency = data["currency"]
                    if first_currency is None:
                        first_currency = currency  # Сохраняем первую валюту
                    for p in periods:
                        period = p["period"]
                        conversion = p["conversion"]
                        requisites = p["requisites"]
                        disputes = p["disputes"]
                        weight = data["weight"]
                        tags = data["tags"]
                        rows = {
                            "ID Каскада": id_cascada,
                            "Название Каскада": name_cascada,
                            "ID Аккаунта": id_account,
                            "Название Аккаунта": name_account,
                            "Валюта": currency,
                            "Период": period,
                            "Конверсия": conversion,
                            "Реквизиты": requisites,
                            "Споры": disputes,
                            "Вес": weight,
                            "Теги": tags,
                        }
                        tables.append(rows)

        if first_currency:
            filename = os.path.join(json_path, f"{first_currency}.json")
        else:
            filename = "json_data.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(tables, file, ensure_ascii=False, indent=4)
        print(f"Данные по валюте сохраннены {filename}")


# Фукция для подключения к sheet
def get_google():
    spreadsheet_id_admin = "1ot1RkXNsIGFbxuTVAwPNaX0i9OO0TBFZGaky2FqXnGY"
    spreadsheet_id_manager = "1LO7Po0a7qgplazvBSe6R6_4X7GGbWLleXvpebL5lWdE"
    current_directory = os.getcwd()
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_file = os.path.join(current_directory, "for-gt2-b96166ae6643.json")
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)

    return client, spreadsheet_id_admin, creds, spreadsheet_id_manager


# Чтение json для дальнейшего использваония
def read_json_file(item):
    with open(item, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Функция для трансформации данных для таблицы
def transform_data(data):
    # Словарь для агрегации данных по ID Каскада и ID Аккаунта
    transformed = {}
    for entry in data:
        key = (entry["ID Каскада"], entry["ID Аккаунта"])
        if key not in transformed:
            transformed[key] = {
                "ID Каскада": entry["ID Каскада"],
                "Название Каскада": entry["Название Каскада"],
                "ID Аккаунта": entry["ID Аккаунта"],
                "Название Аккаунта": entry["Название Аккаунта"],
                "Валюта": entry["Валюта"],
                "Вес": entry["Вес"],
                "Теги": entry["Теги"],
            }
        period = entry["Период"]

        transformed[key][f"{period} Конверсия"] = entry["Конверсия"]
        transformed[key][f"{period} Реквизиты"] = entry["Реквизиты"]
        transformed[key][f"{period} Споры"] = entry["Споры"]

    return list(transformed.values())


# Функция записи комментариев
def add_comments(sheet, row_index, text, creds):
    """Добавляет комментарий к ячейке в Google Sheets в колонке D."""
    service = build("sheets", "v4", credentials=creds)
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,  # ID листа
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 3,  # Колонка D
                    "endColumnIndex": 4,
                },
                "cell": {"note": text},  # Затем добавляем новый комментарий
                "fields": "note",
            }
        },
    ]
    body = {"requests": requests}
    # Используйте spreadsheetId таблицы, а не sheet.id
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet.spreadsheet.id,  # Исправлено на правильное свойство
        body=body,
    ).execute()


def clear_comments(sheet, row_index, text, creds):
    """Добавляет комментарий к ячейке в Google Sheets в колонке D."""
    service = build("sheets", "v4", credentials=creds)
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,  # ID листа
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 3,  # Колонка D
                    "endColumnIndex": 4,
                },
                "cell": {
                    "note": ""  # Сначала "очищаем" комментарий, устанавливая пустую строку
                },
                "fields": "note",
            }
        },
    ]
    body = {"requests": requests}
    # Используйте spreadsheetId таблицы, а не sheet.id
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet.spreadsheet.id,  # Исправлено на правильное свойство
        body=body,
    ).execute()


# Функция для загрузки данных
def write_to_sheet():
    client, spreadsheet_id_admin, creds, spreadsheet_id_manager = get_google()
    folder = os.path.join(json_path, "*.json")

    files_json = glob.glob(folder)
    for item in files_json:
        data = read_json_file(item)
        transformed_data = transform_data(data)
        name_sheet = os.path.splitext(os.path.basename(item))[0]
        admin_sheet_name = f"Adm{name_sheet}"
        manager_sheet_name = name_sheet

        # Открытие Admin таблицы
        spreadsheet = client.open_by_key(spreadsheet_id_admin)
        try:
            sheet = spreadsheet.worksheet(admin_sheet_name)
            print(f"Лист '{admin_sheet_name}' уже существует.")
        except gspread.exceptions.WorksheetNotFound:
            # Создайте лист, если он не существует
            sheet = spreadsheet.add_worksheet(
                title=admin_sheet_name, rows="1000", cols="30"
            )
            print(f"Лист '{admin_sheet_name}' создан.")

        # Копирование данных из Admin таблицы в Manager таблицу

        detailed_headers = [
            "ID Каскада",
            "Название Каскада",
            "ID Аккаунта",
            "Название Аккаунта",
            "Валюта",
            "today Конверсия",
            "today Реквизиты",
            "today Споры",
            "yesterday Конверсия",
            "yesterday Реквизиты",
            "yesterday Споры",
            "week Конверсия",
            "week Реквизиты",
            "week Споры",
            "Вес",
        ]
        # Проверяем, содержит ли первая строка заголовки периодов
        if not sheet.cell(1, 6).value:  # Проверяем ячейку в строке 1, колонке 6 (F1)
            sheet.append_row([""] * 15)  # Добавляем пустую строку для объединения ячеек
            sheet.merge_cells("F1:H1")
            sheet.merge_cells("I1:K1")
            sheet.merge_cells("L1:N1")
            sheet.update(
                values=[["today"]], range_name="F1", value_input_option="USER_ENTERED"
            )
            sheet.update(
                values=[["yesterday"]],
                range_name="I1",
                value_input_option="USER_ENTERED",
            )
            sheet.update(
                values=[["week"]], range_name="L1", value_input_option="USER_ENTERED"
            )

        # Проверяем, содержит ли вторая строка детальные заголовки
        if not sheet.cell(2, 1).value:  # Проверяем ячейку в строке 2, колонке 1 (A2)

            sheet.update(values=[detailed_headers], range_name="A2:O2")

        # Чтение и преобразование данных из JSON

        # Начало записи данных с третьей строки
        row_index = 3
        for item in transformed_data:
            row = [item.get(header, "") for header in detailed_headers]
            # Если строка уже существует, обновляем её, иначе добавляем
            if sheet.row_count >= row_index:
                range_to_update = f"A{row_index}:O{row_index}"
                sheet.update(values=[row], range_name=range_to_update)
            else:
                sheet.append_row(row)
            # Добавление комментариев, если есть теги
            if "Теги" in item and isinstance(item["Теги"], list):
                tags_text = "\n".join(
                    item["Теги"]
                )  # Объединяем все теги в одну строку, если они есть
                clear_comments(sheet, row_index, tags_text, creds)

                time.sleep(1)
                add_comments(sheet, row_index, tags_text, creds)
            elif "Теги" in item and item["Теги"] is None:
                clear_comments(sheet, row_index, tags_text, creds)

            row_index += 1
        format_sheet(sheet, creds)
        counts = count_values(sheet)
        format_rows(sheet, creds, counts)
        process_data(sheet)
        time.sleep(60)
        copy_data(
            client,
            spreadsheet_id_admin,
            spreadsheet_id_manager,
            admin_sheet_name,
            manager_sheet_name,
        )
        # # Находим первую свободную строку для добавления данных
        # first_empty_row = (
        #     len(sheet.get_all_values()) + 1
        # )  # Получаем количество всех заполненных строк и добавляем 1

        # # Записываем данные в лист, начиная с первой свободной строки
        # for item in transformed_data:
        #     row = [item.get(header, "") for header in detailed_headers]
        #     sheet.insert_row(row, first_empty_row)
        #     first_empty_row += 1  # Перемещаем указатель строки


# Форматирование строк
def format_sheet(sheet, creds):
    """
    Форматирует лист с помощью объединения ячеек, выравнивания текста и границ.

    Args:
      sheet: Объект листа Google Sheets.
    """
    border_style = {
        "style": "SOLID",
        "width": 1,
        "color": {"red": 0, "green": 0, "blue": 0},
    }

    # Установка границы для каждой ячейки в диапазоне
    requests = [
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 4,  # столбец E
                    "endColumnIndex": 5,  # столбец F
                },
                "right": border_style,  # Use 'right' for border style
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 7,  # столбец H
                    "endColumnIndex": 8,  # столбец I
                },
                "right": border_style,  # Use 'right' for border style
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 10,  # столбец K
                    "endColumnIndex": 11,  # столбец L
                },
                "right": border_style,  # Use 'right' for border style
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 13,  # столбец H
                    "endColumnIndex": 14,  # столбец I
                },
                "right": border_style,  # Use 'right' for border style
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 14,  # столбец H
                    "endColumnIndex": 15,  # столбец I
                },
                "right": border_style,  # Use 'right' for border style
            }
        },
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet.id,
                    "gridProperties": {
                        "frozenRowCount": 2  # Закрепление первых двух строк
                    },
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet.id,
                    "dimension": "COLUMNS",  # Автоматически изменять размеры столбцов
                    "startIndex": 0,  # Начиная с первого столбца
                    "endIndex": 15,  # До пятнадцатого столбца
                }
            }
        },
    ]

    # Отправляем запрос на обновление форматирования
    service = build("sheets", "v4", credentials=creds)
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet.spreadsheet.id, body={"requests": requests}
    ).execute()


# Получаем все значения из первой колонки
def count_values(sheet):
    return sheet.col_values(1)


# Заливка строк
def format_rows(sheet, creds, values_list):
    service = build("sheets", "v4", credentials=creds)
    color_index = 0  # Индекс для выбора цвета из списка

    # Начинаем с первой строки с данными, пропускаем первые две строки (индекс 2 в списке, т.к. он 0-индексированный)
    current_row = 3

    while current_row <= len(values_list):
        value = values_list[current_row - 1]
        start_row = current_row
        while current_row <= len(values_list) and values_list[current_row - 1] == value:
            current_row += 1
        count = current_row - start_row

        # Определение цветов
        colors = [
            {"red": 0.9, "green": 1.0, "blue": 0.9},  # Светло-зеленый
            {"red": 0.9, "green": 1.0, "blue": 1.0},  # Светло-бирюзовый
            {"red": 1.0, "green": 0.9, "blue": 0.9},  # Светло-розовый
            {"red": 1.0, "green": 1.0, "blue": 0.9},  # Светло-желтый
            {"red": 0.9, "green": 0.9, "blue": 1.0},  # Светло-голубой
            {"red": 1.0, "green": 0.9, "blue": 1.0},  # Светло-фиолетовый
            {"red": 0.9, "green": 1.0, "blue": 0.8},  # Светло-лимонный
        ]

        # Выбор цвета из списка
        background_color = colors[color_index % len(colors)]
        color_index += 1  # Переход к следующему цвету для следующей группы

        # Формирование и отправка запроса на форматирование
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet.id,
                        "startRowIndex": start_row - 1,
                        "endRowIndex": start_row + count - 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 15,  # До пятнадцатого столбца
                    },
                    "cell": {
                        "userEnteredFormat": {"backgroundColor": background_color}
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
        ]

        # Отправляем запрос
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet.spreadsheet.id, body={"requests": requests}
        ).execute()


# Из Комиссия % получаем Рейтинг
def process_data(sheet):
    detailed_headers = [
        "Комиссия %",
        "Комиссия fix",
        "Settle fee %",
        "Settle fee fix",
        "Курс вывода (зачисления)",
        "Рейтинг",
    ]
    # Проверяем ячейку в строке 2, колонке 16 (P2)
    if not sheet.cell(2, 16).value:

        sheet.update(values=[detailed_headers], range_name="P2:U2")
    # Получаем все значения из колонок A и P
    data_A = sheet.col_values(1)[2:]  # A3 до конца
    data_P = sheet.col_values(16)[2:]  # P3 до конца

    # Обрезаем списки до минимальной длины
    min_length = min(len(data_A), len(data_P))
    data_A = data_A[:min_length]
    data_P = data_P[:min_length]

    # Преобразуем данные из P в числа, заменяя запятые на точки
    def to_float(value):
        try:
            num = float(value.replace(",", "."))
            return num if num >= 0 else "error!!!"
        except ValueError:
            return "error"

    data_P = [to_float(x) if x else None for x in data_P]

    # Найдем уникальные значения в колонке A
    unique_values = sorted(set(data_A))

    for unique_value in unique_values:
        # Найдем индексы всех строк, которые содержат текущее уникальное значение
        indices = [i for i, x in enumerate(data_A) if x == unique_value]

        # Извлечем соответствующие значения из колонки P
        corresponding_values = [data_P[i] for i in indices]

        # Обработаем соответствующие значения
        non_null_values = [x for x in corresponding_values if isinstance(x, float)]
        if non_null_values:
            min_value = min(non_null_values)
        else:
            min_value = 0

        step = 0.5

        for i, value in zip(indices, corresponding_values):
            # Записываем результат в колонку U (21-я колонка)
            cell = f"U{3 + i}"
            if value is None:
                sheet.update_acell(cell, "")
            elif value == "error":
                sheet.update_acell(cell, "error")
            else:
                # Округляем значение и находим индекс для колонки U
                rounded_value = round(value * 2) / 2
                index_U = int((rounded_value - min_value) / step) + 1
                sheet.update_acell(cell, index_U)


def copy_data(
    client,
    admin_spreadsheet_id,
    manager_spreadsheet_id,
    admin_sheet_name,
    manager_sheet_name,
):
    # Открытие таблиц
    admin_spreadsheet = client.open_by_key(admin_spreadsheet_id)
    manager_spreadsheet = client.open_by_key(manager_spreadsheet_id)

    # Открытие листов
    admin_sheet = admin_spreadsheet.worksheet(admin_sheet_name)
    try:
        manager_sheet = manager_spreadsheet.worksheet(manager_sheet_name)
        print(f"Лист '{manager_sheet_name}' уже существует.")
    except gspread.exceptions.WorksheetNotFound:
        manager_sheet = manager_spreadsheet.add_worksheet(
            title=manager_sheet_name, rows="1000", cols="30"
        )
        print(f"Лист '{manager_sheet_name}' создан.")

    # Получение всех данных из Admin таблицы
    admin_data = admin_sheet.get_all_values()

    # Запись данных в Manager таблицу
    if admin_data:
        manager_sheet.update(admin_data, "A1")

    # Очистка колонки P
    p_column_range = f"P2:P{len(admin_data)}"
    manager_sheet.batch_clear([p_column_range])

    print(
        f"Данные успешно перенесены из '{admin_sheet_name}' в '{manager_sheet_name}' и колонка P очищена."
    )


def pars_json():
    filename = "json_data.json"
    with open(filename, "r", encoding="utf-8") as file:
        datas = json.load(file)
    tables = []
    for data in datas[:1]:
        id_account = data["id"]
        name_account = data["name"]
        periods = data["periods"]
        for p in periods:
            period = p["period"]
            conversion = p["conversion"]
            requisites = p["requisites"]
            disputes = p["disputes"]
            weight = data["weight"]
            tags = data["tags"][0]
            rows = {
                "id_account": id_account,
                "name_account": name_account,
                "period": period,
                "conversion": conversion,
                "requisites": requisites,
                "disputes": disputes,
                "weight": weight,
                "tags": tags,
            }
            tables.append(rows)
    print(tables)


if __name__ == "__main__":
    get_json_data()
    write_to_sheet()
    # pars_json()
