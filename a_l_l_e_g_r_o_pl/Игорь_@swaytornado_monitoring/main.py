import asyncio
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from parser import Parser
from pathlib import Path

from configuration.logger_setup import logger
from dotenv import load_dotenv
from downloader import Downloader
from send_messages import TgBot
from writer import Writer

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
INCOMING_FILE = os.getenv("INCOMING_FILE")
max_workers = int(os.getenv("MAX_WORKERS", "20"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = []

i = 0
while True:
    chat_id = os.getenv(f"CHAT_ID_{i}")
    if chat_id is None:
        break  # Прекращаем, если переменных больше нет
    TELEGRAM_CHAT_IDS.append(chat_id)
    i += 1

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

# Получаем текущую дату
current_date = datetime.now()

# Форматируем дату в нужный формат
formatted_date = current_date.strftime("%Y_%m_%d")
output_json = data_directory / f"{formatted_date}_output.json"
incoming_file = data_directory / INCOMING_FILE
tg_bot = TgBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS)


def determine_file_type(file_path):
    """
    Определяет тип файла: JSON или TXT.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            # Пытаемся разобрать как JSON
            json.loads(content)
            return "json"
    except json.JSONDecodeError:
        # Если не JSON, проверяем, является ли TXT
        if file_path.suffix == ".txt":
            return "txt"
        else:
            raise ValueError(f"Неизвестный формат файла: {file_path.name}")


def process_file(file_path):
    """
    Обрабатывает файл, возвращая список URL.
    """
    file_type = determine_file_type(file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        if file_type == "json":
            urls = json.load(file)
        elif file_type == "txt":
            urls = [line.strip() for line in file if line.strip()]
        else:
            raise ValueError("Поддерживаются только файлы JSON и TXT.")
    return urls


def count_urls(file_path):
    """
    Возвращает количество URL в файле.
    """
    urls = process_file(file_path)
    return len(urls)


def main_loop():
    urls = process_file(incoming_file)
    # Создаем объекты классов
    downloader = Downloader(api_key, html_files_directory, urls, json_scrapy)
    writer = Writer(output_json, tg_bot)
    parser = Parser(
        html_files_directory,
        max_workers,
    )
    # Фиксируем время начала
    start_time_now = datetime.now()
    start_time = start_time_now.strftime("%Y-%m-%d %H:%M:%S")

    # Уведомляем о старте программы
    tg_bot.send_message(f"Старт выполнения программы {start_time}")
    count_url = count_urls(incoming_file)

    tg_bot.send_message(f"Количество товаров на проверку {count_url}")

    try:
        # Основной код программы
        asyncio.run(downloader.main_url())
        all_results = parser.parsing_html()

        writer.save_results_to_json(all_results, tg_bot)

        # Уведомляем о завершении сохранения результатов
        # tg_bot.send_message("Результаты успешно сохранены.")

    except Exception as e:
        # Обработка ошибок
        tg_bot.send_message(f"Произошла ошибка: {e}")
        raise  # Пробрасываем исключение выше, если это критично

    # Фиксируем время окончания
    end_time_now = datetime.now()
    end_time = end_time_now.strftime("%Y-%m-%d %H:%M:%S")
    tg_bot.send_message(f"Конец выполнения программы {end_time}")

    # Рассчитываем длительность
    duration = end_time_now - start_time_now
    minutes, seconds = divmod(duration.total_seconds(), 60)
    tg_bot.send_message(f"Длительность {int(minutes)}мин {int(seconds)}сек")
    number_of_results = len(all_results)

    tg_bot.send_message(f"Обработано {number_of_results}")

    # # Основной цикл программы
    # while True:
    #     print(
    #         "\nВыберите действие:\n"
    #         "1. Асинхронное скачивание товаров\n"
    #         # "2. Парсинг страниц пагинации\n"
    #         "2. Сохранение результатов\n"
    #         "3. Очистить временные папки\n"
    #         "0. Выход"
    #     )
    #     choice = input("Введите номер действия: ")

    #     if choice == "1":

    #     elif choice == "2":
    #         all_results = parser.parsing_html()
    #         writer.save_results_to_json(all_results, tg_bot)
    #     elif choice == "3":
    #         shutil.rmtree(html_files_directory)
    #     elif choice == "0":
    #         break
    #     else:
    #         logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
