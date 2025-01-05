import os
import warnings
from pathlib import Path

import gspread
import whisper
from configuration.logger_setup import logger
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth, ServiceAccountCredentials
from pydrive2.drive import GoogleDrive

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
call_recording_directory = current_directory / "call_recording"
call_recording_directory.mkdir(parents=True, exist_ok=True)
service_account_file = configuration_directory / "service_account.json"
# Подавляем FutureWarning и UserWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

sheet_id = os.getenv("sheet_id")
folder_id = os.getenv("FOLDER_ID")


# Создание объекта Google Drive
def create_drive_instance():
    """
    Создаёт экземпляр Google Drive для взаимодействия с файлами.
    :return: Объект GoogleDrive
    """
    try:
        gauth = GoogleAuth()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        drive = GoogleDrive(gauth)
        return drive
    except Exception as e:
        logger.error(f"Ошибка при создании экземпляра Google Drive: {e}")
        raise e


# Подключение к Google Sheets
def connect_to_google_sheets(sheet_id):
    """
    Устанавливает соединение с Google Sheets по ID таблицы.

    :param sheet_id: ID таблицы Google Sheets
    :return: Объект листа (worksheet)
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        service_account_file, scope
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(sheet_id).sheet1  # Открывает первый лист таблицы
    return sheet


def parse_mp3_filename(filename):
    """
    Разбирает имя файла .mp3 и извлекает дату, номер телефона, линию и менеджера.

    :param filename: Имя файла .mp3 (например, "2024-11-30_15-03-53_380954532414_103_Петро_Ким.mp3")
    :return: Словарь с разобранными данными
    """
    try:
        # Удаляем расширение .mp3
        name_without_extension = filename.rsplit(".", 1)[0]

        # Разделяем имя файла по символу "_"
        parts = name_without_extension.split("_")

        # Извлекаем данные
        date_mp3 = f"{parts[0]}_{parts[1]}"  # Дата и время
        phone_mp3 = parts[2]  # Номер телефона
        line_mp3 = parts[3]  # Линия
        manager_mp3 = " ".join(parts[4:])  # Имя менеджера (могут быть пробелы)

        # Возвращаем данные в виде словаря
        return {
            "Дата": date_mp3,
            "Телефон": phone_mp3,
            "Линия": line_mp3,
            "Имя менеджера": manager_mp3,
            # "Текст звонка Рус": "",
            "Текст звонка Укр": "",
        }

    except IndexError:
        raise ValueError(f"Невозможно разобрать имя файла: {filename}")


def get_mp3_files_from_google_drive(folder_id, drive):
    """
    Получает список MP3 файлов из указанной папки на Google Drive.

    :param folder_id: ID папки на Google Drive
    :param drive: Объект GoogleDrive
    :return: Список словарей с информацией о файлах (имя и ссылка на загрузку)
    """
    try:
        query = f"'{folder_id}' in parents and mimeType='audio/mpeg' and trashed=false"
        file_list = drive.ListFile({"q": query}).GetList()

        mp3_files = []
        for file in file_list:
            mp3_files.append(
                {
                    "name": file["title"],
                    "id": file["id"],
                    "link": file["webContentLink"],
                }
            )

        return mp3_files

    except Exception as e:
        logger.error(f"Ошибка при получении файлов из Google Drive: {e}")
        return []


def process_google_drive_mp3_files():
    """
    Получает MP3 файлы из Google Drive, транскрибирует их и записывает результаты в Google Sheets.

    :param folder_id: ID папки на Google Drive
    """
    try:
        # Создаём объект Google Drive
        drive = create_drive_instance()

        # Получаем список MP3 файлов
        mp3_files = get_mp3_files_from_google_drive(folder_id, drive)
        logger.info(f"Найдено {len(mp3_files)} MP3 файлов в Google Drive")

        # Загрузка модели Whisper
        model = whisper.load_model("base", device="cpu")

        for file_info in mp3_files:
            try:
                file_name = file_info["name"]
                file_id = file_info["id"]
                file_link = file_info["link"]

                # Скачиваем файл локально
                local_file_path = call_recording_directory / file_name
                logger.info(f"Скачивание файла: {file_name}")
                file = drive.CreateFile({"id": file_id})
                file.GetContentFile(str(local_file_path))
                logger.info(f"Файл {file_name} скачан локально")

                # Транскрибируем файл
                result = model.transcribe(str(local_file_path))
                result_text = result["text"]

                # Формируем данные для записи
                all_data = parse_mp3_filename(file_name)
                all_data["Текст звонка Укр"] = result_text
                all_data["Ссылка на MP3"] = file_link  # Добавляем ссылку на MP3

                # Записываем данные в Google Sheets
                write_dict_to_google_sheets(all_data)

                # Удаляем локальный файл после обработки
                os.remove(local_file_path)

            except Exception as e:
                logger.error(f"Ошибка при обработке файла {file_name}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке Google Drive: {e}")


def write_dict_to_google_sheets(data_dict):
    """
    Записывает словарь в Google Sheets, где ключи словаря — это заголовки столбцов.

    :param sheet_id: ID таблицы Google Sheets
    :param data_dict: Словарь данных для записи (ключи — заголовки, значения — данные)
    """
    try:
        # Подключение к Google Sheets
        sheet = connect_to_google_sheets(sheet_id)
        logger.info(f"Подключение к Google Sheets выполнено: {sheet_id}")

        # Получаем заголовки из первого ряда таблицы
        existing_headers = sheet.row_values(1)

        # Если таблица пуста, добавляем заголовки
        if not existing_headers:
            existing_headers = list(data_dict.keys())
            sheet.append_row(existing_headers)
            # logger.info(f"Добавлены заголовки: {existing_headers}")

        # Убедимся, что ключи словаря совпадают с заголовками таблицы
        row = [data_dict.get(header, "") for header in existing_headers]

        # Проверяем, какая строка следующая свободная
        all_rows = sheet.get_all_values()  # Получаем все строки таблицы
        next_free_row = len(all_rows) + 1  # Следующая свободная строка

        # Записываем данные в следующую свободную строку
        sheet.insert_row(row, next_free_row)
        logger.info(f"Добавлены данные: {row} в строку {next_free_row}")

    except Exception as e:
        logger.error(f"Ошибка при записи в Google Sheets: {e}")


if __name__ == "__main__":
    process_google_drive_mp3_files()
