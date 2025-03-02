import os
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


def anali_pdf_02(pdf_path, test_page_no=0):

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            if page_no == test_page_no:
                # Настройки для обнаружения таблиц

                vertical_lines_01 = [50, 60, 137]
                horizontal_lines_01 = [10, 25]
                vertical_lines_02 = [15, 40, 180]
                horizontal_lines_02 = [30, 45]
                vertical_lines_03 = [380, 405, 535]
                horizontal_lines_03 = [30, 45]
                vertical_lines_04 = [550, 572, 610]
                horizontal_lines_04 = [30, 45]
                vertical_lines_05 = [15, 205]
                horizontal_lines_05 = [65, 77, 86, 96, 106, 130]
                vertical_lines_06 = [210, 265, 360]
                horizontal_lines_06 = [65, 75, 84, 93, 103, 110, 118, 130]
                vertical_lines_07 = [15, 59, 90]
                horizontal_lines_07 = [305, 315]
                vertical_lines_08 = [420, 470, 520]
                horizontal_lines_08 = [247, 256, 267, 275]
                vertical_lines_09 = [15, 80]
                horizontal_lines_09 = [445, 453, 464]
                vertical_lines_10 = [120, 150]
                horizontal_lines_10 = [445, 453, 464]
                vertical_lines_11 = [150, 200]
                horizontal_lines_11 = [445, 455, 465]
                vertical_lines_12 = [270, 410]
                horizontal_lines_12 = [445, 455, 465]
                vertical_lines_13 = [14, 95, 170]
                horizontal_lines_13 = [72, 82, 92, 101, 110, 120, 129, 138, 149]

                # Стратегии могут быть: "lines", "text", "explicit"
                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": vertical_lines_13,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": horizontal_lines_13,
                    "snap_tolerance": 3,  # Толерантность при поиске линий (в пикселях)
                    "join_tolerance": 3,  # Толерантность при объединении линий
                    "edge_min_length": 10,  # Минимальная длина линий
                    "min_words_vertical": 1,  # Минимальное количество слов для вертикальной линии
                    "min_words_horizontal": 1,  # Минимальное количество слов для горизонтальной линии
                }
                tables = page.extract_tables(table_settings)

                # Выводим данные всех найденных таблиц
                for table_no, table in enumerate(tables):
                    print(f"Страница №{page_no + 1}, Таблица №{table_no + 1}:")
                    for row in table:
                        print(row)
                    print("\n")  # Добавляем пустую строку для разделения таблиц

                # Визуализация поиска таблиц с настройками
                image = page.to_image(resolution=150)
                image.debug_tablefinder(table_settings)
                filename = os.path.join(temp_directory, "analis.png")
                image.save(filename)
                break


if __name__ == "__main__":
    pdf_file = "R001-014-000.pdf"
    pdf_path = pdf_directory / pdf_file
    # Указываем номер листа, начинается с 0
    test_page_no = 1
    anali_pdf_02(pdf_path, test_page_no=test_page_no)
