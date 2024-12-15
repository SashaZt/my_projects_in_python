import logging
from pathlib import Path

import pandas as pd
import pdfplumber
from configuration.logger_setup import logger

# Директории
current_directory = Path.cwd()
pdf_directory = current_directory / "pdf"
temp_directory = current_directory / "temp"
pdf_directory.mkdir(parents=True, exist_ok=True)
temp_directory.mkdir(parents=True, exist_ok=True)

output_file = current_directory / "extracted_data.xlsx"

# Настройки линий для line_configs_01
line_configs_01 = [
    {
        "vertical": [18, 62, 190],
        "horizontal": [55, 71],
    },
    {
        "vertical": [18, 62, 280],
        "horizontal": [72, 100],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [100, 112],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [112, 125],
    },
    {
        "vertical": [18, 62, 200],
        "horizontal": [124, 139],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [140, 153],
    },
    {
        "vertical": [18, 62, 160, 210, 285],
        "horizontal": [190, 205],
    },
    {
        "vertical": [18, 62, 160, 210, 285],
        "horizontal": [205, 220],
    },
    {
        "vertical": [18, 62, 160],
        "horizontal": [221, 235],
    },
    {
        "vertical": [18, 62, 160, 210, 285],
        "horizontal": [245, 260],
    },
    {
        "vertical": [18, 62, 160, 210, 285],
        "horizontal": [260, 275],
    },
    {
        "vertical": [285, 350, 405, 460, 510],
        "horizontal": [60, 75],
    },
    {
        "vertical": [285, 350, 405, 460, 510],
        "horizontal": [75, 88],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [87, 100],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [100, 110],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [111, 125],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [125, 137],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [334, 350],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [350, 365],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [365, 381],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 402, 450, 520, 580, 670, 720],
        "horizontal": [385, 400],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [401, 416],
    },
]

# Настройки линий
line_configs_02 = [
    # Линии для первого блока (RESIDENTIAL PROPERTY RECORD CARD)
    {
        "vertical": [18, 62, 190],
        "horizontal": [68, 80],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [80, 95],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [110, 124],  # Уменьшили верхнюю линию
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [126, 135],  # Слегка увеличили нижнюю линию
    },
    # Линии для оценок собственности
    {
        "vertical": [18, 62, 190],
        "horizontal": [135, 153],
    },
    {
        "vertical": [18, 62, 190],
        "horizontal": [153, 170],
    },
    {
        "vertical": [18, 62, 160],
        "horizontal": [200, 220],
    },
    {
        "vertical": [160, 215, 285],
        "horizontal": [205, 220],
    },
    {
        "vertical": [18, 62, 160],
        "horizontal": [220, 235],
    },
    # Линии для другого блока данных
    {
        "vertical": [18, 62, 160],
        "horizontal": [235, 250],
    },
    {
        "vertical": [18, 62, 160],
        "horizontal": [260, 275],
    },
    {
        "vertical": [18, 62, 160],
        "horizontal": [275, 290],
    },
    # Линии для подробных таблиц
    {
        "vertical": [160, 215, 285],
        "horizontal": [220, 235],
    },
    {
        "vertical": [160, 215, 285],
        "horizontal": [262, 275],
    },
    {
        "vertical": [160, 215, 285],
        "horizontal": [275, 290],
    },
    # Линии для таблиц с дополнительными данными
    {
        "vertical": [285, 350, 405],
        "horizontal": [75, 88],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [88, 100],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [100, 113],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [113, 125],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [125, 137],
    },
    {
        "vertical": [285, 350, 405],
        "horizontal": [138, 148],
    },
    # Линии для таблиц с итогами
    {
        "vertical": [405, 460, 510],
        "horizontal": [75, 88],
    },
    {
        "vertical": [405, 460, 510],
        "horizontal": [88, 105],
    },
    # Линии для нижних таблиц
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [300, 318],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [318, 334],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [334, 350],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [352, 365],
    },
    {
        "vertical": [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [367, 385],
    },
]


def select_line_configs(page):
    """
    Проверяет наличие 'RESIDENTIAL PROPERTY RECORD CARD' на странице и выбирает конфигурацию линий.
    Если 'RESIDENTIAL PROPERTY RECORD CARD' найден, возвращает line_configs_02.
    Если нет, возвращает line_configs_01.
    """
    # Настройки для быстрой проверки наличия текста
    text_settings = {
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": [260, 265, 520],  # Предварительные линии
        "horizontal_strategy": "explicit",
        "explicit_horizontal_lines": [40, 63],
    }

    # Проверяем наличие выражения 'RESIDENTIAL PROPERTY RECORD CARD'
    tables = page.extract_tables(text_settings)

    for table in tables:
        for row in table:
            if "RESIDENTIAL PROPERTY RECORD CARD" in row:
                logger.info(
                    "Found 'RESIDENTIAL PROPERTY RECORD CARD'. Using line_configs_02."
                )
                return line_configs_02

    logger.info("No 'RESIDENTIAL PROPERTY RECORD CARD' found. Using line_configs_01.")
    return line_configs_01


def extract_table_with_lines(page, vertical_lines, horizontal_lines, config_index):
    """Функция для извлечения таблицы с заданными линиями"""
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

    # Визуализация линий (опционально)
    image = page.to_image(resolution=150)
    image.debug_tablefinder(table_settings)

    # Уникальное имя файла для отладочного изображения
    img_file = temp_directory / f"debug_config_{config_index + 1}.png"
    image.save(img_file)
    logger.info(f"Debug image saved to {img_file}")

    # Извлечение таблиц
    tables = page.extract_tables(table_settings)
    return tables


def get_page_count(pdf_file):
    """
    Определяет количество страниц в PDF-документе.

    Args:
        pdf_file (str): Путь к PDF-файлу.

    Returns:
        int: Количество страниц в документе.
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
        return page_count
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 0  # Возвращаем 0 в случае ошибки


def rows_to_dict(rows, page_count):
    """
    Функция для преобразования списка строк в словарь с добавлением количества страниц документа.

    Args:
        rows (list): Список строк таблицы.
        page_count (int): Количество страниц в PDF-документе.

    Returns:
        dict: Словарь с обработанными данными.
    """
    result_dict = {}
    fallback_keys = [
        "Owner Address",  # Для третьего блока
        "Owner City, State, Zip",  # Для четвёртого блока
    ]
    fallback_index = 0  # Индекс fallback ключа

    for row in rows:
        # Замена символа новой строки на пробел в каждом элементе строки
        row = [
            element.replace("\n", " ") if isinstance(element, str) else element
            for element in row
        ]

        # Если строка имеет формат: ['key1', 'value1', 'key2', 'value2', ...]
        if len(row) > 2 and len(row) % 2 == 0:
            for i in range(0, len(row), 2):
                key = row[i].strip() if row[i].strip() else f"Key_{fallback_index}"
                fallback_index += 1
                value = row[i + 1].strip()
                result_dict[key] = value
        elif len(row) >= 2:  # Для строк формата ['key', 'value']
            key = row[0].strip()
            if not key:  # Если ключ пустой, используем fallback ключ
                if fallback_index < len(fallback_keys):
                    key = fallback_keys[fallback_index]
                    fallback_index += 1
                else:
                    key = f"Key_{fallback_index}"
                    fallback_index += 1

            value = " ".join(map(str, row[1:])).strip()
            result_dict[key] = value

    # Проверка на наличие Owner
    if "Owner" in result_dict:
        owner_value = result_dict["Owner"]
        if "&" in owner_value:  # Если символ '&' найден
            parts = owner_value.split("&", 1)
            result_dict["Owner"] = parts[0].strip()  # До символа '&'
            result_dict["Owner Name 2"] = parts[1].strip()  # После символа '&'

    # Добавление Owner Name 2, если его не существует
    if "Owner Name 2" not in result_dict:
        result_dict["Owner Name 2"] = ""  # Пустое значение по умолчанию

    # Добавление NumBldg с количеством страниц
    result_dict["NumBldg"] = str(page_count)  # Записываем количество страниц как строку
    # Упорядочивание ключей: переместить "Owner Name 2" после "Owner"
    if "Owner Name 2" in result_dict:
        reordered_dict = {}
        for key, value in result_dict.items():
            reordered_dict[key] = value
            if key == "Owner" and "Owner Name 2" in result_dict:
                reordered_dict["Owner Name 2"] = result_dict["Owner Name 2"]
        result_dict = reordered_dict

    return result_dict


def anali_pdf():
    pdf_file = "0002-007-255.pdf"
    all_data = []  # Список для сохранения всех строк таблиц

    # Получаем количество страниц в документе
    page_count = get_page_count(pdf_file)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            page = pdf.pages[0]  # Предполагаем, что обрабатываем только одну страницу

            # Пробуем каждую конфигурацию линий
            for config_index, config in enumerate(line_configs_02):
                tables = extract_table_with_lines(
                    page, config["vertical"], config["horizontal"], config_index
                )

                if tables:
                    for table in tables:
                        for row in table:
                            all_data.append(row)  # Сохраняем строку в общий список

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")

    # Преобразование строк в словарь
    if all_data:
        data_dict = rows_to_dict(all_data, page_count)

        # Вывод словаря для проверки
        for key, value in data_dict.items():
            logger.info(f"{key}: {value}")

        # Сохраняем данные в Excel (опционально)
        df = pd.DataFrame([data_dict])
        df.to_excel(output_file, index=False)
        logger.info(f"Data saved to {output_file}")
    else:
        logger.info("No data extracted from the PDF.")


if __name__ == "__main__":
    anali_pdf()
