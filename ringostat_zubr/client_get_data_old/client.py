import json
from tkinter import END

import requests
import urllib3
from config import ORIGINAL_ACCESS_KEY  # Подключаем ORIGINAL_ACCESS_KEY из config.py
from configuration.logger_setup import logger
from encryption import encrypt_access_key

# Отключаем предупреждения о небезопасных соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_all_data(
    result_text, field_vars, condition_vars, value_entries, operator_vars
):
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

            # Сбор данных из всех фильтров
            filters = [
                (
                    field_vars[i].get(),
                    condition_vars[i].get(),
                    value_entries[i].get(),
                    operator_vars[i].get() if i < 4 else None,
                )
                for i in range(5)
            ]

            # Сохранение отфильтрованных данных в JSON-файл для отладки
            with open("response_debug.json", "w", encoding="utf-8") as f:
                json.dump(filters, f, ensure_ascii=False, indent=4)
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


# def fetch_all_data(
#     result_text, field_vars, condition_vars, value_entries, operator_vars
# ):
#     url = "https://185.233.116.213:5000/get_all_data"
#     encrypted_key = encrypt_access_key(
#         ORIGINAL_ACCESS_KEY
#     )  # Используем ORIGINAL_ACCESS_KEY
#     params = {"access_key": encrypted_key}

#     try:
#         logger.info("Sending GET request to the server")
#         # Добавляем verify=False, чтобы отключить проверку SSL, и подавляем предупреждение
#         response = requests.get(url, params=params, verify=False)
#         result_text.delete(1.0, END)

#         if response.status_code == 200:
#             logger.info("Data fetched successfully")
#             data = response.json().get("data", [])
#             # Логика применения фильтров может быть добавлена здесь, если требуется
#             return data
#         else:
#             logger.warning(f"Failed to fetch data, status code: {response.status_code}")
#             result_text.insert(
#                 END, f"Failed to fetch data, status code: {response.status_code}\n"
#             )
#             result_text.insert(END, response.json())

#     except requests.exceptions.RequestException as e:
#         logger.error(f"An error occurred during the GET request: {e}")
#         result_text.delete(1.0, END)
#         result_text.insert(END, f"An error occurred: {e}")
