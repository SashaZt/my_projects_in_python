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
        "html_dir": base_dir / "html",
        "config_dir": base_dir / "configuration",
        "output_dir": base_dir / "data",
    }

    # Создаем директории
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Возвращаем также пути к основным файлам
    files = {
        "csv_file": directories["output_dir"] / "output.csv",
        "txt_file": directories["output_dir"] / "output.txt",
        "config_file": directories["config_dir"] / "config.txt",
        "credentials": directories["config_dir"] / "credentials.json",
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

    # Получаем все переменные окружения из os.environ и возвращаем их в виде словаря
    return {key: value for key, value in os.environ.items()}
