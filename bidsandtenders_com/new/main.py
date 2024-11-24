from pathlib import Path

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
    "Suite.Web.SecurityProvider.Customer_PRD": "f7ab3be9-f564-43f9-9030-46732cafae0f",
    "__RequestVerificationToken_L01vZHVsZS9UZW5kZXJz0": "AjdFmb8GTgelmLNCbp3e8BjvQDntsPW_pFsQMpIXuOVDQvNgclSei0P_92M9rPLfSBAQrW_kauV-vlrOfbEHWh27gC81",
}


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://bidsandtenders.ic9.esolg.ca/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


while True:
    max_workers = 5
    base_url = ""
    url_sitemap = "https://www.procore.com/network/profiles-sitemap.xml"

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
            headers,
            cookies,
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
    elif user_input == 2:
        response_handler = GetResponse(
            max_workers,
            base_url,
            headers,
            cookies,
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
            headers,
            cookies,
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
        # processor.save_results_to_json(all_results)
        processor.write_to_excel(all_results)

    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
