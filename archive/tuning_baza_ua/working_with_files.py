import json
import threading

import pandas as pd
from configuration.logger_setup import logger


class Working_with_files:
    """Класс для управления операциями с файлами, включая загрузку прокси, чтение и запись JSON и CSV данных."""

    def __init__(self,  file_proxy, json_result) -> None:
        # Сохраняем пути к файлам как атрибуты класса
        self.file_proxy = file_proxy
        self.json_result = json_result
        self.header_written = False  # Флаг для отслеживания записи заголовка
        self.write_lock = threading.Lock()  # Создаем блокировку для записи в файл
        """Инициализирует класс с путями к файлам.

        Args:
            file_proxy (Path): Путь к файлу с прокси-серверами.
            json_result (Path): Путь к JSON файлу для сохранения результатов.
        """

    def load_proxies(self):
        """Загружает список прокси-серверов из файла.

        Returns:
            list: Список строк с прокси или пустой список, если файл отсутствует или пуст.
        """
        if not self.file_proxy.exists():
            logger.warning(
                "Файл с прокси не найден, работа будет продолжена без прокси.")
            return []  # Возвращаем пустой список, если файла нет

        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file if line.strip()]

        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies

    def read_json_result(self):
        """Читает JSON файл и возвращает данные.

        Returns:
            list or dict: Данные из JSON файла или пустой список при ошибке.
        """
        with open(self.json_result, "r", encoding="utf-8") as file:
            json_result_list = json.load(file)

        return json_result_list  # Возвращает данные в виде списка, если JSON представляет список

    def save_urls_to_csv(self, urls, filename="urls.csv"):
        """Записывает список URL в CSV файл.

        Args:
            data (list): Список URL или данных для записи.
            filename (Path): Путь к CSV файлу.

        Returns:
            bool: True если запись успешна, иначе False.
        """
        # Создаем DataFrame из списка URL-адресов
        df = pd.DataFrame(urls, columns=["url"])

        # Сохраняем DataFrame в CSV-файл
        df.to_csv(filename, index=False, encoding="utf-8")
