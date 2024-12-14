import argparse
import json
import os
import platform
import random
import re
import shutil
import time
from pathlib import Path

import pandas as pd
import pdfplumber
from configuration.logger_setup import logger

current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
temp_directory = current_directory / "temp"
pdf_directory = current_directory / "pdf"

configuration_directory.mkdir(parents=True, exist_ok=True)
temp_directory.mkdir(parents=True, exist_ok=True)
pdf_directory.mkdir(parents=True, exist_ok=True)


img_file = temp_directory / "analis.png"


def anali_pdf():
    # Имя файла PDF
    pdf_file = "0002-007-248.pdf"

    # Настройки для поиска таблиц
    vertical_lines_01 = [260, 265, 520]
    horizontal_lines_01 = [40, 63]
    vertical_lines_02 = [18, 62, 190]
    horizontal_lines_02 = [68, 80]
    vertical_lines_03 = [18, 62, 190]
    horizontal_lines_03 = [80, 95]
    vertical_lines_04 = [18, 62, 190]
    horizontal_lines_04 = [112, 125]
    vertical_lines_04_1 = [18, 62, 190]
    horizontal_lines_04_1 = [125, 135]
    vertical_lines_05 = [18, 62, 190]
    horizontal_lines_05 = [135, 153]
    vertical_lines_06 = [18, 62, 190]
    horizontal_lines_06 = [153, 170]
    vertical_lines_07 = [18, 62, 160]
    horizontal_lines_07 = [200, 220]
    vertical_lines_08 = [18, 62, 160]
    horizontal_lines_08 = [220, 235]
    vertical_lines_09 = [18, 62, 160]
    horizontal_lines_09 = [235, 250]
    vertical_lines_10 = [18, 62, 160]
    horizontal_lines_10 = [260, 275]
    vertical_lines_11 = [18, 62, 160]
    horizontal_lines_11 = [275, 290]
    vertical_lines_11_1 = [160, 215, 285]
    horizontal_lines_11_1 = [205, 220]
    vertical_lines_12 = [160, 215, 285]
    horizontal_lines_12 = [220, 235]
    vertical_lines_13 = [160, 215, 285]
    horizontal_lines_13 = [262, 275]
    vertical_lines_14 = [160, 215, 285]
    horizontal_lines_14 = [275, 290]
    vertical_lines_15 = [285, 350, 405]
    horizontal_lines_15 = [75, 88]
    vertical_lines_16 = [285, 350, 405]
    horizontal_lines_16 = [88, 100]
    vertical_lines_17 = [285, 350, 405]
    horizontal_lines_17 = [100, 113]
    vertical_lines_18 = [285, 350, 405]
    horizontal_lines_18 = [113, 125]
    vertical_lines_19 = [285, 350, 405]
    horizontal_lines_19 = [125, 137]
    vertical_lines_20 = [285, 350, 405]
    horizontal_lines_20 = [138, 148]
    vertical_lines_21 = [405, 460, 510]
    horizontal_lines_21 = [75, 88]
    vertical_lines_21 = [405, 460, 510]
    horizontal_lines_21 = [88, 105]
    vertical_lines_22 = [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720]
    horizontal_lines_22 = [300, 318]
    vertical_lines_23 = [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720]
    horizontal_lines_23 = [318, 334]
    vertical_lines_24 = [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720]
    horizontal_lines_24 = [334, 350]
    vertical_lines_25 = [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720]
    horizontal_lines_25 = [352, 365]
    vertical_lines_26 = [90, 185, 205, 290, 325, 405, 450, 520, 580, 670, 720]
    horizontal_lines_26 = [367, 385]

    table_settings = {
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": vertical_lines_21,
        "horizontal_strategy": "explicit",
        "explicit_horizontal_lines": horizontal_lines_21,
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 10,
        "min_words_vertical": 1,
        "min_words_horizontal": 1,
    }

    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Получаем первую (и единственную) страницу
            page = pdf.pages[0]

            # Извлечение таблиц с использованием настроек
            tables = page.extract_tables(table_settings)
            for j, table in enumerate(tables):
                logger.info(f"Table {j + 1}:")
                for row in table:
                    logger.info(row)

            # Визуализация таблиц (опционально)
            image = page.to_image(resolution=150)
            image.debug_tablefinder(table_settings)
            image.save(img_file)

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")


if __name__ == "__main__":
    anali_pdf()
