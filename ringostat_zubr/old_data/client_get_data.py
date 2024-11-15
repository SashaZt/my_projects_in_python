import base64
import json
import os
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
    StringVar,
    Text,
    Tk,
)

import requests
import urllib3
from configuration.logger_setup import logger
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dotenv import load_dotenv
from tkcalendar import Calendar

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"

data_directory.mkdir(parents=True, exist_ok=True)

result_output_file = data_directory / "result.json"

# Загрузка переменных из .env
logger.info("Loading environment variables from .env file")
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

SECRET_AES_KEY = os.getenv("SECRET_AES_KEY")
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


def fetch_all_data():
    url = "https://185.233.116.213:5000/get_all_data"
    encrypted_key = encrypt_access_key(ORIGINAL_ACCESS_KEY)
    params = {"access_key": encrypted_key}

    try:
        logger.info("Sending GET request to the server")
        response = requests.get(url, params=params, verify=False)
        result_text.delete(1.0, END)

        if response.status_code == 200:
            logger.info("Data fetched successfully")
            data = response.json().get("data", [])

            # Собираем данные из всех фильтров
            filters = []
            for i in range(5):
                field = field_vars[i].get()
                condition = condition_vars[i].get()
                value = value_entries[i].get()
                operator = operator_vars[i].get() if i < 4 else None
                filters.append((field, condition, value, operator))

            # Применение комбинированных фильтров
            filtered_data = apply_combined_filter(data, filters)

            result_text.insert(END, "Filtered Data:\n")
            result_text.insert(
                END, json.dumps(filtered_data, ensure_ascii=False, indent=4)
            )

            with open("response_debug.json", "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=4)
            logger.info("Filtered response saved to response_debug.json for debugging")
        else:
            logger.warning(f"Failed to fetch data, status code: {response.status_code}")
            result_text.insert(
                END, f"Failed to fetch data, status code: {response.status_code}\n"
            )
            result_text.insert(END, response.json())

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the GET request: {e}")
        result_text.delete(1.0, END)
        result_text.insert(END, f"An error occurred: {e}")


def download_data_to_file():
    """Скачивает все данные и сохраняет их в result.json"""
    url = "https://185.233.116.213:5000/get_all_data"
    encrypted_key = encrypt_access_key(ORIGINAL_ACCESS_KEY)
    params = {"access_key": encrypted_key}

    try:
        logger.info("Sending GET request to the server")
        response = requests.get(url, params=params, verify=False)

        if response.status_code == 200:
            logger.info("Data fetched successfully")
            data = response.json().get("data", [])

            # Сохраняем данные в файл result.json
            with open(result_output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {result_output_file}")
        else:
            logger.warning(f"Failed to fetch data, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the GET request: {e}")


# Скачиваем данные в файл result.json перед запуском интерфейса
download_data_to_file()


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

# Кнопка получения данных
fetch_button = Button(root, text="Получить данные", command=fetch_all_data)
fetch_button.pack(pady=10)

# Поле вывода результатов
result_text = Text(root, wrap="word", width=80, height=20)
result_text.pack(pady=10)

root.mainloop()
