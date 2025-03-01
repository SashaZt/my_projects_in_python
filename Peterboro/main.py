import csv
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
    - "tabular_data" - для обычных табличных данных со второй страницы
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

    elif table_type == "tabular_data":
        # Для таблиц со второй страницы (lines_13-23)
        # Обрабатываем как набор ключ-значений
        for row in table:
            if len(row) >= 2 and row[0]:
                key = row[0].strip()
                value = row[1].strip() if len(row) > 1 and row[1] else None
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


def get_table_definitions(page_no):
    """
    Возвращает определения таблиц для указанной страницы
    """
    # Таблицы для первой страницы
    if page_no == 0:
        return [
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
    # Таблицы для второй страницы
    elif page_no == 1:
        return [
            {
                "name": "building_style",
                "horizontal_lines": [75, 85, 95, 105, 115],
                "vertical_lines": [30, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "exterior_features",
                "horizontal_lines": [75, 85, 95, 105, 115],
                "vertical_lines": [190, 260, 320],
                "type": "tabular_data",
            },
            {
                "name": "rooms",
                "horizontal_lines": [150, 160, 170, 180],
                "vertical_lines": [30, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "kitchen_info",
                "horizontal_lines": [150, 160, 170, 180],
                "vertical_lines": [190, 260, 320],
                "type": "tabular_data",
            },
            {
                "name": "bathroom_info",
                "horizontal_lines": [205, 215, 225, 235],
                "vertical_lines": [30, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "heat_info",
                "horizontal_lines": [205, 215, 225, 235],
                "vertical_lines": [190, 260, 320],
                "type": "tabular_data",
            },
            {
                "name": "physical_condition",
                "horizontal_lines": [252, 262, 270, 280, 290],
                "vertical_lines": [30, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "interior_features",
                "horizontal_lines": [252, 262, 270, 280],
                "vertical_lines": [190, 260, 320],
                "type": "tabular_data",
            },
            {
                "name": "construction_details",
                "horizontal_lines": [365, 373, 383],
                "vertical_lines": [30, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "value_history",
                "horizontal_lines": [510, 521, 530, 545],
                "vertical_lines": [15, 95, 137],
                "type": "tabular_data",
            },
            {
                "name": "picture_info",
                "horizontal_lines": [275, 287, 390],
                "vertical_lines": [365, 450],
                "type": "tabular_data",
            },
        ]
    else:
        return []


def analyze_pdf_page(pdf_path, page_no=0, save_debug_images=True):
    """
    Анализирует отдельную страницу PDF с множеством таблиц
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

        # Получаем определения таблиц для страницы
        table_definitions = get_table_definitions(page_no)

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
                    print(
                        f"Страница {page_no + 1}, Таблица '{table_name}' #{table_no + 1}:"
                    )
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
                filename = os.path.join(
                    temp_directory, f"page{page_no+1}_{table_name}.png"
                )
                image.save(filename)
                logger.info(f"Сохранено отладочное изображение: {filename}")

        # Дополнительное полное отладочное изображение
        if save_debug_images:
            image = page.to_image(resolution=150)
            filename = os.path.join(temp_directory, f"page_{page_no + 1}_full.png")
            image.save(filename)

    return results


def analyze_pdf_with_multiple_pages(
    pdf_path, pages_to_process=[0, 1], save_debug_images=True
):
    """
    Анализирует несколько страниц PDF и объединяет результаты
    """
    combined_results = {"page_count": 0, "pages_info": [], "data": {}}

    with pdfplumber.open(pdf_path) as pdf:
        combined_results["page_count"] = len(pdf.pages)

        for page_no in pages_to_process:
            if page_no >= len(pdf.pages):
                logger.error(
                    f"Страница {page_no} не существует в документе (всего {len(pdf.pages)} страниц)"
                )
                continue

            logger.info(f"Обработка страницы {page_no + 1}")
            page_results = analyze_pdf_page(pdf_path, page_no, save_debug_images)

            # Сохраняем информацию о странице
            combined_results["pages_info"].append(page_results["page_info"])

            # Объединяем данные
            if page_no == 0:  # Первая страница - основная информация о собственности
                combined_results["data"].update(page_results["data"])
            else:  # Другие страницы - дополнительные данные
                page_key = f"page_{page_no + 1}"
                combined_results["data"][page_key] = page_results["data"]

    return combined_results


def post_process_data(data):
    """
    Обрабатывает объединенные данные для создания структурированного JSON
    """
    processed = {"page_count": data.get("page_count", 0), "property": {}}

    # Данные с первой страницы
    page1_data = data.get("data", {})

    # Базовая информация о недвижимости
    processed["property"]["document_type"] = page1_data.get("document_type", {}).get(
        "document_type", ""
    )

    # Адрес и расположение
    processed["property"]["location"] = {
        "situs": page1_data.get("Situs", ""),
        "card": page1_data.get("Card", ""),
        "class": page1_data.get("Class", ""),
        "total_acres": page1_data.get("Total Acres", ""),
    }

    # Информация о владельце
    owner_address = page1_data.get("owner_address", {})
    processed["property"]["owner"] = {
        "Owner1": owner_address.get("Owner1", ""),
        "Owner2": owner_address.get("Owner2", ""),
        "Owner3": owner_address.get("Owner3", ""),
        "Owner4": owner_address.get("Owner4", ""),
        "Owner5": owner_address.get("Owner5", ""),
    }

    # Детали собственности
    property_details = page1_data.get("property_details", {})
    processed["property"]["details"] = property_details

    # Данные оценки
    value_data = page1_data.get("value_data", {})
    processed["property"]["assessment"] = value_data

    # Информация о передаче прав
    processed["property"]["transfer"] = {
        "date": page1_data.get("transfer_date", {}).get("Transfer Date", ""),
        "price": page1_data.get("transfer_price", {}).get("Price", ""),
        "type": page1_data.get("transfer_type", {}).get("Type", ""),
        "validity": page1_data.get("transfer_validity", {}).get("Validity", ""),
    }

    # Данные со второй страницы
    if "page_2" in data.get("data", {}):
        page2_data = data["data"]["page_2"]

        # Создаем единый словарь для всех строительных характеристик
        building_info = {}

        # Объединяем все словари с информацией о здании в один общий словарь
        building_info.update(page2_data.get("building_style", {}))
        building_info.update(page2_data.get("exterior_features", {}))
        building_info.update(page2_data.get("rooms", {}))
        building_info.update(page2_data.get("kitchen_info", {}))
        building_info.update(page2_data.get("bathroom_info", {}))
        building_info.update(page2_data.get("heat_info", {}))
        building_info.update(page2_data.get("physical_condition", {}))
        building_info.update(page2_data.get("interior_features", {}))
        building_info.update(page2_data.get("construction_details", {}))

        processed["property"]["building_info"] = building_info

        # Отдельный раздел для истории оценки
        processed["property"]["value_history"] = page2_data.get("value_history", {})

        # Информация о изображении
        processed["property"]["picture_info"] = page2_data.get("picture_info", {})

    return processed


def save_json_data(data, output_path):
    """
    Сохраняет данные в JSON-файл
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные сохранены в {output_path}")
    return output_path


def export_multiple_pdfs_to_csv(pdf_data_list, output_directory):
    """
    Экспортирует данные из нескольких PDF файлов в единый CSV файл.

    Args:
        pdf_data_list: Список кортежей (имя_файла, обработанные_данные)
        output_directory: Директория для сохранения CSV файла

    Returns:
        Путь к созданному CSV файлу
    """
    # Определяем заголовки CSV на основе структуры Peterboro.xlsx
    headers = [
        "Parcel ID",
        "File Name",
        "Owner1",
        "Owner2",
        "Owner3",
        "Owner4",
        "Owner5",
        "Situs",
        "Card",
        "Class",
        "District",
        "Zone",
        "Living Units",
        "Neighborhood",
        "Alternate ID",
        "Vol/Pg",
        "Total Acres",
        "Land Value",
        "Building Value",
        "Total Value",
        "Transfer Date",
        "Price",
        "Type",
        "Validity",
        "Style",
        "Story Height",
        "Attic",
        "Exterior Walls",
        # Добавьте другие заголовки из второй страницы
    ]

    # Создаем выходной путь
    output_path = os.path.join(output_directory, "combined_property_data.csv")

    # Запись CSV файла
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for file_name, processed_data in pdf_data_list:
            # Создаем строку данных для экспорта
            data_row = {"File Name": file_name}

            # Извлекаем данные из обработанной структуры
            property_data = processed_data.get("property", {})

            # Информация о владельце
            owner_data = property_data.get("owner", {})
            data_row["Owner1"] = owner_data.get("Owner1", "")
            data_row["Owner2"] = owner_data.get("Owner2", "")
            data_row["Owner3"] = owner_data.get("Owner3", "")
            data_row["Owner4"] = owner_data.get("Owner4", "")
            data_row["Owner5"] = owner_data.get("Owner5", "")

            # Адрес и расположение
            location_data = property_data.get("location", {})
            data_row["Situs"] = location_data.get("situs", "")
            data_row["Card"] = location_data.get("card", "")
            data_row["Class"] = location_data.get("class", "")
            data_row["Total Acres"] = location_data.get("total_acres", "")

            # Детали собственности
            details_data = property_data.get("details", {})
            data_row["District"] = details_data.get("District", "")
            data_row["Zone"] = details_data.get("Zoning", "")
            data_row["Living Units"] = details_data.get("Living Units", "")
            data_row["Neighborhood"] = details_data.get("Neighborhood", "")
            data_row["Alternate ID"] = details_data.get("Alternate ID", "")
            data_row["Vol/Pg"] = details_data.get("Vol / Pg", "")

            # Данные оценки
            assessment_data = property_data.get("assessment", {})
            data_row["Land Value"] = assessment_data.get("Land", "")
            data_row["Building Value"] = assessment_data.get("Building", "")
            data_row["Total Value"] = assessment_data.get("Total", "")

            # Информация о передаче прав
            transfer_data = property_data.get("transfer", {})
            data_row["Transfer Date"] = transfer_data.get("date", "")
            data_row["Price"] = transfer_data.get("price", "")
            data_row["Type"] = transfer_data.get("type", "")
            data_row["Validity"] = transfer_data.get("validity", "")

            # Данные о здании (со второй страницы)
            building_info = property_data.get("building_info", {})
            data_row["Style"] = building_info.get("Style", "")
            data_row["Story Height"] = building_info.get("Story height", "")
            data_row["Attic"] = building_info.get("Attic", "")
            data_row["Exterior Walls"] = building_info.get("Exterior Walls", "")

            # Параметры для записи CSV
            # Определите идентификатор участка (в данном случае используем местоположение)
            parcel_id = location_data.get("situs", "").replace(" ", "_")
            if not parcel_id:
                parcel_id = "unknown_parcel"

            data_row["Parcel ID"] = parcel_id

            # Записываем строку в CSV
            writer.writerow(data_row)

    return output_path


if __name__ == "__main__":
    # pdf_file = "R001-013-000.pdf"
    # pdf_path = pdf_directory / pdf_file

    # # Анализируем обе страницы PDF
    # raw_data = analyze_pdf_with_multiple_pages(
    #     pdf_path,
    #     pages_to_process=[0, 1],  # Обрабатываем первую и вторую страницы
    #     save_debug_images=True,
    # )

    # # Постобработка данных
    # processed_data = post_process_data(raw_data)

    # # Сохраняем сырые данные для отладки
    # raw_output_path = temp_directory / f"{pdf_file.replace('.pdf', '')}_raw_data.json"
    # save_json_data(raw_data, raw_output_path)

    # # Сохраняем обработанные данные
    # output_path = temp_directory / f"{pdf_file.replace('.pdf', '')}_processed.json"
    # saved_path = save_json_data(processed_data, output_path)

    # # Выводим информацию о результате
    # print(f"\nОбработка завершена:")
    # print(f"Обработано страниц: {len(raw_data['pages_info'])}")
    # print(f"Сырые данные сохранены в {raw_output_path}")
    # print(f"Обработанные данные сохранены в {saved_path}")
    # Для обработки нескольких файлов
    pdf_data_list = []
    for pdf_file in pdf_directory.glob("*.pdf"):
        # Анализируем PDF
        raw_data = analyze_pdf_with_multiple_pages(pdf_file, pages_to_process=[0, 1])
        processed_data = post_process_data(raw_data)
        pdf_data_list.append((pdf_file.name, processed_data))

    # Экспортируем все в один CSV
    combined_csv = export_multiple_pdfs_to_csv(pdf_data_list, temp_directory)
    print(f"Данные всех PDF файлов экспортированы в CSV: {combined_csv}")
