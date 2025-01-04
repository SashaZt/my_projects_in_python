import os
import warnings
from pathlib import Path

import gspread
import whisper
from configuration.logger_setup import logger
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

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
            "Текст звонка": "",
        }

    except IndexError:
        raise ValueError(f"Невозможно разобрать имя файла: {filename}")


def transcribe_audio_files():
    """
    Транскрибирует файлы .mp3 из директории call_recording_directory,
    создает .txt файлы с результатами транскрипции.
    """
    logger.info("Старт транскрибирования файлов")
    # Подключение к Google Sheets
    try:

        # Явное указание использования CPU
        logger.info("Загрузка модели Whisper...")
        model = whisper.load_model("base", device="cpu")
        logger.info("Модель Whisper успешно загружена")

        # Перебор всех файлов .mp3 в директории
        for file_path in call_recording_directory.glob("*.mp3"):
            logger.info(f"Проверка файла: {file_path}")
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                continue
            filename_mp3 = file_path.name
            all_data = parse_mp3_filename(filename_mp3)
            txt_file_path = file_path.with_suffix(
                ".txt"
            )  # Путь к .txt файлу с тем же именем

            # Пропускаем, если транскрипция уже выполнена
            if txt_file_path.exists():
                logger.info(f"Транскрипция уже существует: {txt_file_path}")
                continue

            logger.info(f"Транскрибирование файла: {file_path}")

            # Транскрибирование аудиофайла
            try:
                result = model.transcribe(str(file_path))
                # Запись результата в Google Sheets
                message_text = result["text"]
                result = {"text": message_text}
                # Добавляем текст транскрипции
                all_data["Текст звонка"] = result["text"]
                write_dict_to_google_sheets(all_data)
                # Запись текста в файл
                with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(result["text"])
                logger.info(f"Файл транскрибирован и сохранен как: {txt_file_path}")
            except Exception as transcribe_error:
                logger.error(
                    f"Ошибка при транскрибировании файла {file_path}: {transcribe_error}"
                )

    except Exception as e:
        logger.error(f"Общая ошибка при транскрибировании: {e}")


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
            logger.info(f"Добавлены заголовки: {existing_headers}")

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
    transcribe_audio_files()
