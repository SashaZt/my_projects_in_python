import requests
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


# Функция для получение данных с API
def get_json_data():

    # url = f"https://betatransfer.io/excel/cascades/{id_accounts}/accounts"
    url = "https://betatransfer.io/excel/cascades"
    token = "pLaZ2zGFtbKt8UOdw6EAfpIBWwbsGETd"
    headers = {"Authorization": f"Basic {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        datas = response.json()
        tables = []
        for data in datas:

            id_cascada = data["id"]

            name_cascada = data["name"]

            url = f"https://betatransfer.io/excel/cascades/{id_cascada}/accounts"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                datas = response.json()
                for data in datas:
                    id_account = data["id"]
                    name_account = data["name"]
                    periods = data["periods"]
                    currency = data["currency"]
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
        filename = "json_data.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(tables, file, ensure_ascii=False, indent=4)


# Фукция для подключения к sheet
def get_google():
    spreadsheet_id = "1D4YEMQVAUjwrkaUa70uHS8ZpEclxNvfzeT1m7Q6G11U"
    current_directory = os.getcwd()
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_file = os.path.join(current_directory, "access.json")
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).worksheet("Лист1")

    return sheet, creds


# Чтение json для дальнейшего использваония
def read_json_file():
    filename = "json_data.json"
    with open(filename, "r", encoding="utf-8") as file:
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
            }
        period = entry["Период"]
        transformed[key][f"{period} Конверсия"] = entry["Конверсия"]
        transformed[key][f"{period} Реквизиты"] = entry["Реквизиты"]
        transformed[key][f"{period} Споры"] = entry["Споры"]

    return list(transformed.values())


# def write_to_sheet():
#     sheet, creds = get_google()
#     sheet.clear()  # Очистка листа

#     # Первая строка и форматирование
#     sheet.append_row([""] * 15)  # Добавляем пустую строку для объединения ячеек
#     sheet.merge_cells("F1:H1")
#     sheet.merge_cells("I1:K1")
#     sheet.merge_cells("L1:N1")
#     sheet.update(values=[["today"]], range_name="F1", value_input_option="USER_ENTERED")
#     sheet.update(
#         values=[["yesterday"]], range_name="I1", value_input_option="USER_ENTERED"
#     )
#     sheet.update(values=[["week"]], range_name="L1", value_input_option="USER_ENTERED")
#     sheet.format(
#         "A1:N100", {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}
#     )

#     # Вторая строка: Детальные заголовки
#     detailed_headers = [
#         "ID Каскада",
#         "Название Каскада",
#         "ID Аккаунта",
#         "Название Аккаунта",
#         "Валюта",
#         "today Конверсия",
#         "today Реквизиты",
#         "today Споры",
#         "yesterday Конверсия",
#         "yesterday Реквизиты",
#         "yesterday Споры",
#         "week Конверсия",
#         "week Реквизиты",
#         "week Споры",
#         "Вес",
#     ]
#     sheet.update(values=[detailed_headers], range_name="A2:O2")

#     # Читаем и преобразуем данные из JSON-файла
#     data = read_json_file()
#     transformed_data = transform_data(data)

#     # Записываем данные в лист
#     for item in transformed_data:
#         row = [item.get(header, "") for header in detailed_headers]
#         sheet.append_row(row)
#     detailed_headers = [
#         "ID Каскада",
#         "Название Каскада",
#         "ID Аккаунта",
#         "Название Аккаунта",
#         "Валюта",
#         "Конверсия",
#         "Реквизиты",
#         "Споры",
#         "Конверсия",
#         "Реквизиты",
#         "Споры",
#         "Конверсия",
#         "Реквизиты",
#         "Споры",
#         "Вес",
#     ]
#     sheet.update(values=[detailed_headers], range_name="A2:O2")
# format_sheet(sheet, creds)


# Функция для загрузки данных
def write_to_sheet():
    sheet, creds = get_google()
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
            values=[["yesterday"]], range_name="I1", value_input_option="USER_ENTERED"
        )
        sheet.update(
            values=[["week"]], range_name="L1", value_input_option="USER_ENTERED"
        )

    # Проверяем, содержит ли вторая строка детальные заголовки
    if not sheet.cell(2, 1).value:  # Проверяем ячейку в строке 2, колонке 1 (A2)

        sheet.update(values=[detailed_headers], range_name="A2:O2")

    # Чтение и преобразование данных из JSON
    data = read_json_file()
    transformed_data = transform_data(data)

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
        row_index += 1

    # # Находим первую свободную строку для добавления данных
    # first_empty_row = (
    #     len(sheet.get_all_values()) + 1
    # )  # Получаем количество всех заполненных строк и добавляем 1

    # # Записываем данные в лист, начиная с первой свободной строки
    # for item in transformed_data:
    #     row = [item.get(header, "") for header in detailed_headers]
    #     sheet.insert_row(row, first_empty_row)
    #     first_empty_row += 1  # Перемещаем указатель строки
    format_sheet(sheet, creds)
    counts = count_values(sheet)
    format_rows(sheet, creds, counts)


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
    # get_json_data()
    write_to_sheet()
    # pars_json()
