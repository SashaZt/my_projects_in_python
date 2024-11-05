from pathlib import Path

from data_verification import DataVerification  # Импортируем новый класс
from dynamic_postgres import DynamicPostgres
# Ваши модули
from get_response import Get_Response
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
    '_ga': 'GA1.1.971341584.1728630336',
    'G_ENABLED_IDPS': 'google',
    'FCCDCF': '%5Bnull%2Cnull%2Cnull%2C%5B%22CQHdjMAQHdjMAEsACBRUBNFoAP_gAEPgACgAINJD7C7FbSFCwH5zaLsAMAhHRsAAQoQAAASBAmABQAKQIAQCgkAQFASgBAACAAAAICRBIQIECAAAAUAAQAAAAAAEAAAAAAAIIAAAgAEAAAAIAAACAIAAEAAIAAAAEAAAmAgAAIIACAAAgAAAAAAAAAAAAAAAAgCAAAAAAAAAAAAAAAAAAQOhSD2F2K2kKFkPCmwXYAYBCujYAAhQgAAAkCBMACgAUgQAgFJIAgCIFAAAAAAAAAQEiCQAAQABAAAIACgAAAAAAIAAAAAAAQQAABAAIAAAAAAAAEAQAAIAAQAAAAIAABEhCAAQQAEAAAAAAAQAAAAAAAAAAABAAA.eAAAAAAAAAA%22%2C%222~70.89.93.108.122.149.196.236.259.311.313.323.358.415.449.486.494.495.540.574.609.864.981.1029.1048.1051.1095.1097.1126.1205.1276.1301.1365.1415.1449.1514.1570.1577.1598.1651.1716.1735.1753.1765.1870.1878.1889.1958.1960.2072.2253.2299.2373.2415.2506.2526.2531.2568.2571.2575.2624.2677.2778~dv.%22%2C%227A726137-665E-4996-AB78-EE34AADC75B3%22%5D%5D',
    'PHPSESSID': 'costud8pk6aiv1r9tmj59c1bec',
    'FCNEC': '%5B%5B%22AKsRol-FUSJJKA2PEVCwY3UpPnxFYEkprH-sAgaDRgK9ndnRsKiZvXBasFaXaYMGNTtqlXiD9mjvUMdjI7LFUt1HkgaXcNSW1P05uvuiooNTVP5IS6J5dYzid8v1qrd77ZnK6dvBw8KEqvErBTGmoB99LbbMdfygHw%3D%3D%22%5D%5D',
    '__gads': 'ID=9dfe76a1628555ac:T=1728630336:RT=1730794898:S=ALNI_MZCbBbzyjdmU8JXuU73XLaryJoAfw',
    '__gpi': 'UID=00000f39a80dda60:T=1728630336:RT=1730794898:S=ALNI_MYG1tahl8aq2R_Khklg10O-GAqD3Q',
    '__eoi': 'ID=17f00596f6a8a6a0:T=1728630336:RT=1730794898:S=AA-AfjawPgl9YF1wCuiGASsiL8Ln',
    '_ga_TDFGJDHCY1': 'GS1.1.1730794897.6.0.1730794900.57.0.0',
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
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
        response_handler = Get_Response(
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
        response_handler = Get_Response(
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
        response_handler = Get_Response(
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
