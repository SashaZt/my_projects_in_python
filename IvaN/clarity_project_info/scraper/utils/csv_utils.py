# /utils/csv_utils.py
from pathlib import Path
from typing import List

import pandas as pd
from config.logger import logger


def write_csv(file_path: Path, data: List[str]) -> None:
    """Записывает данные в CSV файл."""
    df = pd.DataFrame(data, columns=["url"])
    df.to_csv(file_path, index=False)
    logger.info(f"Записано {len(data)} ссылок в {file_path}")


def load_urls(file_path: Path) -> List[str]:
    """Загружает список URL из CSV файла."""
    df = pd.read_csv(file_path)
    if "url" not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")
    return df["url"].tolist()


def extract_and_save_specific_urls(
    input_csv: Path, output_csv: Path, substring: str
) -> None:
    """Извлекает URL-адреса, содержащие заданную подстроку."""
    df = pd.read_csv(input_csv)

    if "url" not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")

    filtered_df = df[df["url"].str.contains(substring, na=False)]
    filtered_df.to_csv(output_csv, index=False)
    logger.info(f"Отфильтровано {len(filtered_df)} URL и сохранено в: {output_csv}")
