import asyncio
import os
import shutil
from datetime import datetime
from parser import Parser
from pathlib import Path
from urllib.parse import urlencode, urlparse

from configuration.logger_setup import logger
from dotenv import dotenv_values, load_dotenv
from downloader import Downloader
from writer import Writer


# Формирование ссылки на основе данных из файла .env
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


# Загрузка файла .env из папки
def get_env():
    env_path = os.path.join(os.getcwd(), "configuration", ".env")

    if os.path.isfile(env_path):  # Проверяем, существует ли файл
        # Удаляем ранее загруженные переменные
        for key in dotenv_values(env_path).keys():
            if key in os.environ:
                del os.environ[key]

        # Перезагружаем .env
        load_dotenv(env_path)

        # Читаем переменные
        min_count = int(os.getenv("MIN_COUNT", "50"))
        api_key = os.getenv("API_KEY")
        max_workers = int(os.getenv("MAX_WORKERS", "20"))
        url_start = link_formation()
        
        # Получение значения для параметра "premium"
        use_ultra_premium = os.getenv("USE_ULTRA_PREMIUM", "false").lower() == "true"

        logger.info("Файл .env загружен успешно.")
        return min_count, api_key, max_workers, url_start, use_ultra_premium
    else:
        logger.error(f"Файл {env_path} не найден!")
        return None


def make_directory(url_start):

    # Извлекаем путь из URL
    path = urlparse(url_start).path

    # Получаем последний сегмент пути
    last_segment = path.split("/")[-1]

    # Заменяем дефисы на подчеркивания
    directory_name = last_segment.replace("-", "_")
    # Получаем текущую дату
    current_date = datetime.now()

    # Форматируем дату в нужный формат
    formatted_date = current_date.strftime("%Y_%m_%d")

    # Указываем пути к файлам и папкам
    current_directory = Path.cwd()
    configuration_directory = current_directory / "configuration"
    data_directory = current_directory / "data"
    temp_directory = current_directory / "temp"

    # Не удаляем
    json_products = data_directory / "json_products"
    xlsx_files = data_directory / "xlsx"
    csv_files = data_directory / "csv"
    html_files = data_directory / "html_files"
    html_files_directory = html_files / f"{formatted_date}_{directory_name}"
    xlsx_directory = xlsx_files / f"{formatted_date}_{directory_name}"
    csv_directory = csv_files / f"{formatted_date}_{directory_name}"

    # Удаляем

    json_page_directory = temp_directory / "json_page"
    json_scrapy = temp_directory / "json_scrapy"
    data_directory.mkdir(parents=True, exist_ok=True)
    csv_directory.mkdir(parents=True, exist_ok=True)
    xlsx_directory.mkdir(parents=True, exist_ok=True)
    temp_directory.mkdir(parents=True, exist_ok=True)
    html_files_directory.mkdir(exist_ok=True, parents=True)
    json_page_directory.mkdir(exist_ok=True, parents=True)
    json_products.mkdir(parents=True, exist_ok=True)
    json_scrapy.mkdir(parents=True, exist_ok=True)

    configuration_directory.mkdir(parents=True, exist_ok=True)

    return (
        directory_name,
        formatted_date,
        csv_directory,
        data_directory,
        xlsx_directory,
        html_files_directory,
        json_products,
        json_scrapy,
        json_page_directory,
        temp_directory,
    )


# def main_loop():
#     # Основной цикл программы
#     while True:
#         min_count, api_key, max_workers, url_start = get_env()  # Перезагрузка данных
#         (
#             directory_name,
#             formatted_date,
#             csv_directory,
#             data_directory,
#             xlsx_directory,
#             html_files_directory,
#             json_products,
#             json_scrapy,
#             json_page_directory,
#             temp_directory,
#         ) = make_directory(url_start)

#         csv_output_file = csv_directory / f"{formatted_date}_{directory_name}.csv"
#         json_result = data_directory / "result.json"
#         xlsx_result = xlsx_directory / f"{formatted_date}_{directory_name}.xlsx"

#         # Создаем объекты классов
#         downloader = Downloader(
#             min_count,
#             api_key,
#             html_files_directory,
#             csv_output_file,
#             json_products,
#             json_scrapy,
#             url_start,
#             max_workers,
#             json_result,
#             xlsx_result,
#             json_page_directory,
#         )
#         writer = Writer(csv_output_file, json_result, xlsx_result)
#         parser = Parser(
#             min_count,
#             html_files_directory,
#             csv_output_file,
#             max_workers,
#             json_products,
#             json_page_directory,
#         )

#         print(
#             "\nВыберите действие:\n"
#             "1. Скачивание страниц пагинации\n"
#             "2. Асинхронное скачивание товаров\n"
#             "3. Сохранение результатов\n"
#             "4. Запустить все этапы сразу!!!\n"
#             "0. Выход"
#         )
#         choice = input("Введите номер действия: ")

#         if choice == "1":
#             (
#                 directory_name,
#                 formatted_date,
#                 csv_directory,
#                 data_directory,
#                 xlsx_directory,
#                 html_files_directory,
#                 json_products,
#                 json_scrapy,
#                 json_page_directory,
#                 temp_directory,
#             ) = make_directory(url_start)
#             downloader.get_all_page_html()
#         # elif choice == "2":
#         #     parser.get_url_html_csv()
#         elif choice == "2":
#             asyncio.run(downloader.main_url())
#         elif choice == "3":
#             all_results = parser.parsing_html()
#             writer.save_results_to_json(all_results)
#             writer.save_json_to_excel()

#             all_results = parser.parsing_json()
#             # min_count, api_key, max_workers, url_start = get_env()
#             # make_directory()

#         elif choice == "4":
#             (
#                 directory_name,
#                 formatted_date,
#                 csv_directory,
#                 data_directory,
#                 xlsx_directory,
#                 html_files_directory,
#                 json_products,
#                 json_scrapy,
#                 json_page_directory,
#                 temp_directory,
#             ) = make_directory(url_start)
#             # Запуск метода для получения всех страниц HTML
#             logger.info("Запуск хождения по пагинации")
#             downloader.get_all_page_html()

#             # Запуск асинхронного метода для обработки URL
#             logger.info("Запуск скачивания товара")
#             asyncio.run(downloader.main_url())

#             # Парсинг HTML и получение результатов
#             logger.info("Запуск парсинга html страниц")
#             all_results = parser.parsing_html()

#             # Сохранение результатов в JSON и Excel
#             logger.info("Сохранение результатов в Excel")
#             writer.save_results_to_json(all_results)
#             writer.save_json_to_excel()

#             # Парсинг данных из JSON
#             logger.info("Сохранение результатов в JSON")
#             all_results = parser.parsing_json()

#         elif choice == "5":
#             shutil.rmtree(temp_directory)


#         elif choice == "0":
#             break
#         else:
#             logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")
def create_objects(
    min_count, api_key, max_workers, url_start, directories, use_ultra_premium
):
    (
        directory_name,
        formatted_date,
        csv_directory,
        data_directory,
        xlsx_directory,
        html_files_directory,
        json_products,
        json_scrapy,
        json_page_directory,
        temp_directory,
    ) = directories

    csv_output_file = csv_directory / f"{formatted_date}_{directory_name}.csv"
    json_result = data_directory / "result.json"
    xlsx_result = xlsx_directory / f"{formatted_date}_{directory_name}.xlsx"

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
        use_ultra_premium,
    )
    writer = Writer(csv_output_file, json_result, xlsx_result, use_ultra_premium)
    parser = Parser(
        min_count,
        html_files_directory,
        csv_output_file,
        max_workers,
        json_products,
        json_page_directory,
        use_ultra_premium,
    )

    return downloader, writer, parser


def main_loop():
    # Основной цикл программы
    while True:
        downloader = None
        parser = None
        writer = None

        print(
            "\nВыберите действие:\n"
            "1. Скачивание страниц пагинации\n"
            "2. Асинхронное скачивание товаров\n"
            "3. Сохранение результатов\n"
            "4. Запустить все этапы сразу!!!\n"
            "5. Удалить временные файлы\n"
            "0. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1" or choice == "4":
            # Перезагружаем данные из .env и создаем директории
            min_count, api_key, max_workers, url_start, use_ultra_premium = get_env()
            directories = make_directory(url_start)
            downloader, writer, parser = create_objects(
                min_count,
                api_key,
                max_workers,
                url_start,
                directories,
                use_ultra_premium,
            )

        if choice == "1":
            # Выполняем действие 1
            downloader.get_all_page_html()

        elif choice == "2":
            # Перезагружаем данные из .env и создаем директории
            min_count, api_key, max_workers, url_start, use_ultra_premium = get_env()
            directories = make_directory(url_start)
            downloader, writer, parser = create_objects(
                min_count,
                api_key,
                max_workers,
                url_start,
                directories,
                use_ultra_premium,
            )
            asyncio.run(downloader.main_url())

        elif choice == "3":
            # Перезагружаем данные из .env и создаем директории
            min_count, api_key, max_workers, url_start, use_ultra_premium = get_env()
            directories = make_directory(url_start)
            downloader, writer, parser = create_objects(
                min_count,
                api_key,
                max_workers,
                url_start,
                directories,
                use_ultra_premium,
            )
            all_results = parser.parsing_html()
            writer.save_results_to_json(all_results)
            writer.save_json_to_excel()

            all_results = parser.parsing_json()

        elif choice == "4":
            # Запуск всех этапов
            logger.info("Запуск хождения по пагинации")
            downloader.get_all_page_html()
            logger.info("Запуск скачивания товара")
            asyncio.run(downloader.main_url())
            logger.info("Запуск парсинга html страниц")
            all_results = parser.parsing_html()
            logger.info("Сохранение результатов в JSON")
            writer.save_results_to_json(all_results)
            logger.info("Сохранение результатов в Excel")
            writer.save_json_to_excel()
            all_results = parser.parsing_json()

        elif choice == "5":
            shutil.rmtree(directories[-1])  # temp_directory

        elif choice == "0":
            break
        else:
            logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
