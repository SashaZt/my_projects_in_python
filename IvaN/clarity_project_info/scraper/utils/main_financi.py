# import json
# import psycopg2
# from psycopg2.extras import execute_batch
# import time
# import re
# from datetime import datetime
# import numpy as np
# from config.logger import logger
# import math

# # Параметры подключения к базе данных
# db_params = {
#     "database": "clarity_project_info",
#     "user": "clarity_user",
#     "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
#     "host": "localhost",
#     "port": "5429",
# }

# # Путь к JSON файлу
# JSON_FILE_PATH_FINANCIAL = "financial_data.json"

# # Размер пакета для обработки
# BATCH_SIZE = 10000


# def import_finance_json_to_postgres():
#     """Импортирует финансовые данные из JSON в PostgreSQL"""
#     start_time = time.time()

#     # Счетчики для отслеживания прогресса
#     finances_count = 0
#     companies_created = 0

#     try:
#         # Подключение к БД
#         logger.info("Подключение к базе данных...")
#         conn = psycopg2.connect(**db_params)
#         cursor = conn.cursor()

#         # Проверяем существование таблицы
#         cursor.execute("SELECT to_regclass('public.yearly_finances')")
#         table_exists = cursor.fetchone()[0]

#         if not table_exists:
#             logger.warning("Таблица yearly_finances не существует, создаем...")
#             # Создание таблицы
#             cursor.execute(
#                 """
#             CREATE TABLE yearly_finances (
#                 finance_id SERIAL PRIMARY KEY,
#                 edrpou VARCHAR(20) NOT NULL,
#                 year INTEGER NOT NULL,
#                 number_of_employees INTEGER,
#                 katottg VARCHAR(20),

#                 beginning_of_the_year_1012 NUMERIC,
#                 end_of_the_year_1012 NUMERIC,
#                 beginning_of_the_year_1195 NUMERIC,
#                 end_of_the_year_1195 NUMERIC,
#                 beginning_of_the_year_1495 NUMERIC,
#                 end_of_the_year_1495 NUMERIC,
#                 beginning_of_the_year_1595 NUMERIC,
#                 end_of_the_year_1595 NUMERIC,
#                 beginning_of_the_year_1695 NUMERIC,
#                 end_of_the_year_1695 NUMERIC,
#                 beginning_of_the_year_1900 NUMERIC,
#                 end_of_the_year_1900 NUMERIC,
#                 beginning_of_the_year_2000 NUMERIC,
#                 end_of_the_year_2000 NUMERIC,
#                 beginning_of_the_year_2280 NUMERIC,
#                 end_of_the_year_2280 NUMERIC,
#                 beginning_of_the_year_2285 NUMERIC,
#                 end_of_the_year_2285 NUMERIC,
#                 beginning_of_the_year_2350 NUMERIC,
#                 end_of_the_year_2350 NUMERIC,
#                 beginning_of_the_year_1621 NUMERIC,
#                 end_of_the_year_1621 NUMERIC,
#                 beginning_of_the_year_2465 NUMERIC,
#                 end_of_the_year_2465 NUMERIC,
#                 beginning_of_the_year_2505 NUMERIC,
#                 end_of_the_year_2505 NUMERIC,
#                 beginning_of_the_year_2510 NUMERIC,
#                 end_of_the_year_2510 NUMERIC,
#                 beginning_of_the_year_2355 NUMERIC,
#                 end_of_the_year_2355 NUMERIC,

#                 last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

#                 CONSTRAINT fk_company
#                     FOREIGN KEY (edrpou)
#                     REFERENCES companies (edrpou)
#                     ON DELETE CASCADE,

#                 CONSTRAINT unique_company_year UNIQUE (edrpou, year)
#             )
#             """
#             )

#             # Создание индексов
#             cursor.execute(
#                 "CREATE INDEX idx_yearly_finances_edrpou ON yearly_finances (edrpou)"
#             )
#             cursor.execute(
#                 "CREATE INDEX idx_yearly_finances_year ON yearly_finances (year)"
#             )
#             cursor.execute(
#                 "CREATE INDEX idx_yearly_finances_katottg ON yearly_finances (katottg)"
#             )

#             conn.commit()
#             logger.info("Таблица yearly_finances создана")

#         # Чтение JSON файла по частям
#         logger.info(f"Чтение JSON файла ({JSON_FILE_PATH_FINANCIAL})...")

#         with open(JSON_FILE_PATH_FINANCIAL, "r", encoding="utf-8") as f:
#             all_data = json.load(f)

#         total_rows = len(all_data)
#         logger.info(f"Всего записей в JSON файле: {total_rows}")

#         # Обработка данных пакетами
#         batch_num = 0
#         batch_size = 1000

#         for batch_start in range(0, total_rows, batch_size):
#             batch_start_time = time.time()

#             batch_end = min(batch_start + batch_size, total_rows)
#             json_batch = all_data[batch_start:batch_end]

#             # Подготовка данных для вставки
#             batch_data = []
#             # Словарь для отслеживания EDRPOU, которые нужно создать
#             edrpou_to_create = set()

#             for row in json_batch:
#                 try:
#                     edrpou = row.get("edrpou")

#                     # Пропускаем строки без EDRPOU
#                     if not edrpou:
#                         logger.warning(f"Пропущена строка: отсутствует EDRPOU")
#                         continue

#                     # Проверяем, существует ли компания с таким EDRPOU
#                     cursor.execute(
#                         "SELECT EXISTS(SELECT 1 FROM companies WHERE edrpou = %s)",
#                         (edrpou,),
#                     )
#                     company_exists = cursor.fetchone()[0]

#                     if not company_exists:
#                         # Добавляем EDRPOU в список для создания
#                         edrpou_to_create.add(edrpou)

#                     # Преобразование года в целое число
#                     year = int(row.get("year", 2024))

#                     # Преобразование числовых полей
#                     try:
#                         number_of_employees = (
#                             int(row.get("number_of_employees"))
#                             if row.get("number_of_employees")
#                             else None
#                         )
#                     except (ValueError, TypeError):
#                         number_of_employees = None

#                     # Список всех финансовых показателей
#                     finance_fields = [
#                         "beginning_of_the_year_1012",
#                         "end_of_the_year_1012",
#                         "beginning_of_the_year_1195",
#                         "end_of_the_year_1195",
#                         "beginning_of_the_year_1495",
#                         "end_of_the_year_1495",
#                         "beginning_of_the_year_1595",
#                         "end_of_the_year_1595",
#                         "beginning_of_the_year_1695",
#                         "end_of_the_year_1695",
#                         "beginning_of_the_year_1900",
#                         "end_of_the_year_1900",
#                         "beginning_of_the_year_2000",
#                         "end_of_the_year_2000",
#                         "beginning_of_the_year_2280",
#                         "end_of_the_year_2280",
#                         "beginning_of_the_year_2285",
#                         "end_of_the_year_2285",
#                         "beginning_of_the_year_2350",
#                         "end_of_the_year_2350",
#                         "beginning_of_the_year_1621",
#                         "end_of_the_year_1621",
#                         "beginning_of_the_year_2465",
#                         "end_of_the_year_2465",
#                         "beginning_of_the_year_2505",
#                         "end_of_the_year_2505",
#                         "beginning_of_the_year_2510",
#                         "end_of_the_year_2510",
#                         "beginning_of_the_year_2355",
#                         "end_of_the_year_2355",
#                     ]

#                     # Преобразование всех финансовых показателей в числа
#                     finance_values = []
#                     for field in finance_fields:
#                         value = row.get(field)
#                         # Значение уже должно быть очищено на этапе конвертации Excel в JSON
#                         if value:
#                             try:
#                                 finance_values.append(float(value))
#                             except (ValueError, TypeError):
#                                 finance_values.append(None)
#                         else:
#                             finance_values.append(None)

#                     # Формируем кортеж данных для вставки
#                     finance_data = (
#                         edrpou,
#                         year,
#                         number_of_employees,
#                         row.get("katottg"),
#                         *finance_values,  # Распаковываем все финансовые показатели
#                     )

#                     batch_data.append(finance_data)
#                 except Exception as e:
#                     logger.error(f"Ошибка при обработке строки: {e}, данные: {row}")
#                     continue

#             if batch_data:
#                 try:
#                     # Вставка данных с обработкой конфликтов (UPSERT)
#                     execute_batch(
#                         cursor,
#                         """
#                         INSERT INTO yearly_finances (
#                             edrpou, year, number_of_employees, katottg,
#                             beginning_of_the_year_1012, end_of_the_year_1012,
#                             beginning_of_the_year_1195, end_of_the_year_1195,
#                             beginning_of_the_year_1495, end_of_the_year_1495,
#                             beginning_of_the_year_1595, end_of_the_year_1595,
#                             beginning_of_the_year_1695, end_of_the_year_1695,
#                             beginning_of_the_year_1900, end_of_the_year_1900,
#                             beginning_of_the_year_2000, end_of_the_year_2000,
#                             beginning_of_the_year_2280, end_of_the_year_2280,
#                             beginning_of_the_year_2285, end_of_the_year_2285,
#                             beginning_of_the_year_2350, end_of_the_year_2350,
#                             beginning_of_the_year_1621, end_of_the_year_1621,
#                             beginning_of_the_year_2465, end_of_the_year_2465,
#                             beginning_of_the_year_2505, end_of_the_year_2505,
#                             beginning_of_the_year_2510, end_of_the_year_2510,
#                             beginning_of_the_year_2355, end_of_the_year_2355
#                         ) VALUES (
#                             %s, %s, %s, %s,
#                             %s, %s, %s, %s, %s, %s, %s, %s,
#                             %s, %s, %s, %s, %s, %s, %s, %s,
#                             %s, %s, %s, %s, %s, %s, %s, %s,
#                             %s, %s, %s, %s, %s, %s
#                         )
#                         ON CONFLICT (edrpou, year) DO UPDATE SET
#                             number_of_employees = EXCLUDED.number_of_employees,
#                             katottg = EXCLUDED.katottg,
#                             beginning_of_the_year_1012 = EXCLUDED.beginning_of_the_year_1012,
#                             end_of_the_year_1012 = EXCLUDED.end_of_the_year_1012,
#                             beginning_of_the_year_1195 = EXCLUDED.beginning_of_the_year_1195,
#                             end_of_the_year_1195 = EXCLUDED.end_of_the_year_1195,
#                             beginning_of_the_year_1495 = EXCLUDED.beginning_of_the_year_1495,
#                             end_of_the_year_1495 = EXCLUDED.end_of_the_year_1495,
#                             beginning_of_the_year_1595 = EXCLUDED.beginning_of_the_year_1595,
#                             end_of_the_year_1595 = EXCLUDED.end_of_the_year_1595,
#                             beginning_of_the_year_1695 = EXCLUDED.beginning_of_the_year_1695,
#                             end_of_the_year_1695 = EXCLUDED.end_of_the_year_1695,
#                             beginning_of_the_year_1900 = EXCLUDED.beginning_of_the_year_1900,
#                             end_of_the_year_1900 = EXCLUDED.end_of_the_year_1900,
#                             beginning_of_the_year_2000 = EXCLUDED.beginning_of_the_year_2000,
#                             end_of_the_year_2000 = EXCLUDED.end_of_the_year_2000,
#                             beginning_of_the_year_2280 = EXCLUDED.beginning_of_the_year_2280,
#                             end_of_the_year_2280 = EXCLUDED.end_of_the_year_2280,
#                             beginning_of_the_year_2285 = EXCLUDED.beginning_of_the_year_2285,
#                             end_of_the_year_2285 = EXCLUDED.end_of_the_year_2285,
#                             beginning_of_the_year_2350 = EXCLUDED.beginning_of_the_year_2350,
#                             end_of_the_year_2350 = EXCLUDED.end_of_the_year_2350,
#                             beginning_of_the_year_1621 = EXCLUDED.beginning_of_the_year_1621,
#                             end_of_the_year_1621 = EXCLUDED.end_of_the_year_1621,
#                             beginning_of_the_year_2465 = EXCLUDED.beginning_of_the_year_2465,
#                             end_of_the_year_2465 = EXCLUDED.end_of_the_year_2465,
#                             beginning_of_the_year_2505 = EXCLUDED.beginning_of_the_year_2505,
#                             end_of_the_year_2505 = EXCLUDED.end_of_the_year_2505,
#                             beginning_of_the_year_2510 = EXCLUDED.beginning_of_the_year_2510,
#                             end_of_the_year_2510 = EXCLUDED.end_of_the_year_2510,
#                             beginning_of_the_year_2355 = EXCLUDED.beginning_of_the_year_2355,
#                             end_of_the_year_2355 = EXCLUDED.end_of_the_year_2355,
#                             last_updated = CURRENT_TIMESTAMP
#                         """,
#                         batch_data,
#                         page_size=100,
#                     )

#                     conn.commit()
#                     finances_count += len(batch_data)

#                     batch_num += 1
#                     batch_end_time = time.time()
#                     batch_duration = batch_end_time - batch_start_time

#                     logger.info(
#                         f"Обработан пакет {batch_num}, время: {batch_duration:.2f} сек."
#                     )
#                     logger.info(
#                         f"Обработано {batch_end} из {total_rows} строк ({batch_end*100/total_rows:.2f}%)"
#                     )
#                     logger.info(f"Всего импортировано записей: {finances_count}")

#                 except Exception as e:
#                     logger.error(f"Ошибка при вставке пакета данных: {e}")
#                     conn.rollback()

#         # Создание представления
#         try:
#             cursor.execute("SELECT to_regclass('public.company_financial_summary')")
#             view_exists = cursor.fetchone()[0]

#             if view_exists:
#                 cursor.execute("DROP VIEW IF EXISTS company_financial_summary")

#             cursor.execute(
#                 """
#             CREATE VIEW company_financial_summary AS
#             SELECT
#                 c.edrpou,
#                 c.full_name,
#                 c.short_name,
#                 c.org_form,
#                 c.address,
#                 c.status,
#                 c.status_date,
#                 c.registration_date,
#                 c.email,
#                 yf.year,
#                 yf.number_of_employees,
#                 yf.katottg,
#                 -- Финансовые показатели
#                 yf.beginning_of_the_year_1012,
#                 yf.end_of_the_year_1012,
#                 yf.beginning_of_the_year_1195,
#                 yf.end_of_the_year_1195,
#                 yf.beginning_of_the_year_1495,
#                 yf.end_of_the_year_1495,
#                 yf.beginning_of_the_year_1595,
#                 yf.end_of_the_year_1595,
#                 yf.beginning_of_the_year_1695,
#                 yf.end_of_the_year_1695,
#                 yf.beginning_of_the_year_1900,
#                 yf.end_of_the_year_1900,
#                 yf.beginning_of_the_year_2000,
#                 yf.end_of_the_year_2000,
#                 yf.beginning_of_the_year_2280,
#                 yf.end_of_the_year_2280,
#                 yf.beginning_of_the_year_2285,
#                 yf.end_of_the_year_2285,
#                 yf.beginning_of_the_year_2350,
#                 yf.end_of_the_year_2350,
#                 yf.beginning_of_the_year_1621,
#                 yf.end_of_the_year_1621,
#                 yf.beginning_of_the_year_2465,
#                 yf.end_of_the_year_2465,
#                 yf.beginning_of_the_year_2505,
#                 yf.end_of_the_year_2505,
#                 yf.beginning_of_the_year_2510,
#                 yf.end_of_the_year_2510,
#                 yf.beginning_of_the_year_2355,
#                 yf.end_of_the_year_2355
#             FROM
#                 companies c
#             LEFT JOIN
#                 yearly_finances yf ON c.edrpou = yf.edrpou
#             """
#             )

#             conn.commit()
#             logger.info("Представление company_financial_summary создано/обновлено")

#         except Exception as e:
#             logger.error(f"Ошибка при создании представления: {e}")
#             conn.rollback()

#         end_time = time.time()
#         duration = end_time - start_time

#         logger.info(
#             f"Импорт успешно завершен! Обработано {finances_count} финансовых записей"
#         )
#         logger.info(f"Создано {companies_created} заглушек для компаний")
#         logger.info(f"Время выполнения: {duration:.2f} секунд")

#     except Exception as e:
#         logger.error(f"Ошибка при импорте финансовых данных: {e}")
#         if "conn" in locals() and conn:
#             conn.rollback()
#     finally:
#         if "conn" in locals() and conn:
#             conn.close()
#             logger.info("Соединение с базой данных закрыто")


# # Запуск импорта
# if __name__ == "__main__":
#     import_finance_json_to_postgres()
import json
import psycopg2
from psycopg2.extras import execute_batch
import time
import re
from datetime import datetime
import numpy as np
from config.logger import logger
import math

# Параметры подключения к базе данных
db_params = {
    "database": "clarity_project_info",
    "user": "clarity_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "host": "localhost",
    "port": "5429",
}

# Путь к JSON файлу
JSON_FILE_PATH_FINANCIAL = "financial_data.json"

# Размер пакета для обработки
BATCH_SIZE = 10000


def is_nan_value(value):
    """Проверяет, является ли значение NaN (как строка или как число)"""
    if value == "NaN" or (isinstance(value, float) and math.isnan(value)):
        return True
    return False


def clean_numeric_value(value):
    """Очищает числовое значение от суффиксов и форматирования"""
    if value is None or is_nan_value(value) or value == "":
        return None

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        # Убираем "тис.грн" и другие суффиксы
        value = re.sub(r"тис\.грн$|тис\. грн$|тис\.грн\.?$", "", value)
        # Заменяем запятую на точку (если используется как десятичный разделитель)
        value = value.replace(",", ".")
        # Убираем пробелы между цифрами
        value = "".join(value.split())

        if value == "":
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    return None


def create_or_update_materialized_view(cursor, conn):
    """Создает или обновляет материализованное представление"""
    try:
        # Проверяем существование представления
        cursor.execute("SELECT to_regclass('public.company_financial_summary_mat')")
        view_exists = cursor.fetchone()[0]

        if view_exists:
            # Если представление существует, обновляем его данные
            logger.info(
                "Обновление материализованного представления company_financial_summary_mat"
            )
            cursor.execute("REFRESH MATERIALIZED VIEW company_financial_summary_mat")
        else:
            # Если представления нет, создаем его
            logger.info(
                "Создание материализованного представления company_financial_summary_mat"
            )
            cursor.execute(
                """
            CREATE MATERIALIZED VIEW company_financial_summary_mat AS
            SELECT 
                c.edrpou,
                c.full_name,
                c.short_name,
                c.org_form,
                c.address,
                c.status,
                c.status_date,
                c.registration_date,
                c.email,
                yf.year,
                yf.number_of_employees,
                yf.katottg,
                -- Финансовые показатели
                yf.beginning_of_the_year_1012,
                yf.end_of_the_year_1012,
                yf.beginning_of_the_year_1195,
                yf.end_of_the_year_1195,
                yf.beginning_of_the_year_1495,
                yf.end_of_the_year_1495,
                yf.beginning_of_the_year_1595,
                yf.end_of_the_year_1595,
                yf.beginning_of_the_year_1695,
                yf.end_of_the_year_1695,
                yf.beginning_of_the_year_1900,
                yf.end_of_the_year_1900,
                yf.beginning_of_the_year_2000,
                yf.end_of_the_year_2000,
                yf.beginning_of_the_year_2280,
                yf.end_of_the_year_2280,
                yf.beginning_of_the_year_2285,
                yf.end_of_the_year_2285,
                yf.beginning_of_the_year_2350,
                yf.end_of_the_year_2350,
                yf.beginning_of_the_year_1621,
                yf.end_of_the_year_1621,
                yf.beginning_of_the_year_2465,
                yf.end_of_the_year_2465,
                yf.beginning_of_the_year_2505,
                yf.end_of_the_year_2505,
                yf.beginning_of_the_year_2510,
                yf.end_of_the_year_2510,
                yf.beginning_of_the_year_2355,
                yf.end_of_the_year_2355
            FROM 
                companies c
            LEFT JOIN 
                yearly_finances yf ON c.edrpou = yf.edrpou
            """
            )

            # Создаем индекс для ускорения поиска
            cursor.execute(
                "CREATE INDEX idx_company_financial_summary_mat_edrpou ON company_financial_summary_mat (edrpou)"
            )

        conn.commit()
        logger.info("Материализованное представление создано/обновлено успешно")
        return True

    except Exception as e:
        logger.error(
            f"Ошибка при создании/обновлении материализованного представления: {e}"
        )
        conn.rollback()
        return False


def refresh_materialized_view(concurrently=False):
    """Отдельная функция для обновления материализованного представления"""
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Проверяем существование представления
        cursor.execute("SELECT to_regclass('public.company_financial_summary_mat')")
        view_exists = cursor.fetchone()[0]

        if view_exists:
            if concurrently:
                # Проверяем наличие уникального индекса
                cursor.execute(
                    """
                SELECT COUNT(*) FROM pg_indexes 
                WHERE indexname LIKE 'idx_company_financial_summary_mat%' 
                AND indexdef LIKE '%UNIQUE%'
                """
                )
                has_unique_index = cursor.fetchone()[0] > 0

                if not has_unique_index:
                    logger.warning(
                        "Для параллельного обновления требуется уникальный индекс. Создание индекса..."
                    )
                    cursor.execute(
                        """
                    CREATE UNIQUE INDEX idx_company_financial_summary_mat_uniq 
                    ON company_financial_summary_mat (edrpou, year)
                    """
                    )
                    conn.commit()

                logger.info(
                    "Параллельное обновление материализованного представления..."
                )
                cursor.execute(
                    "REFRESH MATERIALIZED VIEW CONCURRENTLY company_financial_summary_mat"
                )
            else:
                logger.info("Обновление материализованного представления...")
                cursor.execute(
                    "REFRESH MATERIALIZED VIEW company_financial_summary_mat"
                )

            conn.commit()
            logger.info("Материализованное представление успешно обновлено")
            return True
        else:
            logger.error("Материализованное представление не существует")
            return False

    except Exception as e:
        logger.error(f"Ошибка при обновлении материализованного представления: {e}")
        if "conn" in locals() and conn:
            conn.rollback()
        return False
    finally:
        if "conn" in locals() and conn:
            conn.close()


def detect_finance_json_format(json_data):
    """Определяет формат JSON с финансовыми данными"""
    if not json_data:
        return "unknown"

    # Берем первую запись с данными для проверки
    sample = None
    for item in json_data:
        if len(item) > 3:  # Ищем запись с финансовыми данными
            sample = item
            break

    if not sample:
        sample = json_data[0]

    # Проверяем наличие ключевых полей
    if "page_title" in sample:
        return "page_title"
    elif "edrpou" in sample:
        return "edrpou"
    else:
        return "unknown"


def extract_finance_data(row, format_type="edrpou", default_year=2024):
    """Извлекает данные из JSON в зависимости от формата"""
    try:
        # В зависимости от формата получаем EDRPOU
        if format_type == "page_title":
            edrpou = row.get("page_title")
        else:  # format_type == "edrpou" или другой
            edrpou = row.get("edrpou")

        # Если EDRPOU отсутствует, пропускаем запись
        if not edrpou:
            return None

        # Очищаем EDRPOU от пробелов и других символов
        edrpou = re.sub(r"\s+", "", str(edrpou))

        # Получаем остальные данные
        year = int(row.get("year", default_year))

        # Пробуем получить и преобразовать number_of_employees
        try:
            number_of_employees = (
                int(row.get("number_of_employees"))
                if row.get("number_of_employees")
                else None
            )
        except (ValueError, TypeError):
            number_of_employees = None

        katottg = row.get("katottg")

        # Список всех финансовых показателей
        finance_fields = [
            "beginning_of_the_year_1012",
            "end_of_the_year_1012",
            "beginning_of_the_year_1195",
            "end_of_the_year_1195",
            "beginning_of_the_year_1495",
            "end_of_the_year_1495",
            "beginning_of_the_year_1595",
            "end_of_the_year_1595",
            "beginning_of_the_year_1695",
            "end_of_the_year_1695",
            "beginning_of_the_year_1900",
            "end_of_the_year_1900",
            "beginning_of_the_year_2000",
            "end_of_the_year_2000",
            "beginning_of_the_year_2280",
            "end_of_the_year_2280",
            "beginning_of_the_year_2285",
            "end_of_the_year_2285",
            "beginning_of_the_year_2350",
            "end_of_the_year_2350",
            "beginning_of_the_year_1621",
            "end_of_the_year_1621",
            "beginning_of_the_year_2465",
            "end_of_the_year_2465",
            "beginning_of_the_year_2505",
            "end_of_the_year_2505",
            "beginning_of_the_year_2510",
            "end_of_the_year_2510",
            "beginning_of_the_year_2355",
            "end_of_the_year_2355",
        ]

        # Преобразование всех финансовых показателей в числа
        finance_values = []
        for field in finance_fields:
            value = clean_numeric_value(row.get(field))
            finance_values.append(value)

        # Формируем кортеж данных для вставки
        finance_data = (
            edrpou,
            year,
            number_of_employees,
            katottg,
            *finance_values,  # Распаковываем все финансовые показатели
        )

        return finance_data

    except Exception as e:
        logger.error(f"Ошибка при извлечении финансовых данных: {e}, данные: {row}")
        return None


def prepare_company_stubs(cursor, edrpou_list):
    """Проверяет наличие компаний в базе и создает заглушки для отсутствующих"""
    if not edrpou_list:
        return 0

    # Получаем список существующих EDRPOU
    placeholders = ",".join(["%s"] * len(edrpou_list))
    cursor.execute(
        f"SELECT edrpou FROM companies WHERE edrpou IN ({placeholders})", edrpou_list
    )
    existing_edrpou = {row[0] for row in cursor.fetchall()}

    # Находим EDRPOU, которых нет в базе
    missing_edrpou = [edrpou for edrpou in edrpou_list if edrpou not in existing_edrpou]

    if not missing_edrpou:
        return 0

    # Создаем заглушки для отсутствующих компаний
    company_data = [
        (edrpou, f"Компания {edrpou} (автоматически создана)")
        for edrpou in missing_edrpou
    ]

    execute_batch(
        cursor,
        """
        INSERT INTO companies (edrpou, full_name, last_updated) 
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (edrpou) DO NOTHING
        """,
        company_data,
        page_size=100,
    )

    return len(missing_edrpou)


def process_finance_batch(batch_data, cursor, conn):
    """Обрабатывает пакет финансовых данных"""
    if not batch_data:
        return 0, 0

    # Получаем список всех EDRPOU из пакета
    edrpou_list = [data[0] for data in batch_data if data]

    # Создаем заглушки для компаний, которых нет в базе
    # stubs_created = prepare_company_stubs(cursor, edrpou_list)

    # Вставка финансовых данных
    try:
        execute_batch(
            cursor,
            """
            INSERT INTO yearly_finances (
                edrpou, year, number_of_employees, katottg,
                beginning_of_the_year_1012, end_of_the_year_1012,
                beginning_of_the_year_1195, end_of_the_year_1195,
                beginning_of_the_year_1495, end_of_the_year_1495,
                beginning_of_the_year_1595, end_of_the_year_1595,
                beginning_of_the_year_1695, end_of_the_year_1695,
                beginning_of_the_year_1900, end_of_the_year_1900,
                beginning_of_the_year_2000, end_of_the_year_2000,
                beginning_of_the_year_2280, end_of_the_year_2280,
                beginning_of_the_year_2285, end_of_the_year_2285,
                beginning_of_the_year_2350, end_of_the_year_2350,
                beginning_of_the_year_1621, end_of_the_year_1621,
                beginning_of_the_year_2465, end_of_the_year_2465,
                beginning_of_the_year_2505, end_of_the_year_2505,
                beginning_of_the_year_2510, end_of_the_year_2510,
                beginning_of_the_year_2355, end_of_the_year_2355
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (edrpou, year) DO UPDATE SET
                number_of_employees = EXCLUDED.number_of_employees,
                katottg = EXCLUDED.katottg,
                beginning_of_the_year_1012 = EXCLUDED.beginning_of_the_year_1012,
                end_of_the_year_1012 = EXCLUDED.end_of_the_year_1012,
                beginning_of_the_year_1195 = EXCLUDED.beginning_of_the_year_1195,
                end_of_the_year_1195 = EXCLUDED.end_of_the_year_1195,
                beginning_of_the_year_1495 = EXCLUDED.beginning_of_the_year_1495,
                end_of_the_year_1495 = EXCLUDED.end_of_the_year_1495,
                beginning_of_the_year_1595 = EXCLUDED.beginning_of_the_year_1595,
                end_of_the_year_1595 = EXCLUDED.end_of_the_year_1595,
                beginning_of_the_year_1695 = EXCLUDED.beginning_of_the_year_1695,
                end_of_the_year_1695 = EXCLUDED.end_of_the_year_1695,
                beginning_of_the_year_1900 = EXCLUDED.beginning_of_the_year_1900,
                end_of_the_year_1900 = EXCLUDED.end_of_the_year_1900,
                beginning_of_the_year_2000 = EXCLUDED.beginning_of_the_year_2000,
                end_of_the_year_2000 = EXCLUDED.end_of_the_year_2000,
                beginning_of_the_year_2280 = EXCLUDED.beginning_of_the_year_2280,
                end_of_the_year_2280 = EXCLUDED.end_of_the_year_2280,
                beginning_of_the_year_2285 = EXCLUDED.beginning_of_the_year_2285,
                end_of_the_year_2285 = EXCLUDED.end_of_the_year_2285,
                beginning_of_the_year_2350 = EXCLUDED.beginning_of_the_year_2350,
                end_of_the_year_2350 = EXCLUDED.end_of_the_year_2350,
                beginning_of_the_year_1621 = EXCLUDED.beginning_of_the_year_1621,
                end_of_the_year_1621 = EXCLUDED.end_of_the_year_1621,
                beginning_of_the_year_2465 = EXCLUDED.beginning_of_the_year_2465,
                end_of_the_year_2465 = EXCLUDED.end_of_the_year_2465,
                beginning_of_the_year_2505 = EXCLUDED.beginning_of_the_year_2505,
                end_of_the_year_2505 = EXCLUDED.end_of_the_year_2505,
                beginning_of_the_year_2510 = EXCLUDED.beginning_of_the_year_2510,
                end_of_the_year_2510 = EXCLUDED.end_of_the_year_2510,
                beginning_of_the_year_2355 = EXCLUDED.beginning_of_the_year_2355,
                end_of_the_year_2355 = EXCLUDED.end_of_the_year_2355,
                last_updated = CURRENT_TIMESTAMP
            """,
            batch_data,
            page_size=100,
        )

        conn.commit()
        # return len(batch_data), stubs_created
        return len(batch_data)

    except Exception as e:
        logger.error(f"Ошибка при вставке финансовых данных: {e}")
        conn.rollback()
        # return 0, stubs_created
        return 0


def import_finance_json_to_postgres(
    json_file_path=None, batch_size=1000, default_year=2024
):
    """Импортирует финансовые данные из JSON в PostgreSQL"""
    if json_file_path is None:
        json_file_path = JSON_FILE_PATH_FINANCIAL

    start_time = time.time()

    # Счетчики для отслеживания прогресса
    finances_count = 0
    companies_created = 0

    try:
        # Подключение к БД
        logger.info("Подключение к базе данных...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute("SELECT to_regclass('public.yearly_finances')")
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            logger.warning("Таблица yearly_finances не существует, создаем...")
            # Создание таблицы
            cursor.execute(
                """
            CREATE TABLE yearly_finances (
                finance_id SERIAL PRIMARY KEY,
                edrpou VARCHAR(20) NOT NULL,
                year INTEGER NOT NULL,
                number_of_employees INTEGER,
                katottg VARCHAR(20),
                
                beginning_of_the_year_1012 NUMERIC,
                end_of_the_year_1012 NUMERIC,
                beginning_of_the_year_1195 NUMERIC,
                end_of_the_year_1195 NUMERIC,
                beginning_of_the_year_1495 NUMERIC,
                end_of_the_year_1495 NUMERIC,
                beginning_of_the_year_1595 NUMERIC,
                end_of_the_year_1595 NUMERIC,
                beginning_of_the_year_1695 NUMERIC,
                end_of_the_year_1695 NUMERIC,
                beginning_of_the_year_1900 NUMERIC,
                end_of_the_year_1900 NUMERIC,
                beginning_of_the_year_2000 NUMERIC,
                end_of_the_year_2000 NUMERIC,
                beginning_of_the_year_2280 NUMERIC,
                end_of_the_year_2280 NUMERIC,
                beginning_of_the_year_2285 NUMERIC,
                end_of_the_year_2285 NUMERIC,
                beginning_of_the_year_2350 NUMERIC,
                end_of_the_year_2350 NUMERIC,
                beginning_of_the_year_1621 NUMERIC,
                end_of_the_year_1621 NUMERIC,
                beginning_of_the_year_2465 NUMERIC,
                end_of_the_year_2465 NUMERIC,
                beginning_of_the_year_2505 NUMERIC,
                end_of_the_year_2505 NUMERIC,
                beginning_of_the_year_2510 NUMERIC,
                end_of_the_year_2510 NUMERIC,
                beginning_of_the_year_2355 NUMERIC,
                end_of_the_year_2355 NUMERIC,
                
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_company
                    FOREIGN KEY (edrpou)
                    REFERENCES companies (edrpou)
                    ON DELETE CASCADE,
                    
                CONSTRAINT unique_company_year UNIQUE (edrpou, year)
            )
            """
            )

            # Создание индексов
            cursor.execute(
                "CREATE INDEX idx_yearly_finances_edrpou ON yearly_finances (edrpou)"
            )
            cursor.execute(
                "CREATE INDEX idx_yearly_finances_year ON yearly_finances (year)"
            )
            cursor.execute(
                "CREATE INDEX idx_yearly_finances_katottg ON yearly_finances (katottg)"
            )

            conn.commit()
            logger.info("Таблица yearly_finances создана")

        # Чтение JSON файла
        logger.info(f"Чтение JSON файла ({json_file_path})...")

        with open(json_file_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        total_rows = len(all_data)
        logger.info(f"Всего записей в JSON файле: {total_rows}")

        # Определяем формат данных
        json_format = detect_finance_json_format(all_data)
        logger.info(f"Определен формат данных: {json_format}")

        # Обработка данных пакетами
        batch_num = 0

        for batch_start in range(0, total_rows, batch_size):
            batch_start_time = time.time()

            batch_end = min(batch_start + batch_size, total_rows)
            json_batch = all_data[batch_start:batch_end]

            # Подготовка данных для вставки
            batch_data = []

            for row in json_batch:
                finance_data = extract_finance_data(row, json_format, default_year)
                if finance_data:
                    batch_data.append(finance_data)

            # Обработка пакета данных
            if batch_data:
                # records_inserted, stubs_created = process_finance_batch(
                #     batch_data, cursor, conn
                # )
                records_inserted = process_finance_batch(batch_data, cursor, conn)
                finances_count += records_inserted
                # companies_created += stubs_created

            batch_num += 1
            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time

            logger.info(
                f"Обработан пакет {batch_num}, время: {batch_duration:.2f} сек."
            )
            logger.info(
                f"Обработано {batch_end} из {total_rows} строк ({batch_end*100/total_rows:.2f}%)"
            )
            logger.info(f"Всего импортировано записей: {finances_count}")

        # Создание или обновление материализованного представления
        create_or_update_materialized_view(cursor, conn)

        end_time = time.time()
        duration = end_time - start_time

        logger.info(
            f"Импорт успешно завершен! Обработано {finances_count} финансовых записей"
        )
        logger.info(f"Создано {companies_created} заглушек для компаний")
        logger.info(f"Время выполнения: {duration:.2f} секунд")

    except Exception as e:
        logger.error(f"Ошибка при импорте финансовых данных: {e}")
        if "conn" in locals() and conn:
            conn.rollback()
    finally:
        if "conn" in locals() and conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто")


# Запуск импорта
if __name__ == "__main__":
    import_finance_json_to_postgres()
