import asyncio
import concurrent.futures
import os
import shutil
import threading
from datetime import datetime, timedelta
from parser import Parser
from pathlib import Path
from urllib.parse import urlencode, urlparse

from batch_requests import Batch
from configuration.logger_setup import logger
from dotenv import dotenv_values, load_dotenv
from downloader import Downloader

# from send_messages import TgBot
# from writer import Writer


def link_formation(url_start):
    order = str(os.getenv("ORDER", "qd"))
    stan = str(os.getenv("STAN", "nowe"))
    price_from = int(os.getenv("PRICE_FROM", "150"))
    price_to = int(os.getenv("PRICE_TO", "1500"))

    # Параметры запроса
    query_params = {
        "order": order,
        "stan": stan,
        "price_from": price_from,
        "price_to": price_to,
    }
    full_url = f"{url_start}?{urlencode(query_params)}"
    return full_url


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
        url_starts = os.getenv("URL_STARTS", "").split(",")  # Считываем список ссылок

        # Получение значения для параметра "premium"
        use_ultra_premium = os.getenv("USE_ULTRA_PREMIUM", "false").lower() == "true"

        # Токен ТГ бота
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

        # Телеграмм чаты
        chat_ids = os.getenv("CHAT_IDS")
        TELEGRAM_CHAT_IDS = chat_ids.split(",") if chat_ids else []

        # tg_bot = TgBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS)

        logger.info("Файл .env загружен успешно.")
        return (
            min_count,
            api_key,
            max_workers,
            url_starts,
            use_ultra_premium,
        )
        # return (
        #     min_count,
        #     api_key,
        #     max_workers,
        #     url_starts,
        #     use_ultra_premium,
        #     tg_bot,
        # )
    else:
        logger.error(f"Файл {env_path} не найден!")
        return None


# Создание директорий
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
    json_page = data_directory / "json_page"
    html_files_directory = html_files / f"{formatted_date}_{url_start}"
    json_files_directory = json_page / f"{formatted_date}_{url_start}"
    xlsx_directory = xlsx_files / f"{formatted_date}_{url_start}"
    csv_directory = csv_files / f"{formatted_date}_{url_start}"

    # Удаляем

    json_page_directory = temp_directory / "json_page"
    json_scrapy = temp_directory / "json_scrapy"
    data_directory.mkdir(parents=True, exist_ok=True)
    csv_directory.mkdir(parents=True, exist_ok=True)
    xlsx_directory.mkdir(parents=True, exist_ok=True)
    temp_directory.mkdir(parents=True, exist_ok=True)
    html_files_directory.mkdir(exist_ok=True, parents=True)
    json_files_directory.mkdir(exist_ok=True, parents=True)
    json_page_directory.mkdir(exist_ok=True, parents=True)
    json_products.mkdir(parents=True, exist_ok=True)
    json_scrapy.mkdir(parents=True, exist_ok=True)
    job_file = (
        json_scrapy / f"{directory_name}_active_jobs.json"
    )  # Файл для хранения задания

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
        json_files_directory,
        job_file,
    )


# Создание объектов
def create_objects(
    min_count, api_key, max_workers, url_start, directories, use_ultra_premium
):
    # def create_objects(
    #     min_count, api_key, max_workers, url_start, directories, use_ultra_premium, tg_bot
    # ):
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
        json_files_directory,
        job_file,
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
        json_files_directory,
    )
    batch = Batch(
        # min_count,
        api_key,
        html_files_directory,
        csv_output_file,
        job_file,
        json_scrapy,
    )
    # downloader = Downloader(
    #     min_count,
    #     api_key,
    #     html_files_directory,
    #     csv_output_file,
    #     json_products,
    #     json_scrapy,
    #     url_start,
    #     max_workers,
    #     json_result,
    #     xlsx_result,
    #     json_page_directory,
    #     use_ultra_premium,
    #     tg_bot,
    #     json_files_directory,
    # )
    # writer = Writer(
    #     csv_output_file,
    #     json_result,
    #     xlsx_result,
    #     use_ultra_premium,
    #     tg_bot,
    #     json_files_directory,
    # )
    parser = Parser(
        min_count,
        html_files_directory,
        csv_output_file,
        max_workers,
        json_products,
        json_page_directory,
        use_ultra_premium,
        json_files_directory,
    )
    # parser = Parser(
    #     min_count,
    #     html_files_directory,
    #     csv_output_file,
    #     max_workers,
    #     json_products,
    #     json_page_directory,
    #     use_ultra_premium,
    #     tg_bot,
    #     json_files_directory,
    # )

    return downloader, parser, batch
    # return downloader, writer, parser


lock = threading.Lock()  # Блокировка для работы с файлами


def main_loop():
    while True:
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
        # РАБОЧИЙ ВАРИАНТ
        # if choice in {"1", "2", "3", "4"}:
        #     # Перезагружаем данные из .env и получаем список ссылок
        #     min_count, api_key, max_workers, url_starts, use_ultra_premium = get_env()
        #     # min_count, api_key, max_workers, url_starts, use_ultra_premium, tg_bot = (
        #     #     get_env()
        #     # )

        #     for url_start in url_starts:
        #         # Базовый путь и суффикс
        #         base = url_start  #
        #         suffix = "c"  # Общая часть после номера страницы
        #         full_url = link_formation(url_start)
        #         directories = make_directory(base)
        #         downloader, parser, batch = create_objects(
        #             min_count,
        #             api_key,
        #             max_workers,
        #             full_url,
        #             directories,
        #             use_ultra_premium,
        #         )
        #         # downloader, writer, parser = create_objects(
        #         #     min_count,
        #         #     api_key,
        #         #     max_workers,
        #         #     full_url,
        #         #     directories,
        #         #     use_ultra_premium,
        #         #     tg_bot,
        #         # )

        #         if choice == "1":
        #             # Скачивание страниц пагинации
        #             # downloader.get_all_page_html()
        #             logger.info(f"Категория {url_start}")
        #             downloader.get_all_page_json(base, suffix)

        #         elif choice == "2":
        #             # Асинхронное скачивание товаров
        #             # asyncio.run(downloader.main_url())
        #             parser.scrap_all_page_json()
        #         elif choice == "3":
        #             # Создаём объекты Batch для всех категорий
        #             batches = []
        #             for url_start in url_starts:
        #                 directories = make_directory(url_start)
        #                 downloader, parser, batch = create_objects(
        #                     min_count,
        #                     api_key,
        #                     max_workers,
        #                     url_start,
        #                     directories,
        #                     use_ultra_premium,
        #                 )
        #                 batches.append(batch)
        #             # Параллельная проверка всех Batch
        #             batch.process_all_jobs_concurrently(
        #                 batches, max_workers=int(len(url_starts))
        #             )
        #         # elif choice == "3":
        #         #     # Обрабатываем все задания в многопоточном режиме
        #         #     batch.main()
        #         # # Сохранение результатов
        #         # all_results = parser.parsing_html()
        #         # writer.save_results_to_json(all_results)
        #         # writer.save_json_to_excel()
        #         # parser.parsing_json()

        #         elif choice == "4":
        #             downloader.get_all_page_json(base, suffix)
        #             parser.scrap_all_page_json()
        #             batch.main()
        #     # Выполнение всех этапов
        #     start_time_now = datetime.now()
        #     tg_bot.send_message(f"Запуск парсера для {url_start}")
        #     downloader.get_all_page_html()
        #     # Уникальность првоеряем
        #     # parser.scrap_page_json()
        #     # Проверяем результат выполнения main_url
        #     try:
        #         success = asyncio.run(downloader.main_url())
        #         if not success:
        #             logger.error(f"Список URL пуст для {url_start}. Пропускаю.")
        #             tg_bot.send_message(
        #                 f"Список URL пуст для {url_start}. Пропускаю."
        #             )
        #             continue  # Пропускаем текущий URL
        #     except Exception as e:
        #         logger.error(
        #             f"Ошибка при выполнении main_url для {url_start}: {str(e)}"
        #         )
        #         tg_bot.send_message(
        #             f"Ошибка при выполнении main_url для {url_start}: {str(e)}"
        #         )
        #         continue  # Пропускаем текущий URL

        #     all_results = parser.parsing_html()
        #     writer.save_results_to_json(all_results)
        #     writer.save_json_to_excel()
        #     parser.parsing_json()
        #     end_time_now = datetime.now()
        #     duration = end_time_now - start_time_now
        #     minutes, seconds = divmod(duration.total_seconds(), 60)
        #     tg_bot.send_message(
        #         f"Обработка {url_start} завершена за {int(minutes)} мин {int(seconds)} сек"
        #     )
        #     # tg_bot.send_message("Все категории собраны")
        #     logger.info("Все категории собраны")
        if choice in {"1", "2", "3", "4"}:
            # Перезагружаем данные из .env и получаем список ссылок
            min_count, api_key, max_workers, url_starts, use_ultra_premium = get_env()

            # Используем ThreadPoolExecutor для многопоточности
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                futures = []
                for url_start in url_starts:
                    base = url_start
                    suffix = "c"  # Общая часть после номера страницы
                    full_url = link_formation(url_start)
                    directories = make_directory(base)
                    downloader, parser, batch = create_objects(
                        min_count,
                        api_key,
                        max_workers,
                        full_url,
                        directories,
                        use_ultra_premium,
                    )

                    # Добавляем задачу в пул в зависимости от выбора
                    if choice == "1":
                        futures.append(
                            executor.submit(downloader.get_all_page_json, base, suffix)
                        )
                    elif choice == "2":
                        futures.append(executor.submit(parser.scrap_all_page_json))
                    elif choice == "3":
                        futures.append(executor.submit(batch.main))
                    elif choice == "4":
                        futures.append(
                            executor.submit(downloader.get_all_page_json, base, suffix)
                        )
                        futures.append(executor.submit(parser.scrap_all_page_json))
                        futures.append(executor.submit(batch.main))

                # Ожидаем завершения всех задач
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()  # Получаем результат выполнения задачи
                        logger.info(f"Задача завершена: {result}")
                    except Exception as e:
                        logger.error(f"Ошибка в задаче: {e}")
        # elif choice == "2":
        #     # Асинхронное скачивание товаров
        #     # asyncio.run(downloader.main_url())
        #     parser.scrap_all_page_json()

        elif choice == "5":
            shutil.rmtree(directories[-1])  # Удаление временных файлов

        elif choice == "0":
            break
        else:
            logger.info("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
