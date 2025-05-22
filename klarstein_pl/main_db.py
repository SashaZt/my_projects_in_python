import json

import psycopg2
from psycopg2.extras import execute_values

# Параметры подключения к базе данных
db_params = {
    "user": "klarstein_pl_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "dbname": "klarstein_pl",
    "host": "localhost",
    "port": 5431,
}


def insert_product_data(json_file_path):
    """
    Вставляет данные из JSON-файла в базу данных PostgreSQL
    """
    # Чтение JSON-файла
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Подключение к базе данных
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    try:
        # 1. Вставка основной информации о продукте
        cur.execute(
            """
            INSERT INTO products (sku, price, created_at, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (data["product"]["sku"], data["product"]["price"]),
        )
        product_id = cur.fetchone()[0]

        # 2. Получение ID языков
        cur.execute("SELECT id, code FROM languages")
        languages = {code: lang_id for lang_id, code in cur.fetchall()}

        # 3. Вставка названий продукта для польского языка
        if "name_pl" in data["product"]:
            cur.execute(
                """
                INSERT INTO product_names (product_id, language_id, name)
                VALUES (%s, %s, %s)
                """,
                (product_id, languages["pl"], data["product"]["name_pl"]),
            )

        # 4. Вставка изображений продукта
        if "images" in data["product"]:
            image_data = [
                (product_id, url, idx)
                for idx, url in enumerate(data["product"]["images"])
            ]
            execute_values(
                cur,
                """
                INSERT INTO product_images (product_id, image_url, position)
                VALUES %s
                """,
                image_data,
            )

        # 5. Вставка категорий (хлебных крошек)
        if "breadcrumbs_pl" in data:
            for breadcrumb in data["breadcrumbs_pl"]:
                # Проверка существования категории
                cur.execute(
                    """
                    WITH new_category AS (
                        INSERT INTO categories (parent_id, created_at)
                        VALUES (NULL, CURRENT_TIMESTAMP)
                        ON CONFLICT DO NOTHING
                        RETURNING id
                    )
                    SELECT id FROM new_category
                    UNION ALL
                    SELECT id FROM categories
                    LIMIT 1
                    """
                )
                category_id = cur.fetchone()[0]

                # Вставка названия категории
                cur.execute(
                    """
                    INSERT INTO category_names (category_id, language_id, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (category_id, language_id) DO UPDATE
                    SET name = EXCLUDED.name
                    """,
                    (category_id, languages["pl"], breadcrumb),
                )

                # Связь продукта с категорией
                cur.execute(
                    """
                    INSERT INTO product_categories (product_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (product_id, category_id),
                )

        # 6. Вставка секций описания
        if "description_pl" in data:
            for idx, section in enumerate(data["description_pl"]):
                section_type = ""

                # Определение типа секции на основе заголовка
                title_lower = section["title_pl"].lower()
                if "zalety" in title_lower:
                    section_type = "advantages"
                elif "szczegóły" in title_lower:
                    section_type = "details"
                elif "podstawowe" in title_lower:
                    section_type = "specs"
                elif "wymiary" in title_lower:
                    section_type = "dimensions"
                else:
                    section_type = "other"

                # Вставка секции
                cur.execute(
                    """
                    INSERT INTO description_sections (product_id, section_type, position)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (product_id, section_type, idx),
                )
                section_id = cur.fetchone()[0]

                # Вставка контента секции
                cur.execute(
                    """
                    INSERT INTO description_section_contents (section_id, language_id, title, description)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        section_id,
                        languages["pl"],
                        section["title_pl"],
                        section["description_pl"],
                    ),
                )

        # Фиксация изменений
        conn.commit()
        print(f"Продукт {data['product']['sku']} успешно добавлен в базу данных!")

    except Exception as e:
        conn.rollback()
        print(f"Произошла ошибка: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # Путь к JSON-файлу
    json_file_path = "file_name.json"
    insert_product_data(json_file_path)
