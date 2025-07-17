from pathlib import Path

from data_verification import DataVerification  # Импортируем новый класс
from dynamic_postgres import DynamicPostgres

# Ваши модули
from get_response import GetResponse
from parsing import Parsing

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
file_proxy = configuration_directory / "proxy.txt"

cookies = {
    "G_ENABLED_IDPS": "google",
    "PHPSESSID": "piq5q77h0nmh57qksd0g49o9qm",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": "https://www.ua-region.com.ua/new-enterprises",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-gpc": "1",
}

while True:
    max_workers = 50
    base_url = "https://www.ua-region.com.ua"
    url_sitemap = "https://www.ua-region.com.ua/sitemap.xml"

    # Запрос ввода от пользователя
    print(
        "Введите 1 для запуска полного процесса\n"
        "Введите 2 для скачивания sitemap\n"
        "Введите 3 для скачивания html файлов\n"
        "Введите 4 для запуска парсинга\n"
        "Введите 5 для записи в БД\n"
        "Введите 6 для запуска сверки данных\n"
        "Введите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        response_handler = GetResponse(
            max_workers,
            base_url,
            cookies,
            headers,
            html_files_directory,
            csv_file_successful,
            output_csv_file,
            file_proxy,
            url_sitemap,
        )
        # Запуск метода для получения всех sitemaps и обработки
        response_handler.get_all_sitemap()

        # Запуск метода скачивания html файлов
        response_handler.process_infox_file()

        # Парсинг html файлов
        processor = Parsing(html_files_directory, xlsx_result, max_workers)
        all_results = processor.parsing_html()
        processor.save_results_to_json(all_results)

        # Создаем экземпляр DynamicPostgres
        db = DynamicPostgres()
        # Создаем или обновляем таблицу
        data = db.load_data_from_json()
        db.create_or_update_table("ua_region_com_ua", data)

        # Вставляем данные
        db.insert_data("ua_region_com_ua", data, num_threads=20)

        # Закрываем соединение с базой данных
        db.close()
    elif user_input == 2:
        response_handler = GetResponse(
            max_workers,
            base_url,
            cookies,
            headers,
            html_files_directory,
            csv_file_successful,
            output_csv_file,
            file_proxy,
            url_sitemap,
        )
        # Запуск метода для получения всех sitemaps и обработки
        response_handler.get_all_sitemap()

    elif user_input == 3:
        response_handler = GetResponse(
            max_workers,
            base_url,
            cookies,
            headers,
            html_files_directory,
            csv_file_successful,
            output_csv_file,
            file_proxy,
            url_sitemap,
        )

        # Запуск метода скачивания html файлов
        response_handler.process_infox_file()

    elif user_input == 4:
        processor = Parsing(html_files_directory, xlsx_result, max_workers)
        all_results = processor.parsing_html()
        processor.save_results_to_json(all_results)

    elif user_input == 5:

        # Создать экземпляр класса DynamicSQLite, указав имя базы данных
        db = DynamicPostgres()
        # Создаем или обновляем таблицу
        data = db.load_data_from_json()
        db.create_or_update_table("ua_region_com_ua", data)

        # Вставляем данные
        db.insert_data("ua_region_com_ua", data, num_threads=20)

        # Закрываем соединение с базой данных
        db.close()
    elif user_input == 6:
        # Логика сверки данных
        db = DynamicPostgres()  # Подключаемся к базе данных
        verifier = DataVerification(
            db.conn_pool
        )  # Создаем экземпляр класса DataVerification

        verifier.export_edrpou_to_csv()  # Экспортируем данные из БД в edrpou.csv
        verifier.verify_and_update_output()  # Сверяем и обновляем output.csv

        db.close()  # Закрываем соединение с БД
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
