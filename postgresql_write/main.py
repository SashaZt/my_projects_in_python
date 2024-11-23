import json
import os
from concurrent.futures import ThreadPoolExecutor

from configuration.logger_setup import logger
from dotenv import load_dotenv
from psycopg2 import connect, extras, pool, sql

# Load environment variables
load_dotenv(dotenv_path="/path/to/your/.env")

# Database configuration
DB_NAME = os.getenv("DB_NAME", "postgres_db")
DB_USER = os.getenv("DB_USER", "postgres_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres_password")
DB_HOST = os.getenv("DB_HOST", "192.168.33.71")
DB_PORT = int(os.getenv("DB_PORT", 5430))

table_name = "kg"
json_file = "result.json"
table_structure_file = "table_structure.json"

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


def load_table_structure(file_path):
    """Load the table structure from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_table(columns):
    """Create the table dynamically based on the provided columns."""
    column_definitions = [f'"{col}" {dtype}' for col, dtype in columns.items()]
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)}
        );
    """
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_query)
            conn.commit()
        logger.info(f"Table '{table_name}' created successfully.")
    finally:
        db_pool.putconn(conn)


def upsert_batch(batch, columns):
    """Insert or update a batch of data into the table."""
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            column_names = [sql.Identifier(col) for col in columns.keys()]
            placeholders = [sql.Placeholder() for _ in columns.keys()]

            upsert_query = sql.SQL(
                """
                INSERT INTO {table_name} ({columns}) VALUES ({placeholders})
                ON CONFLICT ("ИНН") DO UPDATE SET
                {updates};
                """
            ).format(
                table_name=sql.Identifier(table_name),
                columns=sql.SQL(", ").join(column_names),
                placeholders=sql.SQL(", ").join(placeholders),
                updates=sql.SQL(", ").join(
                    [
                        sql.SQL(f'"{col}" = EXCLUDED."{col}"')
                        for col in columns.keys()
                        if col != "ИНН"
                    ]
                ),
            )

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


def process_file(file_path, columns):
    """Read the JSON file and process it."""
    batch_size = 1000
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)  # Load entire JSON as a list of dictionaries

    batch = []
    for record in data:
        batch.append(tuple(record.get(col, None) for col in columns.keys()))
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    """Main function to orchestrate the loading process."""
    # Load table structure from JSON
    table_structure = load_table_structure(table_structure_file)

    # Create table
    create_table(table_structure)

    # Process the JSON file and insert or update data
    with ThreadPoolExecutor(max_workers=4) as executor:
        for batch in process_file(json_file, table_structure):
            executor.submit(upsert_batch, batch, table_structure)

    logger.info("Data loading complete.")


if __name__ == "__main__":
    main()
