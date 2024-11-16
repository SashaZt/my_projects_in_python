import asyncio
from parser import Parser

import pandas as pd
import requests
from aiohttp import ClientSession
from configuration.logger_setup import logger


class Downloader:

    def __init__(
        self,
        api_key,
        html_page_directory,
        html_files_directory,
        csv_output_file,
        max_workers,
    ):
        self.api_key = api_key
        self.html_page_directory = html_page_directory
        self.html_files_directory = html_files_directory
        self.csv_output_file = csv_output_file
        self.max_workers = max_workers
        self.parser = Parser(
            html_files_directory, html_page_directory, csv_output_file
        )  # Создаем экземпляр Parser

    # def get_all_page_html(self, url_start):
    #     html_company = self.html_page_directory / "url_start.html"
    #     payload = {"api_key": self.api_key, "url": url_start}

    #     if html_company.exists():
    #         logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
    #     else:
    #         r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)
    #         if r.status_code == 200:
    #             with open(html_company, "w", encoding="utf-8") as file:
    #                 file.write(r.text)
    #             logger.info(f"Сохранена первая страница: {html_company}")
    #         else:
    #             logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")

    def get_all_page_html(self, url_start):
        # Скачать все страницы пагинации

        html_company = self.html_page_directory / "url_start.html"
        payload = {"api_key": self.api_key, "url": url_start}

        # Проверяем, существует ли уже файл первой страницы
        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
            max_page = (
                self.parser.parsin_page()
            )  # Получаем max_page из существующего файла
        else:
            # Запрос к API для первой страницы
            r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)

            if r.status_code == 200:
                src = r.text
                with open(html_company, "w", encoding="utf-8") as file:
                    file.write(src)
                max_page = (
                    self.parser.parsin_page()
                )  # Получаем max_page из существующего файла
                logger.info(f"Сохранена первая страница: {html_company}")
            else:
                logger.error(
                    f"Ошибка при запросе первой страницы: {
                        r.status_code}"
                )
                return  # Если запрос не успешен, выходим из функции

        # Запрашиваем страницы с 2 по max_page, если max_page определен
        if max_page:
            for page in range(2, max_page + 1):
                html_company = self.html_page_directory / f"url_start_{page}.html"
                # Обновляем payload для каждой страницы
                payload = {"api_key": self.api_key, "url": f"{url_start}&p={page}"}

                if html_company.exists():
                    logger.warning(f"Файл {html_company} уже существует, пропускаем.")
                else:
                    r = requests.get(
                        "https://api.scraperapi.com/", params=payload, timeout=60
                    )

                    if r.status_code == 200:
                        src = r.text
                        with open(html_company, "w", encoding="utf-8") as file:
                            file.write(src)
                        logger.info(f"Сохранена страница {page}: {html_company}")
                    else:
                        logger.error(
                            f"Ошибка при запросе страницы {
                                page}: {r.status_code}"
                        )

    # def get_url(self, url_list):
    #     for url in url_list:
    #         html_company = self.html_files_directory / f"{url.split('/')[-1]}.html"
    #         if html_company.exists():
    #             logger.warning(f"Файл {html_company} уже существует, пропускаем.")
    #             continue
    #         payload = {"api_key": self.api_key, "url": url}
    #         r = requests.get("https://api.scraperapi.com/", params=payload, timeout=30)
    #         if r.status_code == 200:
    #             with open(html_company, "w", encoding="utf-8") as file:
    #                 file.write(r.text)
    #             logger.info(f"Сохранен файл: {html_company}")
    #         else:
    #             logger.warning(f"Ошибка {r.status_code} при загрузке URL: {url}")

    # # Главная функция для запуска асинхронной загрузки

    # def get_url_async(self):
    #     urls = self.read_cities_from_csv(self.csv_output_file)
    #     asyncio.run(self.process_urls(urls))

    # def read_cities_from_csv(self, input_csv_file):
    #     df = pd.read_csv(input_csv_file)
    #     return df["url"].tolist()

    # # Асинхронная функция для запуска задач в очереди с ограниченным количеством потоков

    # async def process_urls(self, urls):
    #     queue = asyncio.Queue()

    #     # Добавляем URL в очередь
    #     for url in urls:
    #         await queue.put(url)

    #     async with ClientSession() as session:
    #         tasks = []
    #         # Запускаем указанное количество потоков
    #         for _ in range(self.max_workers):
    #             task = asyncio.create_task(self.worker(queue, session))
    #             tasks.append(task)

    #         # Ожидаем выполнения всех задач
    #         await queue.join()

    #         # Завершаем все задачи
    #         for task in tasks:
    #             task.cancel()
    #         await asyncio.gather(*tasks, return_exceptions=True)

    # # Асинхронная функция для обработки задач из очереди
    # async def worker(self, queue, session):
    #     while True:
    #         url = await queue.get()
    #         await self.fetch_and_save_html(url, session)
    #         queue.task_done()

    # # Асинхронная функция для загрузки HTML по URL и сохранения в файл
    # async def fetch_and_save_html(self, url, session):
    #     html_company = self.html_files_directory / f"{url.split('/')[-1]}.html"

    #     if html_company.exists():
    #         logger.warning(f"Файл {html_company} уже существует, пропускаем.")
    #         return
    #     logger.info(self.api_key)
    #     payload = {"api_key": self.api_key, "url": url}

    #     try:
    #         async with session.get(
    #             "https://api.scraperapi.com/", params=payload, timeout=30
    #         ) as response:
    #             if response.status == 200:
    #                 html_content = await response.text()
    #                 with open(html_company, "w", encoding="utf-8") as file:
    #                     file.write(html_content)
    #                 logger.info(f"Сохранен файл: {html_company}")
    #             else:
    #                 logger.warning(f"Ошибка {response.status} при загрузке URL: {url}")
    #     except Exception as e:
    #         logger.error(f"Ошибка при запросе {url}: {e}")
