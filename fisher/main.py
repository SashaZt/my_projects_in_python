import requests
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread


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


def get_google():
    spreadsheet_id = "1D4YEMQVAUjwrkaUa70uHS8ZpEclxNvfzeT1m7Q6G11U"
    current_directory = os.getcwd()
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_file = os.path.join(current_directory, "access.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client, spreadsheet_id


def read_json_file():
    filename = "json_data.json"
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


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


def write_to_sheet():
    client, spreadsheet_id = get_google()
    sheet = client.open_by_key(spreadsheet_id).worksheet("Лист1")
    sheet.clear()  # Очистка листа

    # Первая строка и форматирование
    sheet.append_row([""] * 15)  # Добавляем пустую строку для объединения ячеек
    sheet.merge_cells("F1:H1")
    sheet.merge_cells("I1:K1")
    sheet.merge_cells("L1:N1")
    sheet.update(values=[["today"]], range_name="F1", value_input_option="USER_ENTERED")
    sheet.update(
        values=[["yesterday"]], range_name="I1", value_input_option="USER_ENTERED"
    )
    sheet.update(values=[["week"]], range_name="L1", value_input_option="USER_ENTERED")
    sheet.format(
        "A1:N100", {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}
    )

    # Вторая строка: Детальные заголовки
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
    sheet.update(values=[detailed_headers], range_name="A2:O2")

    # Читаем и преобразуем данные из JSON-файла
    data = read_json_file()
    transformed_data = transform_data(data)

    # Записываем данные в лист
    for item in transformed_data:
        row = [item.get(header, "") for header in detailed_headers]
        sheet.append_row(row)
    detailed_headers = [
        "ID Каскада",
        "Название Каскада",
        "ID Аккаунта",
        "Название Аккаунта",
        "Валюта",
        "Конверсия",
        "Реквизиты",
        "Споры",
        "Конверсия",
        "Реквизиты",
        "Споры",
        "Конверсия",
        "Реквизиты",
        "Споры",
        "Вес",
    ]
    sheet.update(values=[detailed_headers], range_name="A2:O2")


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
