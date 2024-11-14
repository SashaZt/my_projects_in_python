import logging

from configuration.config import Config
from data.file_manager import FileManager
from networking.scraper import Scraper
from parsing.html_parser import HTMLParser


def main():
    # Example workflow
    urls = FileManager.read_cities_from_csv(Config.CSV_OUTPUT_FILE)

    # Initialize scraper
    scraper = Scraper(urls)
    html_contents = scraper.run()

    # Parsing HTML and saving
    parsed_data = []
    for content in html_contents:
        parsed_data.append(HTMLParser.parse_product_data(content))

    # Save results
    FileManager.save_results_to_json(parsed_data, Config.JSON_RESULT)
    FileManager.save_json_to_excel(Config.JSON_RESULT, Config.XLSX_RESULT)


def main_loop():
    """Основной цикл программы для обработки пользовательских команд."""
    while True:
        print(
            "\nВыберите действие:\n"
            "1 - Запустить полный процесс\n"
            "2 - Получить весь список Node\n"
            "3 - Скачать все файлы Node\n"
            "4 - Сформировать файл с результатом\n"
            "0 - Завершить программу"
        )

        # Проверка ввода от пользователя
        try:
            user_input = int(input("Введите номер действия: "))
            if user_input not in range(5):
                raise ValueError
        except ValueError:
            print("Ошибка: Введите корректное число от 0 до 4.")
            continue

        if user_input == 1:
            run_full_process()
        elif user_input == 2:
            get_node_list()
        elif user_input == 3:
            download_node_files()
        elif user_input == 4:
            create_result_file()
        elif user_input == 0:
            print("Программа завершена.")
            break


def run_full_process():
    urls = FileManager.read_cities_from_csv(Config.CSV_OUTPUT_FILE)
    scraper = Scraper(urls)
    html_contents = scraper.run()

    # Обработка и сохранение данных
    parsed_data = []
    for content in html_contents:
        parsed_data.append(HTMLParser.parse_name(content))  # Парсим имя для примера
    FileManager.save_results_to_json(parsed_data, Config.JSON_RESULT)


def get_node_list():
    # Заглушка: реализация получения списка узлов
    print("Получение списка Node...")


def download_node_files():
    # Заглушка: реализация скачивания файлов узлов
    print("Скачивание файлов Node...")


def create_result_file():
    # Заглушка: реализация создания файла с результатами
    print("Формирование файла с результатом...")


if __name__ == "__main__":
    main_loop()
