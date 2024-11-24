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
spreadsheet = client.open("TestAhrefs_com")  # Вставь название своей таблицы
sheet = spreadsheet.worksheet("sites")  # Вставь название нужного листа

# Данные для загрузки
data = [
    {
        "domain": "allinsider.net",
        "backlinks_value": 35893,
        "refdomains_value": 3111,
        "domainRating_value": 39.0,
        "organic_traffic_value": 340,
        "organic_keywords_value": 8796,
        "urlRating_value": 19.0,
        "country_00": "United States    70%",
        "country_01": "India    18%",
        "country_02": "Philippines    11%",
        "history_1_date": "2024-06-01",
        "history_1_traffic": 8764,
        "history_2_date": "2024-07-01",
        "history_2_traffic": 5448,
        "history_3_date": "2024-08-01",
        "history_3_traffic": 4379,
        "history_4_date": "2024-09-01",
        "history_4_traffic": 1324,
        "history_5_date": "2024-10-01",
        "history_5_traffic": 462,
        "history_6_date": "2024-11-01",
        "history_6_traffic": 247,
    }
]


# Найти строку с указанным доменом
def find_row_by_domain(sheet, domain):
    cell = sheet.find(domain)
    if cell:
        return cell.row
    return None


# Функция для записи данных в определенные столбцы
def update_sheet_with_data(sheet, data):
    for entry in data:
        domain = entry["domain"]
        row = find_row_by_domain(sheet, domain)

        if row:
            # Укажи соответствие между ключами и колонками
            column_mapping = {
                "backlinks_value": "H",
                "refdomains_value": "I",
                "domainRating_value": "J",
                "organic_traffic_value": "K",
                "organic_keywords_value": "L",
                "urlRating_value": "M",
                "country_00": "N",
                "country_01": "O",
                "country_02": "P",
                "history_1_date": "Q",
                "history_1_traffic": "R",
                # ДОПИШИ СЮДА ДАЛЬШЕ КАКИЕ НУЖНЫ КОЛОНКИ
            }

            for key, column in column_mapping.items():
                if key in entry:
                    sheet.update(range_name=f"{column}{row}", values=[[entry[key]]])


# Запись данных в таблицу
update_sheet_with_data(sheet, data)
