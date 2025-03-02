import json
import os
import re
import sys
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


def detect_document_type(pdf_path):
    """
    Определяет тип документа PDF (RESIDENTIAL или COMMERCIAL)

    Returns:
        str: тип документа ('RESIDENTIAL', 'COMMERCIAL' или 'UNKNOWN')
    """
    document_type = "UNKNOWN"

    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) > 0:
            page = pdf.pages[0]

            # Настройки для определения заголовка документа
            header_settings = {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": [50, 60, 137],
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": [10, 25],
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 10,
                "min_words_vertical": 1,
                "min_words_horizontal": 1,
            }

            # Пытаемся извлечь таблицу заголовка
            header_tables = page.extract_tables(header_settings)

            if header_tables and len(header_tables) > 0 and len(header_tables[0]) > 0:
                header_row = header_tables[0][0]
                if len(header_row) >= 2 and header_row[1]:
                    document_type = header_row[1].strip()
                    logger.info(f"Определен тип документа: {document_type}")
                    return document_type

            # Если не удалось определить тип через таблицу, пытаемся использовать текст
            text = page.extract_text()
            if text:
                if "RESIDENTIAL" in text.upper():
                    document_type = "RESIDENTIAL"
                    logger.info(f"Определен тип документа из текста: {document_type}")
                elif "COMMERCIAL" in text.upper():
                    document_type = "COMMERCIAL"
                    logger.info(f"Определен тип документа из текста: {document_type}")

    logger.warning(
        f"Не удалось определить тип документа, используется по умолчанию: {document_type}"
    )
    return document_type


# Модифицируйте функцию extract_table_data, добавив специальную обработку для picture_info:


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

    # Специальная обработка для picture_info
    if table_name == "picture_info":
        # Проверка наличия "Type" в первой строке и данных во второй строке
        if len(table) >= 2 and table[0][0] == "Type" and table[1][0]:
            result["Type"] = table[1][0]
            logger.info(f"picture_info извлечен: Type = {table[1][0]}")
            return result
        # Другой возможный формат: первая колонка - "Type", вторая - значение
        elif (
            len(table) >= 1
            and len(table[0]) >= 2
            and table[0][0] == "Type"
            and table[0][1]
        ):
            result["Type"] = table[0][1]
            logger.info(f"picture_info извлечен (формат 2): Type = {table[0][1]}")
            return result
        # Еще один возможный формат: просто значения в первой или второй строке
        elif len(table) >= 1 and table[0][0] and "Type" not in table[0][0]:
            result["Type"] = table[0][0]
            logger.info(f"picture_info извлечен (формат 3): Type = {table[0][0]}")
            return result
        elif len(table) >= 2 and table[1][0] and "Type" not in table[1][0]:
            result["Type"] = table[1][0]
            logger.info(f"picture_info извлечен (формат 4): Type = {table[1][0]}")
            return result

    # Обработка по типу таблицы для остальных случаев
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
        # Обрабатываем каждую строку как ключ-значение
        for row in table:
            if len(row) >= 2 and row[0]:  # Если есть ключ и значение
                key = row[0].strip()
                value = row[1].strip() if row[1] else ""
                result[key] = value
    # elif table_type == "tabular_data":
    #     # Для таблиц со второй страницы (lines_13-23)
    #     # Обрабатываем каждую строку как ключ-значение
    #     for row in table:
    #         # Учитываем оба варианта: [ключ, значение] и [ключ]
    #         if row and len(row) > 0 and row[0]:
    #             key = row[0].strip()
    #             # Для строк с двумя элементами, берем второй как значение
    #             if len(row) >= 2:
    #                 value = row[1].strip() if row[1] else ""
    #             # Для строк с одним элементом, значение пустое
    #             else:
    #                 value = ""
    #             result[key] = value

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


def get_table_definitions_residential(page_no):
    """
    Возвращает определения таблиц для RESIDENTIAL документа
    """
    # Таблицы для первой страницы RESIDENTIAL
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
    # Таблицы для второй страницы RESIDENTIAL
    elif page_no == 1:
        return [
            {
                "name": "building_style",
                "horizontal_lines": [75, 85, 95, 105, 115],
                "vertical_lines": [30, 95, 140],
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
                "vertical_lines": [30, 95, 140],
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
                "vertical_lines": [30, 95, 140],
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
                "vertical_lines": [15, 95, 165],
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


def get_table_definitions_commercial(page_no):
    """
    Возвращает определения таблиц для COMMERCIAL документа
    """
    # Таблицы для первой страницы COMMERCIAL
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
                "horizontal_lines": [305, 315],
                "vertical_lines": [15, 59, 90],
                "type": "single_key_value",
            },
            {
                "name": "value_data",
                "horizontal_lines": [247, 256, 267, 275],
                "vertical_lines": [420, 470, 520],
                "type": "value_data",
            },
            {
                "name": "transfer_date",
                "horizontal_lines": [445, 453, 464],
                "vertical_lines": [15, 80],
                "type": "transfer_data",
            },
            {
                "name": "transfer_price",
                "horizontal_lines": [445, 453, 464],
                "vertical_lines": [120, 150],
                "type": "transfer_data",
            },
            {
                "name": "transfer_type",
                "horizontal_lines": [445, 455, 465],
                "vertical_lines": [150, 200],
                "type": "transfer_data",
            },
            {
                "name": "transfer_validity",
                "horizontal_lines": [445, 455, 465],
                "vertical_lines": [270, 410],
                "type": "transfer_data",
            },
        ]
    # Таблицы для второй страницы COMMERCIAL
    elif page_no == 1:
        return [
            {
                "name": "building_info",
                "horizontal_lines": [72, 82, 92, 101, 110, 120, 129, 138, 149],
                "vertical_lines": [14, 95, 170],
                "type": "tabular_data",
            },
            # При необходимости добавьте другие таблицы для второй страницы коммерческого документа
        ]
    else:
        return []


def get_table_definitions(document_type, page_no):
    """
    Возвращает определения таблиц в зависимости от типа документа и номера страницы
    """
    if document_type == "RESIDENTIAL":
        return get_table_definitions_residential(page_no)
    elif document_type == "COMMERCIAL":
        return get_table_definitions_commercial(page_no)
    else:
        # Для неизвестного типа используем определения RESIDENTIAL по умолчанию
        logger.warning(
            f"Неизвестный тип документа: {document_type}, используем RESIDENTIAL по умолчанию"
        )
        return get_table_definitions_residential(page_no)


def analyze_pdf_page(pdf_path, document_type, page_no=0, save_debug_images=True):
    """
    Анализирует отдельную страницу PDF с множеством таблиц
    """
    results = {
        "page_info": {"number": page_no + 1, "document_type": document_type},
        "data": {},
    }

    with pdfplumber.open(pdf_path) as pdf:
        if page_no >= len(pdf.pages):
            logger.error(
                f"Страница {page_no} не существует в документе (всего {len(pdf.pages)} страниц)"
            )
            return results

        page = pdf.pages[page_no]
        results["page_info"]["width"] = page.width
        results["page_info"]["height"] = page.height

        # Получаем определения таблиц для страницы в зависимости от типа документа
        table_definitions = get_table_definitions(document_type, page_no)

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
                "snap_tolerance": 5,  # Увеличиваем для лучшего захвата
                "join_tolerance": 5,  # Увеличиваем для лучшего захвата
                "edge_min_length": 10,
                "min_words_vertical": 1,
                "min_words_horizontal": 1,
            }

            # Извлечение таблицы
            tables = page.extract_tables(table_settings)

            # Вывод для отладки
            if tables:
                for table_no, table in enumerate(tables):
                    logger.info(
                        f"Страница {page_no + 1}, Таблица '{table_name}' #{table_no + 1}:"
                    )
                    for row in table:
                        logger.info(row)

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

    return results


def analyze_pdf_with_multiple_pages(
    pdf_path, pages_to_process=[0, 1], save_debug_images=True
):
    """
    Анализирует несколько страниц PDF и объединяет результаты
    """
    # Сначала определяем тип документа
    document_type = detect_document_type(pdf_path)

    combined_results = {
        "page_count": 0,
        "document_type": document_type,
        "pages_info": [],
        "data": {},
    }

    with pdfplumber.open(pdf_path) as pdf:
        combined_results["page_count"] = len(pdf.pages)

        for page_no in pages_to_process:
            if page_no >= len(pdf.pages):
                logger.error(
                    f"Страница {page_no} не существует в документе (всего {len(pdf.pages)} страниц)"
                )
                continue

            logger.info(f"Обработка страницы {page_no + 1} типа {document_type}")
            page_results = analyze_pdf_page(
                pdf_path, document_type, page_no, save_debug_images
            )
            # Сохраняем информацию о странице
            combined_results["pages_info"].append(page_results["page_info"])

            # Объединяем данные
            if page_no == 0:  # Первая страница - основная информация о собственности
                combined_results["data"].update(page_results["data"])
            else:  # Другие страницы - дополнительные данные
                # Для второй страницы добавляем ключ page_2
                page_key = f"page_{page_no + 1}"
                combined_results["data"][page_key] = page_results["data"]

                # Копируем picture_info со страницы 2 на верхний уровень
                if (
                    document_type == "RESIDENTIAL"
                    and "picture_info" in page_results["data"]
                ):
                    combined_results["data"]["picture_info"] = page_results["data"][
                        "picture_info"
                    ]
                    logger.info(
                        f"Скопирован picture_info на верхний уровень: {page_results['data']['picture_info']}"
                    )

    # Логирование итоговых данных
    logger.info(
        f"Сформированы итоговые данные для файла {pdf_path}: {combined_results}"
    )

    return combined_results


def save_json_data(data, output_path):
    """
    Сохраняет данные в JSON-файл
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные сохранены в {output_path}")
    return output_path


# Если файл запускается напрямую, анализируем один PDF
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        pdf_path = (
            pdf_directory / pdf_file if not os.path.isabs(pdf_file) else Path(pdf_file)
        )

        if not pdf_path.exists():
            logger.error(f"Ошибка: файл {pdf_path} не найден")
            sys.exit(1)

        logger.info(f"Анализ PDF: {pdf_path}")

        # Анализируем PDF
        raw_data = analyze_pdf_with_multiple_pages(pdf_path, pages_to_process=[0, 1])

        # Сохраняем результаты
        output_path = temp_directory / f"{pdf_path.stem}_raw_data.json"
        save_json_data(raw_data, output_path)

        logger.info(f"Данные сохранены в {output_path}")
    else:
        logger.warning("Использование: python parser.py <путь_к_pdf>")
