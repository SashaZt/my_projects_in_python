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

# Путь к PDF-файлу
pdf_path = "0002-007-248.pdf"


# Функция для извлечения текста из PDF
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text += f"--- Page {i + 1} ---\n{text}\n\n"
                else:
                    all_text += f"--- Page {i + 1} ---\n[No text found]\n\n"
        return all_text
    except Exception as e:
        return f"An error occurred: {e}"


# Извлечение текста
extracted_text = extract_text_from_pdf(pdf_path)

# Сохранение текста в файл
output_path = "extracted_text.txt"
with open(output_path, "w", encoding="utf-8") as file:
    file.write(extracted_text)

print(f"Text successfully extracted and saved to {output_path}")
