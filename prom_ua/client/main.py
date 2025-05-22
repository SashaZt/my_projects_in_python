import json
from typing import Any, Dict, List

import psycopg2
from config.logger import logger
from psycopg2.extras import execute_values


def import_data_to_db(json_file: str, db_config: Dict[str, Any]) -> bool:
    """
    Импортирует данные из JSON файла в базу данных PostgreSQL.

    Args:
        json_file (str): Путь к JSON файлу с данными компаний.
        db_config (Dict[str, Any]): Конфигурация подключения к базе данных.
            Пример: {
                "host": "localhost",
                "database": "your_db",
                "user": "your_user",
                "password": "your_password",
                "port": 5432
            }

    Returns:
        bool: True, если импорт успешен, иначе False.
    """
    try:
        # Загружаем данные из JSON файла
        with open(json_file, "r", encoding="utf-8") as f:
            companies_data = json.load(f)

        # Подключаемся к базе данных
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Очищаем таблицы перед импортом
        cursor.execute("TRUNCATE TABLE companyPhones CASCADE;")
        cursor.execute("TRUNCATE TABLE companies CASCADE;")

        # Подготавливаем данные для вставки в таблицу companies
        companies_values = []
        phones_values = []

        for company in companies_data:
            # Извлекаем геокоординаты, если они есть
            latitude = None
            longitude = None
            if "companyGeoCoordinates" in company and company["companyGeoCoordinates"]:
                geo = company["companyGeoCoordinates"]
                latitude = geo.get("latitude")
                longitude = geo.get(
                    "longtitude"
                )  # Обратите внимание на опечатку в ключе

            # Форматируем рейтинг компании
            rating = company.get("rating_company")

            # Подготавливаем данные для вставки в таблицу companies
            company_row = (
                company["companyId"],
                company.get("companyName"),
                company.get("companyPerson"),
                company.get("companyEmail"),
                company.get("companyAddress"),
                company.get("companySlug"),
                company.get("companyWebsite"),
                latitude,
                longitude,
                company.get("totalProducts", 0),
                rating,
                company.get("review_2023", 0),
                company.get("review_2024", 0),
                company.get("review_2025", 0),
            )
            companies_values.append(company_row)

            # Подготавливаем данные для вставки в таблицу companyPhones
            company_id = company["companyId"]
            phones = company.get("companyPhones", [])
            for phone in phones:
                if phone:  # Проверяем, что телефон не пустой
                    phones_values.append((company_id, phone))

        # Вставляем данные в таблицу companies
        companies_query = """
        INSERT INTO companies (
            companyId, companyName, companyPerson, companyEmail, companyAddress,
            companySlug, companyWebsite, latitude, longitude, totalProducts,
            rating_company, review_2023, review_2024, review_2025
        ) VALUES %s;
        """
        execute_values(cursor, companies_query, companies_values)

        # Вставляем данные в таблицу companyPhones
        if phones_values:
            phones_query = """
            INSERT INTO companyPhones (companyId, phone_number) VALUES %s;
            """
            execute_values(cursor, phones_query, phones_values)

        # Фиксируем изменения и закрываем соединение
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(
            f"Успешно импортировано {len(companies_values)} компаний и {len(phones_values)} телефонных номеров"
        )
        return True

    except Exception as e:
        logger.error(f"Ошибка при импорте данных в базу данных: {str(e)}")
        # Если соединение открыто, закрываем его
        if "conn" in locals() and conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return False


def main():
    """Основная функция"""
    # Путь к файлу с данными
    json_file = "merged_data.json"

    # Конфигурация подключения к базе данных
    db_config = {
        "host": "localhost",
        "database": "prom_ua",
        "user": "prom_ua_user",
        "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
        "port": 5430,
    }

    # Импортируем данные в базу данных
    if import_data_to_db(json_file, db_config):
        logger.info("Импорт данных в базу данных успешно завершен")
    else:
        logger.error("Импорт данных в базу данных завершен с ошибками")


if __name__ == "__main__":
    main()
