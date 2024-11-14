import os
from parser import Parser
from pathlib import Path

from dotenv import load_dotenv
from downloader import Downloader
from writer import Writer


def main_loop():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    url_start = os.getenv("URL_START")

    # Указываем пути к файлам и папкам
    current_directory = Path.cwd()
    html_page_directory = current_directory / "html_page"
    html_files_directory = current_directory / "html_files"
    data_directory = current_directory / "data"

    csv_output_file = current_directory / "output.csv"
    json_result = data_directory / "result.json"
    xlsx_result = data_directory / "result.xlsx"

    # Создаем объекты классов
    downloader = Downloader(api_key, html_page_directory, html_files_directory)
    writer = Writer(csv_output_file, json_result, xlsx_result)
    parser = Parser(html_page_directory)

    # Основной цикл программы
    while True:
        print(
            "\nВыберите действие:\n"
            "1. Скачивание страниц\n"
            "2. Парсинг страниц\n"
            "3. Сохранение результатов\n"
            "4. Скачивание товаров\n"
            "5. Асинхронное скачивание\n"
            "6. Выход"
        )
        choice = input("Введите номер действия: ")

        if choice == "1":
            downloader.get_all_page_html(url_start)
        elif choice == "2":
            all_results = parser.parsing_html()
            print("Парсинг завершен.")
        elif choice == "3":
            all_results = parser.parsing_html()
            writer.save_results_to_json(all_results)
            writer.save_json_to_excel()
            print("Результаты сохранены.")
        elif choice == "4":
            url_list = parser.list_html()
            downloader.get_url(url_list)
        elif choice == "5":
            # Здесь будет асинхронная логика скачивания, аналогичная get_url_async из main_old.py
            print("Асинхронное скачивание в разработке.")
        elif choice == "6":
            break
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main_loop()
