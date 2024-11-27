import json
import os
from concurrent.futures import ThreadPoolExecutor

from configuration.logger_setup import logger
from dotenv import load_dotenv
from psycopg2 import connect, extras, pool, sql

# Load environment variables
load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME", "postgres_db")
DB_USER = os.getenv("DB_USER", "postgres_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres_password")
DB_HOST = os.getenv("DB_HOST", "192.168.33.71")
DB_PORT = int(os.getenv("DB_PORT", 5430))

table_name = "kg"
json_file = "result.json"
json_file = "output_data.json"

# Create a connection pool
db_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)


def check_table_data():
    """Check if the table 'kg' has any records."""
    try:
        with connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        ) as conn:
            with conn.cursor() as cursor:
                # Query to count records in the table
                query = "SELECT COUNT(*) FROM public.kg;"
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"Table 'kg' has {count} records.")
    except Exception as e:
        print(f"Error accessing table 'kg': {e}")


def get_tables():
    """Connect to the database and list all tables."""
    try:
        # Connect to the database
        with connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        ) as conn:
            with conn.cursor() as cursor:
                # Query to list all tables
                query = """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name;
                """
                cursor.execute(query)
                tables = cursor.fetchall()

                print("Tables in the database:")
                for schema, table in tables:
                    print(f"Schema: {schema}, Table: {table}")

    except Exception as e:
        print(f"Error retrieving tables: {e}")


def create_table():
    """Create the table if not exists."""
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            "Название" TEXT,
            "Статус" TEXT,
            "ИНН" TEXT UNIQUE,
            "Директор" TEXT,
            "Дополнительная информация 1" TEXT,
            "Дополнительная информация 2" TEXT,
            "Дополнительная информация 3" TEXT,
            "Дополнительная информация 4" TEXT,
            "Дополнительная информация 5" TEXT,
            "Последнее обновление" TEXT,
            "Форма" TEXT,
            "Форма собственности" TEXT,
            "Количество участников" TEXT,
            "Вид деятельности" TEXT,
            "Регистрационный номер" TEXT,
            "ОКПО" TEXT,
            "Адрес" TEXT,
            "Телефон" TEXT
        );
    """
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_query)
            conn.commit()
        logger.info("Table created successfully.")
    finally:
        db_pool.putconn(conn)


def upsert_batch(batch):
    """Insert or update a batch of data into the table."""
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            upsert_query = sql.SQL(
                """
                INSERT INTO {table_name} (
                    "Название", "Статус", "ИНН", "Директор",
                    "Дополнительная информация 1", "Дополнительная информация 2",
                    "Дополнительная информация 3", "Дополнительная информация 4",
                    "Дополнительная информация 5", "Последнее обновление", "Форма",
                    "Форма собственности", "Количество участников", "Вид деятельности",
                    "Регистрационный номер", "ОКПО", "Адрес", "Телефон"
                ) VALUES %s
                ON CONFLICT ("ИНН") DO UPDATE SET
                    "Название" = EXCLUDED."Название",
                    "Статус" = EXCLUDED."Статус",
                    "Директор" = EXCLUDED."Директор",
                    "Дополнительная информация 1" = EXCLUDED."Дополнительная информация 1",
                    "Дополнительная информация 2" = EXCLUDED."Дополнительная информация 2",
                    "Дополнительная информация 3" = EXCLUDED."Дополнительная информация 3",
                    "Дополнительная информация 4" = EXCLUDED."Дополнительная информация 4",
                    "Дополнительная информация 5" = EXCLUDED."Дополнительная информация 5",
                    "Последнее обновление" = EXCLUDED."Последнее обновление",
                    "Форма" = EXCLUDED."Форма",
                    "Форма собственности" = EXCLUDED."Форма собственности",
                    "Количество участников" = EXCLUDED."Количество участников",
                    "Вид деятельности" = EXCLUDED."Вид деятельности",
                    "Регистрационный номер" = EXCLUDED."Регистрационный номер",
                    "ОКПО" = EXCLUDED."ОКПО",
                    "Адрес" = EXCLUDED."Адрес",
                    "Телефон" = EXCLUDED."Телефон";
                """
            ).format(table_name=sql.Identifier(table_name))

            extras.execute_values(
                cursor, upsert_query, batch, template=None, page_size=1000
            )
            conn.commit()
        logger.info(f"Upserted batch of {len(batch)} records.")
    except Exception as e:
        logger.error(f"Error upserting batch: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)


def process_file(file_path):
    """Read the JSON file and process it."""
    batch_size = 1000
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)  # Load entire JSON as a list of dictionaries

    batch = []
    for record in data:
        batch.append(
            (
                record.get("Название"),
                record.get("Статус"),
                record.get("ИНН"),
                record.get("Директор"),
                record.get("Дополнительная информация 1"),
                record.get("Дополнительная информация 2"),
                record.get("Дополнительная информация 3"),
                record.get("Дополнительная информация 4"),
                record.get("Дополнительная информация 5"),
                record.get("Последнее обновление"),
                record.get("Форма"),
                record.get("Форма собственности"),
                record.get("Количество участников"),
                record.get("Вид деятельности"),
                record.get("Регистрационный номер"),
                record.get("ОКПО"),
                record.get("Адрес"),
                record.get("Телефон"),
            )
        )
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def map_record(record):
    """Map JSON keys to database columns."""
    return (
        record.get("Полное фирменное наименование на официальном языке"),  # "Название"
        f"{record.get('Текущий статус', '')} {record.get('Дата первичной регистрации', '')}",  # "Статус"
        record.get("ИНН"),  # "ИНН"
        record.get("Руководитель"),  # "Директор"
        None,  # "Дополнительная информация 1"
        None,  # "Дополнительная информация 2"
        None,  # "Дополнительная информация 3"
        None,  # "Дополнительная информация 4"
        None,  # "Дополнительная информация 5"
        None,  # "Последнее обновление"
        None,  # "Форма"
        None,  # "Форма собственности"
        record.get(
            "Количество учредителей/участников, членов"
        ),  # "Количество участников"
        None,  # "Вид деятельности"
        record.get("Регистрационный номер"),  # "Регистрационный номер"
        record.get("Код ОКПО"),  # "ОКПО"
        record.get("Юридический адрес"),  # "Адрес"
        None,  # "Телефон"
    )


def process_file_miniy(file_path):
    """Read the JSON file and process it."""
    batch_size = 1000
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)  # Load entire JSON as a list of dictionaries

    batch = []
    for record in data:
        mapped_record = map_record(record)  # Apply mapping
        batch.append(mapped_record)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    # get_tables()
    # check_table_data()
    # """Main function to orchestrate the loading process."""
    create_table()  # Ensure the table exists

    # Process the JSON file and insert or update data
    with ThreadPoolExecutor(max_workers=4) as executor:
        # for batch in process_file(json_file):
        for batch in process_file_miniy(json_file):
            executor.submit(upsert_batch, batch)

    logger.info("Data loading complete.")


if __name__ == "__main__":
    main()
