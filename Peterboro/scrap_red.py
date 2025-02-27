# residential
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber
from loguru import logger

# Настройка путей
current_directory = Path.cwd()
pdf_directory = current_directory / "pdf"
log_directory = current_directory / "log"
temp_directory = current_directory / "temp"
temp_directory.mkdir(parents=True, exist_ok=True)
pdf_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def extract_table_data(table, table_name="", table_type=""):
    """
    Преобразует данные таблицы в словарь согласно указанному типу

    table_type:
    - "header" - заголовок документа
    - "key_value_row" - таблица, где в каждой строке ключ: значение
    - "address" - для адресных данных
    - "property_details" - для деталей собственности
    - "value_data" - для данных оценки
    """
    result = {}

    if not table or len(table) == 0:
        logger.warning(f"Таблица {table_name} пуста")
        return result

    # Обработка по типу таблицы
    if table_type == "header":
        # Для заголовка документа (lines_01)
        if len(table) > 0 and len(table[0]) >= 2:
            result["document_type"] = table[0][1] if table[0][1] else ""

    elif table_type == "key_value_row":
        # Для таблиц с ключ:значение в строке (lines_02, lines_03, lines_04)
        if len(table) > 0 and len(table[0]) >= 2:
            key = table[0][0].replace(":", "").strip() if table[0][0] else ""
            value = table[0][1].strip() if table[0][1] else ""
            if key:
                result[key] = value

    elif table_type == "address":
        # Для адресных данных (lines_05) - разделяем на Owner1, Owner2, и т.д.
        for i, row in enumerate(table, 1):
            if row and row[0]:
                owner_key = f"Owner{i}"
                result[owner_key] = row[0].strip()
            else:
                # Если строка пустая, добавляем None
                owner_key = f"Owner{i}"
                result[owner_key] = None

    elif table_type == "property_details":
        # Для деталей собственности (lines_06)
        for row in table:
            if len(row) >= 2 and row[0]:
                key = row[0].strip()
                value = row[1].strip() if len(row) > 1 and row[1] else ""
                result[key] = value

    elif table_type == "single_key_value":
        # Для одиночных ключ-значение (lines_07)
        if len(table) > 0 and len(table[0]) >= 2:
            key = table[0][0].replace(":", "").strip() if table[0][0] else ""
            value = table[0][1].strip() if len(table[0]) > 1 and table[0][1] else ""
            if key:
                result[key] = value

    elif table_type == "value_data":
        # Для данных оценки (lines_08)
        for row in table:
            if len(row) >= 2:
                key = row[0].strip() if row[0] else ""
                value = row[1].strip() if len(row) > 1 and row[1] else ""
                if key:
                    result[key] = value

    elif table_type == "transfer_data":
        # Для данных о передаче прав (lines_09, lines_10, lines_11, lines_12)
        if len(table) >= 2:
            key = table[0][0].strip() if table[0][0] else ""
            value = table[1][0].strip() if len(table) > 1 and table[1][0] else ""
            if key:
                result[key] = value

    else:
        # По умолчанию, возвращаем сырые данные
        raw_data = []
        for row in table:
            cleaned_row = [
                str(cell).strip() if cell is not None else "" for cell in row
            ]
            raw_data.append(cleaned_row)
        result = raw_data

    return result


def analyze_pdf_with_multiple_tables(pdf_path, page_no=0, save_debug_images=True):
    """
    Анализирует PDF с множеством таблиц на странице
    """
    results = {"page_info": {"number": page_no + 1}, "data": {}}

    with pdfplumber.open(pdf_path) as pdf:
        if page_no >= len(pdf.pages):
            logger.error(
                f"Страница {page_no} не существует в документе (всего {len(pdf.pages)} страниц)"
            )
            return results

        page = pdf.pages[page_no]
        results["page_info"]["width"] = page.width
        results["page_info"]["height"] = page.height

        # Определение всех таблиц на странице с типами данных
        table_definitions = [
            {
                "name": "document_type",
                "horizontal_lines": [10, 25],
                "vertical_lines": [50, 60, 137],
                "type": "header",
            },
            {
                "name": "situs",
                "horizontal_lines": [30, 45],
                "vertical_lines": [15, 40, 180],
                "type": "key_value_row",
            },
            {
                "name": "class",
                "horizontal_lines": [30, 45],
                "vertical_lines": [380, 405, 535],
                "type": "key_value_row",
            },
            {
                "name": "card",
                "horizontal_lines": [30, 45],
                "vertical_lines": [550, 572, 610],
                "type": "key_value_row",
            },
            {
                "name": "owner_address",
                "horizontal_lines": [65, 77, 86, 96, 106, 130],
                "vertical_lines": [15, 205],
                "type": "address",
            },
            {
                "name": "property_details",
                "horizontal_lines": [65, 75, 84, 93, 103, 110, 118, 130],
                "vertical_lines": [210, 265, 360],
                "type": "property_details",
            },
            {
                "name": "total_acres",
                "horizontal_lines": [300, 310],
                "vertical_lines": [15, 59, 90],
                "type": "single_key_value",
            },
            {
                "name": "value_data",
                "horizontal_lines": [240, 252, 262, 275],
                "vertical_lines": [420, 470, 520],
                "type": "value_data",
            },
            {
                "name": "transfer_date",
                "horizontal_lines": [437, 449, 458],
                "vertical_lines": [15, 80],
                "type": "transfer_data",
            },
            {
                "name": "transfer_price",
                "horizontal_lines": [437, 449, 458],
                "vertical_lines": [120, 150],
                "type": "transfer_data",
            },
            {
                "name": "transfer_type",
                "horizontal_lines": [437, 449, 458],
                "vertical_lines": [150, 200],
                "type": "transfer_data",
            },
            {
                "name": "transfer_validity",
                "horizontal_lines": [437, 449, 458],
                "vertical_lines": [270, 410],
                "type": "transfer_data",
            },
        ]

        # Обработка каждого определения таблицы
        for table_def in table_definitions:
            table_name = table_def["name"]
            horizontal_lines = table_def["horizontal_lines"]
            vertical_lines = table_def["vertical_lines"]
            table_type = table_def.get("type", "")

            logger.info(f"Обработка таблицы: {table_name} (тип: {table_type})")

            # Настройки таблицы
            table_settings = {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": vertical_lines,
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": horizontal_lines,
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 10,
                "min_words_vertical": 1,
                "min_words_horizontal": 1,
            }

            # Извлечение таблицы
            tables = page.extract_tables(table_settings)

            # Вывод для отладки
            if tables:
                for table_no, table in enumerate(tables):
                    print(f"Таблица '{table_name}' #{table_no + 1}:")
                    for row in table:
                        print(row)
                    print("\n")

                # Преобразование и сохранение данных
                table_data = extract_table_data(tables[0], table_name, table_type)

                # Добавляем данные в результаты
                if table_type == "key_value_row" or table_type == "single_key_value":
                    # Добавляем ключи-значения непосредственно в корень результатов
                    results["data"].update(table_data)
                else:
                    # Сохраняем блок данных под именем таблицы
                    results["data"][table_name] = table_data
            else:
                logger.warning(f"Таблица '{table_name}' не найдена")

            # Сохранение отладочного изображения
            if save_debug_images:
                image = page.to_image(resolution=150)
                image.debug_tablefinder(table_settings)
                filename = os.path.join(temp_directory, f"{table_name}.png")
                image.save(filename)
                logger.info(f"Сохранено отладочное изображение: {filename}")

        # Дополнительное полное отладочное изображение
        if save_debug_images:
            image = page.to_image(resolution=150)
            filename = os.path.join(temp_directory, f"page_{page_no + 1}_full.png")
            image.save(filename)

    return results


def post_process_data(data):
    """
    Дополнительная обработка данных для создания более удобной структуры
    """
    processed = {}

    # Копируем информацию о странице
    processed["page_info"] = data.get("page_info", {})

    # Создаем основную структуру данных
    property_data = {}

    # Базовая информация о недвижимости
    property_data["document_type"] = (
        data.get("data", {}).get("document_type", {}).get("document_type", "")
    )

    # Адрес и расположение
    property_data["location"] = {
        "situs": data.get("data", {}).get("Situs", ""),
        "card": data.get("data", {}).get("Card", ""),
        "class": data.get("data", {}).get("Class", ""),
        "total_acres": data.get("data", {}).get("Total Acres", ""),
    }

    # Информация о владельце
    owner_address = data.get("data", {}).get("owner_address", {})
    property_data["owner"] = {
        "Owner1": owner_address.get("Owner1", ""),
        "Owner2": owner_address.get("Owner2", ""),
        "Owner3": owner_address.get("Owner3", ""),
        "Owner4": owner_address.get("Owner4", ""),
        "Owner5": owner_address.get("Owner5", ""),
    }

    # Детали собственности
    property_details = data.get("data", {}).get("property_details", {})
    property_data["details"] = property_details

    # Данные оценки
    value_data = data.get("data", {}).get("value_data", {})
    property_data["assessment"] = value_data

    # Информация о передаче прав
    property_data["transfer"] = {
        "date": data.get("data", {}).get("transfer_date", {}).get("Transfer Date", ""),
        "price": data.get("data", {}).get("transfer_price", {}).get("Price", ""),
        "type": data.get("data", {}).get("transfer_type", {}).get("Type", ""),
        "validity": data.get("data", {})
        .get("transfer_validity", {})
        .get("Validity", ""),
    }

    processed["property"] = property_data

    return processed


def save_table_data(data, output_path):
    """
    Сохраняет данные таблиц в JSON-файл
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные таблиц сохранены в {output_path}")
    return output_path


if __name__ == "__main__":
    pdf_file = "R001-017-002.pdf"
    pdf_path = pdf_directory / pdf_file

    # Анализируем PDF с множественными таблицами
    raw_data = analyze_pdf_with_multiple_tables(
        pdf_path, page_no=0, save_debug_images=True
    )

    # Постобработка данных
    processed_data = post_process_data(raw_data)

    # Сохраняем сырые данные для отладки
    raw_output_path = temp_directory / f"{pdf_file.replace('.pdf', '')}_raw_data.json"
    save_table_data(raw_data, raw_output_path)

    # Сохраняем обработанные данные
    output_path = temp_directory / f"{pdf_file.replace('.pdf', '')}_processed.json"
    saved_path = save_table_data(processed_data, output_path)

    # Выводим информацию о результате
    print(f"\nОбработка завершена:")
    print(f"Данные успешно извлечены для {pdf_file}")
    print(f"Сырые данные сохранены в {raw_output_path}")
    print(f"Обработанные данные сохранены в {saved_path}")
