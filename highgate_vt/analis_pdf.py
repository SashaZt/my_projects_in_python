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
    pdf_file = "0002-010-016.pdf"

    vertical = [18, 62, 190]
    horizontal = [126, 135]
    table_settings = {
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": vertical,
        "horizontal_strategy": "explicit",
        "explicit_horizontal_lines": horizontal,
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
