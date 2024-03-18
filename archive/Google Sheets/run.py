import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np

# Укажите путь к файлу с учетными данными JSON и идентификатор таблицы
CREDENTIALS_FILE = 'C:\\scrap_tutorial-master\\manyvids\\access.json'
spreadsheet_id = '145mee2ZsApZXiTnASng4lTzbocYCJWM5EDksTx_FVYY'


# Создаем функцию для обновления данных в конкретном листе
def update_sheet_from_csv(credentials_file, spreadsheet_id, sheet_name, csv_file):
    # Устанавливаем scope и создаем объекты для авторизации
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(credentials)

    # Открываем таблицу по идентификатору
    try:
        sheet = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Таблица с идентификатором '{spreadsheet_id}' не найдена.")
        return

    # Читаем данные из CSV-файла с помощью pandas
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Файл '{csv_file}' не найден.")
        return
    except ValueError as e:
        print(f"Ошибка при чтении файла '{csv_file}': {e}")
        return

    # Получаем объект листа по его названию
    try:
        worksheet = sheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Лист с названием '{sheet_name}' не найден.")
        return

    # Обновляем данные в указанном листе
    worksheet.clear()  # Очищаем лист перед обновлением
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    cell_list = worksheet.range('A1:' + gspread.utils.rowcol_to_a1(df.shape[0], df.shape[1]))
    cell_values = [df.columns.tolist()] + df.values.tolist()

    for cell, value in zip(cell_list, cell_values):
        cell.value = value

    df.fillna('', inplace=True)
    worksheet.update([df.columns.tolist()] + df.values.tolist())

    print(f"Данные успешно обновлены в листе '{sheet_name}'!")


# Укажите путь к CSV-файлам и соответствующим названиям листов
csv_file_synevo = 'C:\scrap_tutorial-master\synevo\synevo.csv'
csv_file_esculab = 'C:\scrap_tutorial-master\synevo\esculab.csv'
csv_file_onelab = 'C:\scrap_tutorial-master\synevo\onelab.csv'

# Обновляем данные в каждом листе
update_sheet_from_csv(CREDENTIALS_FILE, spreadsheet_id, "synevo", csv_file_synevo)
update_sheet_from_csv(CREDENTIALS_FILE, spreadsheet_id, "esculab", csv_file_esculab)
update_sheet_from_csv(CREDENTIALS_FILE, spreadsheet_id, "onelab", csv_file_onelab)
