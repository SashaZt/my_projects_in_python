import csv
import threading
from pathlib import Path

import pandas as pd
from configuration.logger_setup import logger

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


class Working_with_files:

    def __init__(self, csv_file_successful, output_csv_file, file_proxy) -> None:
        # Сохраняем пути к файлам как атрибуты класса
        self.csv_file_successful = csv_file_successful
        self.output_csv_file = output_csv_file
        self.file_proxy = file_proxy
        self.header_written = False  # Флаг для отслеживания записи заголовка
        self.write_lock = threading.Lock()  # Создаем блокировку для записи в файл

    def load_proxies(self):
        # Загружаем список прокси-серверов из файла
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        return proxies

    def write_to_csv(self, data, filename):
        # Проверяем, существует ли файл
        file_path = Path(filename)

        with self.write_lock:  # Используем блокировку для защиты кода записи в файл
            # Проверка на необходимость добавления заголовка
            if not self.header_written:
                if not file_path.exists() or file_path.stat().st_size == 0:
                    with open(filename, "a", encoding="utf-8") as f:
                        f.write("url\n")
                self.header_written = (
                    True  # Устанавливаем флаг после добавления заголовка
                )

            # Проверяем, является ли `data` итерируемым (множеством, списком) или одиночным значением
            if isinstance(data, (set, list, tuple)):
                urls_to_write = data
            else:
                urls_to_write = [data]  # Преобразуем одиночный URL в список

            # Записываем каждый URL в новую строку CSV-файла
            with open(filename, "a", encoding="utf-8") as f:
                for url in urls_to_write:
                    f.write(f"{url}\n")

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

    def remove_successful_urls(self):
        # Проверяем, существует ли файл с успешными URL и не является ли он пустым
        if (
            not self.csv_file_successful.exists()
            or self.csv_file_successful.stat().st_size == 0
        ):
            logger.info(
                "Файл urls_successful.csv не существует или пуст, ничего не делаем."
            )
            return

        # Загружаем данные из обоих CSV файлов
        try:
            # Читаем output_csv_file с заголовком
            df_products = pd.read_csv(self.output_csv_file)

            # Читаем csv_file_successful с заголовком
            df_successful = pd.read_csv(self.csv_file_successful)
        except FileNotFoundError as e:
            logger.error(f"Ошибка: {e}")
            return
        except pd.errors.EmptyDataError as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            return

        # Проверка на наличие столбца 'url' в df_products
        if "url" not in df_products.columns or "url" not in df_successful.columns:
            logger.info("Один из файлов не содержит колонку 'url'.")
            return

        # Удаляем успешные URL из списка продуктов
        initial_count = len(df_products)
        df_products = df_products[~df_products["url"].isin(df_successful["url"])]
        final_count = len(df_products)

        # Если были удалены какие-то записи
        if initial_count != final_count:
            # Перезаписываем файл output_csv_file
            df_products.to_csv(self.output_csv_file, index=False)
            logger.info(
                f"Удалено {initial_count -
                           final_count} записей из {self.output_csv_file.name}."
            )

            # Очищаем файл csv_file_successful
            open(self.csv_file_successful, "w").close()
            logger.info(f"Файл {self.csv_file_successful.name} очищен.")
        else:
            logger.info("Не было найдено совпадающих URL для удаления.")
