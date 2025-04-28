# /utils/csv_utils.py
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import pandas as pd
from config.constants import HTML_FILES_DIR
from config.logger import logger


def write_csv(file_path: Path, data: List[str]) -> None:
    """Записывает данные в CSV файл."""
    df = pd.DataFrame(data, columns=["url"])
    df.to_csv(file_path, index=False)
    logger.info(f"Записано {len(data)} ссылок в {file_path}")


def extract_and_save_specific_urls(
    input_csv: Path, output_csv: Path, substring: str, skip_existing: bool = False
) -> List[str]:
    """
    Извлекает URL-адреса, содержащие заданную подстроку.
    Если skip_existing=True, возвращает только те URL, для которых ещё нет HTML файлов.
    """
    df = pd.read_csv(input_csv)

    if "url" not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")

    filtered_df = df[df["url"].str.contains(substring, na=False)]

    # Всегда сохраняем полный результат фильтрации
    filtered_df.to_csv(output_csv, index=False)
    logger.info(f"Отфильтровано {len(filtered_df)} URL и сохранено в: {output_csv}")

    # Если нужно пропустить существующие файлы, проверяем наличие HTML файлов
    if skip_existing:

        urls = filtered_df["url"].tolist()
        not_downloaded = []

        logger.info(f"Проверка существующих HTML файлов для {len(urls)} URL...")

        for url in urls:
            filename = HTML_FILES_DIR / f"{urlparse(url).path.replace('/', '_')}.html"
            if not filename.exists():
                not_downloaded.append(url)

        logger.info(f"Найдено {len(not_downloaded)} URL без скачанных HTML файлов")
        return not_downloaded

    return filtered_df["url"].tolist()


def load_urls(file_path: Path, skip_existing: bool = False) -> List[str]:
    """
    Загружает список URL из CSV файла.
    Если skip_existing=True, возвращает только те URL, для которых ещё нет HTML файлов.
    """
    df = pd.read_csv(file_path)
    if "url" not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")

    urls = df["url"].tolist()

    # Если нужно пропустить существующие файлы, проверяем наличие HTML файлов
    if skip_existing:

        not_downloaded = []
        total = len(urls)

        logger.info(f"Проверка существующих HTML файлов для {total} URL...")

        for i, url in enumerate(urls):
            if i % 1000 == 0 and i > 0:
                logger.info(f"Проверено {i}/{total} файлов...")

            filename = HTML_FILES_DIR / f"{urlparse(url).path.replace('/', '_')}.html"
            if not filename.exists():
                not_downloaded.append(url)

        logger.info(f"Найдено {len(not_downloaded)} URL без скачанных HTML файлов")
        return not_downloaded

    return urls
