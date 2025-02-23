import asyncio
import json
from pathlib import Path

import aiosqlite
import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
DB_PATH = config_directory / "rrr_lt.db"


# 1. Создание базы данных и таблицы
async def create_database():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT,
                search_query TEXT,
                code TEXT,
                category_name TEXT,
                description TEXT,
                total_price REAL,
                product_price REAL,
                delivery_price REAL,
                quantity INTEGER,
                used INTEGER,
                photo TEXT
            )
        """
        )
        # Новая таблица codes с уникальным индексом на code
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_time BOOLEAN DEFAULT FALSE

            )
        """
        )
        # Создаем уникальный индекс на поле code (необязательно, так как UNIQUE уже в определении)
        # await db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_code ON codes (code)')
        await db.commit()


# Асинхронная запись в БД
async def insert_data(db, data):
    await db.execute(
        """
        INSERT INTO products (brand,search_query, code,category_name, description, total_price, product_price, delivery_price, quantity, used, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    """,
        (
            data["Бренд"],
            data["Код"],
            data["Поисковый_запрос"],
            data["Категория"],
            data["Описание"],
            data["Цена товара и доставки"],
            data["Цена товара"],
            data["Цена только доставки"],
            int(data["Количество, ШТ."]),
            int(data["Б/У"]),
            data["Фото товара"],
        ),
    )
    await db.commit()


# Асинхронная обработка JSON и запись в БД
async def extract_and_save_product(json_data: str, id_product: str):
    # logger.info(f"Обработка данных для продукта: {id_product}")

    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при парсинге JSON для продукта {id_product}: {e}")
        return

    parts = data.get("parts", [])
    if not parts:
        # logger.error(f"Не найдены детали в JSON для продукта {id_product}")
        await set_search_time_true(id_product)  # Используем await

        return

    min_price_part = min(
        parts, key=lambda x: float(x.get("price", float("inf"))), default=None
    )
    sku = data.get("search_query", None)

    categories = data.get("categories", {})
    category_name = next(
        (
            category["name"]
            for category in categories.values()
            if category.get("part_count", 0) > 0
        ),
        None,
    )

    if min_price_part and category_name:
        manufacturer_code = min_price_part.get("manufacturer_code", None)
        if not manufacturer_code:
            # logger.warning(f"Отсутствует manufacturer_code в {id_product}")
            return

        delivery_price_str = min_price_part.get("delivery_price", "0")
        delivery_price_str = (
            delivery_price_str.replace(" €", "") if delivery_price_str else "0"
        )

        price_str = min_price_part.get("price", "0") or "0"

        try:
            delivery_price = float(delivery_price_str)
            price = float(price_str)
        except ValueError as e:
            logger.error(f"Ошибка преобразования цен в числа в {id_product}: {e}")
            return
        code = manufacturer_code.replace("#", "").strip()
        result = {
            "Бренд": min_price_part.get("car", {}).get("manufacturer", None),
            "Код": code,
            "Поисковый_запрос": sku,
            "Категория": category_name,
            "Описание": f"{category_name} | Оригінал | Гарантія на весь товар | Гарантійне встановлення запчастини у нас в СТО | Запчастини з Євро-розборів | Відповідальність | Телефонуйте | Мирного дня.",
            "Цена товара и доставки": delivery_price + price,
            "Цена товара": price,
            "Цена только доставки": delivery_price,
            "Количество, ШТ.": "1",
            "Б/У": "1",
            "Фото товара": None,
        }

        async with aiosqlite.connect(DB_PATH) as db:
            await insert_data(db, result)
            # logger.info(f"Данные из {id_product} успешно записаны в БД")


# Новая функция для получения всех search_query и code из таблицы products
async def get_all_codes_products():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT search_query, code FROM products")
        rows = await cursor.fetchall()
        # Возвращаем список кортежей (search_query, code)
        return rows


# Асинхронная запись кодов в таблицу codes
async def insert_data_codes(db, codes: list[str]):
    # Используем INSERT OR IGNORE, чтобы не записывать дубликаты
    await db.executemany(
        """
        INSERT OR IGNORE INTO codes (code) VALUES (?)
        """,
        [(code,) for code in codes],  # Преобразуем список кодов в список кортежей
    )
    await db.commit()


# Извлечение кодов из response.text и запись в БД
async def extract_and_save_codes(
    src: str,
):
    # logger.info(f"Извлечение кодов для продукта: {id_product}")

    all_data = []
    soup = BeautifulSoup(src, "lxml")
    code_tag = soup.find_all("button", attrs={"data-testid": "part-code"})

    if not code_tag:
        # logger.error(f"Не найдены коды в ответе для продукта {id_product}")
        return

    for code in code_tag:
        code_text = code.text.strip()  # Убираем лишние пробелы
        all_data.append(code_text)

    if all_data:
        async with aiosqlite.connect(DB_PATH) as db:
            await insert_data_codes(db, all_data)
            # logger.info(
            #     # f"Записано {len(all_data)} уникальных кодов для продукта {id_product}"
            # )
    # else:
    # logger.warning(f"Нет кодов для записи для продукта {id_product}")


# Новая функция для получения всех search_query и code из таблицы products
async def get_all_codes():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT code FROM codes")
        rows = await cursor.fetchall()
        # Возвращаем список строк code
        return [row[0] for row in rows]


async def set_search_time_true(id_product: str):
    """
    Устанавливает search_time = True для записи с code = id_product в таблице codes.

    Args:
        id_product (str): Значение code, для которого нужно установить search_time = True.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            # Обновляем search_time на True для указанного code
            result = await db.execute(
                """
                UPDATE codes 
                SET search_time = TRUE 
                WHERE code = ?
                """,
                (id_product,),
            )
            await db.commit()

            # Проверяем, сколько строк было обновлено
            rows_affected = result.rowcount
            if rows_affected > 0:
                pass
                # logger.info(f"Для продукта {id_product} установлен search_time = True")
            else:
                logger.warning(f"Продукт {id_product} не найден в таблице codes")

        except Exception as e:
            logger.error(f"Ошибка при обновлении search_time для {id_product}: {e}")


# # Пример генерации данных (замените на вашу логику)
# async def generate_sample_data(batch_size=1000):
#     for _ in range(0, 5_000_000, batch_size):
#         batch = []
#         for i in range(_, min(_ + batch_size, 5_000_000)):
#             result = {
#                 "Бренд": f"Brand_{i}",
#                 "Код": f"CODE{i:07d}",
#                 "Описание": "Category | Оригінал | Гарантія на весь товар | Гарантійне встановлення запчастини у нас в СТО | Запчастини з Євро-розборів | Відповідальність | Телефонуйте | Мирного дня.",
#                 "Цена товара и доставки": 150.5 + (i % 100),
#                 "Цена товара": 100.0 + (i % 50),
#                 "Цена только доставки": 50.5 + (i % 25),
#                 "Количество, ШТ.": "1",
#                 "Б/У": "1",
#                 "Фото товара": None,
#             }
#             batch.append(
#                 (
#                     result["Бренд"],
#                     result["Код"],
#                     result["Описание"],
#                     result["Цена товара и доставки"],
#                     result["Цена товара"],
#                     result["Цена только доставки"],
#                     int(result["Количество, ШТ."]),
#                     int(result["Б/У"]),
#                     result["Фото товара"],
#                 )
#             )
#         yield batch


# 3. Выгрузка данных в Excel
async def export_to_excel():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT brand, code, description, total_price, quantity, used, photo
            FROM products
            """
        )
        rows = await cursor.fetchall()

        # Создаем словарь для группировки по category_name
        data_by_category = {}

        for row in rows:
            brand, code, description, total_price, quantity, used, photo = row
            # Извлекаем category_name из description (первая часть до "|")
            category_name = (
                description.split(" | ")[0].strip() if description else "Unknown"
            )

            # Добавляем данные в словарь по категориям
            if category_name not in data_by_category:
                data_by_category[category_name] = []
            data_by_category[category_name].append(
                {
                    "Бренд": brand,
                    "Код": code,
                    "Описание": description,
                    "Цена товара": total_price,
                    "Количество, ШТ.": quantity,
                    "Б/У": used,
                    "Фото товара": photo,
                }
            )

        # Сохраняем данные в Excel-файлы по категориям
        for category_name, category_data in data_by_category.items():
            df = pd.DataFrame(
                category_data,
                columns=[
                    "Бренд",
                    "Код",
                    "Описание",
                    "Цена товара",
                    "Количество, ШТ.",
                    "Б/У",
                    "Фото товара",
                ],
            )
            # Формируем имя файла на основе category_name
            # Заменяем недопустимые символы в имени файла
            safe_category_name = "".join(
                c if c.isalnum() or c in " _-" else "_" for c in category_name
            )
            file_name = data_directory / f"{safe_category_name}.xlsx"
            df.to_excel(file_name, index=False, engine="openpyxl")
            logger.info(
                f"Данные для категории '{category_name}' выгружены в {file_name}"
            )


# # Основная функция
# async def main():
#     # Создаем базу данных
#     await create_database()

#     # Записываем данные
#     async for batch in generate_sample_data():
#         await insert_data(batch)
#         print(f"Записано {len(batch)} строк")

#     # Выгружаем в Excel
#     await export_to_excel()


# if __name__ == "__main__":
#     asyncio.run(main())
