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
# JSON_FILE_PATH_EDRPO = "edrpo_data.json"

# # Размер пакета для обработки
# BATCH_SIZE = 10000


# def is_nan_value(value):
#     """Проверяет, является ли значение NaN (как строка или как число)"""
#     if value == "NaN" or (isinstance(value, float) and math.isnan(value)):
#         return True
#     return False


# def safe_str(value):
#     """Безопасно преобразует значение в строку или None"""
#     if value is None or is_nan_value(value) or value == "":
#         return None
#     return str(value).strip()


# def parse_date(date_str):
#     """Конвертирует строку даты в объект date, либо None если невозможно преобразовать"""
#     if date_str is None or is_nan_value(date_str) or date_str == "":
#         return None

#     try:
#         return datetime.strptime(date_str, "%d.%m.%Y").date()
#     except (ValueError, TypeError):
#         logger.warning(f"Не удалось преобразовать дату: {date_str}")
#         return None


# def parse_activity_types(activity_text):
#     """Парсит строку с видами деятельности на отдельные записи"""
#     if activity_text is None or is_nan_value(activity_text) or activity_text == "":
#         return []

#     activities = []
#     try:
#         patterns = re.findall(r"(\d+\.\d+(?:\s*\.\s*\d+)?\s+[^;]+)", str(activity_text))

#         for pattern in patterns:
#             parts = pattern.strip().split(None, 1)
#             if len(parts) >= 2:
#                 code = parts[0].strip()
#                 description = parts[1].strip()
#                 activities.append((code, description))
#             else:
#                 activities.append((None, pattern.strip()))

#         if not activities and activity_text:
#             activities.append((None, str(activity_text).strip()))
#     except Exception as e:
#         logger.warning(f"Ошибка при парсинге видов деятельности: {e}")

#     return activities


# def parse_authorized_persons(persons_text):
#     """Парсит строку с уполномоченными лицами на отдельные записи"""
#     if persons_text is None or is_nan_value(persons_text) or persons_text == "":
#         return []

#     persons = []
#     try:
#         for person_info in re.split(r"[,;]\s*", str(persons_text)):
#             if "-" in person_info:
#                 parts = person_info.split("-", 1)
#                 full_name = parts[0].strip()
#                 position = parts[1].strip() if len(parts) > 1 else None
#                 persons.append((full_name, position))
#             else:
#                 if person_info.strip():
#                     persons.append((person_info.strip(), None))
#     except Exception as e:
#         logger.warning(f"Ошибка при парсинге уполномоченных лиц: {e}")

#     return persons


# def parse_phones(phones_text):
#     """Парсит строку с телефонами на отдельные записи"""
#     if phones_text is None or is_nan_value(phones_text) or phones_text == "":
#         return []

#     phones = []
#     try:
#         for phone in re.split(r"[,;]\s*", str(phones_text)):
#             if phone.strip():
#                 phones.append(phone.strip())
#     except Exception as e:
#         logger.warning(f"Ошибка при парсинге телефонов: {e}")

#     return phones


# def process_json_batch_edrpo(
#     json_data,
#     cursor,
#     conn,
#     company_count=0,
#     phone_count=0,
#     person_count=0,
#     activity_count=0,
# ):
#     """Обрабатывает пакет JSON данных и записывает их в базу данных"""
#     companies_data = []

#     # Обработка компаний
#     for row in json_data:
#         try:
#             # Получаем данные из строки с обработкой исключений
#             edrpou = safe_str(row.get("edrpou"))

#             # Пропускаем строки без EDRPOU
#             if not edrpou:
#                 logger.warning(f"Пропущена строка: отсутствует EDRPOU")
#                 continue

#             full_name = safe_str(row.get("full_name"))
#             short_name = safe_str(row.get("short_name"))
#             org_form = safe_str(row.get("org_form"))
#             address = safe_str(row.get("address"))
#             status = safe_str(row.get("status"))

#             # Преобразование дат
#             status_date = parse_date(row.get("status_date"))
#             registration_date = parse_date(row.get("registration_date"))
#             email = safe_str(row.get("email"))

#             # Добавляем данные в список для batch-вставки
#             companies_data.append(
#                 (
#                     edrpou,
#                     full_name,
#                     short_name,
#                     org_form,
#                     address,
#                     status,
#                     status_date,
#                     registration_date,
#                     email,
#                 )
#             )
#         except Exception as e:
#             logger.error(f"Ошибка при обработке строки: {e}, строка: {row}")
#             continue

#     # Вставка данных в основную таблицу
#     if companies_data:
#         try:
#             execute_batch(
#                 cursor,
#                 """
#                 INSERT INTO companies (
#                     edrpou, full_name, short_name, org_form, address,
#                     status, status_date, registration_date, email
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 ON CONFLICT (edrpou) DO UPDATE SET
#                     full_name = EXCLUDED.full_name,
#                     short_name = EXCLUDED.short_name,
#                     org_form = EXCLUDED.org_form,
#                     address = EXCLUDED.address,
#                     status = EXCLUDED.status,
#                     status_date = EXCLUDED.status_date,
#                     registration_date = EXCLUDED.registration_date,
#                     email = EXCLUDED.email,
#                     last_updated = CURRENT_TIMESTAMP
#                 """,
#                 companies_data,
#                 page_size=100,
#             )
#             conn.commit()

#             # Обновляем счетчик
#             company_count += len(companies_data)

#             # Обработка связанных данных
#             phones_data = []
#             persons_data = []
#             activities_data = []

#             # Получаем список EDRPOU для обработанных компаний
#             valid_edrpous = [item[0] for item in companies_data]

#             # Обработка каждой строки для создания связанных данных
#             for row in json_data:
#                 try:
#                     edrpou = safe_str(row.get("edrpou"))

#                     # Пропускаем строки без EDRPOU или компании, которые не были добавлены
#                     if not edrpou or edrpou not in valid_edrpous:
#                         continue

#                     # Обрабатываем телефоны
#                     for phone in parse_phones(row.get("phones")):
#                         phones_data.append((edrpou, phone))
#                         phone_count += 1

#                     # Обрабатываем уполномоченных лиц
#                     for name, position in parse_authorized_persons(
#                         row.get("authorized_persons")
#                     ):
#                         persons_data.append((edrpou, name, position))
#                         person_count += 1

#                     # Обрабатываем виды деятельности
#                     for code, description in parse_activity_types(
#                         row.get("activity_types")
#                     ):
#                         activities_data.append((edrpou, code, description))
#                         activity_count += 1

#                 except Exception as e:
#                     logger.error(f"Ошибка при обработке связанных данных: {e}")
#                     continue

#             # Получаем все уникальные edrpou из обработанных данных
#             all_edrpou = list(set(valid_edrpous))

#             if all_edrpou:
#                 # Удаляем связанные данные для обработанных компаний
#                 cursor.execute(
#                     "DELETE FROM company_phones WHERE edrpou = ANY(%s)", (all_edrpou,)
#                 )
#                 cursor.execute(
#                     "DELETE FROM authorized_persons WHERE edrpou = ANY(%s)",
#                     (all_edrpou,),
#                 )
#                 cursor.execute(
#                     "DELETE FROM activity_types WHERE edrpou = ANY(%s)", (all_edrpou,)
#                 )

#                 # Массовая вставка связанных данных
#                 if phones_data:
#                     execute_batch(
#                         cursor,
#                         """
#                         INSERT INTO company_phones (edrpou, phone_number)
#                         VALUES (%s, %s)
#                         """,
#                         phones_data,
#                         page_size=1000,
#                     )

#                 if persons_data:
#                     execute_batch(
#                         cursor,
#                         """
#                         INSERT INTO authorized_persons (edrpou, full_name, position)
#                         VALUES (%s, %s, %s)
#                         """,
#                         persons_data,
#                         page_size=1000,
#                     )

#                 if activities_data:
#                     execute_batch(
#                         cursor,
#                         """
#                         INSERT INTO activity_types (edrpou, code, description)
#                         VALUES (%s, %s, %s)
#                         """,
#                         activities_data,
#                         page_size=1000,
#                     )

#                 conn.commit()

#         except Exception as e:
#             logger.error(f"Ошибка при обработке пакета данных: {e}")
#             conn.rollback()

#     return company_count, phone_count, person_count, activity_count


# def import_edrpo_json_to_postgres():
#     """Основная функция для импорта данных из JSON в PostgreSQL"""
#     total_start_time = time.time()

#     # Счетчики для отслеживания прогресса
#     companies_count = 0
#     phones_count = 0
#     persons_count = 0
#     activities_count = 0

#     try:
#         # Подключение к БД
#         logger.info("Подключение к базе данных...")
#         conn = psycopg2.connect(**db_params)
#         cursor = conn.cursor()

#         # Чтение JSON файла
#         logger.info(f"Чтение JSON файла ({JSON_FILE_PATH_EDRPO})...")

#         with open(JSON_FILE_PATH_EDRPO, "r", encoding="utf-8") as f:
#             all_data = json.load(f)

#         total_rows = len(all_data)
#         logger.info(f"Всего записей в JSON файле: {total_rows}")

#         # Обработка данных пакетами
#         batch_num = 0
#         for batch_start in range(0, total_rows, BATCH_SIZE):
#             batch_start_time = time.time()

#             batch_end = min(batch_start + BATCH_SIZE, total_rows)
#             json_batch = all_data[batch_start:batch_end]

#             # Обработка пакета
#             companies_count, phones_count, persons_count, activities_count = (
#                 process_json_batch_edrpo(
#                     json_batch,
#                     cursor,
#                     conn,
#                     companies_count,
#                     phones_count,
#                     persons_count,
#                     activities_count,
#                 )
#             )

#             batch_end_time = time.time()
#             batch_duration = batch_end_time - batch_start_time

#             batch_num += 1
#             logger.info(
#                 f"Обработан пакет {batch_num}, время: {batch_duration:.2f} сек."
#             )
#             logger.info(
#                 f"Обработано {batch_end} из {total_rows} строк ({batch_end*100/total_rows:.2f}%)"
#             )
#             logger.info(
#                 f"Статистика: {companies_count} компаний, {phones_count} телефонов, "
#                 f"{persons_count} лиц, {activities_count} видов деятельности"
#             )

#         logger.info(f"Импорт успешно завершен! Обработано:")
#         logger.info(f"- {companies_count} компаний")
#         logger.info(f"- {phones_count} телефонных номеров")
#         logger.info(f"- {persons_count} уполномоченных лиц")
#         logger.info(f"- {activities_count} видов деятельности")

#         total_end_time = time.time()
#         total_duration = total_end_time - total_start_time
#         logger.info(f"Общее время выполнения: {total_duration:.2f} секунд")

#     except Exception as e:
#         logger.error(f"Ошибка при импорте данных: {e}")
#         if "conn" in locals() and conn:
#             conn.rollback()
#     finally:
#         if "conn" in locals() and conn:
#             conn.close()
#             logger.info("Соединение с базой данных закрыто")


# # Запуск импорта
# if __name__ == "__main__":
#     import_edrpo_json_to_postgres()
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
JSON_FILE_PATH_EDRPO = "edrpo_data.json"

# Размер пакета для обработки
BATCH_SIZE = 10000


def is_nan_value(value):
    """Проверяет, является ли значение NaN (как строка или как число)"""
    if value == "NaN" or (isinstance(value, float) and math.isnan(value)):
        return True
    return False


def safe_str(value):
    """Безопасно преобразует значение в строку или None"""
    if value is None or is_nan_value(value) or value == "":
        return None
    return str(value).strip()


def parse_date(date_str):
    """Конвертирует строку даты в объект date, либо None если невозможно преобразовать"""
    if date_str is None or is_nan_value(date_str) or date_str == "":
        return None

    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except (ValueError, TypeError):
        logger.warning(f"Не удалось преобразовать дату: {date_str}")
        return None


def parse_activity_types(activity_text):
    """Парсит строку с видами деятельности на отдельные записи"""
    if activity_text is None or is_nan_value(activity_text) or activity_text == "":
        return []

    activities = []
    try:
        patterns = re.findall(r"(\d+\.\d+(?:\s*\.\s*\d+)?\s+[^;]+)", str(activity_text))

        for pattern in patterns:
            parts = pattern.strip().split(None, 1)
            if len(parts) >= 2:
                code = parts[0].strip()
                description = parts[1].strip()
                activities.append((code, description))
            else:
                activities.append((None, pattern.strip()))

        if not activities and activity_text:
            activities.append((None, str(activity_text).strip()))
    except Exception as e:
        logger.warning(f"Ошибка при парсинге видов деятельности: {e}")

    return activities


def parse_authorized_persons(persons_text):
    """Парсит строку с уполномоченными лицами на отдельные записи"""
    if persons_text is None or is_nan_value(persons_text) or persons_text == "":
        return []

    persons = []
    try:
        for person_info in re.split(r"[,;]\s*", str(persons_text)):
            if "-" in person_info:
                parts = person_info.split("-", 1)
                full_name = parts[0].strip()
                position = parts[1].strip() if len(parts) > 1 else None
                persons.append((full_name, position))
            else:
                if person_info.strip():
                    persons.append((person_info.strip(), None))
    except Exception as e:
        logger.warning(f"Ошибка при парсинге уполномоченных лиц: {e}")

    return persons


def parse_phones(phones_text):
    """Парсит строку с телефонами на отдельные записи"""
    if phones_text is None or is_nan_value(phones_text) or phones_text == "":
        return []

    phones = []
    try:
        for phone in re.split(r"[,;]\s*", str(phones_text)):
            if phone.strip():
                phones.append(phone.strip())
    except Exception as e:
        logger.warning(f"Ошибка при парсинге телефонов: {e}")

    return phones


def extract_company_data_en(row):
    """Извлекает данные компании из JSON с английскими ключами"""
    try:
        edrpou = safe_str(row.get("edrpou"))

        # Пропускаем строки без EDRPOU
        if not edrpou:
            return None

        full_name = safe_str(row.get("full_name"))
        short_name = safe_str(row.get("short_name"))
        org_form = safe_str(row.get("org_form"))
        address = safe_str(row.get("address"))
        status = safe_str(row.get("status"))

        # Преобразование дат
        status_date = parse_date(row.get("status_date"))
        registration_date = parse_date(row.get("registration_date"))
        email = safe_str(row.get("email"))

        # Дополнительные данные для связанных таблиц
        phones = parse_phones(row.get("phones"))
        authorized_persons = parse_authorized_persons(row.get("authorized_persons"))
        activity_types = parse_activity_types(row.get("activity_types"))

        return {
            "company_data": (
                edrpou,
                full_name,
                short_name,
                org_form,
                address,
                status,
                status_date,
                registration_date,
                email,
            ),
            "phones": [(edrpou, phone) for phone in phones],
            "persons": [
                (edrpou, name, position) for name, position in authorized_persons
            ],
            "activities": [
                (edrpou, code, description) for code, description in activity_types
            ],
        }
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных компании (EN): {e}, строка: {row}")
        return None


def extract_company_data_uk(row):
    """Извлекает данные компании из JSON с украинскими ключами"""
    try:
        edrpou = safe_str(row.get("ЄДРПОУ"))

        # Пропускаем строки без EDRPOU
        if not edrpou:
            return None

        full_name = safe_str(row.get("Назва"))
        short_name = safe_str(row.get("Коротка назва"))
        org_form = safe_str(row.get("Організаційна форма"))
        address = safe_str(row.get("Адреса"))
        status = safe_str(row.get("Стан"))

        # Преобразование дат
        status_date = parse_date(row.get("Дата стану"))
        registration_date = parse_date(row.get("Дата реєстрації"))
        email = safe_str(row.get("Email"))

        # Дополнительные данные для связанных таблиц
        phones = parse_phones(row.get("Телефони"))
        authorized_persons = parse_authorized_persons(row.get("Уповноважені особи"))
        activity_types = parse_activity_types(row.get("Види діяльності"))

        return {
            "company_data": (
                edrpou,
                full_name,
                short_name,
                org_form,
                address,
                status,
                status_date,
                registration_date,
                email,
            ),
            "phones": [(edrpou, phone) for phone in phones],
            "persons": [
                (edrpou, name, position) for name, position in authorized_persons
            ],
            "activities": [
                (edrpou, code, description) for code, description in activity_types
            ],
        }
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных компании (UK): {e}, строка: {row}")
        return None


def detect_json_format(json_data):
    """Определяет формат JSON данных (английский или украинский)"""
    if not json_data:
        return "unknown"

    # Берем первую запись для проверки
    sample = json_data[0]

    # Проверяем наличие ключевых полей на украинском
    if "ЄДРПОУ" in sample:
        return "uk"
    elif "edrpou" in sample:
        return "en"
    else:
        return "unknown"


def prepare_data_batch(json_data, format_type=None):
    """Подготавливает данные из JSON для пакетной вставки"""
    if not format_type:
        format_type = detect_json_format(json_data)

    companies_data = []
    phones_data = []
    persons_data = []
    activities_data = []

    # Выбираем функцию извлечения в зависимости от формата
    extract_function = (
        extract_company_data_uk if format_type == "uk" else extract_company_data_en
    )

    # Обработка компаний
    for row in json_data:
        extracted = extract_function(row)

        if extracted:
            companies_data.append(extracted["company_data"])
            phones_data.extend(extracted["phones"])
            persons_data.extend(extracted["persons"])
            activities_data.extend(extracted["activities"])

    return {
        "companies": companies_data,
        "phones": phones_data,
        "persons": persons_data,
        "activities": activities_data,
    }


def insert_companies_batch(cursor, companies_data):
    """Вставляет пакет данных о компаниях"""
    if not companies_data:
        return 0

    execute_batch(
        cursor,
        """
        INSERT INTO companies (
            edrpou, full_name, short_name, org_form, address,
            status, status_date, registration_date, email
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (edrpou) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            short_name = EXCLUDED.short_name,
            org_form = EXCLUDED.org_form,
            address = EXCLUDED.address,
            status = EXCLUDED.status,
            status_date = EXCLUDED.status_date,
            registration_date = EXCLUDED.registration_date,
            email = EXCLUDED.email,
            last_updated = CURRENT_TIMESTAMP
        """,
        companies_data,
        page_size=100,
    )

    return len(companies_data)


def delete_related_data(cursor, edrpous):
    """Удаляет связанные данные для списка EDRPOU"""
    if not edrpous:
        return

    cursor.execute("DELETE FROM company_phones WHERE edrpou = ANY(%s)", (edrpous,))
    cursor.execute("DELETE FROM authorized_persons WHERE edrpou = ANY(%s)", (edrpous,))
    cursor.execute("DELETE FROM activity_types WHERE edrpou = ANY(%s)", (edrpous,))


def insert_related_data(cursor, phones_data, persons_data, activities_data):
    """Вставляет связанные данные (телефоны, лица, виды деятельности)"""
    counts = {"phones": 0, "persons": 0, "activities": 0}

    if phones_data:
        execute_batch(
            cursor,
            """
            INSERT INTO company_phones (edrpou, phone_number)
            VALUES (%s, %s)
            """,
            phones_data,
            page_size=1000,
        )
        counts["phones"] = len(phones_data)

    if persons_data:
        execute_batch(
            cursor,
            """
            INSERT INTO authorized_persons (edrpou, full_name, position)
            VALUES (%s, %s, %s)
            """,
            persons_data,
            page_size=1000,
        )
        counts["persons"] = len(persons_data)

    if activities_data:
        execute_batch(
            cursor,
            """
            INSERT INTO activity_types (edrpou, code, description)
            VALUES (%s, %s, %s)
            """,
            activities_data,
            page_size=1000,
        )
        counts["activities"] = len(activities_data)

    return counts


def process_json_batch(json_data, cursor, conn, counters=None, format_type=None):
    """Обрабатывает пакет JSON данных и записывает их в базу данных"""
    if counters is None:
        counters = {"companies": 0, "phones": 0, "persons": 0, "activities": 0}

    try:
        # Подготовка данных
        batch_data = prepare_data_batch(json_data, format_type)

        if not batch_data["companies"]:
            logger.warning("Нет данных для вставки в пакете")
            return counters

        # Вставка компаний
        inserted_companies = insert_companies_batch(cursor, batch_data["companies"])
        counters["companies"] += inserted_companies

        if inserted_companies > 0:
            # Получаем список EDRPOU для обработанных компаний
            edrpous = [item[0] for item in batch_data["companies"]]

            # Удаляем связанные данные
            delete_related_data(cursor, edrpous)

            # Вставляем связанные данные
            related_counts = insert_related_data(
                cursor,
                batch_data["phones"],
                batch_data["persons"],
                batch_data["activities"],
            )

            counters["phones"] += related_counts["phones"]
            counters["persons"] += related_counts["persons"]
            counters["activities"] += related_counts["activities"]

            # Фиксируем изменения
            conn.commit()

    except Exception as e:
        logger.error(f"Ошибка при обработке пакета данных: {e}")
        conn.rollback()

    return counters


def import_json_to_postgres(json_file_path=None, format_type=None, batch_size=None):
    """Основная функция для импорта данных из JSON в PostgreSQL"""
    if json_file_path is None:
        json_file_path = JSON_FILE_PATH_EDRPO

    if batch_size is None:
        batch_size = BATCH_SIZE

    total_start_time = time.time()

    # Счетчики для отслеживания прогресса
    counters = {"companies": 0, "phones": 0, "persons": 0, "activities": 0}

    try:
        # Подключение к БД
        logger.info("Подключение к базе данных...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Чтение JSON файла
        logger.info(f"Чтение JSON файла ({json_file_path})...")

        with open(json_file_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        total_rows = len(all_data)
        logger.info(f"Всего записей в JSON файле: {total_rows}")

        # Определяем формат данных, если не указан
        if format_type is None:
            format_type = detect_json_format(all_data)
            logger.info(f"Определен формат данных: {format_type}")

        # Обработка данных пакетами
        batch_num = 0
        for batch_start in range(0, total_rows, batch_size):
            batch_start_time = time.time()

            batch_end = min(batch_start + batch_size, total_rows)
            json_batch = all_data[batch_start:batch_end]

            # Обработка пакета
            counters = process_json_batch(
                json_batch, cursor, conn, counters, format_type
            )

            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time

            batch_num += 1
            logger.info(
                f"Обработан пакет {batch_num}, время: {batch_duration:.2f} сек."
            )
            logger.info(
                f"Обработано {batch_end} из {total_rows} строк ({batch_end*100/total_rows:.2f}%)"
            )
            logger.info(
                f"Статистика: {counters['companies']} компаний, {counters['phones']} телефонов, "
                f"{counters['persons']} лиц, {counters['activities']} видов деятельности"
            )

        logger.info(f"Импорт успешно завершен! Обработано:")
        logger.info(f"- {counters['companies']} компаний")
        logger.info(f"- {counters['phones']} телефонных номеров")
        logger.info(f"- {counters['persons']} уполномоченных лиц")
        logger.info(f"- {counters['activities']} видов деятельности")

        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        logger.info(f"Общее время выполнения: {total_duration:.2f} секунд")

    except Exception as e:
        logger.error(f"Ошибка при импорте данных: {e}")
        if "conn" in locals() and conn:
            conn.rollback()
    finally:
        if "conn" in locals() and conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто")

    return counters


# Запуск импорта
if __name__ == "__main__":
    import_json_to_postgres()
