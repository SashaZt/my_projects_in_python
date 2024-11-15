# import base64
# import os

# import requests
# import urllib3
# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import padding
# from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from dotenv import load_dotenv

# # Укажите точный путь к .env файлу, если он не загружается автоматически
# env_path = os.path.join(os.getcwd(), "configuration", ".env")
# load_dotenv(env_path)
# # Попробуйте получить ключи с проверкой на None
# SECRET_AES_KEY = os.getenv("SECRET_AES_KEY")
# ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")

# if SECRET_AES_KEY is None or ORIGINAL_ACCESS_KEY is None:
#     raise ValueError("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")

# # Преобразуем SECRET_AES_KEY в байты
# SECRET_AES_KEY = SECRET_AES_KEY.encode()  # Ключ для шифрования (32 байта)


# def encrypt_access_key(access_key: str) -> str:
#     # Генерация случайного 16-байтового IV
#     iv = os.urandom(16)

#     # Паддинг для обеспечения кратности 16 байтам
#     padder = padding.PKCS7(algorithms.AES.block_size).padder()
#     padded_data = padder.update(access_key.encode()) + padder.finalize()

#     # Шифрование с использованием SECRET_AES_KEY и сгенерированного iv
#     cipher = Cipher(
#         algorithms.AES(SECRET_AES_KEY),
#         modes.CBC(iv),
#         backend=default_backend(),
#     )
#     encryptor = cipher.encryptor()
#     encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

#     # Кодируем IV и зашифрованные данные в base64 для передачи
#     return base64.b64encode(iv + encrypted_data).decode()


# def fetch_all_data():
#     url = "https://185.233.116.213:5000/get_all_data"
#     encrypted_key = encrypt_access_key(
#         ORIGINAL_ACCESS_KEY
#     )  # Шифруем исходный access_key

#     params = {"access_key": encrypted_key}
#     try:
#         response = requests.get(url, params=params, verify=False)
#         if response.status_code == 200:
#             print("Data fetched successfully:")
#             print(response.json())
#         else:
#             print(f"Failed to fetch data, status code: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")


# if __name__ == "__main__":
# import base64
# import json
# import os
# from tkinter import END, Button, Entry, Label, OptionMenu, StringVar, Text, Tk

# import requests
# import urllib3
# from configuration.logger_setup import logger  # Импортируем loguru логгер
# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import padding
# from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from dotenv import load_dotenv

# # Загрузка переменных из .env
# logger.info("Loading environment variables from .env file")
# env_path = os.path.join(os.getcwd(), "configuration", ".env")
# load_dotenv(env_path)

# SECRET_AES_KEY = os.getenv("SECRET_AES_KEY")
# ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")

# if SECRET_AES_KEY is None or ORIGINAL_ACCESS_KEY is None:
#     logger.error("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")
#     raise ValueError("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")

# SECRET_AES_KEY = SECRET_AES_KEY.encode()
# logger.info("Environment variables loaded successfully")

# # Отключение предупреждений о небезопасном соединении
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # Опции для фильтрации
# FIELDS = [
#     "call_recording",
#     "utm_campaign",
#     "utm_source",
#     "utm_term",
#     "utm_content",
#     "call_duration",
#     "call_date",
#     "employee",
#     "employee_ext_number",
#     "caller_number",
#     "unique_call",
#     "unique_target_call",
#     "number_pool_name",
#     "utm_medium",
#     "substitution_type",
#     "call_id",
# ]
# CONDITIONS = [
#     "равно",
#     "не равно",
#     "содержит",
#     "не содержит",
#     "начинается с",
#     "заканчивается на",
# ]


# def encrypt_access_key(access_key: str) -> str:
#     logger.info("Encrypting access key")
#     iv = os.urandom(16)
#     padder = padding.PKCS7(algorithms.AES.block_size).padder()
#     padded_data = padder.update(access_key.encode()) + padder.finalize()

#     cipher = Cipher(
#         algorithms.AES(SECRET_AES_KEY), modes.CBC(iv), backend=default_backend()
#     )
#     encryptor = cipher.encryptor()
#     encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
#     encrypted_key = base64.b64encode(iv + encrypted_data).decode()

#     logger.info("Access key encrypted successfully")
#     return encrypted_key


# def fetch_filtered_data():
#     url = "https://185.233.116.213:5000/get_all_data"
#     encrypted_key = encrypt_access_key(ORIGINAL_ACCESS_KEY)
#     params = {"access_key": encrypted_key}

#     # Добавляем фильтрованные параметры
#     field = field_var.get()
#     condition = condition_var.get()
#     value = value_entry.get()

#     logger.info(f"Applying filter: field={field}, condition={condition}, value={value}")
#     if field and condition and value:
#         if condition == "равно":
#             params[field] = value
#         elif condition == "не равно":
#             params[field] = f"!{value}"
#         elif condition == "содержит":
#             params[field] = f"*{value}*"
#         elif condition == "не содержит":
#             params[field] = f"!*{value}*"
#         elif condition == "начинается с":
#             params[field] = f"{value}*"
#         elif condition == "заканчивается на":
#             params[field] = f"*{value}"

#     try:
#         logger.info("Sending GET request to the server")
#         response = requests.get(url, params=params, verify=False)
#         result_text.delete(1.0, END)  # Очистка текстового поля

#         if response.status_code == 200:
#             logger.info("Data fetched successfully")
#             result_text.insert(END, "Data fetched successfully:\n")
#             result_text.insert(END, response.json())

#             # Сохранение результата в файл JSON для отладки
#             with open("response_debug.json", "w", encoding="utf-8") as f:
#                 json.dump(response.json(), f, ensure_ascii=False, indent=4)
#             logger.info("Response saved to response_debug.json for debugging")
#         else:
#             logger.warning(f"Failed to fetch data, status code: {response.status_code}")
#             result_text.insert(
#                 END, f"Failed to fetch data, status code: {response.status_code}\n"
#             )
#             result_text.insert(END, response.json())

#             # Сохранение ошибки в JSON
#             with open("response_debug.json", "w", encoding="utf-8") as f:
#                 json.dump(response.json(), f, ensure_ascii=False, indent=4)
#             logger.warning("Error response saved to response_debug.json for debugging")
#     except requests.exceptions.RequestException as e:
#         logger.error(f"An error occurred during the GET request: {e}")
#         result_text.delete(1.0, END)
#         result_text.insert(END, f"An error occurred: {e}")

#         # Сохранение ошибки в файл для отладки
#         with open("response_debug.json", "w", encoding="utf-8") as f:
#             json.dump({"error": str(e)}, f, ensure_ascii=False, indent=4)
#         logger.error("Exception details saved to response_debug.json for debugging")


# # Интерфейс с фильтрами
# logger.info("Setting up the GUI interface")
# root = Tk()
# root.title("Data Fetcher with Filters")

# # Метка и выпадающее меню для выбора поля
# Label(root, text="Выберите поле:").pack()
# field_var = StringVar(root)
# field_var.set(FIELDS[0])  # Установить значение по умолчанию
# field_menu = OptionMenu(root, field_var, *FIELDS)
# field_menu.pack()

# # Метка и выпадающее меню для выбора условия
# Label(root, text="Выберите условие:").pack()
# condition_var = StringVar(root)
# condition_var.set(CONDITIONS[0])  # Установить значение по умолчанию
# condition_menu = OptionMenu(root, condition_var, *CONDITIONS)
# condition_menu.pack()

# # Метка и текстовое поле для значения фильтра
# Label(root, text="Введите значение:").pack()
# value_entry = Entry(root)
# value_entry.pack()

# # Кнопка для выполнения фильтрованного запроса
# fetch_button = Button(root, text="Получить данные", command=fetch_filtered_data)
# fetch_button.pack(pady=10)

# # Текстовое поле для отображения результата
# result_text = Text(root, wrap="word", width=80, height=20)
# result_text.pack(pady=10)

# logger.info("GUI setup complete. Starting the application")
# # Запуск интерфейса
# root.mainloop()


import base64
import json
import os
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

# Отключение предупреждений о небезопасном соединении
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Предполагаем, что переменные LOGICAL_OPERATORS и FIELDS определены где-то в коде
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
LOGICAL_OPERATORS = ["И", "ИЛИ"]
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


def apply_filter(data, field, condition, value):
    """Применяет фильтр к данным на основе условия."""
    if condition == "равно":
        return [record for record in data if record.get(field) == value]
    elif condition == "не равно":
        return [record for record in data if record.get(field) != value]
    elif condition == "содержит":
        return [record for record in data if value in record.get(field, "")]
    elif condition == "не содержит":
        return [record for record in data if value not in record.get(field, "")]
    elif condition == "начинается с":
        return [record for record in data if record.get(field, "").startswith(value)]
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
        result_text.delete(1.0, END)  # Очистка текстового поля

        if response.status_code == 200:
            logger.info("Data fetched successfully")
            data = response.json().get("data", [])

            # Применение фильтрации на клиенте
            field = field_var.get()
            condition = condition_var.get()
            value = value_entry.get()
            logger.info(
                f"Applying filter: field={field}, condition={condition}, value={value}"
            )
            filtered_data = apply_filter(data, field, condition, value)

            result_text.insert(END, "Filtered Data:\n")
            result_text.insert(
                END, json.dumps(filtered_data, ensure_ascii=False, indent=4)
            )

            # Сохранение результата в файл JSON для отладки
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


# Интерфейс с фильтрами
logger.info("Setting up the GUI interface")

# root = Tk()
# root.title("Data Fetcher with Filters")

# # Метка и выпадающее меню для выбора поля
# Label(root, text="Выберите поле:").pack()
# field_var = StringVar(root)
# field_var.set(FIELDS[0])  # Установить значение по умолчанию
# field_menu = OptionMenu(root, field_var, *FIELDS)
# field_menu.pack()

# # Метка и выпадающее меню для выбора условия
# Label(root, text="Выберите условие:").pack()
# condition_var = StringVar(root)
# condition_var.set(CONDITIONS[0])  # Установить значение по умолчанию
# condition_menu = OptionMenu(root, condition_var, *CONDITIONS)
# condition_menu.pack()

# # Метка и текстовое поле для значения фильтра
# Label(root, text="Введите значение:").pack()
# value_entry = Entry(root)
# value_entry.pack()

# # Кнопка для выполнения фильтрованного запроса
# fetch_button = Button(root, text="Получить данные", command=fetch_all_data)
# fetch_button.pack(pady=10)

# # Текстовое поле для отображения результата
# result_text = Text(root, wrap="word", width=80, height=20)
# result_text.pack(pady=10)


# logger.info("GUI setup complete. Starting the application")
# # Запуск интерфейса
# root.mainloop()
# Изменение интерфейса на размещение в одну строку для каждого фильтра
# Изменение интерфейса на размещение в одну строку для каждого фильтра
# Изменение интерфейса с принудительным выравниванием в строке для каждого фильтра
# Функция для добавления контекстного меню
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


# Функция для отображения календаря и выбора даты
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


# Основное окно
root = Tk()
root.title("Data Fetcher with Filters")

field_vars, condition_vars, value_entries, operator_vars = [], [], [], []

# Создаем фрейм для фильтров
filter_frame = Frame(root)
filter_frame.pack(pady=10, padx=10)

# Создание фильтров
for i in range(5):
    Label(filter_frame, text=f"Фильтр {i + 1}").grid(
        row=i, column=0, padx=5, pady=5, sticky="w"
    )

    # Поле фильтра
    field_var = StringVar(filter_frame)
    field_var.set(FIELDS[0])
    field_vars.append(field_var)
    field_menu = OptionMenu(filter_frame, field_var, *FIELDS)
    field_menu.config(width=15)  # Устанавливаем ширину
    field_menu.grid(row=i, column=1, padx=5, pady=5, sticky="w")

    # Условие фильтра
    condition_var = StringVar(filter_frame)
    condition_var.set(CONDITIONS[0])
    condition_vars.append(condition_var)
    condition_menu = OptionMenu(filter_frame, condition_var, *CONDITIONS)
    condition_menu.config(width=15)  # Устанавливаем ширину
    condition_menu.grid(row=i, column=2, padx=5, pady=5, sticky="w")

    # Значение фильтра
    value_entry = Entry(filter_frame, width=20)  # Устанавливаем ширину
    value_entries.append(value_entry)
    value_entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")

    # Добавляем контекстное меню к полю для ввода значений
    add_context_menu(value_entry)

    # Календарь для поля call_date
    field_var.trace_add(
        "write",
        lambda *args, entry=value_entry, field=field_var: (
            show_calendar(entry) if field.get() == "call_date" else None
        ),
    )

    # Логический оператор (только для первых четырёх фильтров)
    if i < 4:
        operator_var = StringVar(filter_frame)
        operator_var.set(LOGICAL_OPERATORS[0])
        operator_vars.append(operator_var)
        operator_menu = OptionMenu(filter_frame, operator_var, *LOGICAL_OPERATORS)
        operator_menu.config(width=5)  # Устанавливаем ширину
        operator_menu.grid(row=i, column=4, padx=5, pady=5, sticky="w")

# Кнопка получения данных
fetch_button = Button(
    root, text="Получить данные", command=lambda: print("Данные получены")
)
fetch_button.pack(pady=10)

# Поле вывода результатов
result_text = Text(root, wrap="word", width=80, height=20)
result_text.pack(pady=10)

root.mainloop()
