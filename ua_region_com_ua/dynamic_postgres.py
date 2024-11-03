import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg2
from configuration.logger_setup import logger
from dotenv import load_dotenv
from psycopg2 import pool, sql
from tqdm import tqdm

# Загрузка переменных окружения из файла .env
load_dotenv(Path("configuration") / ".env")

# Установка директорий для логов и данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
json_result = data_directory / "result.json"


class DynamicPostgres:
    def __init__(self):
        # Получение параметров подключения из .env файла с проверкой
        db_name = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5430")

        if not all([db_name, user, password, host, port]):
            raise ValueError(
                "Отсутствуют обязательные параметры подключения в .env файле"
            )

        try:
            # Инициализируем пул соединений
            self.conn_pool = psycopg2.pool.SimpleConnectionPool(
                1,
                20,
                dbname=db_name,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            logger.info(
                "Успешное подключение к базе данных PostgreSQL через пул соединений"
            )
        except Exception as e:
            logger.error(
                f"Ошибка при создании пула соединений к базе данных: {e}")
            raise

    def create_or_update_table(self, table_name, data):
        # Проверка наличия данных
        if not data:
            logger.warning(
                "Пустой набор данных, создание или обновление таблицы пропущено"
            )
            return

        try:
            # Получить все уникальные ключи из списка словарей
            all_columns = set(key for row in data for key in row.keys())
            with self.conn_pool.getconn() as conn:
                with conn.cursor() as cursor:
                    # Создать таблицу с необходимыми столбцами, если она не существует
                    columns_definitions = ", ".join(
                        [f'"{key}" TEXT' for key in all_columns]
                    )
                    create_table_query = sql.SQL(
                        "CREATE TABLE IF NOT EXISTS {} (id SERIAL PRIMARY KEY, {});"
                    ).format(sql.Identifier(table_name), sql.SQL(columns_definitions))
                    cursor.execute(create_table_query)

                    # Проверка и добавление новых столбцов, если они отсутствуют
                    cursor.execute(
                        sql.SQL(
                            "SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
                        ),
                        (table_name,),
                    )
                    existing_columns = {col[0] for col in cursor.fetchall()}
                    new_columns = all_columns - existing_columns

                    for column in new_columns:
                        alter_table_query = sql.SQL(
                            "ALTER TABLE {} ADD COLUMN {} TEXT;"
                        ).format(sql.Identifier(table_name), sql.Identifier(column))
                        cursor.execute(alter_table_query)

                    conn.commit()
                    if new_columns:
                        logger.info(
                            f"Добавлены новые столбцы: {
                                ', '.join(new_columns)}"
                        )
                    else:
                        logger.info(
                            f"Все столбцы уже существуют для таблицы {
                                table_name}"
                        )
        except Exception as e:
            logger.error(
                f"Ошибка при создании или обновлении таблицы {table_name}: {e}"
            )
            raise

    def insert_data(self, table_name, data, num_threads=20):
        # Вставка данных с использованием многопоточности
        if not data:
            logger.warning("Пустой набор данных, вставка данных пропущена")
            return

        valid_data = [row for row in data if "Код ЄДРПОУ" in row]
        if len(valid_data) != len(data):
            logger.warning(
                "Некоторые записи были пропущены, так как отсутствует поле 'Код ЄДРПОУ'"
            )

        def insert_or_update_record(row):
            # Используем соединение из пула для каждого потока
            conn = self.conn_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    # Проверка существования записи по "Код ЄДРПОУ"
                    check_query = sql.SQL(
                        'SELECT id FROM {} WHERE "Код ЄДРПОУ" = %s;'
                    ).format(sql.Identifier(table_name))
                    cursor.execute(check_query, (row["Код ЄДРПОУ"],))
                    existing_record = cursor.fetchone()

                    if existing_record:
                        # Обновление существующей записи
                        update_columns = [
                            sql.SQL(f'"{key}" = %s') for key in row.keys()
                        ]
                        update_values = tuple(
                            row.values()) + (existing_record[0],)
                        update_query = sql.SQL(
                            "UPDATE {} SET {} WHERE id = %s;"
                        ).format(
                            sql.Identifier(table_name),
                            sql.SQL(", ").join(update_columns),
                        )
                        cursor.execute(update_query, update_values)
                    else:
                        # Вставка новой записи
                        columns = [sql.Identifier(key) for key in row.keys()]
                        placeholders = [sql.Placeholder() for _ in row.keys()]
                        values = tuple(row.values())
                        insert_query = sql.SQL(
                            "INSERT INTO {} ({}) VALUES ({});"
                        ).format(
                            sql.Identifier(table_name),
                            sql.SQL(", ").join(columns),
                            sql.SQL(", ").join(placeholders),
                        )
                        cursor.execute(insert_query, values)

                    conn.commit()
            except Exception as e:
                logger.error(f"Ошибка при вставке или обновлении записи: {e}")
                conn.rollback()
            finally:
                self.conn_pool.putconn(conn)

        # Используем ThreadPoolExecutor для многопоточной вставки данных
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            list(
                tqdm(
                    executor.map(insert_or_update_record, valid_data),
                    total=len(valid_data),
                    desc="Processing data",
                )
            )

    def close(self):
        # Закрыть пул соединений
        try:
            self.conn_pool.closeall()
            logger.info("Соединение с базой данных PostgreSQL закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединений: {e}")

    def load_data_from_json(self):
        # Загрузить данные из JSON файла
        try:
            with open(json_result, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            logger.info(f"Данные успешно загружены из файла {json_result}")
            return data
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из файла {
                         json_result}: {e}")
            raise
