import psycopg2
from psycopg2 import sql
from pg_config import postgres_config, database
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)


def check_data_day_zcnx():
    """
    Функция для получения данных из БД дневных продаж (PostgreSQL)
    """
    try:
        # Подключение к базе данных PostgreSQL
        connection = psycopg2.connect(**postgres_config)
        cursor = connection.cursor()

        # Выполнение запроса с указанием схемы public
        query = sql.SQL(
            """
            SELECT buyer_user_id, sales_date, sales_time, seller_commission_price
            FROM {}.transactions;
            """
        ).format(sql.Identifier("public"))

        cursor.execute(query)

        # Извлечение данных
        data = {(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()}

    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(f"Ошибка при работе с PostgreSQL: {error}")
        data = set()

    finally:
        # Закрытие курсора и соединения
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")

    return data
