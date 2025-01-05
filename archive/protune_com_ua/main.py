import re
from pathlib import Path

# Ваши модули
from get_response import GetResponse
from parsing import Parsing

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
img_files_directory = current_directory / "img_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
html_files_directory.mkdir(parents=True, exist_ok=True)
img_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"


def get_cookies():
    """Извлекает заголовки и cookies из файла конфигурации.

    Функция читает конфигурационный файл, содержащий строку cURL, и извлекает из неё
    значения заголовков и cookies для последующего использования в HTTP-запросах.

    Returns:
        tuple: Кортеж, содержащий два словаря - headers и cookies, которые могут
        быть переданы в запросы для авторизации и других настроек.
    """
    with open(config_txt_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def main_loop():
    """Основной цикл программы для обработки пользовательских команд.

    Функция выводит меню команд, запрашивает у пользователя действие и выполняет
    соответствующие задачи, такие как загрузка sitemap, HTML файлов, парсинг,
    скачивание изображений и сохранение результатов. Ввод проверяется на корректность,
    и при ошибках программа повторно запрашивает команду.

    Available commands:
        1: Запустить полный процесс
        2: Скачать sitemap
        3: Скачать HTML файлы
        4: Запустить парсинг HTML файлов
        5: Скачать изображения
        6: Сформировать файл с результатом
        0: Завершить программу
    """
    headers, cookies = get_cookies()
    max_workers = 50
    url_sitemap = "https://protune.com.ua/sitemap.xml"

    while True:
        print(
            "\nВыберите действие:\n"
            "1 - Запустить полный процесс\n"
            "2 - Скачать sitemap\n"
            "3 - Скачать HTML файлы\n"
            "4 - Запустить парсинг HTML файлов\n"
            "5 - Скачать изображения\n"
            "6 - Сформировать файл с результатом\n"
            "0 - Завершить программу"
        )

        # Проверка ввода от пользователя
        try:
            user_input = int(input("Введите номер действия: "))
            if user_input not in range(7):
                raise ValueError
        except ValueError:
            print("Ошибка: Введите корректное число от 0 до 6.")
            continue

        if user_input == 1:
            response_handler = GetResponse(
                max_workers, cookies, headers,
                html_files_directory, file_proxy, url_sitemap,
                json_result, output_csv_file, img_files_directory
            )
            response_handler.parsing_sitemap_start()
            response_handler.process_infox_file()

            processor = Parsing(
                html_files_directory, xlsx_result,
                max_workers, file_proxy, json_result, img_files_directory
            )
            all_results = processor.parsing_html()
            processor.save_results_to_json(all_results)
            response_handler.process_infox_img()
            processor.save_results_to_xlsx()

        elif user_input == 2:
            response_handler = GetResponse(
                max_workers, cookies, headers,
                html_files_directory, file_proxy, url_sitemap,
                json_result, output_csv_file, img_files_directory
            )
            response_handler.parsing_sitemap_start()

        elif user_input == 3:
            response_handler = GetResponse(
                max_workers, cookies, headers,
                html_files_directory, file_proxy, url_sitemap,
                json_result, output_csv_file, img_files_directory
            )
            response_handler.process_infox_file()

        elif user_input == 4:
            processor = Parsing(
                html_files_directory, xlsx_result,
                max_workers, file_proxy, json_result, img_files_directory
            )
            all_results = processor.parsing_html()
            processor.save_results_to_json(all_results)

        elif user_input == 5:
            response_handler = GetResponse(
                max_workers, cookies, headers,
                html_files_directory, file_proxy, url_sitemap,
                json_result, output_csv_file, img_files_directory
            )
            response_handler.process_infox_img()

        elif user_input == 6:
            processor = Parsing(
                html_files_directory, xlsx_result,
                max_workers, file_proxy, json_result, img_files_directory
            )
            processor.save_results_to_xlsx()

        elif user_input == 0:
            print("Программа завершена.")
            break  # Завершение программы


if __name__ == "__main__":
    main_loop()
