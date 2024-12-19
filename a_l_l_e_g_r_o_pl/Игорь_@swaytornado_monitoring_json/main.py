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

# Получаем текущую дату
current_date = datetime.now()

# Форматируем дату в нужный формат
formatted_date = current_date.strftime("%Y_%m_%d")
# Загружаем файл .env
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
# API_KEY с сайта scraperapi.com
api_key = os.getenv("API_KEY")
# Количество потоков при парсинге
max_workers = int(os.getenv("MAX_WORKERS", "20"))
# Получение значения для параметра "premium"
use_ultra_premium = os.getenv("USE_ULTRA_PREMIUM", "false").lower() == "true"

# Имя входящего файла
INCOMING_FILE = os.getenv("INCOMING_FILE")

# Токен ТГ бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Имя входящей папки
SOURCE_FOLDER = os.getenv("SOURCE_FOLDER")

# Имя исходящей папки
DESTINATION_FOLDER = os.getenv("DESTINATION_FOLDER")

# Телеграмм чаты
chat_ids = os.getenv("CHAT_IDS")
TELEGRAM_CHAT_IDS = chat_ids.split(",") if chat_ids else []

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
source_folder = current_directory / SOURCE_FOLDER
destination_folder = current_directory / DESTINATION_FOLDER
temp_directory = current_directory / "temp"
json_products = destination_folder / f"{formatted_date}_json_products"
html_files_directory = destination_folder / f"{formatted_date}_html"
json_scrapy = temp_directory / "json_scrapy"

source_folder.mkdir(exist_ok=True, parents=True)
destination_folder.mkdir(exist_ok=True, parents=True)
temp_directory.mkdir(exist_ok=True, parents=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
json_products.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
json_scrapy.mkdir(parents=True, exist_ok=True)


output_json = destination_folder / f"{formatted_date}_output.json"
incoming_file = source_folder / INCOMING_FILE
if not incoming_file.exists():
    logger.warning(f"Нету файла {INCOMING_FILE} в папке {source_folder}")




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


def count_files_in_directory(directory):
    """
    Считает количество файлов в указанной директории.

    Args:
        directory (Path): Путь к директории.

    Returns:
        int: Количество файлов в директории.
    """
    if not directory.exists() or not directory.is_dir():
        return 0  # Если директория не существует или это не папка

    # Считаем только файлы
    file_count = sum(1 for file in directory.iterdir() if file.is_file())
    return file_count


def main_loop():
    urls = process_file(incoming_file)
    # Создаем объекты классов
    downloader = Downloader(
        api_key, html_files_directory, urls, json_scrapy, use_ultra_premium
    )
    # writer = Writer(output_json, tg_bot)
    parser = Parser(html_files_directory, max_workers, json_products)
    # Фиксируем время начала
    start_time_now = datetime.now()
    start_time = start_time_now.strftime("%Y-%m-%d %H:%M:%S")
    count_url = count_urls(incoming_file)
    # Уведомляем о старте программы
    tg_bot.send_message(
        f"Старт программы мониторинг Json\n{start_time}\nКоличество товаров на проверку {count_url}"
    )

    # tg_bot.send_message(f"Количество товаров на проверку {count_url}")

    try:
        # Основной код программы
        asyncio.run(downloader.main_url())
        parser.parsing_json()

        # writer.save_results_to_json(all_results, tg_bot)
        # Рассчитываем длительность
        end_time_now = datetime.now()
        end_time = end_time_now.strftime("%Y-%m-%d %H:%M:%S")
        duration = end_time_now - start_time_now
        minutes, seconds = divmod(duration.total_seconds(), 60)
        # Фиксируем время окончания

        file_count = count_files_in_directory(html_files_directory)
        # Уведомляем о завершении сохранения результатов
        tg_bot.send_message(
            f"Результаты успешно сохранены.\nОбработано {file_count}\nНе обработано {int(count_url) - int(file_count)}\nКонец выполнения программы {end_time}\nДлительность {int(minutes)}мин {int(seconds)}сек"
        )

    except Exception as e:
        logger.error(e)
        # Обработка ошибок
        tg_bot.send_message(f"Произошла ошибка: {e}")
        raise  # Пробрасываем исключение выше, если это критично

    # tg_bot.send_message(f"Конец выполнения программы {end_time}")

    # tg_bot.send_message(f"Длительность {int(minutes)}мин {int(seconds)}сек")
    # file_count = count_files_in_directory(html_files_directory)

    # # number_of_results = len(all_results)

    # tg_bot.send_message(
    #     f"Обработано {file_count}\nНе обработано {int(count_url) - int(file_count)}"
    # )


if __name__ == "__main__":
    main_loop()
