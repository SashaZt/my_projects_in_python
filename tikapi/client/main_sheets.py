import asyncio
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import asyncpg
import gspread
from config.logger import logger
from google.oauth2.service_account import Credentials
from loguru import logger

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
# Создание директорий, если они не существуют
config_directory.mkdir(parents=True, exist_ok=True)

# Файлы
service_account_file = config_directory / "credentials.json"
config_file = config_directory / "config.json"


def get_config():
    """Загружает конфигурацию из JSON файла."""
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config()
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


sheet = get_google_sheet()


async def fetch_data():
    # Параметры подключения к базе данных
    dsn = "postgresql://tiktok_user:xnZEuWm3NBu0BR5TU1N5UGWyAPSU6Y@localhost:5432/tiktok_analytics"

    try:
        # Подключение к базе данных
        conn = await asyncpg.connect(dsn)

        # SQL-запрос для извлечения данных
        query = """
        SELECT 
            u.unique_id,
            dla.date,
            dla.diamonds_total,
            dla.live_duration_total
        FROM 
            public.daily_live_analytics dla
        JOIN 
            public.users u ON dla.user_id = u.id
        ORDER BY 
            dla.date, u.unique_id;
        """

        # Выполнение запроса
        rows = await conn.fetch(query)

        # Закрытие соединения
        await conn.close()

        # Форматирование данных для таблицы
        # Группируем данные по датам
        data_by_date = defaultdict(dict)
        unique_ids = set()

        for row in rows:
            unique_id = row["unique_id"]
            date = datetime.fromtimestamp(row["date"]).strftime(
                "%d.%m"
            )  # Формат: DD.MM
            diamonds = row["diamonds_total"]
            duration = row["live_duration_total"]

            unique_ids.add(unique_id)
            data_by_date[date][unique_id] = (diamonds, duration)

        # Сортировка дат и unique_ids
        unique_ids = sorted(unique_ids)
        dates = sorted(
            data_by_date.keys(),
            key=lambda x: (int(x.split(".")[1]), int(x.split(".")[0])),
        )

        headers = ["Дата"]
        for uid in unique_ids:
            headers.extend([uid, "ЗАРАБОТОК", "ВРЕМЯ"])

        # Данные для строк
        table_data = []
        for date in dates:
            row = [date]
            for uid in unique_ids:
                if uid in data_by_date[date]:
                    diamonds, duration = data_by_date[date][uid]
                    row.extend([uid, diamonds, duration])
                else:
                    row.extend([uid, 0, 0])  # Если данных нет, заполняем нули
            table_data.append(row)

        return headers, table_data, unique_ids

    except Exception as e:
        logger.error(f"Ошибка при извлечении данных: {e}")
        return None, None, None


def upload_to_google_sheets(headers, table_data, unique_ids):
    try:
        # Получение листа Google Sheets
        worksheet = sheet

        # Очистка листа перед записью
        worksheet.clear()

        # Правильная сортировка дат в формате DD.MM (день.месяц)
        table_data.sort(
            key=lambda x: (
                int(x[0].split(".")[1]),  # Сначала сортировка по месяцу
                int(x[0].split(".")[0]),  # Затем по дню
            )
        )

        # Готовим данные для выгрузки
        all_values = []

        # Строка с датой
        header_row = ["Дата"]
        # Строка с названиями колонок
        subheader_row = [""]

        # Подготавливаем заголовки для каждого стримера
        merge_cells = []  # Для хранения диапазонов для объединения
        current_col = 1

        def get_column_letter(index):
            """Преобразует числовой индекс в буквенное обозначение столбца Excel."""
            if index <= 0:
                return ""
            result = ""
            while index > 0:
                index -= 1
                result = chr(65 + (index % 26)) + result
                index = index // 26
            return result

        for uid in unique_ids:
            # Добавляем имя стримера и заголовки колонок
            header_row.extend([uid, ""])
            subheader_row.extend(["ЗАРАБОТОК", "ВРЕМЯ"])

            # Формируем диапазон для объединения правильно, используя функцию get_column_letter
            start_col = get_column_letter(current_col + 1)  # B, D, F...
            end_col = get_column_letter(current_col + 2)  # C, E, G...
            merge_cells.append(f"{start_col}1:{end_col}1")

            current_col += 2

        all_values.append(header_row)
        all_values.append(subheader_row)

        # Добавляем данные
        for row_data in table_data:
            date = row_data[0]
            new_row = [date]

            # Формируем строку данных для каждого стримера
            for uid in unique_ids:
                diamonds = 0
                duration = 0

                # Ищем данные для этого стримера в строке
                for j in range(1, len(row_data), 3):
                    if j + 2 < len(row_data) and row_data[j] == uid:
                        diamonds = row_data[j + 1]
                        duration = int(row_data[j + 2])
                        duration = round(duration / 60)
                        break

                new_row.extend([diamonds, duration])

            all_values.append(new_row)

        # Обновляем таблицу одним запросом
        last_col_index = len(all_values[0]) - 1
        last_col = get_column_letter(last_col_index + 1)
        range_name = f"A1:{last_col}{len(all_values)}"

        logger.debug(f"Количество столбцов: {len(all_values[0])}")
        logger.debug(f"Последний столбец: {last_col}")
        logger.debug(f"Диапазон для обновления: {range_name}")

        # Отправляем данные в таблицу
        worksheet.update(values=all_values, range_name=range_name)
        logger.info(f"Данные загружены в Google Sheets. Размер: {range_name}")

        # Объединяем ячейки с помощью batch-запроса вместо индивидуальных запросов
        batch_size = (
            10  # Размер пакета - можно регулировать в зависимости от ограничений API
        )

        # Подготовка batch-запросов для объединения ячеек
        logger.info(
            f"Подготовка пакетных запросов для объединения {len(merge_cells)} ячеек"
        )

        # Разбиваем merge_cells на пакеты
        for i in range(0, len(merge_cells), batch_size):
            batch_chunk = merge_cells[i : i + batch_size]
            logger.info(
                f"Обработка пакета {i//batch_size + 1} из {(len(merge_cells) + batch_size - 1)//batch_size}"
            )

            try:
                # Создаем список запросов для batch_update
                batch_requests = []
                for merge_range in batch_chunk:
                    # Парсим диапазон для разбора на компоненты для API
                    start_cell, end_cell = merge_range.split(":")

                    # Извлекаем координаты из обозначений ячеек
                    start_col_name = "".join([c for c in start_cell if c.isalpha()])
                    start_row = int("".join([c for c in start_cell if c.isdigit()]))

                    end_col_name = "".join([c for c in end_cell if c.isalpha()])
                    end_row = int("".join([c for c in end_cell if c.isdigit()]))

                    # Преобразуем буквенное обозначение в числовое (A=0, B=1, ...)
                    def col_to_num(col_str):
                        num = 0
                        for c in col_str:
                            num = num * 26 + (ord(c.upper()) - ord("A") + 1)
                        return num - 1  # 0-based

                    # Формируем запрос на объединение в формате API
                    batch_requests.append(
                        {
                            "mergeCells": {
                                "range": {
                                    "sheetId": worksheet.id,
                                    "startRowIndex": start_row
                                    - 1,  # API использует 0-based индексы
                                    "endRowIndex": end_row,
                                    "startColumnIndex": col_to_num(start_col_name),
                                    "endColumnIndex": col_to_num(end_col_name) + 1,
                                },
                                "mergeType": "MERGE_ALL",
                            }
                        }
                    )

                # Выполняем batch-запрос
                if batch_requests:
                    logger.info(
                        f"Выполнение пакетного объединения для {len(batch_requests)} диапазонов"
                    )
                    worksheet.spreadsheet.batch_update({"requests": batch_requests})
                    logger.info(f"Пакет {i//batch_size + 1} успешно обработан")

                    # Добавляем задержку между пакетами, чтобы не превысить квоту API
                    if i + batch_size < len(merge_cells):
                        sleep_time = 5  # Увеличенная задержка между пакетами
                        logger.info(
                            f"Ожидание {sleep_time} секунд перед следующим пакетом..."
                        )
                        time.sleep(sleep_time)

            except gspread.exceptions.APIError as e:
                if "429" in str(e):
                    # Если превышена квота API, ждем дольше и повторяем
                    sleep_time = 60  # Гораздо большая задержка при ошибке квоты
                    logger.warning(
                        f"Превышение квоты API при пакетном объединении, ожидание {sleep_time} секунд..."
                    )
                    time.sleep(sleep_time)

                    try:
                        # Повторная попытка с тем же пакетом
                        if batch_requests:
                            worksheet.spreadsheet.batch_update(
                                {"requests": batch_requests}
                            )
                            logger.info(
                                f"Повторная попытка для пакета {i//batch_size + 1} успешна"
                            )
                    except gspread.exceptions.APIError as retry_error:
                        logger.error(
                            f"Не удалось выполнить повторную попытку: {retry_error}"
                        )
                        # Продолжаем с следующим пакетом, не останавливая весь процесс
                else:
                    logger.error(f"Ошибка API при пакетном объединении: {e}")
                    # Продолжаем с следующим пакетом

        logger.info("Данные успешно загружены в Google Sheets и ячейки объединены!")

    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        if "429" in str(e):
            logger.warning("Превышение квоты API, повторяем с задержкой...")
            time.sleep(60)  # Увеличенное время ожидания для полного сброса квоты
            upload_to_google_sheets(
                headers, table_data, unique_ids
            )  # Рекурсивный вызов с задержкой
        else:
            raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке в Google Sheets: {e}")
        raise


async def sheets():
    # Извлечение данных
    headers, table_data, unique_ids = await fetch_data()
    if headers and table_data and unique_ids:
        # Загрузка в Google Sheets
        upload_to_google_sheets(headers, table_data, unique_ids)
    else:
        logger.error("Не удалось извлечь данные для загрузки.")


if __name__ == "__main__":
    asyncio.run(sheets())
