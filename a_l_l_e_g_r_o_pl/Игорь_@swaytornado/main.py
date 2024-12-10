import asyncio
import os
import shutil
from parser import Parser
from pathlib import Path
from urllib.parse import urlencode

from configuration.logger_setup import logger
from dotenv import load_dotenv
from downloader import Downloader
from writer import Writer


def link_formation():
    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    load_dotenv(env_path)
    url_start = os.getenv("URL_START")
    order = str(os.getenv("ORDER", "qd"))
    stan = str(os.getenv("STAN", "nowe"))
    price_from = int(os.getenv("PRICE_FROM", "150"))
    price_to = int(os.getenv("PRICE_TO", "1500"))

    # page = int(os.getenv("PAGE", "1"))
    # Параметры запроса
    query_params = {
        "order": order,
        "stan": stan,
        "price_from": price_from,
        "price_to": price_to,
        # "page": page,
    }
    full_url = f"{url_start}?{urlencode(query_params)}"
    return full_url


def main_loop():
    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    if os.path.isfile(env_path):  # Проверяем, существует ли файл
        load_dotenv(env_path)
        min_count = int(os.getenv("MIN_COUNT", "50"))
        api_key = os.getenv("API_KEY")
        max_workers = int(os.getenv("MAX_WORKERS", "20"))
        url_start = (
            link_formation()
        )  # Предполагается, что link_formation() возвращает URL
        logger.info("Файл .env загружен успешно.")
    else:
        logger.error(f"Файл {env_path} не найден!")

    # Указываем пути к файлам и папкам
    current_directory = Path.cwd()
    configuration_directory = current_directory / "configuration"
    data_directory = current_directory / "data"
    temp_directory = current_directory / "temp"

    # Не удаляем
    json_products = data_directory / "json_products"

    # Удаляем
    html_files_directory = temp_directory / "html_files"
    json_page_directory = temp_directory / "json_page"
    json_scrapy = temp_directory / "json_scrapy"

    data_directory.mkdir(parents=True, exist_ok=True)
    temp_directory.mkdir(parents=True, exist_ok=True)
    html_files_directory.mkdir(exist_ok=True, parents=True)
    json_page_directory.mkdir(exist_ok=True, parents=True)
    json_products.mkdir(parents=True, exist_ok=True)
    json_scrapy.mkdir(parents=True, exist_ok=True)

    configuration_directory.mkdir(parents=True, exist_ok=True)

    csv_output_file = data_directory / "output.csv"
    json_result = data_directory / "result.json"
    xlsx_result = data_directory / "result.xlsx"

    # Создаем объекты классов
    downloader = Downloader(
        min_count,
        api_key,
        html_files_directory,
        csv_output_file,
        json_products,
        json_scrapy,
        url_start,
        max_workers,
        json_result,
        xlsx_result,
        json_page_directory,
    )
    writer = Writer(csv_output_file, json_result, xlsx_result)
    parser = Parser(
        min_count,
        html_files_directory,
        csv_output_file,
        max_workers,
        json_products,
        json_page_directory,
    )

    # Основной цикл программы
    while True:
        print(
            "\nВыберите действие:\n"
            "1. Скачивание страниц пагинации\n"
            # "2. Парсинг страниц пагинации\n"
            "2. Асинхронное скачивание товаров\n"
            "3. Сохранение результатов\n"
            "4. Очистить временные папки\n"
            "0. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1":
            downloader.get_all_page_html()
        # elif choice == "2":
        #     parser.get_url_html_csv()
        elif choice == "2":
            asyncio.run(downloader.main_url())
        elif choice == "3":
            all_results = parser.parsing_html()
            writer.save_results_to_json(all_results)
            writer.save_json_to_excel()

            all_results = parser.parsing_json()

        elif choice == "4":
            shutil.rmtree(temp_directory)
        elif choice == "0":
            break
        else:
            logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
