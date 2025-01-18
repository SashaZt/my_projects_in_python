import os
from pathlib import Path

import pandas as pd

# Установка директорий для логов и данных
current_directory = Path.cwd()
csv_directory = current_directory / "csv"
csv_directory_new = current_directory / "csv_new"

# Пути к файлам
csv_directory.mkdir(parents=True, exist_ok=True)
csv_directory_new.mkdir(parents=True, exist_ok=True)


def fix_csv_with_proper_format(input_file, output_file):
    """
    Исправляет CSV-файл, удаляя переносы строк внутри значений.

    :param input_file: str - Путь к исходному CSV-файлу.
    :param output_file: str - Путь к выходному исправленному CSV-файлу.
    """
    try:
        # Чтение файла с обработкой переносов строк
        df = pd.read_csv(
            input_file, lineterminator="\n", quotechar='"', skip_blank_lines=False
        )

        # Удаляем переносы строк в строковых колонках
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].str.replace("\n", " ", regex=False)

        # Сохраняем файл с исправленным форматом
        df.to_csv(
            output_file, index=False, quotechar='"', quoting=1
        )  # quoting=csv.QUOTE_ALL
        print(f"Файл успешно исправлен и сохранён в {output_file}.")
    except Exception as e:
        print(f"Ошибка: {e}")


def process_csv_directory(csv_directory, csv_directory_new):
    """
    Обрабатывает все файлы CSV из csv_directory, исправляет их формат и сохраняет в csv_directory_new.

    :param csv_directory: Path - Путь к папке с исходными CSV-файлами.
    :param csv_directory_new: Path - Путь к папке для сохранения исправленных CSV-файлов.
    """
    # Убедиться, что папка для сохранения существует
    csv_directory_new.mkdir(parents=True, exist_ok=True)

    # Проход по всем CSV-файлам в директории
    for csv_file in csv_directory.glob("*.csv"):
        output_file = csv_directory_new / csv_file.name  # Создаём путь для сохранения
        fix_csv_with_proper_format(csv_file, output_file)


process_csv_directory(csv_directory, csv_directory_new)
