import requests
from configuration.logger_setup import logger
import xml.etree.ElementTree as ET
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)



SPREADSHEET = os.getenv("SPREADSHEET")
SHEET = os.getenv("SHEET")
time_a = os.getenv("TIME_A")
time_b = os.getenv("TIME_B")
BATCH_SIZE = os.getenv("BATCH_SIZE")
PAUSE_DURATION = os.getenv("PAUSE_DURATION")
# Путь к папкам и файлу для данных
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
service_account_file = configuration_directory / "credentials.json"


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Настройка доступа и авторизация
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_file, scope)
        client = gspread.authorize(creds)

        # Открыть таблицу по ключу
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Все нормально, получили spreadsheet")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        raise FileNotFoundError("Файл credentials.json не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


# Получение листа Google Sheets
sheet = get_google_sheet()

def download_xml():
    save_path = "sitemap.xml"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "max-age=0",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://ramiz.pl/xml?key=94255d59993348493376710e55697842&lang=pl&curr=pln",
        headers=headers,
        timeout=200,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен в: {save_path}")
    else:
        logger.error(f"Ошибка при скачивании файла: {response.status_code}")

# Функция для парсинга XML и извлечения данных
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Извлечение данных из XML
    items = []
    for item in root.findall('item'):
        # Проверка на наличие элемента и текста
        prod_name = item.find('prod_name').text.strip() if item.find('prod_name') is not None and item.find('prod_name').text is not None else ""
        prod_symbol = item.find('prod_symbol').text.strip() if item.find('prod_symbol') is not None and item.find('prod_symbol').text is not None else ""
        prod_ean = item.find('prod_ean').text.strip() if item.find('prod_ean') is not None and item.find('prod_ean').text is not None else ""
        prod_tax_id = item.find('prod_tax_id').text.strip().replace('.', ',')  if item.find('prod_tax_id') is not None and item.find('prod_tax_id').text is not None else "0"
        prod_amount = item.find('prod_amount').text.strip() if item.find('prod_amount') is not None and item.find('prod_amount').text is not None else "0"
        
        # items.append([prod_name, prod_symbol, prod_ean, prod_tax_id, prod_amount])
        result = {
            "Назва": prod_name,
            "Kod produktu": prod_symbol,
            "EAN": prod_ean,
            "Price netto": prod_tax_id,
            "Quantity": prod_amount,
        }
        items.append(result)
    update_sheet_with_data(sheet, items)
    return items
# Функция для сохранения данных в CSV
def save_to_csv(data, csv_file_path):
    # Заголовки столбцов
    headers = ["Назва", "Kod produktu", "EAN", "Price netto", "Quantity"]
    
    # Создание DataFrame и сохранение в CSV
    df = pd.DataFrame(data, columns=headers)
    df.to_csv(csv_file_path, index=False, encoding="utf-8-sig")
    print(f"Данные успешно сохранены в {csv_file_path}")

def ensure_row_limit(sheet, required_rows=8000):
    """Увеличивает количество строк в листе Google Sheets, если оно меньше требуемого.

    Args:
        sheet: Объект листа Google Sheets, в котором будет проверяться количество строк.
        required_rows (int): Минимальное количество строк, которое должно быть в листе.
    """
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


# Увеличиваем количество строк до 1500, если необходимо
ensure_row_limit(sheet, 8000)

# Функция для записи данных в указанные столбцы листа Google Sheets с использованием пакетного обновления
def update_sheet_with_data(sheet, data, total_rows=8000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления.

    Для каждой записи в `data`, функция формирует строки данных и обновляет соответствующие столбцы,
    начиная со второй строки листа Google Sheets. Обновления выполняются пакетно для повышения эффективности.

    Args:
        sheet: Объект листа Google Sheets, в который будет производиться запись.
        data (list of dict): Список словарей, содержащих данные для обновления.
        total_rows (int, optional): Общее количество строк, включая пустые строки для заполнения листа. По умолчанию 1500.

    Raises:
        ValueError: Если список данных пуст.

    Примечания:
        - Заголовки формируются из ключей словарей `data` и записываются в первую строку листа.
        - Если данных меньше `total_rows`, добавляются пустые строки для достижения указанного количества.
        - Данные записываются с использованием диапазона от A2 до указанного столбца и строки.
        - Параметр `value_input_option="USER_ENTERED"` используется для того, чтобы значения воспринимались так, как если бы они вводились пользователем, что позволяет интерпретировать формулы и форматировать данные.
        - Пустая директория `html_dir` удаляется после завершения обновления.
    """
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Получаем заголовки из ключей словаря
    headers = list(data[0].keys())

    # Записываем заголовки в первую строку
    sheet.update(range_name="A1", values=[headers], value_input_option="RAW")

    # Формируем данные для записи
    rows = []
    for entry in data:
        row = [entry.get(header, "") for header in headers]
        rows.append(row)

    # Добавляем пустые строки, если их меньше total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)  # Пустая строка с нужным числом столбцов
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Записываем данные начиная со второй строки
    end_col = chr(
        65 + len(headers) - 1
    )  # Преобразуем номер колонки в букву (например, A, B, C)
    range_name = (
        f"A2:{end_col}{total_rows + 1}"  # Диапазон включает заголовок и 1500 строк
    )
    sheet.update(range_name=range_name, values=rows, value_input_option="USER_ENTERED")

if __name__ == "__main__":
    download_xml()
    # Путь к XML-файлу
    xml_file_path = "sitemap.xml"
    # Путь для сохранения CSV-файла
    csv_file_path = "products.csv"
    
    # Извлечение данных из XML
    extracted_data = parse_xml(xml_file_path)
    # Сохранение данных в CSV
    # save_to_csv(extracted_data, csv_file_path)
