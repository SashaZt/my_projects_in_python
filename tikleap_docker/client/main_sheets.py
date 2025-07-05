import json
import sqlite3
import sys
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from loguru import logger

# Настройка директорий и логирования
# Настройка путей
current_directory = Path.cwd()
parent_directory = current_directory.parent

cookies_directory = parent_directory / "cookies"
cookies_file = cookies_directory / "cookies_important.json"

config_directory = current_directory / "config"
db_directory = current_directory / "db"
json_directory = current_directory / "json"
log_directory = current_directory / "log"
db_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)


output_json_file = json_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"
db_path = db_directory / "tikleap_users.db"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)


# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_config(file):
    """Загружает конфигурацию из JSON файла."""
    with open(file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config(config_file)
cookies = get_config(cookies_file)
cookies_dict = cookies["cookies"]

countries = config["country"]


SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]


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


# Получение листа Google Sheets
sheet = get_google_sheet()


def ensure_row_limit(sheet, required_rows=100000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


ensure_row_limit(sheet, 1000)


def export_unloaded_users_to_google_sheets():
    """
    Функция для выгрузки пользователей, у которых loading_table = False, в Google Sheets
    """
    try:
        logger.info("Выгрузка данных в Google Sheets...")
        if not db_path.exists():
            logger.error(f"База данных не найдена по пути: {db_path}")
            return

        # Подключаемся к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Получаем все записи с loading_table = False
        cursor.execute(
            """
        SELECT current_datetime, country_code, profile_link, rank, earning
        FROM tikleap_users
        WHERE loading_table = 0
        ORDER BY country_code, rank
        """
        )

        unloaded_users = cursor.fetchall()

        if not unloaded_users:
            logger.info("Нет новых записей для выгрузки в Google Sheets")
            conn.close()
            return

        logger.info(
            f"Найдено {len(unloaded_users)} записей для выгрузки в Google Sheets"
        )

        # Получаем лист Google Sheets
        sheet = get_google_sheet()

        # Проверяем, есть ли заголовки
        headers = sheet.row_values(1)
        expected_headers = [
            "Дата добавления",
            "Источник",
            "Ссылка",
            "Место в рейтинге",
            "Заработок",
        ]

        # Если нет заголовков или они не соответствуют ожидаемым, добавляем их
        if not headers or headers != expected_headers:
            sheet.clear()  # Очищаем лист для установки заголовков
            sheet.update(values=[expected_headers], range_name="A1:E1")
            logger.info("Добавлены заголовки в Google Sheets")

        # Находим первую пустую строку
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1

        # Подготавливаем данные для записи
        rows_to_insert = []
        updated_user_ids = []

        for user in unloaded_users:
            rows_to_insert.append(list(user))

            # Получаем ID пользователя для последующего обновления loading_table
            cursor.execute(
                """
            SELECT id FROM tikleap_users 
            WHERE profile_link = ?
            """,
                (user[2],),
            )

            user_id = cursor.fetchone()
            if user_id:
                updated_user_ids.append(user_id[0])

        # Записываем данные в Google Sheets
        if rows_to_insert:
            # Определяем диапазон для записи (A{next_row}:E{next_row+len(rows_to_insert)-1})
            range_to_update = f"A{next_row}:E{next_row+len(rows_to_insert)-1}"

            # Исправлено: сначала values, потом range_name
            sheet.update(values=rows_to_insert, range_name=range_to_update)

            logger.success(
                f"Успешно выгружено {len(rows_to_insert)} записей в Google Sheets"
            )

            # Обновляем флаг loading_table для выгруженных записей
            for user_id in updated_user_ids:
                cursor.execute(
                    """
                UPDATE tikleap_users
                SET loading_table = 1
                WHERE id = ?
                """,
                    (user_id,),
                )

            conn.commit()
            logger.info(
                f"Обновлен статус loading_table для {len(updated_user_ids)} записей"
            )

        # Закрываем соединение с БД
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при выгрузке данных в Google Sheets: {e}")
        logger.exception("Подробная информация об ошибке:")
        # Если возникла ошибка, пытаемся закрыть соединение с БД
        try:
            if "conn" in locals() and conn:
                conn.close()
        except:
            pass


def get_column_b_data(sheet_name="СПИСОК СТРАН ДЛЯ ОБРАБОТКИ"):
    """
    Получает все заполненные значения из колонки B указанного листа.

    Args:
        sheet_name (str): Название листа в Google Sheets

    Returns:
        list: Список всех непустых значений из колонки B
    """
    try:
        # Подключаемся к Google Sheets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(SPREADSHEET)
        worksheet = spreadsheet.worksheet(sheet_name)

        logger.info(f"Успешное подключение к листу '{sheet_name}'")

        # Получаем все значения из колонки B
        column_b_values = worksheet.col_values(2)  # 2 = колонка B

        # Фильтруем пустые значения
        filtered_values = [value.strip() for value in column_b_values if value.strip()]

        logger.info(f"Получено {len(filtered_values)} заполненных строк из колонки B")
        return filtered_values

    except gspread.exceptions.WorksheetNotFound:
        logger.error(f"Лист '{sheet_name}' не найден в таблице")
        raise
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка при получении данных: {e}")
        raise
