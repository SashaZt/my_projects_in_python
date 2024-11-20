import os
from pathlib import Path

from dotenv import load_dotenv


def initialize_directories(base_dir: Path) -> dict:
    """Создает необходимые директории и возвращает их пути.

    Args:
        base_dir (Path): Базовая директория проекта.

    Returns:
        dict: Словарь с путями к директориям и файлам.
    """
    directories = {
        "json_data_dir": base_dir / "json_data",
        "config_dir": base_dir / "configuration",
        "output_dir": base_dir / "data",
    }

    # Создаем директории
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Возвращаем также пути к основным файлам
    files = {
        "csv_file": directories["output_dir"] / "output.csv",
        "config_file": directories["config_dir"] / "config.txt",
        "traffic_report": directories["output_dir"] / "Traffic_History_Charts.xlsx",
        "results_report": directories["output_dir"] / "All_Result.xlsx",
    }

    return {**directories, **files}


def load_environment_variables(env_file: Path) -> dict:
    """Загружает переменные окружения из указанного файла.

    Args:
        env_file (Path): Путь к файлу .env.

    Returns:
        dict: Словарь с переменными окружения.
    """
    load_dotenv(env_file)

    try:
        return {
            "time_a": int(os.getenv("TIME_A", "30")),
            "time_b": int(os.getenv("TIME_B", "60")),
            "site_limit": int(os.getenv("LIMIT", "100")),
        }
    except ValueError as e:
        raise ValueError(
            "Некорректные значения в файле .env. Ожидались целые числа."
        ) from e
