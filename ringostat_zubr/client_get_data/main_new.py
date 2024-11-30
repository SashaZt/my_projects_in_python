import base64
import json
import os
import wave
from datetime import datetime
from pathlib import Path
from tkinter import (
    END,
    Button,
    Entry,
    Frame,
    Label,
    Menu,
    OptionMenu,
    Scrollbar,
    StringVar,
    Text,
    Tk,
)

import lameenc
import requests
import urllib3
from configuration.logger_setup import logger
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dotenv import load_dotenv
from pydrive2.auth import GoogleAuth, ServiceAccountCredentials
from pydrive2.drive import GoogleDrive
from tkcalendar import Calendar

# Загрузка переменных из .env
logger.info("Loading environment variables from .env file")
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

SECRET_AES_KEY = os.getenv("SECRET_AES_KEY")
IP = os.getenv("IP")
FOLDER_ID = os.getenv("FOLDER_ID")
ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")

if SECRET_AES_KEY is None or ORIGINAL_ACCESS_KEY is None:
    logger.error("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")
    raise ValueError("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")

SECRET_AES_KEY = SECRET_AES_KEY.encode()
logger.info("Environment variables loaded successfully")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FIELDS = [
    "call_recording",
    "utm_campaign",
    "utm_source",
    "utm_term",
    "utm_content",
    "call_duration",
    "call_date",
    "employee",
    "employee_ext_number",
    "caller_number",
    "unique_call",
    "unique_target_call",
    "number_pool_name",
    "utm_medium",
    "substitution_type",
    "call_id",
    "talk_time",
]
CONDITIONS = [
    "равно",
    "не равно",
    "содержит",
    "не содержит",
    "начинается с",
    "заканчивается на",
    "больше чем",
    "меньше чем",
    "больше или равно",
    "меньше или равно",
]
LOGICAL_OPERATORS = ["И", "ИЛИ"]

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
call_recording_directory = current_directory / "call_recording"
data_directory.mkdir(parents=True, exist_ok=True)
call_recording_directory.mkdir(parents=True, exist_ok=True)
temp_data_output_file = data_directory / "temp_data.json"
recordings_output_file = data_directory / "recording.json"
result_output_file = data_directory / "result.json"


def encrypt_access_key(access_key: str) -> str:
    logger.info("Encrypting access key")
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(access_key.encode()) + padder.finalize()

    cipher = Cipher(
        algorithms.AES(SECRET_AES_KEY), modes.CBC(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_key = base64.b64encode(iv + encrypted_data).decode()

    logger.info("Access key encrypted successfully")
    return encrypted_key


def download_data_to_file():
    """Скачивает все данные и сохраняет их в result.json"""
    url = f"https://{IP}/get_all_data"
    encrypted_key = encrypt_access_key(ORIGINAL_ACCESS_KEY)
    params = {"access_key": encrypted_key}

    try:
        logger.info("Sending GET request to the server")
        response = requests.get(url, params=params, timeout=30, verify=False)

        if response.status_code == 200:
            logger.info("Data fetched successfully")
            data = response.json().get("data", [])

            # Сохраняем данные в файл result.json
            with open(temp_data_output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {temp_data_output_file}")
        else:
            logger.warning(f"Failed to fetch data, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the GET request: {e}")


def load_data_from_file():
    """Загружает данные из файла result.json для фильтрации"""
    if temp_data_output_file.exists():
        with open(temp_data_output_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                logger.info("Data loaded from result.json")
                return data
            except json.JSONDecodeError:
                logger.error("Error decoding JSON from result.json")
                return []
    else:
        logger.error("result.json file not found")
        return []


def apply_combined_filter(data, filters):
    filtered_data = data
    for i, filter_data in enumerate(filters):
        field, condition, value, operator = filter_data
        if field and condition and value:
            logger.info(
                f"Applying filter {i + 1}: field={field}, condition={condition}, value={value}, operator={operator}"
            )
            current_filtered = apply_single_filter(
                filtered_data, field, condition, value
            )

            # Объединяем фильтрованные данные в зависимости от оператора "И" или "ИЛИ"
            if operator == "И":
                filtered_data = [
                    record for record in filtered_data if record in current_filtered
                ]
            elif operator == "ИЛИ":
                filtered_data = list({*filtered_data, *current_filtered})
    return filtered_data


def apply_single_filter(data, field, condition, value):
    if field == "call_date":
        filter_date = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        if condition == "больше чем":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                > filter_date
            ]
        elif condition == "меньше чем":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                < filter_date
            ]
        elif condition == "больше или равно":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                >= filter_date
            ]
        elif condition == "меньше или равно":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                <= filter_date
            ]
    else:
        if condition == "равно":
            return [record for record in data if record.get(field) == value]
        elif condition == "не равно":
            return [record for record in data if record.get(field) != value]
        elif condition == "содержит":
            return [record for record in data if value in record.get(field, "")]
        elif condition == "не содержит":
            return [record for record in data if value not in record.get(field, "")]
        elif condition == "начинается с":
            return [
                record for record in data if record.get(field, "").startswith(value)
            ]
        elif condition == "заканчивается на":
            return [record for record in data if record.get(field, "").endswith(value)]
    return data


def write_recordings_to_json(data_output_file, data):
    # Сохраняем данные в файл result.json
    with open(data_output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def fetch_all_data():
    """Загружает данные из файла result.json и применяет фильтры, выводя результат в интерфейсе"""
    data = load_data_from_file()

    # Собираем данные из всех фильтров
    filters = []
    for i in range(5):
        field = field_vars[i].get()
        condition = condition_vars[i].get()
        value = value_entries[i].get()
        operator = operator_vars[i].get() if i < 4 else None
        filters.append((field, condition, value, operator))

    # Применение фильтров
    filtered_data = apply_combined_filter(data, filters)
    all_recordings = []

    for call in filtered_data:
        call_recording = call.get("call_recording")  # Получение записи
        call_date = call.get("call_date")  # Получение даты

        if call_recording and call_date:  # Проверка на наличие данных
            file_name = datetime.strptime(call_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            data_result = {file_name: call_recording}  # Формирование результата
            all_recordings.append(data_result)  # Добавление в список
    write_recordings_to_json(recordings_output_file, all_recordings)

    # Очищаем текстовое поле перед выводом
    result_text.delete(1.0, END)
    result_text.insert(END, "Filtered Data:\n")
    result_text.insert(END, json.dumps(filtered_data, ensure_ascii=False, indent=4))


def download_and_convert_to_mp3():
    """
    Скачивает запись по URL, сохраняет как .wav, и конвертирует в .mp3.

    :param call_recording_url: Ссылка на файл записи
    :param output_directory: Директория для сохранения файла
    :return: Путь к сохраненному файлу mp3
    """

    with open(recordings_output_file, "r", encoding="utf-8") as f:
        datas = json.load(f)

    # Итерация по данным
    for data in datas:
        # Получаем ключ (дата) и значение (URL) из каждого словаря
        for file_name, call_recording_url in data.items():
            try:
                # Скачиваем файл
                response = requests.get(call_recording_url, timeout=30, stream=True)
                wav_file_path = call_recording_directory / f"{file_name}.wav"
                mp3_file_path = call_recording_directory / f"{file_name}.mp3"
                if wav_file_path.exists():
                    continue
                if response.status_code == 200:
                    with open(wav_file_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"File downloaded: {wav_file_path}")

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
                    logger.info(f"File converted to MP3: {mp3_file_path}")

                    # Удаление оригинального WAV файла
                    os.remove(wav_file_path)
                else:
                    logger.error(
                        f"Failed to download file. Status code: {response.status_code}"
                    )
            except Exception as e:
                logger.error(f"An error occurred: {e}")
    recordings_output_file.unlink()


def upload_to_google_drive():
    """
    Загрузка всех файлов из директории call_recording_directory в указанную папку Google Drive.
    """
    try:
        # Аутентификация с использованием сервисного аккаунта
        gauth = GoogleAuth()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "kotelzubr-c6c2d314f075.json",  # Укажите путь к вашему JSON-файлу сервисного аккаунта
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        drive = GoogleDrive(gauth)

        # Перебор всех файлов в директории
        for file_path in call_recording_directory.iterdir():
            if file_path.is_file():  # Проверяем, что это файл
                file_name = file_path.name
                print(f"Uploading file: {file_name}")

                # Создание файла на Google Drive
                file_drive = drive.CreateFile(
                    {"title": file_name, "parents": [{"id": FOLDER_ID}]}
                )
                file_drive.SetContentFile(str(file_path))
                file_drive.Upload()
                print(f"File uploaded to Google Drive: {file_name}")
    except Exception as e:
        print(f"An error occurred while uploading to Google Drive: {e}")


def show_calendar(entry):
    calendar_window = Tk()
    calendar_window.title("Выберите дату")

    cal = Calendar(calendar_window, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=20)

    def set_date():
        selected_date = cal.get_date() + " 00:00:00"
        entry.delete(0, END)
        entry.insert(0, selected_date)
        calendar_window.destroy()

    select_button = Button(calendar_window, text="Выбрать", command=set_date)
    select_button.pack()

    calendar_window.mainloop()


def add_context_menu(entry_widget):
    context_menu = Menu(entry_widget, tearoff=0)
    context_menu.add_command(
        label="Копировать", command=lambda: root.clipboard_append(entry_widget.get())
    )
    context_menu.add_command(
        label="Вставить", command=lambda: entry_widget.insert(END, root.clipboard_get())
    )

    def show_context_menu(event):
        context_menu.post(event.x_root, event.y_root)

    entry_widget.bind("<Button-3>", show_context_menu)


# Основное окно
root = Tk()
root.title("Data Fetcher with Filters")


field_vars, condition_vars, value_entries, operator_vars = [], [], [], []

# Создаем фрейм для фильтров
filter_frame = Frame(root)
filter_frame.pack(pady=10, padx=10)

# Создаем фильтры с поддержкой календаря и контекстного меню
for i in range(5):
    Label(filter_frame, text=f"Фильтр {i + 1}").grid(
        row=i, column=0, padx=5, pady=5, sticky="w"
    )

    field_var = StringVar(filter_frame)
    field_var.set(FIELDS[0])
    field_vars.append(field_var)
    field_menu = OptionMenu(filter_frame, field_var, *FIELDS)
    field_menu.config(width=15)
    field_menu.grid(row=i, column=1, padx=5, pady=5, sticky="w")

    # Условие фильтра
    condition_var = StringVar(filter_frame)
    condition_var.set(CONDITIONS[0])
    condition_vars.append(condition_var)
    condition_menu = OptionMenu(filter_frame, condition_var, *CONDITIONS)
    condition_menu.config(width=15)
    condition_menu.grid(row=i, column=2, padx=5, pady=5, sticky="w")

    # Поле ввода значения с контекстным меню
    value_entry = Entry(filter_frame, width=20)
    value_entries.append(value_entry)
    value_entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")
    add_context_menu(value_entry)  # Добавляем контекстное меню

    # Проверка поля на 'call_date' и вызов календаря
    def on_field_change(*args, entry=value_entry, var=field_var):
        if var.get() == "call_date":
            show_calendar(entry)

    field_var.trace_add("write", on_field_change)

    # Логический оператор для первых четырех фильтров
    if i < 4:
        operator_var = StringVar(filter_frame)
        operator_var.set(LOGICAL_OPERATORS[0])
        operator_vars.append(operator_var)
        operator_menu = OptionMenu(filter_frame, operator_var, *LOGICAL_OPERATORS)
        operator_menu.config(width=5)
        operator_menu.grid(row=i, column=4, padx=5, pady=5, sticky="w")

# Создаем фрейм для кнопок
button_frame = Frame(root)
button_frame.pack(pady=10, padx=10)

# Кнопки в один ряд
fetch_button_1 = Button(
    button_frame, text="Получить данные с сервера", command=download_data_to_file
)
fetch_button_1.pack(side="left", padx=5, pady=5)

fetch_button_2 = Button(button_frame, text="Отфильтровать", command=fetch_all_data)
fetch_button_2.pack(side="left", padx=5, pady=5)

download_button = Button(
    button_frame, text="Скачать записи", command=download_and_convert_to_mp3
)
download_button.pack(side="left", padx=5, pady=5)

upload_button = Button(
    button_frame, text="Загрузить на GoogleDrive", command=upload_to_google_drive
)
upload_button.pack(side="left", padx=5, pady=5)


# Поле вывода результатов
result_text = Text(root, wrap="word", width=80, height=20)
result_text.pack(pady=10)
scrollbar = Scrollbar(root, orient="vertical", command=result_text.yview)
result_text.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

root.mainloop()
