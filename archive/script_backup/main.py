from __future__ import print_function
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import os
from dotenv import load_dotenv
import subprocess
import shutil
import glob

# Авторизация и создание сервиса Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SERVICE_ACCOUNT_FILE = "credentials.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)


service = build("drive", "v3", credentials=credentials)


def create_date_named_archive():
    load_dotenv()
    backup_path = os.getenv("BACKUP_PATH")
    source_folder = "/root/storage"

    # Определение имени архива без расширения
    backup_archive_storage = os.path.join(
        backup_path, datetime.now().strftime("%d.%m.%Y")
    )

    # Создание архива без сжатия
    shutil.make_archive(
        base_name=backup_archive_storage,
        format="zip",
        root_dir=source_folder,
        base_dir=".",
    )


# Функция для создания директории
def create_folder():
    parent_folder_id = "16ffhIuTnfxb1j3YdXlDCsSbDz20HwO33"
    # Получение сегодняшней даты в формате ДД.ММ.ГГГГ
    today_date = datetime.now().strftime("%d.%m.%Y")
    file_metadata = {
        "name": today_date,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    try:
        folder = service.files().create(body=file_metadata, fields="id").execute()
        print(f'Folder ID: {folder.get("id")}')
        return folder.get("id")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Функция для загрузки файла
def upload_file(folder_id):
    # Загрузка переменных окружения из файла .env
    load_dotenv()
    backup_path = os.getenv("BACKUP_PATH")

    # Определение имени файла с текущей датой (без расширения)
    date_str = datetime.now().strftime("%d.%m.%Y")
    search_pattern = os.path.join(backup_path, f"{date_str}.*")

    # Поиск всех файлов с текущей датой в имени
    files_to_upload = glob.glob(search_pattern)

    if not files_to_upload:
        print(f"No files found with the pattern {search_pattern}.")
        return

    for file_path in files_to_upload:
        if not os.path.exists(file_path):
            print(f"Error: The file {file_path} does not exist.")
            continue
        print(file_path)
        file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        try:
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File ID: {file.get("id")} for {file_path}')
        except Exception as e:
            print(f"An error occurred while uploading {file_path}: {e}")


def backup_postgres():
    # Загрузка переменных окружения из файла .env
    load_dotenv()

    # Получение значений переменных из окружения
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    backup_path = os.getenv("BACKUP_PATH")

    # Создание имени файла резервной копии с датой и временем
    backup_file = os.path.join(
        backup_path, f"{datetime.now().strftime('%d.%m.%Y')}.dump"
    )

    # Выполнение команды pg_dump
    try:
        # Установка переменной окружения для пароля
        os.environ["PGPASSWORD"] = db_password

        # Создание команды для выполнения pg_dump
        command = [
            "pg_dump",
            "-U",
            db_user,
            "-h",
            db_host,
            "-p",
            db_port,
            "-d",
            db_name,
            "-F",
            "c",  # Формат custom
            "-b",  # Включить большие объекты
            "-v",  # Подробный режим
            "-f",
            backup_file,
        ]

        # Выполнение команды
        result = subprocess.run(command, check=True)
        if result.returncode == 0:
            print(f"Резервная копия базы данных успешно создана: {backup_file}")
        else:
            print(f"Ошибка при создании резервной копии базы данных.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Удаление переменной окружения PGPASSWORD
        del os.environ["PGPASSWORD"]


if __name__ == "__main__":
    backup_postgres()
    # Создание директории с сегодняшней датой
    dated_folder_id = create_folder()
    create_date_named_archive()

    # Загрузка файла в созданную директорию
    if dated_folder_id:
        upload_file(dated_folder_id)
