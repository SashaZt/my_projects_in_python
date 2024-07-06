from oauth2client.service_account import ServiceAccountCredentials
import os
import gspread
from config import (
    spreadsheet_id,
)

current_directory = os.getcwd()


def get_google():
    """
    Функция для подключения к Google sheets
    """
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
