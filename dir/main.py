import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from configuration.logger_setup import logger
from openpyxl import Workbook


def get_folder_size(folder_path):
    """Рекурсивно вычисляет размер папки."""
    return sum(f.stat().st_size for f in Path(folder_path).rglob("*") if f.is_file())


def process_folder(folder_path, current_depth, max_depth, indent, results):
    """
    Обрабатывает папку, вычисляя размер и отображая дерево.
    """
    folder_path = Path(folder_path)
    folder_size = get_folder_size(folder_path) / (1024 * 1024)  # Размер в МБ

    # Логируем только папки больше 10 МБ
    if folder_size > 10:
        logger.info(" " * indent + f"[{folder_size:.2f} MB] {folder_path.name}")
        results.append((str(folder_path), folder_size))

    # Прекращаем обработку, если достигнут максимальный уровень вложенности
    if current_depth >= max_depth:
        return []

    return [entry for entry in folder_path.iterdir() if entry.is_dir()]


def display_folder_tree(folder_path, max_depth, workers=8):
    """
    Параллельно обрабатывает дерево папок с заданной глубиной.
    """
    folder_path = Path(folder_path)
    tasks = [(folder_path, 0)]  # Начальная папка и уровень вложенности
    indent_map = {folder_path: 0}
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        while tasks:
            # Асинхронно выполняем обработку папок
            futures = []
            for task_folder, current_depth in tasks:
                indent = indent_map[task_folder]
                futures.append(
                    executor.submit(
                        process_folder,
                        task_folder,
                        current_depth,
                        max_depth,
                        indent,
                        results,
                    )
                )

            tasks = []
            for future in futures:
                subfolders = future.result()
                if subfolders:
                    for subfolder in subfolders:
                        tasks.append((subfolder, current_depth + 1))
                        indent_map[subfolder] = indent + 4

    return results


def save_to_excel(results, output_file="output.xlsx"):
    """
    Сохраняет результаты в Excel.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Folder Analysis"
    sheet.append(["Директория", "Размер (MB)"])  # Заголовки столбцов

    for folder, size in results:
        sheet.append([folder, f"{size:.2f}"])  # Записываем директорию и размер

    workbook.save(output_file)
    logger.info(f"Результаты сохранены в {output_file}")


if __name__ == "__main__":
    # Запрашиваем директорию у пользователя
    directory = input("Введите путь к директории для анализа: ")
    max_depth = int(input("Введите максимальную глубину анализа (0 - не ограничено): "))
    # Проверяем существование директории
    while not os.path.isdir(directory):
        print("Указанная директория не существует. Попробуйте снова.")
        directory = input("Введите путь к директории для анализа: ")

    # # Устанавливаем максимально возможную глубину
    # max_depth = 1  # Практически неограниченная глубина для SSD

    # Увеличиваем количество workers для SSD
    workers = 8  # Увеличено для быстрой работы с SSD

    output_file = "output.xlsx"

    logger.info("Анализируем папки больше 10Мб")
    logger.info(f"Директория: {directory}")
    logger.info(f"Максимальная глубина: {max_depth}")
    logger.info(f"Количество параллельных потоков (workers): {workers}")

    results = display_folder_tree(directory, max_depth=max_depth, workers=workers)

    # Сохранение результатов в Excel
    save_to_excel(results, output_file)

    print(f"Анализ завершен. Результаты сохранены в файл {output_file}")
