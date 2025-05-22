import json
import psycopg2
from config.logger import logger
from psycopg2.extras import execute_values

# Параметры подключения к базе данных
db_params = {
    "user": "prom_ua_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "dbname": "prom_ua",
    "host": "localhost",
    "port": 5430,
}


def create_total_product_table(conn):
    """Создание таблицы totalProduct, если она не существует"""
    with conn.cursor() as cursor:
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS totalProduct (
            id SERIAL PRIMARY KEY,
            companyId INTEGER NOT NULL,
            totalProducts INTEGER DEFAULT 0,
            CONSTRAINT fk_company_total_product
                FOREIGN KEY (companyId)
                REFERENCES companies (companyId)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_total_product_company_id ON totalProduct (companyId);
        """
        )
        conn.commit()
        logger.info("Таблица totalProduct создана или уже существует")


def import_total_products(conn, data_file_path):
    """Импорт данных в таблицу totalProduct из JSON файла"""
    try:
        # Открываем и читаем JSON файл
        with open(data_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        with conn.cursor() as cursor:
            # Вставляем или обновляем данные
            for item in data[:100]:  # Для тестирования берем только первый элемент
                company_id = int(item["companyId"])
                total_products = item["totalProducts"]

                # Проверяем, существует ли компания
                cursor.execute(
                    "SELECT 1 FROM companies WHERE companyId = %s", (company_id,)
                )
                if cursor.fetchone() is None:
                    logger.warning(
                        f"Компания с ID {company_id} не найдена в таблице companies. Запись будет пропущена."
                    )
                    skipped_count += 1
                    continue

                # Проверяем, существует ли запись в totalProduct
                cursor.execute(
                    "SELECT 1 FROM totalProduct WHERE companyId = %s", (company_id,)
                )
                if cursor.fetchone() is None:
                    # Вставляем новую запись
                    cursor.execute(
                        """
                        INSERT INTO totalProduct (companyId, totalProducts)
                        VALUES (%s, %s)
                        """,
                        (company_id, total_products),
                    )
                    inserted_count += 1
                else:
                    # Обновляем существующую запись
                    cursor.execute(
                        """
                        UPDATE totalProduct
                        SET totalProducts = %s
                        WHERE companyId = %s
                        """,
                        (total_products, company_id),
                    )
                    updated_count += 1

            conn.commit()
            logger.info(
                f"Результат импорта: добавлено {inserted_count}, обновлено {updated_count}, пропущено {skipped_count}"
            )

    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при импорте данных: {str(e)}")
        raise


def main():
    """Основная функция для создания таблицы и импорта данных"""
    conn = None
    try:
        # Устанавливаем соединение с базой данных
        conn = psycopg2.connect(**db_params)
        logger.info("Соединение с базой данных установлено")

        # Создаем таблицу если не существует
        create_total_product_table(conn)

        # Путь к файлу с данными
        data_file_path = "result_products.json"  # Замените на реальный путь к файлу

        # Импортируем данные
        import_total_products(conn, data_file_path)

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
    finally:
        if conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто")


if __name__ == "__main__":
    main()
