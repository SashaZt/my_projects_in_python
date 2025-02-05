import json
import os
import shutil
import time
import unicodedata
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import List  # Добавляем импорт
import os
import asyncio
from openai import AsyncOpenAI
from configuration.logger_setup import logger
from dotenv import load_dotenv
import gspread
import httplib2
import lameenc
import requests
from configuration.logger_setup import logger
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth, ServiceAccountCredentials
from pydrive2.drive import GoogleDrive

# Загрузка переменных из .env
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
IP = os.getenv("IP")
FOLDER_ID = os.getenv("FOLDER_ID")
SHEET_ID = os.getenv("SHEET_ID")
API_KEY = os.getenv("API_KEY")
GRAPHQL_URL = os.getenv("GRAPHQL_URL")
SALESDRIVE_API = os.getenv("SALESDRIVE_API")
client_gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Заголовки для запроса
headers_api = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
call_recording_directory = current_directory / "call_recording"
data_directory.mkdir(parents=True, exist_ok=True)
call_recording_directory.mkdir(parents=True, exist_ok=True)
temp_data_output_file = data_directory / "temp_data.json"
recordings_output_file = data_directory / "recording.json"
result_output_file = data_directory / "result.json"
invalid_json = data_directory / "invalid.json"
PROCESSED_FILES_CACHE = data_directory / "processed_files.json"
service_account_file = configuration_directory / "service_account.json"

# Принудительно включаем TLS 1.2
httplib2.Http(ca_certs=None, disable_ssl_certificate_validation=False)


def download_data_to_file():
    """Скачивает все данные и сохраняет их в result.json"""
    if call_recording_directory:
        shutil.rmtree(call_recording_directory)
    url = f"https://{IP}/get_all_data"
    try:
        # logger.info("Sending GET request to the server")
        response = requests.get(url, timeout=30, verify=False)

        if response.status_code == 200:
            # logger.info("Data fetched successfully")
            data = response.json().get("data", [])
            # logger.info("Данные с сервера получены")
            return data
            # Сохраняем данные в файл result.json
        else:
            logger.warning(f"Failed to fetch data, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the GET request: {e}")


def load_data_from_file(file_name):
    """Загружает данные из файла result.json для фильтрации"""
    if temp_data_output_file.exists() or file_name.exists():
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # logger.info("Data loaded from result.json")
                return data
            except json.JSONDecodeError:
                logger.error("Error decoding JSON from result.json")
                return []
    else:
        logger.error("result.json file not found")
        return []


def write_recordings_to_json(data_output_file, data):
    # Сохраняем данные в файл result.json
    with open(data_output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def comparison_tables(mp3_files_drive, mp3_files_sql):
    """
    Сравнивает два списка и возвращает файлы, которых нет в Google Drive.

    :param mp3_files_drive: Список файлов, уже загруженных в Google Drive.
    :param mp3_files_sql: Список всех файлов, которые должны быть.
    :return: Список файлов из mp3_files_sql, которых нет в mp3_files_drive.
    """
    # Извлекаем имена файлов без расширения из mp3_files_drive
    drive_file_names = {file["name"].rsplit(".", 1)[0] for file in mp3_files_drive}

    # Сравниваем списки и находим записи из mp3_files_sql, которых нет в mp3_files_drive
    missing_files = [
        sql_entry
        for sql_entry in mp3_files_sql
        if list(sql_entry.keys())[0] not in drive_file_names
    ]

    return missing_files


def fetch_all_data():
    """Загружает данные из файла result.json и применяет фильтры, выводя результат в интерфейсе"""
    # data = load_data_from_file()
    # Создаём объект Google Drive
    # logger.info("Пауза в 10 сек перед запуском")
    time.sleep(10)
    drive = create_drive_instance()
    all_recordings = []
    calls = download_data_to_file()
    # Удалем из БД файлы которые не нужны
    if invalid_json.exists():
        # logger.info(f"Файл есть {invalid_json}")
        json_invalid = load_data_from_file(invalid_json)
        deleting_data_in_database(json_invalid)
    for call in calls:
        # Пропускаем записи с talk_time = 0 или null
        talk_time = call.get("talk_time")
        if talk_time in [0, None]:  # Проверяем, если значение 0 или None
            continue
        call_recording = call.get("call_recording")  # Получение записи
        call_date = call.get("call_date")  # Получение даты
        caller_number = call.get("caller_number")  # Получение номера
        employee_ext_number = call.get(
            "employee_ext_number"
        )  # Получение внутреннего номера
        employee = call.get("employee").replace(" ", "_")  # Получение сотрудника

        if call_recording and call_date:  # Проверка на наличие данных
            call_date_format = datetime.strptime(
                call_date, "%Y-%m-%d %H:%M:%S"
            ).strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"{call_date_format}_{caller_number}_{
                    employee_ext_number}_{employee}"
            # Формирование результата
            data_result = {file_name: call_recording}
            all_recordings.append(data_result)  # Добавление в список

    while True:
        # Получаем список MP3 файлов
        mp3_files_drive = get_mp3_files_from_google_drive(drive)

        if mp3_files_drive:
            # Если список не пустой, выполняем сравнение и запись
            missing_files = comparison_tables(mp3_files_drive, all_recordings)
            task_download_and_convert_to_mp3(missing_files)
            # write_recordings_to_json(recordings_output_file, missing_files)
            break  # Выход из цикла, если обработка завершена
        else:
            # Если список пустой, ждем 30 секунд
            time.sleep(30)


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


def get_mp3_files_from_google_drive(drive):
    """
    Получает список MP3 файлов из указанной папки на Google Drive.
    :param drive: Объект GoogleDrive
    :return: Список словарей с информацией о файлах (имя и ссылка на загрузку)
    """
    query = f"'{
        FOLDER_ID}' in parents and mimeType='audio/mpeg' and trashed=false"
    try:
        for attempt in range(3):  # 3 попытки
            try:
                # logger.info(f"Попытка {attempt + 1} выполнения запроса к Google Drive")
                file_list = drive.ListFile({"q": query}).GetList()
                # logger.info("Успешное выполнение запроса к Google Drive")
                return [
                    {
                        "name": file["title"],
                        "id": file["id"],
                        "link": file["webContentLink"],
                    }
                    for file in file_list
                ]
            except Exception as e:
                logger.warning(f"Ошибка при запросе: {e}")
                if attempt < 2:
                    time.sleep(5)  # Задержка перед повторной попыткой
                else:
                    raise e
    except Exception as e:
        logger.error(f"Ошибка при обработке Google Drive: {e}")
        return []


def task_download_and_convert_to_mp3(datas):
    # # Здесь можно разместить вашу функцию download_and_convert_to_mp3
    # with open(recordings_output_file, "r", encoding="utf-8") as f:
    #     datas = json.load(f)
    # Итерация по данным

    if not call_recording_directory.exists():
        call_recording_directory.mkdir(parents=True, exist_ok=True)
    for data in datas:
        for file_name, call_recording_url in data.items():
            try:
                # Скачиваем файл
                response = requests.get(call_recording_url, timeout=30, stream=True)
                wav_file_path = call_recording_directory / f"{file_name}.wav"
                mp3_file_path = call_recording_directory / f"{file_name}.mp3"

                # Пропускаем файл, если он уже существует
                if wav_file_path.exists():
                    logger.info(f"Файл в наличии {wav_file_path}\n")
                    continue
                if mp3_file_path.exists():
                    logger.info(f"Файл в наличии {mp3_file_path}\n")
                    continue

                if response.status_code == 200:
                    with open(wav_file_path, "wb") as f:
                        f.write(response.content)
                    # Конвертация .wav в .mp3 через lameenc
                    with wave.open(str(wav_file_path), "rb") as wav_file:
                        params = wav_file.getparams()
                        num_channels = params.nchannels
                        sample_rate = params.framerate
                        pcm_data = wav_file.readframes(params.nframes)

                        encoder = lameenc.Encoder()
                        encoder.set_bit_rate(128)
                        encoder.set_in_sample_rate(sample_rate)
                        encoder.set_channels(num_channels)
                        mp3_data = encoder.encode(pcm_data)
                        mp3_data += encoder.flush()

                    # Сохранение MP3 файла
                    with open(mp3_file_path, "wb") as mp3_file:
                        mp3_file.write(mp3_data)

                    # Удаление оригинального WAV файла
                    os.remove(wav_file_path)
                else:
                    logger.error(
                        f"Failed to download: {call_recording_url} (status code: {response.status_code})"
                    )

            except Exception as e:
                logger.error(f"An error occurred: {e}\n")

    # Удаление временного файла JSON (при необходимости)
    task_upload_to_google_drive()


def task_upload_to_google_drive():
    """
    Загрузка всех файлов из директории call_recording_directory в указанную папку Google Drive.
    """
    try:
        # Аутентификация с использованием сервисного аккаунта
        drive = create_drive_instance()

        # Получение списка файлов в целевой папке на Google Drive
        existing_files = {
            file["title"]: file["id"]
            for file in drive.ListFile(
                {"q": f"'{FOLDER_ID}' in parents and trashed=false"}
            ).GetList()
        }

        # Перебор всех файлов в директории
        for file_path in call_recording_directory.iterdir():
            if file_path.is_file():  # Проверяем, что это файл
                file_name = file_path.name

                if file_name in existing_files:
                    logger.info(f"Файл {file_name} уже существует на Google Drive\n")
                    continue  # Пропускаем загрузку

                # Создание и загрузка нового файла
                file_drive = drive.CreateFile(
                    {"title": file_name, "parents": [{"id": FOLDER_ID}]}
                )
                file_drive.SetContentFile(str(file_path))
                file_drive.Upload()
                logger.info(f"Файл {file_name} загружен на Google Drive\n")

    except Exception as e:
        logger.error(f"An error occurred: {e}\n")


def load_processed_files():
    """
    Загружает список обработанных файлов из локального кэша.
    Если кэш отсутствует, возвращает пустой список.
    """
    if Path(PROCESSED_FILES_CACHE).exists():
        with open(PROCESSED_FILES_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_processed_files(processed_files):
    """
    Сохраняет обновлённый список обработанных файлов в локальный кэш.
    """
    with open(PROCESSED_FILES_CACHE, "w", encoding="utf-8") as f:
        json.dump(processed_files, f, ensure_ascii=False, indent=4)


def get_new_files_from_drive(mp3_files, processed_files):
    """
    Находит файлы из Google Drive, которых нет в локальном кэше.
    :param mp3_files: Список файлов из Google Drive.
    :param processed_files: Список обработанных файлов из локального кэша.
    :return: Список новых файлов для обработки.
    """
    processed_file_names = {entry["file_name"] for entry in processed_files}
    return [file for file in mp3_files if file["name"] not in processed_file_names]


def clean_text(text):
    # Заменяем \n на пробел
    text = text.replace("\n", " ")

    # Заменяем множественные пробелы на один пробел
    text = " ".join(text.split())

    return text.strip()


def process_google_drive_mp3_files():
    """
    Получает MP3 файлы из Google Drive, транскрибирует их и записывает результаты в Google Sheets.
    """
    try:

        # Подключение к Google Sheets
        sheet = connect_to_google_sheets(SHEET_ID)

        existing_rows = sheet.get_all_values()
        value_promt = get_promt_value()
        # logger.info(value_promt)
        # Преобразуем данные в список словарей, анализируя последнюю колонку
        existing_files = [
            {"transcript_id": row[-1], "Имя файла": row[-2]}
            for row in existing_rows[1:]
            if len(row) >= 2
        ]

        # Преобразуем данные в два отдельных множества для быстрой проверки
        existing_transcripts = {entry["transcript_id"] for entry in existing_files}
        existing_file_names = {entry["Имя файла"] for entry in existing_files}

        # Создаём объект Google Drive
        drive = create_drive_instance()
        # Загружаем обработанные файлы
        processed_files = load_processed_files()
        # Получаем список MP3 файлов
        mp3_files = get_mp3_files_from_google_drive(drive)
        new_files = get_new_files_from_drive(mp3_files, processed_files)

        invalid_data = []

        # logger.info(f"Найдено {len(new_files)} новых файлов для обработки.")
        for file_info in new_files:
            try:

                file_name = file_info["name"]
                file_link = file_info["link"]
                transcript_id = get_id_tr(file_name)
                # Проверяем наличие transcript_id или file_name в существующих данных
                if (
                    transcript_id in existing_transcripts
                    or file_name in existing_file_names
                ):
                    logger.info(f"Добавили в кеш {file_name}")
                    # Добавляем обработанный файл в локальный кэш
                    processed_files.append(
                        {"transcript_id": transcript_id, "file_name": file_name}
                    )
                    continue

                if transcript_id:
                    # Если transcript_title совпадает с file_name и есть transcript_id
                    result_text = get_transcrip(transcript_id)
                    logger.info("-" * 100)
                    logger.info(f"переходим к result_summary")
                    result_summary = get_transcript_summary(transcript_id)
                    # logger.info(f"result_summary -> {result_summary}")
                    # Проверка: если result_summary или его ключ summary равен None, пропускаем файл
                    if result_summary is None or result_summary.get("summary") is None:
                        logger.error(f"Не удалось получить данные транскрипта для {file_name}. Пропускаем файл.")
                        datas = parse_mp3_filename_sql(file_name)
                        invalid_data.append(datas)
                        continue
                    
                else:
                    logger.info("Запускаем upload_audio")
                    transcript_id = upload_audio(file_link, file_name)
                    logger.info(f"Получили {transcript_id}")
                    if transcript_id is None:
                        datas = parse_mp3_filename_sql(file_name)
                        invalid_data.append(datas)
                        logger.error(
                            f"Не удалось получить transcript_id для {file_name}. Удаляем файл из Google Drive."
                        )
                        # Поиск файла в Google Drive
                        query = f"title = '{file_name}' and trashed = false"
                        try:
                            file_list = drive.ListFile({"q": query}).GetList()
                            if file_list:
                                for file in file_list:
                                    try:
                                        file.Delete()
                                        logger.info(
                                            f"Файл {file_name} успешно удалён из Google Drive."
                                        )
                                    except Exception as e:
                                        logger.error(
                                            f"Ошибка при удалении файла {file_name}: {e}"
                                        )
                            else:
                                logger.warning(
                                    f"Файл {file_name} не найден в Google Drive."
                                )
                        except Exception as e:
                            logger.error(f"Ошибка при поиске файла {file_name}: {e}")
                        continue  # Добавляем continue здесь!
                    logger.info("-" * 100)
                    logger.info("Запускаем result_summary")
                    result_summary = get_transcript_summary(transcript_id)
                    logger.info(f"result_summary -> {result_summary}")
                    # Проверка: если result_summary или его ключ summary равен None, пропускаем файл
                    if result_summary is None or result_summary.get("summary") is None:
                        logger.error(f"Не удалось получить данные транскрипта для {file_name}. Пропускаем файл.")
                        datas = parse_mp3_filename_sql(file_name)
                        invalid_data.append(datas)
                        continue
                logger.info("Заходим в функцию result_gpt")
                # Запускаем асинхронную функцию через asyncio.run()
                try:
                    result_gpt = asyncio.run(question_gpt(value_promt, result_text))
                except Exception as e:
                    logger.error(e)

                # Теперь можно безопасно получать overview и shorthand_bullet
                overview = result_summary.get("summary", {}).get("overview", None)
                shorthand_bullet = result_summary.get("summary", {}).get("shorthand_bullet", None)
                # logger.debug(
                #     f"Подготовка данных для записи: {file_name}, transcript_id: {transcript_id}"
                # )

                # Формируем данные для записи
                all_data = parse_mp3_filename(file_name)

                notes = (
                    clean_text(shorthand_bullet)
                    if shorthand_bullet is not None
                    else None
                )
                all_data["Текст звонка Укр"] = result_text
                all_data["Overview"] = overview
                all_data["Notes"] = notes
                all_data["transcript_id"] = transcript_id
                all_data["result_gpt"] = result_gpt
                # Добавляем ссылку на MP3
                all_data["Ссылка на MP3"] = file_link

                # logger.debug(f"result_summary: {result_summary}")
                # logger.debug(f"shorthand_bullet: {shorthand_bullet}")
                # logger.debug(f"all_data: {all_data}")

                # Записываем в БД
                write_add_call_data(all_data)
                # # Записываем данные в Google Sheets
                write_dict_to_google_sheets(all_data)

            except Exception as e:
                # ОТКРЫТЬ КАК ПРОТЕСТИРУЮ
                logger.error(f"Ошибка при обработке файла {file_name}: {e}")
                datas = parse_mp3_filename_sql(file_name)
                invalid_data.append(datas)
        # Сохраняем данные в файл result.json
        with open(invalid_json, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f, ensure_ascii=False, indent=4)

        save_processed_files(processed_files)
        # logger.info(f"Обновлённый кэш сохранён в {PROCESSED_FILES_CACHE}.")

    except Exception as e:
        logger.error(f"Ошибка при обработке Google Drive: {e}")


# Подключение к Google Sheets


def connect_to_google_sheets(SHEET_ID, retries=3, delay=5):
    """
    Устанавливает соединение с Google Sheets по ID таблицы с обработкой ошибок и тайм-аутами.

    :param SHEET_ID: ID таблицы Google Sheets
    :param retries: Количество попыток подключения
    :param delay: Задержка между попытками
    :return: Объект листа (worksheet)
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        service_account_file, scope
    )

    for attempt in range(retries):
        try:
            # Устанавливаем HTTP-клиент с тайм-аутом
            http = httplib2.Http(timeout=30)
            http = credentials.authorize(http)  # Авторизуем HTTP-клиент
            client = gspread.Client(auth=credentials)
            client.session = http  # Устанавливаем HTTP-клиент для gspread
            sheet = client.open_by_key(SHEET_ID).sheet1
            # logger.info("Успешное подключение к Google Sheets")
            return sheet
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error("Все попытки подключения к Google Sheets исчерпаны.")
                raise


# def get_id_tr(file_name):
#     logger.info(f"Проверяем {file_name}")
#     # GraphQL запрос для получения всех транскрипций
#     query = """
#     query {
#     transcripts {
#         id
#         title
#         # Здесь можно добавить другие поля, которые вам нужны
#     }
#     }
#     """

#     # Отправляем запрос на получение всех транскрипций
#     response = requests.post(
#         GRAPHQL_URL, headers=headers_api, json={"query": query}, timeout=60
#     )


#     if response.status_code == 200:
#         result = response.json()
#         if "data" in result and "transcripts" in result["data"]:
#             for transcript in result["data"]["transcripts"]:
#                 transcript_id = transcript["id"]
#                 transcript_title = transcript["title"]
#                 if file_name == transcript_title:
#                     return transcript_id
#         else:
#             logger.error("Нет доступных транскрипций или ошибка в структуре ответа.")
#     else:
#         logger.error(f"Ошибка запроса: {response.status_code}")
#         logger.error(response.text)
def get_id_tr(file_name):
    logger.info(f"Проверяем {file_name}")

    # GraphQL запрос с сортировкой по дате
    query = """
    query GetTranscript($title: String!) {
        transcripts(title: $title) {
            id
            title
            date
        }
    }
    """

    variables = {"title": file_name}

    try:
        response = requests.post(
            GRAPHQL_URL,
            headers=headers_api,
            json={"query": query, "variables": variables},
            timeout=60,
        )

        response.raise_for_status()

        result = response.json()
        if "data" in result and "transcripts" in result["data"]:
            transcripts = result["data"]["transcripts"]
            if transcripts:
                # Сортируем по дате (самый новый первый) и берем первый
                sorted_transcripts = sorted(
                    transcripts, key=lambda x: x.get("date", 0), reverse=True
                )
                latest_transcript = sorted_transcripts[0]
                # logger.info(f"Найдено {len(transcripts)} транскриптов для {file_name}. "
                #           f"Используется самый последний с ID: {latest_transcript['id']}")
                return latest_transcript["id"]
            else:
                # logger.info(f"Транскрипт с названием {file_name} не найден")
                return None
        else:
            logger.error("Ошибка в структуре ответа")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса: {str(e)}")
        return None


def upload_audio(file_link, file_name):
    # logger.info(f"Загружаем {file_name}")
    # GraphQL запрос для загрузки аудио
    upload_query = """
    mutation UploadAudio($input: AudioUploadInput!) {
    uploadAudio(input: $input) {
        success
        title
        message
    }
    }
    """

    # Данные для запроса
    variables = {
        "input": {
            "url": file_link,
            "title": file_name,  # Вы можете изменить это на желаемое название встречи
        }
    }

    # Отправляем POST запрос для загрузки файла
    response = requests.post(
        GRAPHQL_URL,
        headers=headers_api,
        json={"query": upload_query, "variables": variables},
        timeout=60,
    )

    if response.status_code == 200:
        result = response.json()
        # logger.info(result)
        # Если 'data': None, немедленно возвращаем None
        if result.get("data") is None:
            # logger.error(f"Ошибка загрузки файла {file_name}: {result['errors'][0]['message']}")
            return None

        if result["data"]["uploadAudio"]["success"]:
            logger.info("Аудио успешно загружено.")

            # Теперь нужно получить transcript_id, когда аудио будет обработано
            get_transcript_query = """
            query GetTranscriptByTitle($title: String!) {
            transcripts(title: $title) {
                id
            }
            }
            """

            # Ждем, пока аудио не будет обработано
            while True:
                get_transcript_response = requests.post(
                    GRAPHQL_URL,
                    headers=headers_api,
                    json={
                        "query": get_transcript_query,
                        "variables": {"title": file_name},
                    },
                    timeout=60,
                )

                if get_transcript_response.status_code == 200:
                    get_transcript_result = get_transcript_response.json()
                    if get_transcript_result["data"]["transcripts"]:
                        transcript_id = get_transcript_result["data"]["transcripts"][0][
                            "id"
                        ]
                        return transcript_id
                    else:
                        logger.warning("Ожидание обработки аудио...")
                        # Ждем 10 секунд перед следующим запросом
                        time.sleep(30)
                else:
                    logger.error(
                        f"Ошибка при получении transcript_id: {
                            get_transcript_response.status_code}"
                    )
                    logger.error(get_transcript_response.text)
                    return None
        else:
            return None
    else:
        return None
        logger.error(f"Ошибка при загрузке: {response.status_code}")
        logger.error(response.text)


# Функция для обработки ответа и извлечения сообщения об ошибке
def extract_error_message(response):
    """
    Извлекает сообщение об ошибке из ответа, если оно существует.

    :param response: JSON-объект с ошибкой
    :return: Текст сообщения об ошибке или None
    """
    if "errors" in response and isinstance(response["errors"], list):
        for error in response["errors"]:
            if "message" in error:
                return error["message"]
    return None


# Думаю что рабочий
# def get_transcrip(transcript_id):
#     logger.info(f"Получаем текст из {transcript_id}")
#     if transcript_id is None:
#         logger.info(f"Нету {transcript_id}")
#         return None
#     # GraphQL запрос для получения предложений
#     query_transcript = """
#     query {
#     transcripts {
#         id
#         title
#         sentences {
#         text
#         raw_text
#         }
#     }
#     }
#     """
#     # Данные для запроса
#     variables = {"transcriptId": transcript_id}
#     # Отправка запроса
#     response = requests.post(
#         GRAPHQL_URL,
#         headers=headers_api,
#         json={"query": query_transcript, "variables": variables},
#         timeout=60,
#     )


#     # Обработка ответа
#     if response.status_code == 200:
#         data = response.json()
#         if "data" in data and "transcripts" in data["data"]:
#             for transcript in data["data"]["transcripts"]:
#                 transcript_id = transcript["id"]
#                 # Сбор всех предложений в одну строку
#                 full_text = " ".join(
#                     sentence["text"] for sentence in transcript.get("sentences", [])
#                 )
#                 return full_text
#             logger.error("Нет данных.")
#     else:
#         logger.error(f"Ошибка: {response.status_code}")
#         logger.error(response.text)
def get_transcrip(transcript_id):
    MAX_RETRIES = 10
    DELAY_SECONDS = 30

    logger.info(f"Получаем текст из {transcript_id}")
    if transcript_id is None:
        logger.info(f"Нету {transcript_id}")
        return None

    # GraphQL запрос
    query_transcript = """
   query GetTranscriptText($transcriptId: String!) {
       transcript(id: $transcriptId) {
           sentences {
               text
               raw_text
           }
       }
   }
   """

    variables = {"transcriptId": transcript_id}
    retry_count = 0

    while retry_count < MAX_RETRIES:
        # Отправка запроса
        try:
            response = requests.post(
                GRAPHQL_URL,
                headers=headers_api,
                json={"query": query_transcript, "variables": variables},
                timeout=60,
            )

            # Обработка ответа
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "transcript" in data["data"]:
                    transcript = data["data"]["transcript"]
                    # Сбор всех предложений в одну строку
                    full_text = " ".join(
                        sentence["text"] for sentence in transcript.get("sentences", [])
                    )
                    if full_text:
                        # logger.info(f"Полный текст получен {full_text}")
                        return full_text

            # Если дошли сюда, значит результат пустой или некорректный
            retry_count += 1
            logger.warning(
                f"Попытка {retry_count} из {MAX_RETRIES} не удалась. Ожидание {DELAY_SECONDS} секунд..."
            )
            time.sleep(DELAY_SECONDS)

        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logger.warning(
                    f"Попытка {retry_count} из {MAX_RETRIES} не удалась. Ожидание {DELAY_SECONDS} секунд..."
                )
                time.sleep(DELAY_SECONDS)

    logger.error(f"Не удалось получить данные после {MAX_RETRIES} попыток")
    return None


def parse_mp3_filename(filename):
    """
    Разбирает имя файла .mp3 и извлекает дату, номер телефона, линию и менеджера.
    Добавляет имя файла как отдельное поле.

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
            "Текст звонка Укр": "",
            "Overview": "",
            "Notes": "",
            "Result_GpT": "",
            "Ссылка на MP3": "",
            "Имя файла": filename,  # Имя файла как отдельное поле
            "transcript_id": "",  # Имя файла как отдельное поле
        }

    except IndexError:
        raise ValueError(f"Невозможно разобрать имя файла: {filename}")


def parse_mp3_filename_sql(filename):
    """
    Разбирает имя файла .mp3 и извлекает дату, номер телефона, линию и менеджера.
    Добавляет имя файла как отдельное поле.

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

        all_data = {
            "call_date": date_mp3,
            "caller_number": phone_mp3,
            "employee_ext_number": line_mp3,
            "employee": manager_mp3,
        }

        return all_data
    except IndexError:
        raise ValueError(f"Невозможно разобрать имя файла: {filename}")


def write_dict_to_google_sheets(data_dict):
    """
    Записывает словарь в Google Sheets, где ключи словаря — это заголовки столбцов.

    :param SHEET_ID: ID таблицы Google Sheets
    :param data_dict: Словарь данных для записи (ключи — заголовки, значения — данные)
    """
    try:
        # Подключение к Google Sheets
        sheet = connect_to_google_sheets(SHEET_ID)

        # Получаем заголовки из первого ряда таблицы
        existing_headers = sheet.row_values(1)

        # Если таблица пуста, добавляем заголовки
        if not existing_headers:
            existing_headers = list(data_dict.keys())
            sheet.append_row(existing_headers)

        # Убедимся, что ключи словаря совпадают с заголовками таблицы
        row = [data_dict.get(header, "") for header in existing_headers]

        # Проверяем, какая строка следующая свободная
        all_rows = sheet.get_all_values()  # Получаем все строки таблицы
        next_free_row = len(all_rows) + 1  # Следующая свободная строка

        # Записываем данные в следующую свободную строку
        sheet.insert_row(row, next_free_row)

    except Exception as e:
        logger.error(f"Ошибка при записи в Google Sheets: {e}")


def deleting_data_in_database(data):
    # Если data пустой список, логируем сообщение и пропускаем
    if not data:
        logger.info("Список данных пуст, пропуск выполнения.")
        return
    # URL API для удаления записей
    url = f"https://{IP}/delete_records"
    # Заголовки запроса
    headers_database = {"Content-Type": "application/json"}
    try:
        # Отправляем DELETE-запрос
        response = requests.delete(
            url,
            headers=headers_database,
            data=json.dumps(data),
            verify=False,
            timeout=30,
        )  # verify=False отключает проверку SSL

        # Проверяем статус ответа
        if response.status_code == 200:
            # logger.info(f"Успех: {response.json()}")
            invalid_json.unlink()
            shutil.rmtree(call_recording_directory)
        else:
            logger.error(f"Ошибка: {response.status_code}, {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")


def get_transcript_summary(transcript_id):
    """
    Получает данные транскрипта (Summary: keywords, action_items, overview и т.д.).
    
    :param transcript_id: ID транскрипции
    :return: Словарь с данными Summary (возвращается только после успешного получения данных)
    """
    if transcript_id is None:
        return None

    query = """
    query Transcript($transcriptId: String!) {
      transcript(id: $transcriptId) {
        id
        title
        summary {
          keywords
          action_items
          outline
          shorthand_bullet
          overview
          bullet_gist
          gist
          short_summary
        }
      }
    }
    """
    variables = {"transcriptId": transcript_id}

    while True:
        try:
            
            response = requests.post(
                GRAPHQL_URL,
                headers=headers_api,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            logger.info(response.status_code)
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            time.sleep(30)
            continue

        if response.status_code != 200:
            logger.error(f"Ошибка запроса: {response.status_code}")
            logger.error(response.text)
            time.sleep(30)
            continue

        try:
            data = response.json()
            # logger.info(data)
        except Exception as e:
            logger.error(f"Ошибка при разборе JSON: {e}")
            time.sleep(30)
            continue

        data_field = data.get("data")
        if not data_field or not isinstance(data_field, dict) or "transcript" not in data_field:
            logger.error("Ошибка: данные не найдены.")
            logger.error(data)
            time.sleep(30)
            continue

        transcript = data_field["transcript"]
        if transcript is None:
            logger.warning("Транскрипт отсутствует, повтор запроса через 30 секунд...")
            time.sleep(30)
            continue

        id_transcript = transcript.get("id")
        title_transcript = transcript.get("title")
        summary = transcript.get("summary", {})

        # Проверяем наличие и содержимое "overview"
        if "overview" in summary and summary["overview"]:
            all_data = {
                "id": id_transcript,
                "title": title_transcript,
                "summary": summary,
            }
            return all_data
        else:
            logger.warning("Обзор отсутствует или пуст. Ожидание 30 секунд...")
            time.sleep(30)
            continue



def convert_keys_to_english(data):
    """Преобразует ключи словаря с русского на английский для модели CallData."""
    key_mapping = {
        "Дата": "date",
        "Телефон": "phone",
        "Линия": "line",
        "Имя менеджера": "manager_name",
        "Текст звонка Укр": "call_text_ukr",
        "Overview": "overview",
        "Notes": "notes",
        "result_gpt": "result_gpt",
        "Ссылка на MP3": "mp3_link",
        "Имя файла": "file_name",
        "transcript_id": "transcript_id",
    }
    return {key_mapping[k]: v for k, v in data.items() if k in key_mapping}


def write_add_call_data(call_data):
    """Отправляет данные на маршрут /add_call_data и сохраняет результат в result.json."""
    url = f"https://{IP}/add_call_data"

    # Преобразуем ключи перед отправкой
    call_data = convert_keys_to_english(call_data)

    try:
        response = requests.post(
            url,
            json=call_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False,
        )

        if response.status_code == 200:
            result = response.json()
            # logger.info(f"Данные успешно отправлены")
        else:
            logger.error(
                f"Ошибка отправки данных: {response.status_code} - {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка подключения: {e}")


def fetch_comment_orders(date_from=None, date_to=None):
    try:
        # Если даты не указаны, используем последние 24 часа
        if not date_from or not date_to:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59)
            date_from = date_from.replace(hour=0, minute=0, second=0)

        # Форматируем даты для URL
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        url = f"https://{IP}/comment_orders"
        params = {"date_from": date_from_str, "date_to": date_to_str}

        # logger.info(f"Отправляем запрос на URL: {url} с параметрами: {params}")

        response = requests.get(url, params=params, timeout=30, verify=False)
        # logger.info(f"Получен ответ со статусом: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            return data["data"]
        else:
            error_data = response.json()
            raise Exception(
                f"API request failed: {error_data.get('message', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Error fetching comment orders: {e}")
        raise


def get_salesdrive_orders(date_from=None, date_to=None):
    try:
        # Если даты не указаны, используем последние 24 часа
        if not date_from or not date_to:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59)
            date_from = date_from.replace(hour=0, minute=0, second=0)

        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        url = "https://zubr.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        params = {
            "filter[orderTime][from]": date_from_str,
            "filter[orderTime][to]": date_to_str,
            "page": 1,
            "limit": 100,
        }

        #    logger.info(f"Отправляем запрос на URL: {url} с параметрами: {params}")

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=(10, 30),  # (connect timeout, read timeout)
        )

        #    logger.info(f"Получен ответ со статусом: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            processed_data = process_data(data)
            return processed_data
        else:
            raise Exception(
                f"API request failed with status code: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        logger.error("Timeout при запросе к API")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        raise


def extract_user_name(user_id, user_options):
    filtered_user = list(filter(lambda x: x["value"] == user_id, user_options))
    return filtered_user[0]["text"] if filtered_user else None


def process_data(data):
    result = []
    user_options = data["meta"]["fields"]["userId"]["options"]

    for item in data["data"]:
        try:
            entry = {
                "id_data": item["id"],
                "phone_contact": (
                    item["contacts"][0]["phone"][0] if item["contacts"] else None
                ),
                "user_name": extract_user_name(item["userId"], user_options),
                "orderTime":item["orderTime"]
            }
            result.append(entry)
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка обработки записи: {e}")
            continue

    return result


# def find_matching_records(records_bd, records_salesdrive):
#     formatted_records = []  # Список для хранения всех совпадений
#     matched_ids = (
#         []
#     )  # Список для хранения id из records_bd, по которым найдены совпадения

#     for bd_record in records_bd:
#         phone_bd = bd_record["phone"]
#         phone_bd_no_prefix = phone_bd[2:] if phone_bd.startswith("38") else phone_bd
#         manager_name_bd = bd_record["manager_name"]

#         # Будем хранить все совпадения для текущей записи
#         matches = []

#         # Поиск совпадений по полному номеру
#         for sd_record in records_salesdrive:
#             if (
#                 sd_record["phone_contact"] == phone_bd
#                 and sd_record["user_name"] == manager_name_bd
#             ):
#                 matches.append(sd_record)

#         # Поиск совпадений без префикса 38, если не нашли по полному номеру
#         if not matches:
#             for sd_record in records_salesdrive:
#                 if (
#                     sd_record["phone_contact"] == phone_bd_no_prefix
#                     and sd_record["user_name"] == manager_name_bd
#                 ):
#                     matches.append(sd_record)

#         # # Если нашли совпадения, берем запись с максимальным id_data
#         # if matches:
#         #     # Сортируем по id_data в убывающем порядке и берем первый элемент
#         #     best_match = max(matches, key=lambda x: x["id_data"])

#         #     formatted_record = {
#         #         "id": best_match["id_data"],
#         #         "data": {"comment": bd_record["notes"]},
#         #     }
#         #     formatted_records.append(formatted_record)
#         #     matched_ids.append(bd_record["id"])  # Добавляем id в список найденных
#         # Если нашли совпадения, берем запись с минимальным id_data
#         if matches:
#             # Сортируем по id_data в возрастающем порядке и берем первый элемент
#             best_match = min(matches, key=lambda x: x["id_data"])

#             formatted_record = {
#                 "id": best_match["id_data"],
#                 "data": {"comment": bd_record["notes"]},
#             }
#             formatted_records.append(formatted_record)
#             matched_ids.append(bd_record["id"])  # Добавляем id в список найденных


#     return formatted_records, matched_ids
def normalize_phone(phone):
    """
    Удаляем все нецифровые символы и, если номер начинается с "38",
    возвращаем его без первых двух символов.
    Например, "380681003392" -> "0681003392".
    """
    digits = "".join(filter(str.isdigit, phone))
    if digits.startswith("38") and len(digits) >= 10:
        return digits[2:]
    return digits


def normalize_name(name):
    """
    Приводим имя к нормальной форме:
      - Нормализация Unicode (NFKC)
      - Приведение к нижнему регистру
    """
    norm = unicodedata.normalize("NFKC", name).strip().lower()
    # Если в имени может встречаться латинская "c" вместо кириллической "с", заменим её.
    norm = norm.replace("cухотерин", "сухотерин")
    return norm


def swap_name(name):
    """
    Если имя состоит ровно из двух слов, меняем их местами.
    Например: "Cухотерин Виталий" -> "Виталий Cухотерин"
    """
    parts = name.split()
    if len(parts) == 2:
        swapped = f"{parts[1]} {parts[0]}"
        # logger.debug(f"Меняем местами имя: '{name}' -> '{swapped}'")
        return swapped
    else:
        logger.debug(f"Имя '{name}' не состоит из двух слов, оставляем без изменений.")
        return name


def find_all_matching_records(records_bd, records_salesdrive):
    """
    Перебирает все записи из records_bd и для каждой ищет первое совпадение в records_salesdrive.
    Если совпадение найдено, сохраняет (для Salesdrive) только уникальную заявку (по id из Salesdrive)
    и добавляет id записи BD в список bd_ids.
    
    Args:
        records_bd (list): Список заявок из BD.
        records_salesdrive (list): Список заявок из Salesdrive.
    
    Returns:
        tuple: (orders_data, bd_ids)
            orders_data: список словарей для обновления в Salesdrive (уникальные заявки);
            bd_ids: список id заявок из BD, для которых найдены совпадения.
    """
    sd_matches = {}  # Ключ: id заявки из Salesdrive, значение: форматированная запись для обновления
    bd_ids = []      # Список id из BD

    for bd_record in records_bd:
        normalized_phone_bd = normalize_phone(bd_record["phone"])
        normalized_name_bd = normalize_name(bd_record["manager_name"])
        swapped_name_bd = swap_name(bd_record["manager_name"])
        normalized_swapped_bd = normalize_name(swapped_name_bd)

        matched = False
        for sd_record in records_salesdrive:
            user_name = sd_record.get("user_name")
            # Если у записи из Salesdrive нет имени, пропускаем её
            if user_name is None:
                logger.warning(
                    "Пропускаем запись Salesdrive id_data=%s, так как user_name отсутствует",
                    sd_record.get("id_data")
                )
                continue

            normalized_phone_sd = normalize_phone(sd_record["phone_contact"])
            normalized_name_sd = normalize_name(user_name)

            # Если нормализованные номера совпадают и имя совпадает (либо напрямую, либо после перестановки):
            if normalized_phone_bd == normalized_phone_sd and (
                normalized_name_bd == normalized_name_sd or normalized_swapped_bd == normalized_name_sd
            ):
                sd_id = sd_record["id_data"]
                # Если для этой заявки из Salesdrive ещё не добавлено обновление,
                # сохраняем форматированную запись, взятую из первой найденной BD-записи
                if sd_id not in sd_matches:
                    formatted_record = {
                        "id": sd_id,
                        "data": {"comment": bd_record["notes"]}
                    }
                    sd_matches[sd_id] = formatted_record
                matched = True
                break  # Для каждой BD записи выбираем только первое совпадение в Salesdrive
        if matched:
            bd_ids.append(bd_record["id"])

    orders_data = list(sd_matches.values())
    return orders_data, bd_ids


def update_order_comments(orders_data):
    """
    Обновляет комментарии для списка заявок

    Args:
        orders_data (list): Список словарей с данными заявок

    Returns:
        list: Список результатов обновления для каждой заявки
    """
    results = []

    try:
        url = "https://zubr.salesdrive.me/api/order/update/"
        headers = {
            "Form-Api-Key": SALESDRIVE_API,
            "Content-Type": "application/json",
        }

        for order_data in orders_data:
            try:
                # logger.info(
                #     f"Отправляем запрос на обновление заявки {order_data['id']}"
                # )

                response = requests.post(
                    url,
                    headers=headers,
                    json=order_data,
                    timeout=(10, 30),  # (connect timeout, read timeout)
                )

                logger.info(f"Обновляем заявку в salesdrive {order_data["id"]}")

                if response.status_code == 200:
                    results.append(
                        {
                            "id": order_data["id"],
                            "status": "success",
                            "response": response.json(),
                        }
                    )
                else:
                    results.append(
                        {
                            "id": order_data["id"],
                            "status": "error",
                            "error": f"API request failed with status code: {response.status_code}",
                        }
                    )

            except requests.exceptions.Timeout:
                logger.error(f"Timeout при запросе к API для заявки {order_data['id']}")
                results.append(
                    {
                        "id": order_data["id"],
                        "status": "error",
                        "error": "Timeout error",
                    }
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении заявки {order_data['id']}: {e}")
                results.append(
                    {"id": order_data["id"], "status": "error", "error": str(e)}
                )

    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении заявок: {e}")
        raise

    return results


def update_comment_orders(order_ids: List[int]) -> dict:
    """
    Отправляет POST запрос для обновления статуса comment_order.

    Args:
        order_ids: список ID записей для обновления

    Returns:
        dict: ответ от сервера
    """
    try:

        url = f"https://{IP}/comment_orders"
        headers = {"Content-Type": "application/json", "accept": "application/json"}
        data = {"ids": order_ids}

        # Отправляем запрос
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30,
            verify=False,  # Эквивалент --insecure в curl
        )

        # Проверяем статус ответа
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке запроса: {e}")
        return {"status": "error", "message": str(e)}

# Работа с CRM
def work_salesdrive():
    records_bd = fetch_comment_orders()
    records_salesdrive = get_salesdrive_orders()
    # logger.info(records_bd)
    # logger.info(records_salesdrive)
    # Получаем списки совпадений (всех найденных пар)
    orders_data, ids_to_update = find_all_matching_records(records_bd, records_salesdrive)
    
    # Если совпадений нет (список пуст), выходим из функции
    if not orders_data or not ids_to_update:
        logger.info("Нет совпадений – записи для обновления отсутствуют.")
        return
    
    update_order_comments(orders_data)
    result = update_comment_orders(ids_to_update)
    logger.info(f"Результат обновления: {result}")

def get_promt_value():
    """
    Подключается к Google Sheets по указанному SHEET_ID, открывает лист с именем 'promt'
    и возвращает значение ячейки A1.
    
    :param SHEET_ID: ID таблицы Google Sheets
    :return: Значение ячейки A1 листа 'promt'
    """
    # Используем существующую функцию для подключения (она возвращает лист sheet1)
    default_sheet = connect_to_google_sheets(SHEET_ID)
    
    # Получаем объект Spreadsheet из возвращённого листа
    spreadsheet = default_sheet.spreadsheet
    
    # Получаем лист с именем "promt"
    promt_sheet = spreadsheet.worksheet("promt")
    
    # Читаем значение ячейки A1
    a1_value = promt_sheet.acell("A1").value
    
    return a1_value

async def question_gpt(value_promt, result_text):
    question = f"{value_promt}\n\n{result_text}"
    response = await client_gpt.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    message = response.choices[0].message.content
    return message
if __name__ == "__main__":

    start_time = datetime.now()  # Здесь используется datetime из модуля
    logger.info(f"Скрипт запущен в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    fetch_all_data()
    process_google_drive_mp3_files()

    work_salesdrive()
    # Логирование паузы
    pause_duration = 1800
    logger.info(f"Остановка для {pause_duration} секунд")
    time.sleep(pause_duration)
