import logging
from pathlib import Path

import pandas as pd
import pdfplumber
from configuration.logger_setup import logger

# Директории
current_directory = Path.cwd()
temp_directory = current_directory / "temp"
temp_directory.mkdir(parents=True, exist_ok=True)

img_file = temp_directory / "debug_table.png"
output_file = temp_directory / "extracted_data.xlsx"

# Настройки линий
line_configs = [
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


def rows_to_dict(rows):
    """Функция для преобразования списка строк в словарь"""
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

    return result_dict


def anali_pdf():
    pdf_file = "0002-007-248.pdf"
    all_data = []  # Список для сохранения всех строк таблиц

    try:
        with pdfplumber.open(pdf_file) as pdf:
            page = pdf.pages[0]  # Предполагаем, что обрабатываем только одну страницу

            # Пробуем каждую конфигурацию линий
            for config_index, config in enumerate(line_configs):
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
        data_dict = rows_to_dict(all_data)

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
