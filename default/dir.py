import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

# Загрузка параметров из файла .env
load_dotenv()

# Получение параметров
directory = os.getenv("DIRECTORY", ".")
depth = int(os.getenv("DEPTH", 1))


def get_folder_size(folder_path):
    """Рекурсивно вычисляет размер папки."""
    return sum(f.stat().st_size for f in Path(folder_path).rglob("*") if f.is_file())


def process_folder(folder_path, current_depth, max_depth, indent):
    """
    Обрабатывает папку, вычисляя размер и отображая дерево.
    """
    folder_path = Path(folder_path)
    folder_size = get_folder_size(folder_path) / (1024 * 1024)  # Размер в МБ
    print(" " * indent + f"[{folder_size:.2f} MB] {folder_path.name}")

    # Прекращаем обработку, если достигнут максимальный уровень вложенности
    if current_depth >= max_depth:
        return []

    return [entry for entry in folder_path.iterdir() if entry.is_dir()]


def display_folder_tree(folder_path, max_depth, workers=4):
    """
    Параллельно обрабатывает дерево папок с заданной глубиной.
    """
    folder_path = Path(folder_path)
    tasks = [(folder_path, 0)]  # Начальная папка и уровень вложенности
    indent_map = {folder_path: 0}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        while tasks:
            # Асинхронно выполняем обработку папок
            futures = []
            for task_folder, current_depth in tasks:
                indent = indent_map[task_folder]
                futures.append(
                    executor.submit(
                        process_folder, task_folder, current_depth, max_depth, indent
                    )
                )

            tasks = []
            for future in futures:
                subfolders = future.result()
                if subfolders:
                    for subfolder in subfolders:
                        tasks.append((subfolder, current_depth + 1))
                        indent_map[subfolder] = indent + 4


# Запуск анализа папки с параметрами из .env
if __name__ == "__main__":
    display_folder_tree(directory, max_depth=depth, workers=4)
