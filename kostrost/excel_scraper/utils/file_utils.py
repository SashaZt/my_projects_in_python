import json
from pathlib import Path

import pandas as pd
from config.logger import logger


def ensure_directory(directory_path):
    """
    Создает директорию, если она не существует

    Args:
        directory_path: путь к директории
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_html_content(file_path, content):
    """
    Сохраняет HTML-контент в файл

    Args:
        file_path: путь к файлу
        content: HTML-контент

    Returns:
        bool: True если сохранение успешно, иначе False
    """
    try:
        # Убедимся, что родительская директория существует
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем контент
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"HTML успешно сохранен в {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении HTML в {file_path}: {str(e)}")
        return False


def save_job_info(json_dir, job_id, job_info):
    """
    Сохраняет информацию о задании в JSON файл

    Args:
        json_dir: директория для JSON файлов
        job_id: идентификатор задания
        job_info: информация о задании

    Returns:
        bool: True если сохранение успешно, иначе False
    """
    try:
        json_dir = Path(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)

        json_file = json_dir / f"{job_id}.json"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(job_info, f, indent=4)

        logger.info(f"Информация о задании сохранена в {json_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении информации о задании: {str(e)}")
        return False


def load_job_info(json_file_path):
    """
    Загружает информацию о задании из JSON файла

    Args:
        json_file_path: путь к JSON файлу

    Returns:
        dict: информация о задании или None в случае ошибки
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            job_info = json.load(f)
        return job_info
    except Exception as e:
        logger.error(
            f"Ошибка при загрузке информации о задании из {json_file_path}: {str(e)}"
        )
        return None


def delete_job_file(json_file_path):
    """
    Удаляет файл задания

    Args:
        json_file_path: путь к JSON файлу

    Returns:
        bool: True если удаление успешно, иначе False
    """
    try:
        Path(json_file_path).unlink()
        logger.info(f"Файл задания {json_file_path} удален")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении файла задания {json_file_path}: {str(e)}")
        return False


def extract_urls_from_excel(excel_file_path, base_html_dir):
    """
    Извлекает URL из всех листов Excel файла

    Args:
        excel_file_path: путь к Excel файлу
        base_html_dir: базовая директория для сохранения HTML файлов

    Returns:
        dict: словарь с именами листов и списками URL
    """
    sheet_urls = {}

    try:
        # Читаем Excel файл
        xl = pd.ExcelFile(excel_file_path)
        sheet_names = xl.sheet_names

        for sheet_name in sheet_names:
            # Создаем директорию для листа
            sheet_name = sheet_name.strip()
            sheet_dir = Path(base_html_dir) / sheet_name
            sheet_dir.mkdir(parents=True, exist_ok=True)

            # Читаем только столбец A из листа
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name, usecols=[0])

            # Извлекаем URL из столбца A, исключая пустые значения
            urls = [str(value) for value in df.iloc[:, 0].dropna()]

            if urls:
                sheet_urls[sheet_name] = urls
                logger.info(f"Найдено {len(urls)} URL в листе '{sheet_name}'")
            else:
                logger.warning(f"В листе '{sheet_name}' не найдено URL")
    except Exception as e:
        logger.error(f"Ошибка при извлечении URL из Excel: {str(e)}")

    return sheet_urls
