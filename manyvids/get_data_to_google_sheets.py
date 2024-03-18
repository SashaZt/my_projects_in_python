import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import csv
from config import db_config, use_table_daily_sales, headers, host, user, password, database, use_table_payout_history, \
    use_table_monthly_sales, use_table_chat, spreadsheet_id, time_a, time_b


def get_google_sheet_data():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    creds_file = os.path.join(os.getcwd(), 'access.json')  # Убедитесь, что файл access.json находится в текущей директории
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).worksheet('daily_sales')

    # Получаем все данные с заголовками
    data = sheet.get_all_records()  # Возвращает данные в виде списка словарей

    # Для определения номера следующей строки, используем get_all_values() чтобы получить весь лист
    all_values = sheet.get_all_values()
    # Номер следующей пустой строки равен количеству непустых строк + 1
    next_empty_row = len(all_values) + 1

    return next_empty_row



# def save_data_to_csv(data, file_name='data.csv'):
#     keys = data[0].keys() if data else []
#     with open(file_name, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=keys, delimiter=';')
#         writer.writeheader()
#         for row in data:
#             writer.writerow(row)

next_empty_row = get_google_sheet_data()
# Сохраняем данные в CSV
# save_data_to_csv(data, 'daily_sales_to_google.csv')
print(next_empty_row)

# Использование функции
