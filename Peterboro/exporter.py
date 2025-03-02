import csv
import json
import os
import sys

# Импортируем функции из модуля парсера
from parser import (
    analyze_pdf_with_multiple_pages,
    current_directory,
    pdf_directory,
    save_json_data,
    temp_directory,
)
from pathlib import Path

from loguru import logger

# Настройка директорий для экспорта
output_directory = current_directory / "output"
output_directory.mkdir(parents=True, exist_ok=True)


def post_process_data(data):
    """
    Обрабатывает объединенные данные для создания структурированного JSON
    """
    document_type = data.get("document_type", "UNKNOWN")
    processed = {
        "page_count": data.get("page_count", 0),
        "document_type": document_type,
        "property": {},
    }

    # Данные с первой страницы
    page1_data = data.get("data", {})

    # Базовая информация о недвижимости
    processed["property"]["document_type"] = document_type

    # Обработка в зависимости от типа документа
    if document_type == "RESIDENTIAL":
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

        # Данные со второй страницы для RESIDENTIAL
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

    # Добавьте в функцию post_process_data в файле exporter.py
    # в части обработки типа COMMERCIAL:

    elif document_type == "COMMERCIAL":
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

        # Данные со второй страницы для COMMERCIAL
        if "page_2" in data.get("data", {}):
            page2_data = data["data"]["page_2"]

            # Обработка данных о здании для коммерческих свойств
            building_info = page2_data.get("building_info", {})
            processed["property"]["commercial_building_info"] = building_info
    else:
        # Для неизвестного типа используем базовую структуру
        processed["property"]["raw_data"] = page1_data

    return processed


def export_to_json(raw_data, output_path):
    """
    Экспортирует обработанные данные в JSON файл
    """
    # Постобработка данных
    processed_data = post_process_data(raw_data)

    # Сохраняем в JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Данные экспортированы в JSON: {output_path}")
    return output_path


def export_multiple_pdfs_to_csv(pdf_data_list, output_path):
    """
    Экспортирует данные из нескольких PDF файлов в единый CSV файл.

    Args:
        pdf_data_list: Список кортежей (имя_файла, обработанные_данные)
        output_path: Путь для сохранения CSV файла

    Returns:
        Путь к созданному CSV файлу
    """
    # Определяем заголовки CSV на основе структуры Peterboro.xlsx
    headers = [
        "File Name",
        "Document Type",
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
        # Заголовки для RESIDENTIAL
        "Style",
        "Story Height",
        "Attic",
        "Exterior Walls",
        # Заголовки для COMMERCIAL
        "Year Built/Eff Year",
        "Building #",
        "Structure Type",
        "Identical Units",
        "Total Units",
        "Grade",
        "# Covered Parking",
        "# Uncovered Parking",
    ]

    # Запись CSV файла
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for file_name, processed_data in pdf_data_list:
            # Создаем строку данных для экспорта
            data_row = {
                "File Name": file_name,
                "Document Type": processed_data.get("document_type", "UNKNOWN"),
            }

            # Извлекаем данные из обработанной структуры
            property_data = processed_data.get("property", {})

            # Если документ не распознан или имеет неподдерживаемый тип,
            # записываем только базовую информацию
            if data_row["Document Type"] not in ["RESIDENTIAL", "COMMERCIAL"]:
                writer.writerow(data_row)
                continue

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

            # В зависимости от типа документа обрабатываем соответствующие поля
            if data_row["Document Type"] == "RESIDENTIAL":
                # Данные о здании для RESIDENTIAL
                building_info = property_data.get("building_info", {})
                data_row["Style"] = building_info.get("Style", "")
                data_row["Story Height"] = building_info.get("Story height", "")
                data_row["Attic"] = building_info.get("Attic", "")
                data_row["Exterior Walls"] = building_info.get("Exterior Walls", "")

            elif data_row["Document Type"] == "COMMERCIAL":
                # Данные о здании для COMMERCIAL
                building_info = property_data.get("commercial_building_info", {})
                data_row["Year Built/Eff Year"] = building_info.get(
                    "Year Built/Eff Year", ""
                )
                data_row["Building #"] = building_info.get("Building #", "")
                data_row["Structure Type"] = building_info.get("Structure Type", "")
                data_row["Identical Units"] = building_info.get("Identical Units", "")
                data_row["Total Units"] = building_info.get("Total Units", "")
                data_row["Grade"] = building_info.get("Grade", "")
                data_row["# Covered Parking"] = building_info.get(
                    "# Covered Parking", ""
                )
                data_row["# Uncovered Parking"] = building_info.get(
                    "# Uncovered Parking", ""
                )

            # Записываем строку в CSV
            writer.writerow(data_row)

    logger.info(f"Данные экспортированы в CSV: {output_path}")
    return output_path


def process_single_pdf(pdf_path):
    """
    Обрабатывает один PDF файл и экспортирует данные в JSON и CSV
    """
    pdf_name = pdf_path.name

    # Анализируем PDF
    raw_data = analyze_pdf_with_multiple_pages(pdf_path, pages_to_process=[0, 1])

    # Экспортируем в JSON
    json_output_path = output_directory / f"{pdf_path.stem}_processed.json"
    export_to_json(raw_data, json_output_path)

    # Экспортируем в CSV (индивидуальный файл)
    csv_output_path = output_directory / f"{pdf_path.stem}.csv"
    processed_data = post_process_data(raw_data)
    export_multiple_pdfs_to_csv([(pdf_name, processed_data)], csv_output_path)

    return {
        "pdf_path": pdf_path,
        "json_path": json_output_path,
        "csv_path": csv_output_path,
    }


def process_directory(directory_path=pdf_directory):
    """
    Обрабатывает все PDF файлы в указанной директории
    """
    pdf_files = list(directory_path.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"PDF файлы не найдены в директории {directory_path}")
        return []

    logger.info(f"Найдено {len(pdf_files)} PDF файлов для обработки")

    # Список для хранения обработанных данных
    pdf_data_list = []
    results = []

    for pdf_file in pdf_files:
        logger.info(f"Обработка файла {pdf_file.name}")

        # Анализируем PDF
        raw_data = analyze_pdf_with_multiple_pages(pdf_file, pages_to_process=[0, 1])

        # Постобработка данных
        processed_data = post_process_data(raw_data)

        # Сохраняем индивидуальный JSON
        json_output_path = output_directory / f"{pdf_file.stem}_processed.json"
        save_json_data(processed_data, json_output_path)

        # Добавляем в список для общего CSV
        pdf_data_list.append((pdf_file.name, processed_data))

        results.append({"pdf_path": pdf_file, "json_path": json_output_path})

    # Экспортируем все данные в один CSV
    csv_output_path = output_directory / "peterboro.csv"
    export_multiple_pdfs_to_csv(pdf_data_list, csv_output_path)

    logger.info(f"Все данные экспортированы в общий CSV: {csv_output_path}")

    return results


# Если файл запускается напрямую
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Режим обработки одного файла
        pdf_file = sys.argv[1]
        pdf_path = (
            pdf_directory / pdf_file if not os.path.isabs(pdf_file) else Path(pdf_file)
        )

        if not pdf_path.exists():
            print(f"Ошибка: файл {pdf_path} не найден")
            sys.exit(1)

        print(f"Обработка файла: {pdf_path}")
        result = process_single_pdf(pdf_path)
        print(f"Данные экспортированы в JSON: {result['json_path']}")
        print(f"Данные экспортированы в CSV: {result['csv_path']}")
    else:
        # Режим обработки всей директории
        print(f"Обработка всех PDF файлов в директории: {pdf_directory}")
        results = process_directory()
        print(f"Обработано {len(results)} файлов")
        print(f"Все данные экспортированы в CSV: {output_directory / 'peterboro.csv'}")
