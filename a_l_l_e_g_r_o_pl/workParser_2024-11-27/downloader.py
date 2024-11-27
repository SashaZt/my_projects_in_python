import asyncio
import json
import time
from parser import Parser

import pandas as pd
import requests
from configuration.logger_setup import logger

# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 30
RETRY_DELAY = 5  # Задержка между попытками в секундах


class Downloader:

    def __init__(
        self,
        api_key,
        html_page_directory,
        html_files_directory,
        csv_output_file,
        json_files_directory,
        url_start,
        max_workers,
    ):
        self.api_key = api_key
        self.json_files_directory = json_files_directory
        self.html_files_directory = html_files_directory
        self.html_page_directory = html_page_directory
        self.csv_output_file = csv_output_file
        self.url_start = url_start
        self.parser = Parser(
            html_files_directory, html_page_directory, csv_output_file, max_workers
        )  # Создаем экземпляр Parser

    # def get_all_page_html(self):
    #     # Скачать все страницы пагинации

    #     html_company = self.html_page_directory / "url_start.html"
    #     payload = {
    #         "api_key": self.api_key,
    #         "url": self.url_start,
    #         "ultra_premium": "true",
    #     }

    #     # Проверяем, существует ли уже файл первой страницы
    #     if html_company.exists():
    #         logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
    #         max_page = (
    #             self.parser.parsin_page()
    #         )  # Получаем max_page из существующего файла
    #     else:
    #         # Запрос к API для первой страницы
    #         r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)

    #         retries = 0
    #         while retries < MAX_RETRIES:
    #             try:
    #                 r = self.get_request()  # Замените на ваш метод выполнения запроса
    #                 if r.status_code == 200:
    #                     src = r.text
    #                     with open(html_company, "w", encoding="utf-8") as file:
    #                         file.write(src)
    #                     max_page = (
    #                         self.parser.parsin_page()
    #                     )  # Получаем max_page из существующего файла
    #                     logger.info(f"Сохранена первая страница: {html_company}")
    #                     break  # Прерываем цикл, если статус код 200
    #                 else:
    #                     logger.error(f"Ошибка при запросе страницы: {r.status_code}")
    #                     retries += 1
    #                     if retries < MAX_RETRIES:
    #                         logger.info(
    #                             f"Повторная попытка через {RETRY_DELAY} секунд..."
    #                         )
    #                         time.sleep(RETRY_DELAY)
    #             except Exception as e:
    #                 logger.error(f"Произошла ошибка: {e}")
    #                 retries += 1
    #                 if retries < MAX_RETRIES:
    #                     logger.info(f"Повторная попытка через {RETRY_DELAY} секунд...")
    #                     time.sleep(RETRY_DELAY)

    #         if retries >= MAX_RETRIES:
    #             logger.error(
    #                 "Не удалось получить статус 200 после максимального числа попыток."
    #             )
    #             return  # Выходим из функции, если все попытки не удались

    #     # Запрашиваем страницы с 2 по max_page, если max_page определен
    #     if max_page:
    #         for page in range(2, max_page + 1):
    #             html_company = self.html_page_directory / f"url_start_{page}.html"
    #             # Обновляем payload для каждой страницы
    #             payload = {"api_key": self.api_key, "url": f"{self.url_start}&p={page}"}

    #             if html_company.exists():
    #                 logger.warning(f"Файл {html_company} уже существует, пропускаем.")
    #             else:
    #                 r = requests.get(
    #                     "https://api.scraperapi.com/", params=payload, timeout=60
    #                 )

    #                 if r.status_code == 200:
    #                     src = r.text
    #                     with open(html_company, "w", encoding="utf-8") as file:
    #                         file.write(src)
    #                     logger.info(f"Сохранена страница {page}: {html_company}")
    #                 else:
    #                     logger.error(
    #                         f"Ошибка при запросе страницы {
    #                             page}: {r.status_code}"
    #                     )
    #         logger.info("Скачали все страницы пагинации")
    def get_all_page_html(self):
        """
        Скачивает все страницы пагинации до тех пор, пока количество файлов
        в директории не будет равно max_page.
        """
        payload = {
            "api_key": self.api_key,
            "url": self.url_start,
            "ultra_premium": "true",
        }

        # Проверяем первую страницу
        html_company = self.html_page_directory / "url_start.html"
        if html_company.exists():
            logger.info(f"Файл {html_company} уже существует, пропускаем загрузку.")
            max_page = self.parser.parsin_page()
        else:
            retries = 0
            while True:
                try:
                    r = requests.get(
                        "https://api.scraperapi.com/", params=payload, timeout=60
                    )
                    if r.status_code == 200:
                        src = r.text
                        with open(html_company, "w", encoding="utf-8") as file:
                            file.write(src)
                        max_page = self.parser.parsin_page()
                        logger.info(f"Сохранена первая страница: {html_company}")
                        break
                    else:
                        logger.error(
                            f"Ошибка при запросе первой страницы: {r.status_code}"
                        )
                        retries += 1
                        if retries >= MAX_RETRIES:
                            raise Exception(
                                "Превышено максимальное количество попыток."
                            )
                        logger.info(f"Повторная попытка через {RETRY_DELAY} секунд...")
                        time.sleep(RETRY_DELAY)
                except Exception as e:
                    logger.error(f"Произошла ошибка при запросе первой страницы: {e}")
                    retries += 1
                    if retries >= MAX_RETRIES:
                        raise Exception(
                            "Не удалось загрузить первую страницу после повторных попыток."
                        )
                    time.sleep(RETRY_DELAY)

        # Цикл для загрузки всех страниц до достижения max_page
        while True:
            downloaded_files = [
                f
                for f in self.html_page_directory.iterdir()
                if f.name.startswith("url_start_") and f.suffix == ".html"
            ]

            if len(downloaded_files) >= max_page:
                logger.info("Все страницы успешно загружены.")
                break

            # Определяем, какие страницы ещё нужно скачать, начиная со второй страницы
            pages_to_download = set(range(2, max_page + 1)) - {
                int(f.stem.split("_")[-1])
                for f in downloaded_files
                if f.stem.split("_")[-1].isdigit()
            }

            for page in pages_to_download:
                page_file = self.html_page_directory / f"url_start_{page}.html"
                page_payload = {
                    "api_key": self.api_key,
                    "url": f"{self.url_start}&p={page}",
                }

                retries = 0
                while True:
                    try:
                        r = requests.get(
                            "https://api.scraperapi.com/",
                            params=page_payload,
                            timeout=60,
                        )
                        if r.status_code == 200:
                            src = r.text
                            with open(page_file, "w", encoding="utf-8") as file:
                                file.write(src)
                            logger.info(f"Сохранена страница {page}: {page_file}")
                            break
                        else:
                            logger.error(
                                f"Ошибка при запросе страницы {page}: {r.status_code}"
                            )
                            retries += 1
                            if retries >= MAX_RETRIES:
                                logger.error(
                                    f"Пропущена страница {page} после {MAX_RETRIES} попыток."
                                )
                                break
                            logger.info(
                                f"Повторная попытка через {RETRY_DELAY} секунд..."
                            )
                            time.sleep(RETRY_DELAY)
                    except Exception as e:
                        logger.error(
                            f"Произошла ошибка при запросе страницы {page}: {e}"
                        )
                        retries += 1
                        if retries >= MAX_RETRIES:
                            logger.error(
                                f"Пропущена страница {page} после {MAX_RETRIES} попыток."
                            )
                            break
                        time.sleep(RETRY_DELAY)

    async def fetch_results_async(self):
        while True:
            all_finished = True
            for json_file in self.json_files_directory.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        response_data = json.load(file)
                    html_company = (
                        self.html_files_directory
                        / f"{response_data.get('url').split('/')[-1]}.html"
                    )
                    # Если файл HTML уже существует, удаляем JSON файл и пропускаем
                    if html_company.exists():
                        logger.info(
                            f"Файл {html_company} уже существует, удаляем JSON файл и пропускаем."
                        )
                        try:
                            json_file.unlink()
                        except PermissionError as e:
                            logger.error(f"Не удалось удалить файл {json_file}: {e}")
                        continue

                    status_url = response_data.get("statusUrl")
                    response = requests.get(url=status_url, timeout=30)
                    if response.status_code == 200:
                        job_status = response.json().get("status")
                        if job_status == "finished":
                            body = response.json().get("response").get("body")
                            with open(html_company, "w", encoding="utf-8") as file:
                                file.write(body)
                            logger.info(
                                f"Результаты для {status_url} сохранены в файл {html_company}"
                            )
                            # Удаление JSON файла после успешного сохранения результата
                            try:
                                json_file.unlink()
                            except PermissionError as e:
                                logger.error(
                                    f"Не удалось удалить файл {json_file}: {e}"
                                )
                        else:
                            all_finished = False
                            logger.info(f"Статус задачи для {status_url}: {job_status}")
                    else:
                        logger.error(
                            f"Ошибка при получении статуса задачи: {response.status_code}"
                        )
                except PermissionError as e:
                    logger.error(f"Не удалось открыть файл {json_file}: {e}")
            if all_finished:
                break
            # Подождите 10 секунд перед повторной проверкой
            await asyncio.sleep(10)

    # Функция для отправки задач на ScraperAPI
    def submit_jobs(self):
        urls = self.read_cities_from_csv(self.csv_output_file)
        batch_size = 40000  # Размер каждой порции URL
        # Разделяем список urls на подсписки по batch_size
        for i in range(0, len(urls), batch_size):
            url_batch = urls[i : i + batch_size]  # Берем следующую порцию до 50 000
            for url in url_batch:

                html_company = self.html_files_directory / f"{url.split('/')[-1]}.html"
                # Если файл HTML уже существует, удаляем JSON файл и пропускаем
                if html_company.exists():
                    # logger.warning(
                    #     f"Файл {html_company} уже существует, пропускаем.")
                    continue

                response = requests.post(
                    url="https://async.scraperapi.com/jobs",
                    json={"apiKey": self.api_key, "url": url},
                    timeout=30,
                )
                if response.status_code == 200:
                    response_data = response.json()
                    job_id = response_data.get("id")
                    json_file = self.json_files_directory / f"{job_id}.json"
                    with open(json_file, "w", encoding="utf-8") as file:
                        json.dump(response_data, file, indent=4)
                    logger.info(f"Задача отправлена для URL {url}")
                    # logger.info(
                    #     f"Задача отправлена для URL {url}, статус доступен по адресу: {response_data.get('statusUrl')}"
                    # )
                else:
                    logger.error(
                        f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
                    )

    # Функция для чтения городов из CSV файла

    def read_cities_from_csv(self, input_csv_file):
        df = pd.read_csv(input_csv_file)
        return df["url"].tolist()

    # Основная функция для скачивания все товаров
    async def main_url(self):
        # Проверка наличия файлов в json_files_directory
        if any(self.json_files_directory.glob("*.json")):
            # Получение результатов задач, если есть несохраненные результаты
            await self.fetch_results_async()
        else:
            # Отправка задач на ScraperAPI, если json файлов нет
            self.submit_jobs()
            # Получение результатов задач
            await self.fetch_results_async()
