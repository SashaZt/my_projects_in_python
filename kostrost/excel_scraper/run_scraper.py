import asyncio
import os
import shutil
import sys
from pathlib import Path

from config.logger import logger
from main_export import process_all_json_files
from run_site_parsers import main_all
from scrapers.excel_scraper import ExcelSheetScraper

current_directory = Path.cwd()
config_directory = current_directory / "config"
log_directory = current_directory / "log"
html_directory = current_directory / "html_pages"
html_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"


def main():
    """Основная функция для запуска скрапера без аргументов"""
    logger.info("Запуск скрапера в непрерывном режиме без аргументов")

    # Инициализируем скрапер с дефолтными параметрами
    scraper = ExcelSheetScraper()

    try:
        # Запускаем основную функцию скрапера
        asyncio.run(scraper.main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":

    while True:
        print(
            "\nВыберите действие:\n"
            "1. Скачивание данные\n"
            "2. Парсинг данных\n"
            "3. Записать результат в Ексель\n"
            "3. Очистить временные файлы\n"
            "0. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1":
            main()

        elif choice == "2":
            main_all()
        elif choice == "3":
            process_all_json_files()
        elif choice == "4":
            shutil.rmtree(html_directory)
            if not os.path.exists(html_directory):
                html_directory.mkdir(parents=True, exist_ok=True)
        elif choice == "0":
            exit()
        else:
            logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")
