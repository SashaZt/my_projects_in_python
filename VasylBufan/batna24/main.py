import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import gspread
import requests
from google.oauth2.service_account import Credentials
from loguru import logger

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
log_directory = current_directory / "log"

# Создание директорий, если они не существуют
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

# Файлы
output_xml_file = data_directory / "output.xml"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"

# Настройка логгера
logger.remove()
# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]
# Добавьте URL в конфигурацию вместо жесткого кодирования
XML_URL = config.get("xml", {}).get(
    "url",
    "https://v5.batna24.com/file/c2cf6c76e3-c2cf6c76e3dbbc52d27a679845b4997d289289425fa10b8ec8cb81051fe15405.xml",
)


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


def ensure_row_limit(sheet, required_rows=10000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


def update_sheet_with_data(sheet, data, total_rows=8000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Добавление пустых строк до общего количества total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A2:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")
    logger.info(f"Обновлено {len(data)} строк в Google Sheets")


def download_xml():
    """Скачивает XML файл по указанному URL."""
    headers = {
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    try:
        logger.info(f"Начинаем скачивание XML с {XML_URL}")
        response = requests.get(
            XML_URL,
            headers=headers,
            timeout=100,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(output_xml_file, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {output_xml_file}")
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")
            raise Exception(f"Ошибка при скачивании файла: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        raise


def parsing_xml():
    """Парсит XML файл и возвращает данные о продуктах."""
    logger.info("Начинаем парсинг XML файла")
    try:
        # Открываем и читаем XML файл
        with open(output_xml_file, "r", encoding="utf-8") as file:
            xml_content = file.read()

        # Парсим XML контент
        root = ET.fromstring(xml_content)

        # Создаем список для хранения словарей с данными о каждом продукте
        products_list = []

        # Итерируем по элементам <product>
        for product in root.findall("product"):
            # Создаем словарь для хранения данных о текущем продукте
            product_dict = {}

            # Извлекаем нужные поля
            product_dict["Назва"] = (
                product.find("Name").text if product.find("Name") is not None else ""
            )
            product_dict["Ціна"] = (
                product.find("NetPrice").text.replace(".", ",")
                if product.find("NetPrice") is not None
                else ""
            )
            product_dict["Код"] = (
                product.find("ProductCode").text
                if product.find("ProductCode") is not None
                else ""
            )
            # Сначала получаем строковое значение
            quantity_str = (
                product.find("Quantity").text
                if product.find("Quantity") is not None
                else "0"
            )
            # Затем преобразуем в целое число (с проверкой пустой строки)
            quantity_int = int(quantity_str) if quantity_str.strip() else 0
            # Теперь определяем статус наличия
            if quantity_int > 0:
                availability = "В наявності"
            else:
                availability = "Немає в наявності"
            product_dict["Наявність"] = availability

            # Добавляем словарь с данными о текущем продукте в список
            products_list.append(product_dict)

        logger.info(f"Успешно обработано {len(products_list)} продуктов")
        return products_list
    except Exception as e:
        logger.error(f"Ошибка при парсинге XML: {e}")
        raise


def main():
    """Основная функция программы."""
    try:
        # Получение листа Google Sheets
        sheet = get_google_sheet()

        # Обеспечение достаточного количества строк
        ensure_row_limit(sheet, 1000)

        # Скачивание XML
        download_xml()

        # Парсинг XML и получение данных
        products_data = parsing_xml()

        # Обновление данных в Google Sheets
        update_sheet_with_data(sheet, products_data)

        logger.info("Программа успешно завершена")
    except Exception as e:
        logger.error(f"Программа завершилась с ошибкой: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
