import asyncio
import os
import shutil
from parser import Parser
from pathlib import Path

from configuration.logger_setup import logger
from dotenv import load_dotenv
from downloader import Downloader
from writer import Writer


def main_loop():

    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    load_dotenv(env_path)
    api_key = os.getenv("API_KEY")
    max_workers = int(os.getenv("MAX_WORKERS", "20"))

    # Указываем пути к файлам и папкам
    current_directory = Path.cwd()
    html_files_directory = current_directory / "html_files"
    data_directory = current_directory / "data"
    configuration_directory = current_directory / "configuration"
    json_scrapy = current_directory / "json_scrapy"

    html_files_directory.mkdir(exist_ok=True, parents=True)
    data_directory.mkdir(parents=True, exist_ok=True)
    configuration_directory.mkdir(parents=True, exist_ok=True)
    json_scrapy.mkdir(parents=True, exist_ok=True)

    output_json = data_directory / "output.json"
    incoming_json = data_directory / "incoming.json"

    # Создаем объекты классов
    downloader = Downloader(api_key, html_files_directory, incoming_json, json_scrapy)
    writer = Writer(output_json)
    parser = Parser(
        html_files_directory,
        max_workers,
    )

    # Основной цикл программы
    while True:
        print(
            "\nВыберите действие:\n"
            "1. Асинхронное скачивание товаров\n"
            # "2. Парсинг страниц пагинации\n"
            "2. Сохранение результатов\n"
            "3. Очистить временные папки\n"
            "0. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1":
            asyncio.run(downloader.main_url())
        elif choice == "2":
            all_results = parser.parsing_html()
            writer.save_results_to_json(all_results)
        elif choice == "3":
            shutil.rmtree(html_files_directory)
        elif choice == "0":
            break
        else:
            logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
