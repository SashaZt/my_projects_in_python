import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import requests
import random
import csv


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
file_proxy = configuration_directory / "roman.txt"


cookies = {
    "PHPSESSID": "994gpk9m3pm3v0b33t8lv5m3nv",
    "G_ENABLED_IDPS": "google",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


class Get_Response:
    def __init__(
        self,
        max_workers,
        base_url,
        cookies,
        headers,
        html_files_directory,
        csv_file_successful,
        output_csv_file,
        file_proxy,
    ) -> None:
        # Инициализация переданных параметров как атрибутов класса
        self.max_workers = max_workers
        self.base_url = base_url
        self.cookies = cookies
        self.headers = headers
        self.html_files_directory = Path(html_files_directory)
        self.csv_file_successful = csv_file_successful
        self.output_csv_file = output_csv_file
        self.file_proxy = file_proxy

        # Создание экземпляра класса для работы с файлами
        self.working_files = Working_with_files(
            self.csv_file_successful, self.file_proxy
        )

    def process_infox_file(self):
        # Загружаем список прокси-серверов из файла
        proxies = self.working_files.load_proxies()

        # Загружаем уже обработанные URL, чтобы не обрабатывать их повторно
        successful_urls = self.working_files.get_successful_urls()

        # Загружаем список URL для обработки из CSV-файла
        urls_df = pd.read_csv(self.output_csv_file)

        # Инициализация прогресс-бара
        total_urls = len(urls_df)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        # Запускаем многопоточную обработку
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи для каждого URL в списке
            futures = [
                executor.submit(self.fetch_and_save_html, url, successful_urls, proxies)
                for url in urls_df["identifier"]
            ]

            # Отслеживаем выполнение задач
            for future in as_completed(futures):
                try:
                    future.result()  # Получаем результат выполнения задачи
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                finally:
                    # Обновляем прогресс-бар после каждой завершенной задачи
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        logger.info("Все запросы выполнены.")

    def fetch_and_save_html(self, identifier, successful_urls, proxies):
        # Проверяем, обрабатывался ли этот URL ранее
        if identifier in successful_urls:
            logger.info(f"| Компания уже была обработана, пропускаем. |")
            return

        try:
            # Выбираем случайный прокси-сервер для запроса
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}

            # Формируем полный URL для запроса
            url = f"{self.base_url}/{identifier}"

            # Отправляем запрос
            response = requests.get(
                url,
                proxies=proxies_dict,
                headers=self.headers,
                cookies=self.cookies,
            )

            # Проверяем успешность запроса
            if response.status_code == 200:
                # Сохраняем HTML-файл в указанную директорию
                file_path = self.html_files_directory / f"{identifier}.html"
                file_path.write_text(response.text, encoding="utf-8")

                # Добавляем идентификатор в множество успешных
                successful_urls.add(identifier)

                # Сохраняем идентификатор в CSV для отслеживания
                self.working_files.write_to_csv(identifier, self.csv_file_successful)
            else:
                logger.error(
                    f"Ошибка: не удалось получить данные для {identifier}. Статус: {response.status_code}"
                )

        except Exception as e:
            # Логирование ошибки, если запрос или обработка завершаются с ошибкой
            logger.error(f"Произошла ошибка при обработке {identifier}: {e}")


class Working_with_files:
    def __init__(self, csv_file_successful, file_proxy) -> None:
        # Сохраняем пути к файлам как атрибуты класса
        self.csv_file_successful = csv_file_successful
        self.file_proxy = file_proxy

    def load_proxies(self):
        # Загружаем список прокси-серверов из файла
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(len(proxies))  # Логируем количество прокси
        return proxies

    def write_to_csv(self, data, filename):
        # Проверяем, существует ли файл и добавляем заголовок, если он пустой
        file_path = Path(filename)
        if not file_path.exists() or file_path.stat().st_size == 0:
            with open(filename, "a", encoding="utf-8") as f:
                f.write("identifier\n")

        # Записываем новый идентификатор в CSV-файл
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{data}\n")

    def get_successful_urls(self):
        # Загружаем уже обработанные идентификаторы из CSV-файла
        if not Path(self.csv_file_successful).exists():
            return set()

        with open(self.csv_file_successful, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            successful_urls = {
                row[0] for row in reader if row
            }  # Собираем идентификаторы в множество
        return successful_urls


max_workers = 20
base_url = "https://www.ua-region.com.ua"
response_handler = Get_Response(
    max_workers,
    base_url,
    cookies,
    headers,
    html_files_directory,
    csv_file_successful,
    output_csv_file,
    file_proxy,
)
response_handler.process_infox_file()
