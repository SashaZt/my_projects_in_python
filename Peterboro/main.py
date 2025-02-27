import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber
from loguru import logger

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

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


def anali_pdf_02():
    test_page_no = 1
    pdf_path = pdf_directory / "R001-017-002.pdf"
    # pdf_path = pdf_directory / "R001-014-000.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            if page_no == test_page_no:
                # Настройки для обнаружения таблиц

                horizontal_lines_13 = [75, 85, 95, 105, 115]
                vertical_lines_13 = [
                    30,
                    95,
                    137,
                ]
                horizontal_lines_14 = [75, 85, 95, 105, 115]
                vertical_lines_14 = [
                    190,
                    260,
                    320,
                ]
                horizontal_lines_15 = [30, 45]
                vertical_lines_15 = [
                    380,
                    405,
                    535,
                ]
                horizontal_lines_04 = [30, 45]
                vertical_lines_04 = [
                    550,
                    572,
                    610,
                ]
                horizontal_lines_05 = [65, 77, 86, 96, 106, 130]
                vertical_lines_05 = [
                    15,
                    205,
                ]
                horizontal_lines_06 = [65, 75, 84, 93, 103, 110, 118, 130]
                vertical_lines_06 = [
                    210,
                    265,
                    360,
                ]
                horizontal_lines_07 = [300, 310]
                vertical_lines_07 = [15, 59, 90]
                horizontal_lines_08 = [240, 252, 262, 275]
                vertical_lines_08 = [420, 470, 520]
                horizontal_lines_09 = [437, 449, 458]
                vertical_lines_09 = [15, 80]
                # 10,11,12 Сверху ключ, снизу значение
                horizontal_lines_10 = [437, 449, 458]
                vertical_lines_10 = [120, 150]
                horizontal_lines_11 = [437, 449, 458]
                vertical_lines_11 = [150, 200]
                horizontal_lines_12 = [437, 449, 458]
                vertical_lines_12 = [270, 410]
                # Стратегии могут быть: "lines", "text", "explicit"
                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": vertical_lines_15,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": horizontal_lines_15,
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

    anali_pdf_02()
