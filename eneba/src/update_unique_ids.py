# src/update_unique_ids.py
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from config_utils import load_config
from logger import logger

# Загружаем конфигурацию
config = load_config()
BASE_DIR = Path(__file__).parent.parent  # Для модулей в папке src
db_path = BASE_DIR / config["files"]["db_file"]


def extract_ids_from_excel(file_path):
    """
    Извлекает Код_товару и Унікальний_ідентифікатор из Excel-файла

    Args:
        file_path (str): Путь к Excel-файлу

    Returns:
        dict: Словарь с product_code в качестве ключа и unique_id в качестве значения
    """
    try:
        # Загружаем Excel-файл
        logger.info(f"Загрузка Excel-файла: {file_path}")
        df = pd.read_excel(file_path)

        # Получаем реальные названия колонок
        column_names = list(df.columns)
        logger.info(f"Найденные колонки в файле: {column_names}")

        # Словарь для маппинга возможных имен колонок
        column_mapping = {
            "Код_товару": ["Код_товару", "Код товару", "Код", "A"],
            "Унікальний_ідентифікатор": [
                "Унікальний_ідентифікатор",
                "Унікальний ідентифікатор",
                "ID",
                "Y",
            ],
        }

        # Находим реальные имена колонок
        real_columns = {}
        for req_col, possible_names in column_mapping.items():
            found = False
            for name in possible_names:
                if name in column_names:
                    real_columns[req_col] = name
                    found = True
                    break

            if not found:
                # Если колонка не найдена по имени, попробуем по индексу
                if req_col == "Код_товару" and len(column_names) > 0:
                    # Первая колонка (A)
                    real_columns[req_col] = column_names[0]
                    logger.warning(
                        f"Колонка 'Код_товару' не найдена по имени. Используем первую колонку: {column_names[0]}"
                    )
                elif req_col == "Унікальний_ідентифікатор" and len(column_names) > 24:
                    # 25-я колонка (Y)
                    real_columns[req_col] = column_names[24]
                    logger.warning(
                        f"Колонка 'Унікальний_ідентифікатор' не найдена по имени. Используем колонку Y: {column_names[24]}"
                    )
                else:
                    logger.error(f"Не удалось найти колонку {req_col} в файле")
                    return None

        logger.info(f"Используемые колонки: {real_columns}")

        # Извлекаем данные
        result = {}
        for idx, row in df.iterrows():
            product_code = row[real_columns["Код_товару"]]
            unique_id = row[real_columns["Унікальний_ідентифікатор"]]

            # Пропускаем записи с пустыми значениями
            if pd.isna(product_code) or pd.isna(unique_id):
                continue

            # Преобразуем значения к строкам
            product_code = str(product_code).strip()
            unique_id = str(unique_id).strip()

            # Добавляем в результат, только если оба значения не пусты
            if product_code and unique_id:
                result[product_code] = unique_id

        logger.info(f"Извлечено {len(result)} пар ID из Excel-файла")
        return result

    except Exception as e:
        logger.error(f"Ошибка при обработке Excel-файла: {str(e)}")
        return None


def update_unique_ids_in_db(id_mapping):
    """
    Обновляет значения unique_id в базе данных

    Args:
        id_mapping (dict): Словарь с product_code в качестве ключа и unique_id в качестве значения

    Returns:
        tuple: (обновлено, ошибок)
    """
    if not id_mapping:
        logger.error("Пустой словарь ID для обновления")
        return 0, 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    errors = 0
    not_found = 0

    # Проверяем существование таблицы
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
    )
    if not cursor.fetchone():
        logger.error("Таблица 'products' не существует в базе данных")
        conn.close()
        return 0, 0

    # Проверяем существование колонок
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]

    if "product_code" not in columns or "unique_id" not in columns:
        logger.error("Необходимые колонки не найдены в таблице 'products'")
        conn.close()
        return 0, 0

    # Создаем словарь существующих кодов товаров для оптимизации запросов
    cursor.execute("SELECT product_code FROM products")
    existing_codes = set(row[0] for row in cursor.fetchall() if row[0])

    # Обновляем unique_id для каждого product_code
    for product_code, unique_id in id_mapping.items():
        try:
            if product_code in existing_codes:
                cursor.execute(
                    "UPDATE products SET unique_id = ? WHERE product_code = ?",
                    (unique_id, product_code),
                )

                if cursor.rowcount > 0:
                    updated += 1
                    if updated % 100 == 0:  # Логируем каждые 100 обновлений
                        logger.info(f"Обновлено записей: {updated}")
                else:
                    not_found += 1
            else:
                not_found += 1
                if not_found % 100 == 0:  # Логируем каждые 100 не найденных
                    logger.warning(f"Код товара не найден в БД: {product_code}")

        except sqlite3.Error as e:
            logger.error(
                f"Ошибка при обновлении записи с кодом {product_code}: {str(e)}"
            )
            errors += 1

    conn.commit()
    conn.close()

    logger.info(f"Обновление уникальных идентификаторов завершено:")
    logger.info(f"- Обновлено записей: {updated}")
    logger.info(f"- Не найдено кодов товаров: {not_found}")
    logger.info(f"- Ошибок: {errors}")

    return updated, errors


def select_excel_file():
    """Предлагает выбрать Excel-файл"""
    # Ищем Excel-файлы в текущей директории
    excel_files = list(Path(".").glob("*.xlsx")) + list(Path(".").glob("*.xls"))

    if not excel_files:
        print("Не найдено Excel-файлов в текущей директории.")
        print("Укажите путь к Excel-файлу:")
        excel_file = input("> ").strip()

        if not os.path.exists(excel_file):
            print(f"Файл {excel_file} не найден.")
            return None
    else:
        # Выводим список найденных файлов
        print("Найдены следующие Excel-файлы:")
        for i, file in enumerate(excel_files, 1):
            print(f"{i}. {file}")

        # Просим пользователя выбрать файл
        choice = input(f"Выберите файл (1-{len(excel_files)}): ").strip()
        try:
            idx = int(choice) - 1
            excel_file = str(excel_files[idx])
        except (ValueError, IndexError):
            print("Некорректный выбор.")
            return None

    return excel_file


def main():
    print("\n===== ОБНОВЛЕНИЕ УНИКАЛЬНЫХ ИДЕНТИФИКАТОРОВ В БАЗЕ ДАННЫХ =====\n")

    # Проверяем, указан ли файл в аргументах командной строки
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        if not os.path.exists(excel_file):
            print(f"Файл {excel_file} не найден.")
            return
    else:
        excel_file = select_excel_file()
        if not excel_file:
            return

    # Проверяем существование базы данных
    if not os.path.exists(db_path):
        print(f"База данных {db_path} не найдена.")
        return

    print(f"Используется база данных: {db_path}")
    print(f"Обрабатывается файл: {excel_file}")

    # Извлекаем данные из Excel
    id_mapping = extract_ids_from_excel(excel_file)
    if not id_mapping:
        print("Не удалось извлечь данные из Excel-файла.")
        return

    print(f"Извлечено {len(id_mapping)} пар ID из Excel-файла")

    # Запрашиваем подтверждение перед обновлением
    confirm = (
        input(
            f"Обновить {len(id_mapping)} уникальных идентификаторов в базе данных? (y/n): "
        )
        .strip()
        .lower()
    )
    if confirm != "y":
        print("Операция отменена.")
        return

    # Обновляем данные в БД
    updated, errors = update_unique_ids_in_db(id_mapping)

    # Выводим итоговую статистику
    print("\n===== РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ =====")
    print(f"Обработано записей: {len(id_mapping)}")
    print(f"Успешно обновлено: {updated}")
    print(f"Ошибок: {errors}")
    print(f"Не обновлено: {len(id_mapping) - updated - errors}")
    print("===================================\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {str(e)}")
        logger.exception("Непредвиденная ошибка при выполнении скрипта:")
