import logging
from pathlib import Path

import pandas as pd
import pdfplumber
from configuration.logger_setup import logger

# Директории
current_directory = Path.cwd()
pdf_directory = current_directory / "pdf"
temp_directory = current_directory / "temp"
temp_directory.mkdir(parents=True, exist_ok=True)

output_file = temp_directory / "extracted_all_data.xlsx"

# Настройки линий для line_configs_01
line_configs_01 = [
    {
        "vertical": [18, 62, 190],
        "horizontal": [55, 71],
    },
    {
        "vertical": [18, 62, 280],
        "horizontal": [72, 84],
    },
    {
        "vertical": [18, 62, 280],
        "horizontal": [86, 100],
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
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [334, 350],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [350, 365],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [365, 381],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 402, 450, 520, 580, 670, 720],
        "horizontal": [385, 400],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
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
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [300, 318],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [318, 334],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [334, 350],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [352, 365],
    },
    {
        "vertical": [90, 185, 205, 270, 325, 405, 450, 520, 580, 670, 720],
        "horizontal": [367, 385],
    },
]


def get_page_count(pdf_file):
    """Определяет количество страниц в PDF-документе."""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            return len(pdf.pages)
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return 0


def select_line_configs(page):
    """Выбирает конфигурацию линий на основе наличия 'RESIDENTIAL PROPERTY RECORD CARD'."""
    text_settings = {
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": [260, 265, 520],
        "horizontal_strategy": "explicit",
        "explicit_horizontal_lines": [40, 63],
    }
    tables = page.extract_tables(text_settings)
    for table in tables:
        for row in table:
            if "RESIDENTIAL PROPERTY RECORD CARD" in row:
                # logger.info(
                #     "Найдено 'RESIDENTIAL PROPERTY RECORD CARD'. используем line_configs_02."
                # )
                return line_configs_02
    # logger.info(
    #     "Не найдено 'RESIDENTIAL PROPERTY RECORD CARD' используем. Using line_configs_01."
    # )
    return line_configs_01


def extract_table_with_lines(page, vertical_lines, horizontal_lines, config_index):
    """Извлекает таблицы с заданными линиями."""
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
    tables = page.extract_tables(table_settings)
    # logger.info(tables)
    return tables


def rows_to_dict(rows, page_count):
    """Преобразует строки таблиц в словарь с учётом количества страниц."""
    result_dict = {}
    fallback_keys = [
        "Owner_02",
        "Owner_03",
        "Owner_04",
    ]
    fallback_index = 0
    # Добавление Owner Name 2

    for row in rows:
        row = [
            element.replace("\n", " ") if isinstance(element, str) else element
            for element in row
        ]
        if len(row) > 2 and len(row) % 2 == 0:
            for i in range(0, len(row), 2):
                key = row[i].strip() if row[i].strip() else f"Key_{fallback_index}"
                fallback_index += 1
                value = row[i + 1].strip()
                result_dict[key] = value
        elif len(row) >= 2:
            key = row[0].strip()
            if not key:
                if fallback_index < len(fallback_keys):
                    key = fallback_keys[fallback_index]
                    fallback_index += 1
                else:
                    key = f"Key_{fallback_index}"
                    fallback_index += 1
            value = " ".join(map(str, row[1:])).strip()
            result_dict[key] = value

    result_dict["NumBldg"] = str(page_count)  # Добавляем номер здания

    return result_dict
    # # Проверка на наличие Owner
    # if "Owner" in result_dict:
    #     owner_value = result_dict["Owner"]
    #     if "&" in owner_value:  # Если символ '&' найден
    #         parts = owner_value.split("&", 1)  # Делим по первому символу '&'
    #         logger.info(parts[1].strip())  # Логируем вторую часть
    #         result_dict["Owner"] = parts[0].strip()  # Первая часть до '&'
    #         result_dict["Owner Name 2"] = parts[1].strip()  # Вторая часть после '&'

    # # Добавление Owner Name 2, если его не существует
    # if "Owner Name 2" not in result_dict:
    #     result_dict["Owner Name 2"] = ""  # Пустое значение по умолчанию
    # result_dict["Owner Name 2"] = ""
    # Добавление NumBldg


def process_fallback_tables(tables, fallback_keys):
    """
    Обрабатывает таблицы 2, 3, 4 и распределяет значения по fallback_keys.
    """
    result_dict = {}
    fallback_index = 0  # Индекс для текущего ключа из fallback_keys

    for table in tables:
        for row in table:
            # Заменяем \n на пробелы
            row = [
                element.replace("\n", " ") if isinstance(element, str) else element
                for element in row
            ]

            if len(row) >= 2:  # Если строка содержит минимум 2 элемента
                value = " ".join(
                    map(str, row[1:])
                ).strip()  # Берём значение из второго элемента
                if fallback_index < len(
                    fallback_keys
                ):  # Проверяем, есть ли ещё свободный ключ
                    key = fallback_keys[fallback_index]
                    result_dict[key] = value
                    fallback_index += 1  # Переходим к следующему ключу

    # Заполняем оставшиеся fallback_keys пустыми значениями
    for remaining_key in fallback_keys[fallback_index:]:
        result_dict[remaining_key] = ""

    return result_dict


def anali_pdf():
    all_data = []  # Список для сохранения данных (одна строка на файл)

    # Проходим по всем файлам в директории PDF
    for pdf_file in pdf_directory.glob("*.pdf"):
        try:
            page_count = get_page_count(pdf_file)  # Получаем количество страниц
            file_data = {}  # Данные для одной строки (одного PDF)

            with pdfplumber.open(pdf_file) as pdf:
                if pdf.pages:  # Проверяем, есть ли страницы в документе
                    page = pdf.pages[0]  # Берём только первую страницу
                    selected_line_configs = select_line_configs(page)

                    for config_index, config in enumerate(selected_line_configs):
                        # logger.info(
                        #     config_index
                        # )  # Логируем текущий индекс конфигурации

                        tables = extract_table_with_lines(
                            page, config["vertical"], config["horizontal"], config_index
                        )

                        if not tables:
                            continue  # Пропускаем, если таблицы пусты

                        # Если индекс конфигурации равен 2, 3 или 4, обрабатываем специально
                        if config_index in [2, 3, 4]:
                            fallback_keys = [
                                "Owner_02",
                                "Owner_03",
                                "Owner_04",
                            ]
                            # Проверяем, чтобы config_index соответствовал нужному ключу
                            fallback_index = config_index - 2  # Смещение для 2, 3, 4
                            for table in tables:
                                for row in table:
                                    # Если строка содержит значение, записываем в соответствующий ключ
                                    if len(row) > 1 and row[1].strip():
                                        key = fallback_keys[fallback_index]
                                        value = row[1].strip()
                                        # logger.info(f"Adding {key}: {value}")
                                        file_data[key] = value
                        else:
                            # Для всех других конфигураций обрабатываем как обычно
                            for table in tables:
                                row_dict = rows_to_dict(table, page_count)
                                file_data.update(row_dict)  # Обновляем данные для файла

            # Добавляем данные из этого файла как одну строку в общий список
            if file_data:
                all_data.append(file_data)

        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
    # logger.info(all_data)
    # Записываем все данные в Excel
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_excel(output_file, index=False)
        logger.info(f"Data saved to {output_file}")
    else:
        logger.info("No data extracted from the PDFs.")


if __name__ == "__main__":
    anali_pdf()
