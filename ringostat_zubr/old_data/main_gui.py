import json
from datetime import datetime

import PySimpleGUI as sg
import requests
from configuration.logger_setup import logger

# Конфигурация полей и условий
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


# Функция для применения фильтров (упрощенная для демонстрации)
def apply_combined_filter(data, filters):
    filtered_data = data  # Здесь должна быть логика фильтрации
    return filtered_data


# Основная функция для получения данных с применением фильтров
def fetch_all_data(values):
    url = "https://185.233.116.213:5000/get_all_data"
    # Шифрование ключа доступа и получение данных (упрощено для демонстрации)
    encrypted_key = "example_encrypted_key"
    params = {"access_key": encrypted_key}

    try:
        response = requests.get(url, params=params, verify=False)
        if response.status_code == 200:
            data = response.json().get("data", [])

            # Создаем список фильтров из значений интерфейса
            filters = [
                (
                    values[f"field{i}"],
                    values[f"condition{i}"],
                    values[f"value{i}"],
                    values.get(f"operator{i}"),
                )
                for i in range(5)
            ]

            # Применяем фильтры
            filtered_data = apply_combined_filter(data, filters)
            return json.dumps(filtered_data, ensure_ascii=False, indent=4)
        else:
            return f"Failed to fetch data, status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"


# Настройка интерфейса PySimpleGUI
layout = [
    [
        sg.Text(f"Фильтр {i+1}"),
        sg.Combo(FIELDS, key=f"field{i}", size=(15, 1)),
        sg.Combo(CONDITIONS, key=f"condition{i}", size=(15, 1)),
        sg.InputText(key=f"value{i}", size=(20, 1)),
        (
            sg.Combo(LOGICAL_OPERATORS, key=f"operator{i}", size=(5, 1))
            if i < 4
            else sg.Text("")
        ),
    ]
    for i in range(5)
] + [
    [sg.Button("Получить данные"), sg.Button("Выход")],
    [sg.Multiline(size=(80, 20), key="result", disabled=True)],
]

window = sg.Window("Data Fetcher with Filters", layout)

# Цикл обработки событий интерфейса
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED or event == "Выход":
        break
    elif event == "Получить данные":
        # Получаем данные с фильтрами
        result = fetch_all_data(values)
        window["result"].update(result)

window.close()
