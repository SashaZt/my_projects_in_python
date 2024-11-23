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
    "pc_geo": "UA",
    "AMCVS_FE154C895C73B0C90A495CD8%40AdobeOrg": "1",
    "OptanonAlertBoxClosed": "2024-11-22T06:51:52.363Z",
    "amp_82bb66": "O0_ds2el4VntKH4kbQtPO0...1idafd32q.1idahid6j.1s.0.1s",
    "AMCV_FE154C895C73B0C90A495CD8%40AdobeOrg": "179643557%7CMCIDTS%7C20049%7CMCMID%7C50082547089028713869048408370093990545%7CMCOPTOUT-1732306735s%7CNONE%7CvVersion%7C5.5.0",
    "OptanonConsent": "isGpcEnabled=0&datestamp=Fri+Nov+22+2024+20%3A18%3A55+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202403.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=b249128c-9aed-4d2f-88aa-6cd0d6c4b15c&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&intType=1&geolocation=UA%3B18&AwaitingReconsent=false",
    "__cf_bm": "YMG_CHE65nnWGlXDcQ_JxtzAOolOdMNpyeS2qM2_8xc-1732299538-1.0.1.1-hwH7loD5MkHA94XqyUoMP7Lj7M8yZyHmkEzhjfntBEi3ZSDEiBNqPwaX65YhK4.MRUJYuDOy.qeg6yMAJ7F4Fg",
    "_cfuvid": "EjFjQWJwJ_cCTWqIBlCfnBj3A54m0YRREfvb4erurcw-1732299538505-0.0.1.1-604800000",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'pc_geo=UA; AMCVS_FE154C895C73B0C90A495CD8%40AdobeOrg=1; OptanonAlertBoxClosed=2024-11-22T06:51:52.363Z; amp_82bb66=O0_ds2el4VntKH4kbQtPO0...1idafd32q.1idahid6j.1s.0.1s; AMCV_FE154C895C73B0C90A495CD8%40AdobeOrg=179643557%7CMCIDTS%7C20049%7CMCMID%7C50082547089028713869048408370093990545%7CMCOPTOUT-1732306735s%7CNONE%7CvVersion%7C5.5.0; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Nov+22+2024+20%3A18%3A55+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202403.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=b249128c-9aed-4d2f-88aa-6cd0d6c4b15c&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&intType=1&geolocation=UA%3B18&AwaitingReconsent=false; __cf_bm=YMG_CHE65nnWGlXDcQ_JxtzAOolOdMNpyeS2qM2_8xc-1732299538-1.0.1.1-hwH7loD5MkHA94XqyUoMP7Lj7M8yZyHmkEzhjfntBEi3ZSDEiBNqPwaX65YhK4.MRUJYuDOy.qeg6yMAJ7F4Fg; _cfuvid=EjFjQWJwJ_cCTWqIBlCfnBj3A54m0YRREfvb4erurcw-1732299538505-0.0.1.1-604800000',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


while True:
    max_workers = 50
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
