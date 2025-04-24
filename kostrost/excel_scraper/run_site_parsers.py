import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from config.logger import logger


def run_parser(parser_path):
    """
    Запускает отдельный парсер и ожидает его завершения

    Args:
        parser_path: полный путь к файлу парсера

    Returns:
        dict: результат выполнения с полями success, elapsed_time, output, error
    """
    parser_file = os.path.basename(parser_path)
    logger.info(f"Запуск парсера: {parser_file}")
    start_time = time.time()

    result = {"success": False, "elapsed_time": 0, "output": "", "error": ""}

    try:
        # Запускаем парсер в отдельном процессе
        process = subprocess.run(
            [sys.executable, parser_path], check=True, capture_output=True, text=True
        )

        # Сохраняем вывод
        result["output"] = process.stdout
        result["error"] = process.stderr
        result["success"] = True

        # Выводим stdout и stderr
        if process.stdout:
            logger.info(f"Вывод парсера {parser_file}:\n{process.stdout}")
        if process.stderr:
            logger.warning(f"Ошибки парсера {parser_file}:\n{process.stderr}")

    except subprocess.CalledProcessError as e:
        result["output"] = e.stdout if e.stdout else ""
        result["error"] = e.stderr if e.stderr else str(e)

        logger.error(f"Ошибка при выполнении парсера {parser_file}: {str(e)}")

        if e.stdout:
            logger.info(f"Вывод парсера:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Ошибки парсера:\n{e.stderr}")

    except Exception as e:
        result["error"] = str(e)
        logger.error(
            f"Непредвиденная ошибка при запуске парсера {parser_file}: {str(e)}"
        )

    # Вычисляем затраченное время
    result["elapsed_time"] = time.time() - start_time

    # Выводим информацию о результате
    status = "успешно" if result["success"] else "с ошибкой"
    logger.info(
        f"Парсер {parser_file} завершен {status} за {result['elapsed_time']:.2f} секунд"
    )

    return result


def get_parser_files():
    """
    Получает список файлов парсеров в директории site с правильным определением путей

    Returns:
        list: отсортированный список путей к файлам парсеров
    """
    # Получаем абсолютный путь к директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Определяем путь к директории site
    site_dir = os.path.join(script_dir, "site")

    # Проверяем, существует ли директория
    if not os.path.exists(site_dir):
        logger.error(f"Директория site не существует по пути: {site_dir}")
        # Выводим текущую директорию для отладки
        logger.info(f"Текущая директория скрипта: {script_dir}")
        logger.info(f"Содержимое текущей директории: {os.listdir(script_dir)}")
        return []

    # Ищем файлы с расширением .py
    parser_files = []

    logger.info(f"Поиск .py файлов в директории: {site_dir}")
    try:
        for file in os.listdir(site_dir):
            if file.endswith(".py"):
                full_path = os.path.join(site_dir, file)
                if os.path.isfile(full_path):
                    parser_files.append(full_path)
                    logger.debug(f"Найден файл парсера: {full_path}")
    except Exception as e:
        logger.error(f"Ошибка при чтении директории {site_dir}: {str(e)}")

    # Сортируем файлы по алфавиту
    parser_files.sort()

    logger.info(f"Всего найдено парсеров: {len(parser_files)}")
    return parser_files


def run_all_parsers(parsers):
    """
    Последовательно запускает все парсеры

    Args:
        parsers: список путей к файлам парсеров

    Returns:
        dict: статистика выполнения
    """
    # Счетчики для статистики
    stats = {"success": 0, "failed": 0, "total": len(parsers), "results": {}}

    # Последовательно запускаем каждый парсер
    for idx, parser_path in enumerate(parsers, 1):
        parser_file = os.path.basename(parser_path)
        logger.info(f"[{idx}/{len(parsers)}] Запуск парсера: {parser_file}")

        # Запускаем парсер
        result = run_parser(parser_path)

        # Обновляем статистику
        if result["success"]:
            stats["success"] += 1
        else:
            stats["failed"] += 1

        # Сохраняем результат
        stats["results"][parser_file] = result

        # # Небольшая пауза между запусками (1 секунда)
        # if idx < len(parsers):
        #     logger.info("Ожидание 1 секунду перед запуском следующего парсера...")
        #     time.sleep(1)

    return stats


def main_all():
    """
    Основная функция для последовательного запуска всех парсеров
    """
    start_time = time.time()
    logger.info("Запуск парсеров из директории 'site'")

    # Получаем список файлов парсеров
    parsers = get_parser_files()

    if not parsers:
        logger.warning("Python-файлы в директории 'site' не найдены")
        return

    logger.info(f"Найдено {len(parsers)} парсеров:")
    for idx, parser in enumerate(parsers, 1):
        logger.info(f"{idx}. {os.path.basename(parser)}")

    # Запускаем все парсеры
    stats = run_all_parsers(parsers)

    # Выводим итоговую статистику
    total_time = time.time() - start_time
    logger.info(f"Все парсеры обработаны за {total_time:.2f} секунд")
    logger.info(
        f"Успешно: {stats['success']}, С ошибками: {stats['failed']}, Всего: {stats['total']}"
    )

    # Выводим статистику по каждому парсеру
    logger.info("\nСтатистика выполнения:")
    for parser, result in stats["results"].items():
        status = "✓" if result["success"] else "✗"
        logger.info(f"{status} {parser}: {result['elapsed_time']:.2f} сек")


# if __name__ == "__main__":
#     main()
