import psycopg2
from psycopg2 import sql
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from configuration.logger_setup import logger
from pathlib import Path
import os
import json

# Загрузка переменных окружения из файла .env
load_dotenv(Path("configuration") / ".env")
# Установка директорий для логов и данных
current_directory = Path.cwd()
data_directory = current_directory / "data"

data_directory.mkdir(parents=True, exist_ok=True)
json_result = data_directory / "result.json"


class DynamicPostgres:
    def __init__(self):
        # Получение параметров подключения из .env файла
        db_name = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5430")

        # Инициализировать соединение с базой данных PostgreSQL
        try:
            self.conn = psycopg2.connect(
                dbname=db_name, user=user, password=password, host=host, port=port
            )
            self.cursor = self.conn.cursor()
            logger.info("Успешное подключение к базе данных PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def create_or_update_table(self, table_name, data):
        # Предполагается, что data - это список словарей
        if not data:
            logger.warning(
                "Пустой набор данных, создание или обновление таблицы пропущено"
            )
            return

        try:
            # Создать строку с определениями столбцов на основе ключей словаря
            columns_definitions = ", ".join([f'"{key}" TEXT' for key in data[0].keys()])
            # SQL-запрос для создания таблицы, если она не существует, включая автоинкрементируемый первичный ключ
            create_table_query = sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} (id SERIAL PRIMARY KEY, {});"
            ).format(sql.Identifier(table_name), sql.SQL(columns_definitions))
            self.cursor.execute(create_table_query)
            self.conn.commit()
            logger.info(f"Таблица {table_name} создана или уже существует")

            # Добавить новые столбцы, если их нет в текущей таблице
            self.cursor.execute(
                sql.SQL(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
                ),
                (table_name,),
            )
            existing_columns = [col[0] for col in self.cursor.fetchall()]
            new_columns = [key for key in data[0].keys() if key not in existing_columns]
            for key in new_columns:
                # SQL-запрос для добавления нового столбца, если он не существует
                alter_table_query = sql.SQL(
                    "ALTER TABLE {} ADD COLUMN {} TEXT;"
                ).format(sql.Identifier(table_name), sql.Identifier(key))
                self.cursor.execute(alter_table_query)
            self.conn.commit()
            if new_columns:
                logger.info(
                    f"Добавлены новые столбцы в таблицу {table_name}: {', '.join(new_columns)}"
                )
        except Exception as e:
            logger.error(
                f"Ошибка при создании или обновлении таблицы {table_name}: {e}"
            )
            raise

    def insert_data(self, table_name, data, num_threads=4):
        # Вставить каждый словарь из списка data в таблицу
        if not data:
            logger.warning("Пустой набор данных, вставка данных пропущена")
            return

        def insert_or_update_record(row):
            # Создать новое соединение для каждого потока
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5430"),
            )
            cursor = conn.cursor()
            try:
                # Проверить, существует ли запись с тем же значением "Код ЄДРПОУ"
                check_query = sql.SQL(
                    'SELECT id FROM {} WHERE "Код ЄДРПОУ" = %s;'
                ).format(sql.Identifier(table_name))
                cursor.execute(check_query, (row["Код ЄДРПОУ"],))
                existing_record = cursor.fetchone()

                if existing_record:
                    # Если запись существует, обновить её
                    update_columns = [sql.SQL(f'"{key}" = %s') for key in row.keys()]
                    update_values = tuple(row.values()) + (existing_record[0],)
                    update_query = sql.SQL("UPDATE {} SET {} WHERE id = %s;").format(
                        sql.Identifier(table_name), sql.SQL(", ").join(update_columns)
                    )
                    cursor.execute(update_query, update_values)
                    # logger.info(
                    #     f"Запись с id {existing_record[0]} в таблице {table_name} обновлена"
                    # )
                else:
                    # Если запись не существует, вставить новую
                    columns = [sql.Identifier(key) for key in row.keys()]
                    placeholders = [sql.Placeholder() for _ in row.keys()]
                    values = tuple(row.values())
                    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({});").format(
                        sql.Identifier(table_name),
                        sql.SQL(", ").join(columns),
                        sql.SQL(", ").join(placeholders),
                    )
                    cursor.execute(insert_query, values)
                    # logger.info(f"Новая запись добавлена в таблицу {table_name}")
                conn.commit()
            except Exception as e:
                logger.error(
                    f"Ошибка при вставке или обновлении записи в таблице {table_name}: {e}"
                )
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

        # Используем ThreadPoolExecutor для многопоточной вставки данных
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            list(
                tqdm(
                    executor.map(insert_or_update_record, data),
                    total=len(data),
                    desc="Processing data",
                )
            )

    def close(self):
        # Закрыть соединение с базой данных PostgreSQL
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Соединение с базой данных PostgreSQL закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с базой данных: {e}")

    def load_data_from_json(self):
        # Загрузить данные из JSON файла
        try:
            with open(json_result, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            logger.info(f"Данные успешно загружены из файла {json_result}")
            return data
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из файла {json_result}: {e}")
            raise
