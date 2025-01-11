import json
import os
import shutil
import time
import wave
from datetime import datetime  # Убедитесь, что импорт правильный
from pathlib import Path

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
# logger.info("Loading environment variables from .env file")
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
folder_id = os.getenv("FOLDER_ID")
sheet_id = os.getenv("sheet_id")
IP = os.getenv("IP")
FOLDER_ID = os.getenv("FOLDER_ID")


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
            logger.info("Данные с сервера получены\n")
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
    drive = create_drive_instance()
    all_recordings = []
    calls = download_data_to_file()
    for call in calls:
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


# def get_mp3_files_from_google_drive(drive):
#     """
#     Получает список MP3 файлов из указанной папки на Google Drive.

#     :param folder_id: ID папки на Google Drive
#     :param drive: Объект GoogleDrive
#     :return: Список словарей с информацией о файлах (имя и ссылка на загрузку)
#     """
#     try:
#         query = f"'{
#             folder_id}' in parents and mimeType='audio/mpeg' and trashed=false"
#         file_list = drive.ListFile({"q": query}).GetList()

#         mp3_files = []
#         for file in file_list:
#             mp3_files.append(
#                 {
#                     "name": file["title"],
#                     "id": file["id"],
#                     "link": file["webContentLink"],
#                 }
#             )

#         return mp3_files


#     except Exception as e:
#         logger.error(f"Ошибка при получении файлов из Google Drive: {e}")
#         return []
def get_mp3_files_from_google_drive(drive):
    """
    Получает список MP3 файлов из указанной папки на Google Drive.
    :param drive: Объект GoogleDrive
    :return: Список словарей с информацией о файлах (имя и ссылка на загрузку)
    """
    query = f"'{
        folder_id}' in parents and mimeType='audio/mpeg' and trashed=false"
    try:
        for attempt in range(3):  # 3 попытки
            try:
                logger.info(f"Попытка {attempt + 1} выполнения запроса к Google Drive")
                file_list = drive.ListFile({"q": query}).GetList()
                logger.info("Успешное выполнение запроса к Google Drive")
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
                        f"Failed to download: {call_recording_url} (status code: {
                            response.status_code})\n",
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


def process_google_drive_mp3_files():
    """
    Получает MP3 файлы из Google Drive, транскрибирует их и записывает результаты в Google Sheets.
    """
    try:
        if invalid_json.exists():
            logger.info(f"Файл есть {invalid_json}")
            json_invalid = load_data_from_file(invalid_json)
            deleting_data_in_database(json_invalid)
        # Подключение к Google Sheets
        sheet = connect_to_google_sheets(sheet_id)

        # # Получаем уже существующие записи из первой колонки
        existing_rows = sheet.get_all_values()  # Получаем все строки
        existing_files = {
            row[-1] for row in existing_rows[1:] if row
        }  # Имена файлов в последней колонке

        # Создаём объект Google Drive
        drive = create_drive_instance()

        # Получаем список MP3 файлов
        mp3_files = get_mp3_files_from_google_drive(drive)
        invalid_data = []
        for file_info in mp3_files:
            try:

                file_name = file_info["name"]
                file_link = file_info["link"]
                transcript_id = get_id_tr(file_name)

                # Проверяем, есть ли файл уже в таблице
                if transcript_id in existing_files:
                    logger.info(
                        f"Файл {
                            transcript_id} уже существует в Google Sheets. Пропуск..."
                    )
                    continue
                if transcript_id:
                    # Если transcript_title совпадает с file_name и есть transcript_id
                    result_text = get_transcrip(transcript_id)
                else:
                    # Если нет transcript_id или названия не совпадают
                    transcript_id = upload_audio(file_link, file_name)
                    result_text = get_transcrip(transcript_id)

                # Формируем данные для записи
                all_data = parse_mp3_filename(file_name)
                all_data["Текст звонка Укр"] = result_text
                all_data["transcript_id"] = transcript_id
                # Добавляем ссылку на MP3
                all_data["Ссылка на MP3"] = file_link

                # Записываем данные в Google Sheets
                write_dict_to_google_sheets(all_data)

            except Exception as e:
                logger.error(f"Ошибка при обработке файла {file_name}: {e}")
                datas = parse_mp3_filename_sql(file_name)
                invalid_data.append(datas)
        # Сохраняем данные в файл result.json
        with open(invalid_json, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при обработке Google Drive: {e}")


# Подключение к Google Sheets


def connect_to_google_sheets(sheet_id, retries=3, delay=5):
    """
    Устанавливает соединение с Google Sheets по ID таблицы с обработкой ошибок и тайм-аутами.

    :param sheet_id: ID таблицы Google Sheets
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
            sheet = client.open_by_key(sheet_id).sheet1
            logger.info("Успешное подключение к Google Sheets")
            return sheet
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error("Все попытки подключения к Google Sheets исчерпаны.")
                raise


# def connect_to_google_sheets(sheet_id):
#     """
#     Устанавливает соединение с Google Sheets по ID таблицы.

#     :param sheet_id: ID таблицы Google Sheets
#     :return: Объект листа (worksheet)
#     """
#     scope = [
#         "https://spreadsheets.google.com/feeds",
#         "https://www.googleapis.com/auth/drive",
#     ]
#     credentials = ServiceAccountCredentials.from_json_keyfile_name(
#         service_account_file, scope
#     )
#     client = gspread.authorize(credentials)
#     # Открывает первый лист таблицы
#     sheet = client.open_by_key(sheet_id).sheet1
#     logger.info("Получили sheet")
#     return sheet


def get_id_tr(file_name):
    logger.info(f"Проверяем {file_name}")
    # Ваш API ключ
    api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

    # URL для получения всех транскрипций
    transcripts_url = "https://api.fireflies.ai/graphql"

    # Заголовки для запроса
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # GraphQL запрос для получения всех транскрипций
    query = """
    query {
    transcripts {
        id
        title
        # Здесь можно добавить другие поля, которые вам нужны
    }
    }
    """

    # Отправляем запрос на получение всех транскрипций
    response = requests.post(
        transcripts_url, headers=headers, json={"query": query}, timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        if "data" in result and "transcripts" in result["data"]:
            for transcript in result["data"]["transcripts"]:
                transcript_id = transcript["id"]
                transcript_title = transcript["title"]
                if file_name == transcript_title:
                    return transcript_id
        else:
            logger.error("Нет доступных транскрипций или ошибка в структуре ответа.")
    else:
        logger.error(f"Ошибка запроса: {response.status_code}")
        logger.error(response.text)


def upload_audio(file_link, file_name):
    logger.info(f"Загружаем {file_name}")
    # Ваш API ключ
    api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

    # URL для загрузки аудиофайла и получения транскрипции
    api_url = "https://api.fireflies.ai/graphql"

    # Заголовки для запроса
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

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
        api_url,
        headers=headers,
        json={"query": upload_query, "variables": variables},
        timeout=60,
    )

    if response.status_code == 200:
        result = response.json()
        logger.info(result)

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
                    api_url,
                    headers=headers,
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
                        time.sleep(10)
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


def get_transcrip(transcript_id):
    logger.info(f"Получаем текст из {transcript_id}")
    # Ваш API ключ
    api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"
    # URL для загрузки аудиофайла и получения транскрипции
    api_url = "https://api.fireflies.ai/graphql"
    # Заголовки для запроса
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # GraphQL запрос для получения предложений
    query_transcript = """
    query {
    transcripts {
        id
        title
        sentences {
        text
        raw_text
        }
    }
    }
    """
    # Данные для запроса
    variables = {"transcriptId": transcript_id}
    # Отправка запроса
    response = requests.post(
        api_url,
        headers=headers,
        json={"query": query_transcript, "variables": variables},
        timeout=60,
    )

    # Обработка ответа
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "transcripts" in data["data"]:
            for transcript in data["data"]["transcripts"]:
                transcript_id = transcript["id"]
                # Сбор всех предложений в одну строку
                full_text = " ".join(
                    sentence["text"] for sentence in transcript.get("sentences", [])
                )
                return full_text
            logger.error("Нет данных.")
    else:
        logger.error(f"Ошибка: {response.status_code}")
        logger.error(response.text)


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

    :param sheet_id: ID таблицы Google Sheets
    :param data_dict: Словарь данных для записи (ключи — заголовки, значения — данные)
    """
    try:
        # Подключение к Google Sheets
        sheet = connect_to_google_sheets(sheet_id)
        # logger.info(f"Подключение к Google Sheets выполнено: {sheet_id}")

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
        # logger.info(f"Добавлены данные: {row} в строку {next_free_row}")

    except Exception as e:
        logger.error(f"Ошибка при записи в Google Sheets: {e}")


def deleting_data_in_database(data):
    logger.info(data)
    # URL API для удаления записей
    url = f"https://{IP}/delete_records"
    # Заголовки запроса
    headers = {"Content-Type": "application/json"}
    try:
        # Отправляем DELETE-запрос
        response = requests.delete(
            url, headers=headers, data=json.dumps(data), verify=False, timeout=30
        )  # verify=False отключает проверку SSL

        # Проверяем статус ответа
        if response.status_code == 200:
            logger.info(f"Успех: {response.json()}")
        else:
            logger.error(f"Ошибка: {response.status_code}, {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    start_time = datetime.now()  # Здесь используется datetime из модуля

    logger.info(f"Скрипт запущен в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    fetch_all_data()
    process_google_drive_mp3_files()
    # Логирование паузы
    pause_duration = 600
    logger.info(f"Остановка для {pause_duration}")
    time.sleep(pause_duration)
