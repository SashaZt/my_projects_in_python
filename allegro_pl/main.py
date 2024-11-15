import os
from parser import Parser
from pathlib import Path

from async_downloader import AsyncDownloader
from dotenv import load_dotenv
from downloader import Downloader
from writer import Writer


def main_loop():

    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    load_dotenv(env_path)
    api_key = os.getenv("API_KEY")
    url_start = os.getenv("URL_START")
    max_workers = int(os.getenv("MAX_WORKERS", "20"))

    # Указываем пути к файлам и папкам
    current_directory = Path.cwd()
    html_page_directory = current_directory / "html_page"
    html_files_directory = current_directory / "html_files"
    data_directory = current_directory / "data"
    configuration_directory = current_directory / "configuration"

    data_directory.mkdir(parents=True, exist_ok=True)
    html_files_directory.mkdir(exist_ok=True, parents=True)
    configuration_directory.mkdir(parents=True, exist_ok=True)
    html_page_directory.mkdir(parents=True, exist_ok=True)

    csv_output_file = data_directory / "output.csv"
    json_result = data_directory / "result.json"
    xlsx_result = data_directory / "result.xlsx"

    # Создаем объекты классов
    downloader = Downloader(
        api_key, html_page_directory, html_files_directory, csv_output_file, max_workers
    )
    async_downloader = AsyncDownloader(
        api_key, html_files_directory, csv_output_file, max_workers
    )
    writer = Writer(csv_output_file, json_result, xlsx_result)
    parser = Parser(html_files_directory, html_page_directory, csv_output_file)

    # Основной цикл программы
    while True:
        print(
            "\nВыберите действие:\n"
            "1. Скачивание страниц пагинации\n"
            "2. Парсинг страниц пагинации\n"
            "3. Сохранение результатов\n"
            "4. Асинхронное скачивание\n"
            "5. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1":
            print(url_start)
            downloader.get_all_page_html(url_start)
        elif choice == "2":
            parser.get_url_html_csv()
            print("Парсинг завершен.")
        elif choice == "3":
            all_results = parser.parsing_html()
            writer.save_results_to_json(all_results)
            writer.save_json_to_excel()
            print("Результаты сохранены.")
        elif choice == "4":
            async_downloader.get_url_async()
            print("Асинхронное скачивание в разработке.")
        elif choice == "5":
            break
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
