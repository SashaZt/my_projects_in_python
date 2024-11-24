import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка доступа и авторизация
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# Укажи путь к файлу с учетными данными для Google API
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Откроем таблицу по названию
spreadsheet = client.open_by_key(SPREADSHEET)
sheet = spreadsheet.worksheet(SHEET)  # Вставь название нужного листа

# Данные для загрузки
data = [
    {
        "domain": "allincstudio.com",
        "backlinks_value": 37,
        "refdomains_value": 37,
        "domainRating_value": 1.4,
        "organic_traffic_value": 0,
        "organic_keywords_value": 0,
        "urlRating_value": 6.0,
        "country_00": None,
        "country_01": None,
        "country_02": None,
        "history_1_date": "2024-06-01",
        "history_1_traffic": 0,
        "history_2_date": "2024-07-01",
        "history_2_traffic": 0,
        "history_3_date": "2024-08-01",
        "history_3_traffic": 0,
        "history_4_date": "2024-09-01",
        "history_4_traffic": 0,
        "history_5_date": "2024-10-01",
        "history_5_traffic": 0,
        "history_6_date": "2024-11-01",
        "history_6_traffic": 0,
    },
    {
        "domain": "allindiaroundup.com",
        "backlinks_value": 8309,
        "refdomains_value": 1315,
        "domainRating_value": 39.0,
        "organic_traffic_value": 177,
        "organic_keywords_value": 137,
        "urlRating_value": 15.0,
        "country_00": "India    98%",
        "country_01": "Nepal    1%",
        "country_02": None,
        "history_1_date": "2024-06-01",
        "history_1_traffic": 418,
        "history_2_date": "2024-07-01",
        "history_2_traffic": 91,
        "history_3_date": "2024-08-01",
        "history_3_traffic": 118,
        "history_4_date": "2024-09-01",
        "history_4_traffic": 180,
        "history_5_date": "2024-10-01",
        "history_5_traffic": 250,
        "history_6_date": "2024-11-01",
        "history_6_traffic": 199,
    },
]


# Найти строку с указанным доменом
def find_row_by_domain(sheet, domain):
    cell = sheet.find(domain)
    if cell:
        return cell.row
    return None


# Добавим дополнительные колонки, если они отсутствуют
def ensure_column_limit(sheet, required_columns):
    current_columns = len(
        sheet.row_values(1)
    )  # Получаем количество существующих колонок по первой строке
    if current_columns < required_columns:
        additional_columns = required_columns - current_columns
        sheet.add_cols(additional_columns)


# Убедимся, что таблица имеет достаточное количество колонок перед обновлением данных
ensure_column_limit(sheet, 28)  # Нам нужно минимум 28 колонок


# Функция для записи данных в определенные столбцы
def update_sheet_with_data(sheet, data):
    for entry in data:
        domain = entry["domain"]
        row = find_row_by_domain(sheet, domain)

        if row:
            # Укажи соответствие между ключами и индексами колонок (начиная с 1, где A=1, B=2, ...)
            column_mapping = {
                "backlinks_value": 8,  # H
                "refdomains_value": 9,  # I
                "domainRating_value": 10,  # J
                "organic_traffic_value": 11,  # K
                "organic_keywords_value": 12,  # L
                "urlRating_value": 13,  # M
                "country_00": 14,  # N
                "country_01": 15,  # O
                "country_02": 16,  # P
                "history_1_date": 17,  # Q
                "history_1_traffic": 18,  # R
                "history_2_date": 19,  # S
                "history_2_traffic": 20,  # T
                "history_3_date": 21,  # U
                "history_3_traffic": 22,  # V
                "history_4_date": 23,  # W
                "history_4_traffic": 24,  # X
                "history_5_date": 25,  # Y
                "history_5_traffic": 26,  # Z
                "history_6_date": 27,  # AA
                "history_6_traffic": 28,  # AB
            }

            for key, column_index in column_mapping.items():
                if (
                    key in entry and entry[key] is not None
                ):  # Проверяем, что значение не None
                    cell_address = (row, column_index)
                    sheet.update_cell(*cell_address, entry[key])


# Запись данных в таблицу
update_sheet_with_data(sheet, data)
